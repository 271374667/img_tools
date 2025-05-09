import os
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from PIL import Image

from src.core.enums import SuperResolutionModel
from src.processor.super_resolution import SuperResolution


class TestSuperResolution:
    @pytest.fixture
    def sample_images(self, tmp_path):
        """创建测试图片供测试使用"""
        test_dir = tmp_path / "test_images"
        test_dir.mkdir()

        # 创建一个子目录用于测试递归功能
        sub_dir = test_dir / "sub_dir"
        sub_dir.mkdir()

        # 创建测试图片的辅助函数
        def create_test_image(path, size=(100, 100), color="red"):
            img = Image.new("RGB", size, color=color)
            img.save(path)
            return path

        # 在主目录创建测试图片
        jpeg_path = create_test_image(test_dir / "test1.jpg")
        png_path = create_test_image(test_dir / "test2.png")
        webp_path = create_test_image(test_dir / "test3.webp")

        # 在子目录创建一个图片
        sub_img_path = create_test_image(sub_dir / "sub_test.jpg", color="blue")

        yield {
            "dir": test_dir,
            "images": [jpeg_path, png_path, webp_path],
            "sub_dir": sub_dir,
            "sub_img": sub_img_path,
        }

        # 清理测试数据
        if test_dir.exists():
            shutil.rmtree(test_dir)

    # process方法的测试用例

    @patch("GPUtil.getFirstAvailable")
    @patch("waifu2x_ncnn_py.Waifu2x")
    def test_process_basic_upscaling(self, mock_waifu2x, mock_gpu, sample_images):
        """测试基本的超分辨率功能"""
        # 模拟GPU和waifu2x
        mock_gpu.return_value = [0]
        mock_instance = MagicMock()
        mock_waifu2x.return_value = mock_instance

        # 模拟处理后的图像（原始尺寸的2倍）
        def mock_process_pil(image):
            width, height = image.size
            return Image.new(image.mode, (width * 2, height * 2), color="green")

        mock_instance.process_pil.side_effect = mock_process_pil

        # 执行超分辨率处理
        processor = SuperResolution()
        jpeg_path = sample_images["images"][0]

        # 获取原始图像尺寸
        with Image.open(jpeg_path) as img:
            original_width, original_height = img.size

        # 执行处理
        output_path = processor.process(jpeg_path, scale=2)

        # 验证输出路径与输入相同（因为override=True）
        assert output_path == jpeg_path

        # 验证模型调用参数
        mock_waifu2x.assert_called_once_with(
            gpuid=0, scale=2, noise=0, model="upconv_7_anime"
        )

        # 验证图像尺寸已放大
        with Image.open(output_path) as img:
            assert img.width == original_width * 2
            assert img.height == original_height * 2

    @patch("GPUtil.getFirstAvailable")
    @patch("waifu2x_ncnn_py.Waifu2x")
    def test_process_with_different_models(self, mock_waifu2x, mock_gpu, sample_images):
        """测试不同超分模型的处理效果"""
        # 模拟GPU和waifu2x
        mock_gpu.return_value = [0]
        mock_instance = MagicMock()
        mock_waifu2x.return_value = mock_instance

        # 模拟处理后的图像
        mock_instance.process_pil.return_value = Image.new("RGB", (200, 200))

        processor = SuperResolution()
        png_path = sample_images["images"][1]

        # 使用不同模型处理
        processor.process(png_path, model=SuperResolutionModel.CunetPhoto)
        processor.process(png_path, model=SuperResolutionModel.UpconvAnime)
        processor.process(png_path, model=SuperResolutionModel.UpconvPhoto)

        # 验证模型参数正确传递
        assert mock_waifu2x.call_count == 3
        model_calls = [call[1]["model"] for call in mock_waifu2x.call_args_list]
        assert "cunet_photo" in model_calls
        assert "upconv_7_anime" in model_calls
        assert "upconv_7_photo" in model_calls

    @patch("GPUtil.getFirstAvailable")
    @patch("waifu2x_ncnn_py.Waifu2x")
    def test_process_without_override(self, mock_waifu2x, mock_gpu, sample_images):
        """测试不覆盖原图的情况"""
        # 模拟GPU和waifu2x
        mock_gpu.return_value = [0]
        mock_instance = MagicMock()
        mock_waifu2x.return_value = mock_instance
        mock_instance.process_pil.return_value = Image.new("RGB", (200, 200))

        processor = SuperResolution()
        webp_path = sample_images["images"][2]

        # 处理但不覆盖原图
        output_path = processor.process(webp_path, override=False)

        # 验证输出路径不同于输入路径，并包含"_out"
        assert output_path != webp_path
        assert "_out" in output_path.name

        # 验证原图和输出图都存在
        assert webp_path.exists()
        assert output_path.exists()

    # process_dir方法的测试用例

    @patch("src.processor.super_resolution.SuperResolution._process_wrapper")
    def test_process_dir_basic(self, mock_process, sample_images):
        """测试基本的目录处理功能"""
        # 模拟处理结果
        mock_process.return_value = "processed_image_path"

        processor = SuperResolution()
        test_dir = sample_images["dir"]

        # 处理目录
        output_dir = processor.process_dir(test_dir)

        # 验证返回的是原目录（因为override=True）
        assert output_dir == test_dir

        # 验证处理被调用的次数等于图片数
        assert (
            mock_process.call_count == len(sample_images["images"]) + 1
        )  # +1是子目录中的图片

    @patch("src.processor.super_resolution.SuperResolution._process_wrapper")
    def test_process_dir_recursion(self, mock_process, sample_images):
        """测试递归处理与非递归处理"""
        # 模拟处理结果
        mock_process.return_value = "processed_image_path"

        processor = SuperResolution()
        test_dir = sample_images["dir"]

        # 非递归处理
        processor.process_dir(test_dir, recursion=False)

        # 计算主目录中的图片数
        main_dir_image_count = len(sample_images["images"])

        # 验证只处理了主目录的图片
        assert mock_process.call_count == main_dir_image_count

        # 重置mock
        mock_process.reset_mock()

        # 递归处理
        processor.process_dir(test_dir, recursion=True)

        # 验证所有图片都被处理（主目录 + 子目录）
        assert mock_process.call_count == main_dir_image_count + 1  # +1是子目录中的图片

    @patch("src.processor.super_resolution.SuperResolution._process_wrapper")
    def test_process_dir_with_suffix_filter(self, mock_process, sample_images):
        """测试使用特定后缀过滤图片"""
        # 模拟处理结果
        mock_process.return_value = "processed_image_path"

        processor = SuperResolution()
        test_dir = sample_images["dir"]

        # 仅处理JPEG图片
        processor.process_dir(test_dir, suffix=(".jpg",))

        # 计算匹配后缀的图片数
        jpg_count = len(
            [p for p in sample_images["images"] if p.suffix.lower() == ".jpg"]
        )
        jpg_count += 1  # 子目录中的jpg图片

        # 验证只处理了JPEG图片
        assert mock_process.call_count == jpg_count

    @patch("src.processor.super_resolution.SuperResolution._process_wrapper")
    def test_process_dir_without_override(self, mock_process, sample_images):
        """测试不覆盖原目录的情况"""
        # 模拟处理结果
        mock_process.return_value = "processed_image_path"

        processor = SuperResolution()
        test_dir = sample_images["dir"]

        # 处理目录，不覆盖原目录
        output_dir = processor.process_dir(test_dir, override=False, scale=3)

        # 验证返回的是新目录
        assert output_dir != test_dir
        assert output_dir.name == f"{test_dir.name}_sr3x"

        # 验证所有图片都被处理
        assert (
            mock_process.call_count == len(sample_images["images"]) + 1
        )  # +1是子目录中的图片

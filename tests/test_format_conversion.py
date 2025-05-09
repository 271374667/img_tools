import shutil

import pytest
from PIL import Image

from src.processor.format_conversion import FormatConversion


class TestFormatConversion:
    @pytest.fixture
    def sample_images(self, tmp_path):
        """创建测试图片供测试使用"""
        test_dir = tmp_path / "test_images"
        test_dir.mkdir()

        # 创建一个子目录用于测试递归功能
        sub_dir = test_dir / "sub_dir"
        sub_dir.mkdir()

        # 创建测试图片的辅助函数
        def create_test_image(path, size=(200, 200), mode="RGB", color="red"):
            img = Image.new(mode, size, color=color)
            img.save(path)
            return path

        # 在主目录创建测试图片
        jpg_path = create_test_image(test_dir / "test1.jpg")
        png_path = create_test_image(
            test_dir / "transparent.png", mode="RGBA", color=(255, 0, 0, 128)
        )
        webp_path = create_test_image(test_dir / "test3.webp")

        # 在子目录创建一个图片
        sub_img_path = create_test_image(sub_dir / "sub_test.jpg", color="blue")

        yield {
            "dir": test_dir,
            "images": [jpg_path, png_path, webp_path],
            "sub_dir": sub_dir,
            "sub_img": sub_img_path,
        }

        # 清理测试数据
        if test_dir.exists():
            shutil.rmtree(test_dir)

    # process方法的测试用例

    def test_process_jpg_to_png(self, sample_images):
        """测试基本的格式转换功能(JPG转PNG)"""
        converter = FormatConversion()
        jpg_path = sample_images["images"][0]

        # 执行转换
        output_path = converter.process(jpg_path, target_format="png", override=True)

        # 验证输出路径正确
        assert output_path.suffix == ".png"
        assert output_path.exists()

        # 验证图片格式
        with Image.open(output_path) as img:
            assert img.format == "PNG"

    def test_process_transparent_png_to_jpg(self, sample_images):
        """测试含透明度的图片转换(透明PNG转JPG)"""
        converter = FormatConversion()
        png_path = sample_images["images"][1]

        # 验证原始PNG有透明通道
        with Image.open(png_path) as img:
            assert img.mode == "RGBA"

        # 执行转换
        output_path = converter.process(png_path, target_format="jpg", override=False)

        # 验证输出路径正确
        assert output_path.suffix == ".jpg"
        assert "_out" in output_path.name
        assert output_path.exists()

        # 验证图片格式和模式(应该没有透明通道)
        with Image.open(output_path) as img:
            assert img.format == "JPEG"
            assert img.mode == "RGB"  # 应该变成RGB模式，没有透明通道

    def test_process_without_override(self, sample_images):
        """测试不覆盖原图的情况"""
        converter = FormatConversion()
        webp_path = sample_images["images"][2]

        # 执行转换但不覆盖原图
        output_path = converter.process(webp_path, target_format="png", override=False)

        # 验证输出路径不同于原路径，并且包含"_out"
        assert output_path != webp_path
        assert "_out" in output_path.name
        assert output_path.suffix == ".png"

        # 验证原图和新图都存在
        assert webp_path.exists()
        assert output_path.exists()

    # process_dir方法的测试用例

    def test_process_dir_basic(self, sample_images):
        """测试基本的目录处理功能"""
        converter = FormatConversion()
        test_dir = sample_images["dir"]

        # 获取处理前的文件数
        original_files = list(test_dir.glob("*.*"))
        original_count = len(original_files)

        # 使用默认参数处理目录
        output_dir = converter.process_dir(test_dir, target_format="png")

        # 验证返回的是原目录（因为override=True）
        assert output_dir == test_dir

        # 验证所有文件都被转换为PNG格式
        processed_files = list(test_dir.glob("*.png"))
        assert len(processed_files) == original_count

        # 验证文件格式
        for file_path in processed_files:
            with Image.open(file_path) as img:
                assert img.format == "PNG"

    def test_process_dir_recursion(self, sample_images):
        """测试递归处理与非递归处理"""
        converter = FormatConversion()
        test_dir = sample_images["dir"]
        sub_img_path = sample_images["sub_img"]

        # 非递归处理（不处理子目录）
        converter.process_dir(test_dir, target_format="webp", recursion=False)

        # 验证子目录图片未被修改
        assert sub_img_path.suffix == ".jpg"  # 子目录图片仍为jpg

        # 递归处理（包括子目录）
        converter.process_dir(test_dir, target_format="webp", recursion=True)

        # 验证子目录图片被处理
        converted_sub_img = sub_img_path.with_suffix(".webp")
        assert converted_sub_img.exists()
        with Image.open(converted_sub_img) as img:
            assert img.format == "WEBP"

    def test_process_dir_without_override(self, sample_images):
        """测试不覆盖原文件的目录处理"""
        converter = FormatConversion()
        test_dir = sample_images["dir"]

        # 获取原始文件
        original_files = list(test_dir.glob("*.*"))

        # 不覆盖原文件处理目录
        output_dir = converter.process_dir(
            test_dir, target_format="bmp", override=False
        )

        # 验证创建了新目录
        assert output_dir != test_dir
        assert output_dir.name == f"{test_dir.name}_bmp"
        assert output_dir.exists()

        # 验证原目录文件未变更
        for file_path in original_files:
            assert file_path.exists()

        # 验证输出目录包含BMP格式文件
        bmp_files = list(output_dir.glob("**/*.bmp"))
        assert len(bmp_files) > 0

        # 验证文件格式
        for bmp_path in bmp_files:
            with Image.open(bmp_path) as img:
                assert img.format == "BMP"

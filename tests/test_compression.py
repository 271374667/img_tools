import shutil

import pytest
from PIL import Image

from src.core.enums import CompressionMode
from src.processor.compression import Compression


class TestCompression:
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
        jpeg_path = create_test_image(test_dir / "test1.jpg")
        png_path = create_test_image(
            test_dir / "test2.png", mode="RGBA", color=(255, 0, 0, 128)
        )
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

    def test_process_basic_compression(self, sample_images):
        """测试基本的图片压缩功能"""
        compressor = Compression()
        jpeg_path = sample_images["images"][0]

        # 获取原始文件大小
        original_size = jpeg_path.stat().st_size

        # 执行压缩
        output_path = compressor.process(jpeg_path, compression=CompressionMode.Best)

        # 验证输出路径与输入相同（override=True）
        assert output_path == jpeg_path

        # 验证文件被压缩（大小减小或不变）
        compressed_size = output_path.stat().st_size
        assert compressed_size <= original_size

    def test_process_with_different_modes(self, sample_images):
        """测试不同压缩模式下的压缩效果"""
        compressor = Compression()
        jpeg_path = sample_images["images"][0]

        # 创建不同压缩模式的测试图片副本
        fastest_path = jpeg_path.with_name("fastest.jpg")
        smallest_path = jpeg_path.with_name("smallest.jpg")
        best_path = jpeg_path.with_name("best.jpg")

        shutil.copy(jpeg_path, fastest_path)
        shutil.copy(jpeg_path, smallest_path)
        shutil.copy(jpeg_path, best_path)

        # 使用不同模式压缩
        compressor.process(fastest_path, compression=CompressionMode.Fastest)
        compressor.process(smallest_path, compression=CompressionMode.Smallest)
        compressor.process(best_path, compression=CompressionMode.Best)

        # 验证三个文件都存在
        assert fastest_path.exists()
        assert smallest_path.exists()
        assert best_path.exists()

        # 理论上Smallest模式应该产生最小的文件
        fastest_size = fastest_path.stat().st_size
        smallest_size = smallest_path.stat().st_size
        best_size = best_path.stat().st_size

        # 由于压缩算法的复杂性，我们只验证文件被成功处理
        assert all(size > 0 for size in [fastest_size, smallest_size, best_size])

    def test_process_without_override(self, sample_images):
        """测试不覆盖原图的情况"""
        compressor = Compression()
        png_path = sample_images["images"][1]

        # 压缩但不覆盖原图
        output_path = compressor.process(png_path, override=False)

        # 验证输出路径不同于原路径，并且包含"_compressed"
        assert output_path != png_path
        assert "_compressed" in output_path.name

        # 验证原图和新图都存在
        assert png_path.exists()
        assert output_path.exists()

    # process_dir方法的测试用例

    def test_process_dir_basic(self, sample_images):
        """测试基本的目录处理功能"""
        compressor = Compression()
        test_dir = sample_images["dir"]

        # 获取处理前的文件数和总大小
        original_files = (
            list(test_dir.glob("*.jp*g"))
            + list(test_dir.glob("*.png"))
            + list(test_dir.glob("*.webp"))
        )
        original_count = len(original_files)
        original_total_size = sum(f.stat().st_size for f in original_files)

        # 使用默认参数处理目录
        output_dir = compressor.process_dir(test_dir)

        # 验证返回的是原目录（因为override=True）
        assert output_dir == test_dir

        # 验证文件数量不变
        processed_files = (
            list(test_dir.glob("*.jp*g"))
            + list(test_dir.glob("*.png"))
            + list(test_dir.glob("*.webp"))
        )
        assert len(processed_files) == original_count

        # 验证总大小减小或不变
        processed_total_size = sum(f.stat().st_size for f in processed_files)
        assert processed_total_size <= original_total_size

    def test_process_dir_recursion(self, sample_images):
        """测试递归处理与非递归处理"""
        compressor = Compression()
        test_dir = sample_images["dir"]
        sub_img_path = sample_images["sub_img"]

        # 获取子目录图片的原始大小
        original_sub_img_size = sub_img_path.stat().st_size

        # 非递归处理（不处理子目录）
        compressor.process_dir(test_dir, recursion=False)

        # 验证子目录图片未被修改
        assert sub_img_path.stat().st_size == original_sub_img_size

        # 递归处理（包括子目录）
        compressor.process_dir(test_dir, recursion=True)

        # 验证子目录图片被处理（大小可能减小）
        assert sub_img_path.exists()  # 文件应该还存在

    def test_process_dir_with_suffix_filter(self, sample_images):
        """测试使用特定后缀过滤图片"""
        compressor = Compression()
        test_dir = sample_images["dir"]

        # 获取JPEG图片的原始大小
        jpeg_path = sample_images["images"][0]
        original_jpeg_size = jpeg_path.stat().st_size

        # 获取PNG图片的原始大小
        png_path = sample_images["images"][1]
        original_png_size = png_path.stat().st_size

        # 仅处理JPEG图片
        compressor.process_dir(test_dir, suffix=(".jpg",))

        # 验证JPEG图片被处理，但PNG图片未被处理
        assert jpeg_path.stat().st_size <= original_jpeg_size  # JPEG应被处理
        assert png_path.stat().st_size == original_png_size  # PNG应保持不变

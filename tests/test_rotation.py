import shutil
from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from src.core.enums import Orientation, RotationMode
from src.processor.rotation import Rotation


class TestRotation:
    @pytest.fixture
    def sample_dir(self, tmp_path):
        """创建临时测试目录和测试图片文件"""
        test_dir = tmp_path / "test_rotation"
        test_dir.mkdir()

        # 创建测试图片
        def create_test_image(path: Path, size=(100, 80), color="red"):
            # 创建非正方形图片以便于测试方向
            img = Image.new("RGB", size, color=color)
            draw = ImageDraw.Draw(img)
            draw.rectangle((10, 10, 30, 30), fill="blue")  # 添加标记以区分旋转效果
            img.save(path, "PNG")

        # 创建水平图片(宽>高)
        create_test_image(test_dir / "horizontal.png", size=(100, 80))
        # 创建垂直图片(高>宽)
        create_test_image(test_dir / "vertical.png", size=(80, 100))
        # 创建正方形图片(宽=高)
        create_test_image(test_dir / "square.png", size=(90, 90))

        # 创建一些子目录测试图片，用于测试递归功能
        sub_dir = test_dir / "subdir"
        sub_dir.mkdir()
        create_test_image(sub_dir / "sub_horizontal.png", size=(100, 80))
        create_test_image(sub_dir / "sub_vertical.png", size=(80, 100))

        yield test_dir

        # 清理临时文件
        if test_dir.exists():
            shutil.rmtree(test_dir)

    # process方法的测试用例
    def test_process_horizontal_to_vertical(self, sample_dir):
        """测试将水平图片旋转为垂直方向"""
        rotator = Rotation()
        img_path = sample_dir / "horizontal.png"

        # 获取原始尺寸
        with Image.open(img_path) as img:
            original_width, original_height = img.size
            assert original_width > original_height  # 确认初始是水平的

        # 执行旋转
        output_path = rotator.process(
            img_path=img_path,
            orientation=Orientation.Vertical,
            rotation_mode=RotationMode.Clockwise,
            override=False,
        )

        # 验证结果
        assert output_path.exists()
        assert output_path.name == "horizontal_out.png"

        # 验证旋转后图片尺寸和方向
        with Image.open(output_path) as rotated_img:
            new_width, new_height = rotated_img.size
            assert new_height > new_width  # 确认旋转后是垂直的
            # 检查宽高是否交换(旋转90度后，宽变高，高变宽)
            assert new_width == original_height
            assert new_height == original_width

    def test_process_vertical_no_rotation_needed(self, sample_dir):
        """测试垂直图片已经符合要求，不需要旋转"""
        rotator = Rotation()
        img_path = sample_dir / "vertical.png"

        # 获取原始尺寸
        with Image.open(img_path) as img:
            original_width, original_height = img.size
            assert original_height > original_width  # 确认初始是垂直的

        # 执行操作(目标也是垂直)
        output_path = rotator.process(
            img_path=img_path, orientation=Orientation.Vertical, override=True
        )

        # 验证结果 - 应该与原始路径相同，因为不需要旋转且override=True
        assert output_path == img_path

        # 验证图片尺寸没有变化
        with Image.open(output_path) as img:
            new_width, new_height = img.size
            assert new_width == original_width
            assert new_height == original_height

    def test_process_square_image(self, sample_dir):
        """测试正方形图片处理(不应该被旋转，因为不是严格的水平或垂直)"""
        rotator = Rotation()
        img_path = sample_dir / "square.png"

        # 获取原始尺寸
        with Image.open(img_path) as img:
            original_width, original_height = img.size
            assert original_width == original_height  # 确认是正方形

        # 执行旋转(尝试转为水平方向)
        output_path = rotator.process(
            img_path=img_path, orientation=Orientation.Horizontal, override=False
        )

        # 验证结果 - 应该被复制而非旋转
        assert output_path.exists()
        assert output_path.name == "square_out.png"

        # 验证图片尺寸没有变化(正方形应该保持不变)
        with Image.open(output_path) as img:
            new_width, new_height = img.size
            assert new_width == original_width
            assert new_height == original_height

    # process_dir方法的测试用例
    def test_process_dir_with_override(self, sample_dir):
        """测试处理目录下所有图片(覆盖模式)"""
        rotator = Rotation()

        # 获取处理前文件数量
        file_count_before = len(list(sample_dir.glob("*.png")))
        assert file_count_before > 0

        # 执行目录处理
        output_dir = rotator.process_dir(
            img_dir_path=sample_dir,
            orientation=Orientation.Vertical,
            override=True,
            recursion=False,  # 仅处理根目录
        )

        # 验证返回的目录就是原目录
        assert output_dir == sample_dir

        # 验证处理前后文件数量相同(应该是覆盖而非创建新文件)
        file_count_after = len(list(sample_dir.glob("*.png")))
        assert file_count_after == file_count_before

        # 验证所有原水平图片现在都是垂直的
        for img_path in sample_dir.glob("*.png"):
            with Image.open(img_path) as img:
                width, height = img.size
                if img_path.name != "square.png":  # 排除正方形图片
                    assert height >= width  # 所有非正方形图片都应该是垂直的或正方形

    def test_process_dir_without_override(self, sample_dir):
        """测试处理目录下所有图片(非覆盖模式)"""
        rotator = Rotation()

        # 记录处理前的原始文件路径
        original_files = list(sample_dir.glob("*.png"))

        # 执行目录处理
        output_dir = rotator.process_dir(
            img_dir_path=sample_dir,
            orientation=Orientation.Horizontal,
            override=False,
            recursion=False,
        )

        # 验证创建了新目录
        assert output_dir != sample_dir
        assert output_dir.name == f"{sample_dir.name}_horizontal"
        assert output_dir.exists()

        # 验证原目录保持不变
        for file in original_files:
            assert file.exists()

        # 验证输出目录中所有图片都是水平的或正方形
        for img_path in output_dir.glob("*.png"):
            with Image.open(img_path) as img:
                width, height = img.size
                if width != height:  # 排除正方形图片
                    assert width >= height  # 所有非正方形图片都应该是水平的

    def test_process_dir_with_recursion(self, sample_dir):
        """测试递归处理子目录中的图片"""
        rotator = Rotation()

        # 获取处理前所有图片(包括子目录)
        all_files_before = list(sample_dir.glob("**/*.png"))
        sub_files_before = list((sample_dir / "subdir").glob("*.png"))
        assert len(sub_files_before) > 0  # 确保子目录有文件

        # 执行递归目录处理
        output_dir = rotator.process_dir(
            img_dir_path=sample_dir,
            orientation=Orientation.Vertical,
            override=False,
            recursion=True,  # 启用递归
        )

        # 验证创建了新目录
        assert output_dir != sample_dir
        assert output_dir.exists()

        # 验证子目录也被处理
        sub_output_dir = output_dir / "subdir"
        assert sub_output_dir.exists()

        # 验证处理后的子目录中的文件数量与原来相同
        sub_files_after = list(sub_output_dir.glob("*.png"))
        assert len(sub_files_after) == len(sub_files_before)

        # 验证所有处理后的图片(包括子目录中的)都是垂直的或正方形
        for img_path in output_dir.glob("**/*.png"):
            with Image.open(img_path) as img:
                width, height = img.size
                if width != height:  # 排除正方形图片
                    assert height >= width  # 所有非正方形图片都应该是垂直的

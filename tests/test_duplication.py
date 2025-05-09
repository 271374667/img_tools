import shutil
from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from src.processor.duplication import Duplication, DuplicationMode, SaveFileMode


# 测试数据准备工具
@pytest.fixture
def sample_dir(tmp_path):
    """创建临时测试目录和测试图片文件"""
    test_dir = tmp_path / "test_images"
    test_dir.mkdir()

    # 创建测试图片
    def create_dummy_image(path: Path, size=(100, 100), color="red"):
        img = Image.new("RGB", size, color=color)
        draw = ImageDraw.Draw(img)
        if "dup" in path.name or "copy" in path.name:
            draw.ellipse(
                (20, 20, 40, 40), fill="blue" if "v2" not in path.name else "green"
            )
        else:
            draw.rectangle((60, 60, 80, 80), fill="yellow")
        img.save(path, "PNG")

    # 创建一组测试图片
    create_dummy_image(test_dir / "image1.png", color="red")
    create_dummy_image(test_dir / "image1_duplicate.png", color="red")  # 重复图片
    create_dummy_image(test_dir / "image2.png", color="blue")  # 唯一图片
    create_dummy_image(test_dir / "image3_large.png", size=(200, 200), color="green")
    create_dummy_image(
        test_dir / "image3_small.png", size=(50, 50), color="green"
    )  # 内容相似但大小不同
    create_dummy_image(test_dir / "unique_image.png", color="purple")  # 唯一图片

    # SaveFirst/SaveLast 测试用
    create_dummy_image(test_dir / "alpha_first.png", color="cyan")
    create_dummy_image(test_dir / "zeta_last.png", color="cyan")  # alpha_first的重复项

    yield test_dir

    # 清理临时文件
    if test_dir.exists():
        shutil.rmtree(test_dir)


# 测试用例
def test_no_override_save_first(sample_dir):
    """测试非覆盖模式 + SaveFirst策略"""
    deduplicator = Duplication()
    output_path = deduplicator.process(
        img_dir=sample_dir,
        duplication_mode=DuplicationMode.Normal,
        save_file_mode=SaveFileMode.SaveFirst,
        override=False,
    )

    # 验证原目录保持不变
    assert len(list(sample_dir.iterdir())) == 8

    # 验证输出目录存在并名称正确
    assert output_path.name == f"{sample_dir.name}_deduplicated"
    assert output_path.exists()

    # 验证输出目录中的文件数量减少（去除了重复）
    assert len(list(output_path.iterdir())) < 8


def test_override_save_bigger(sample_dir):
    """测试覆盖模式 + SaveBigger策略"""
    deduplicator = Duplication()
    output_path = deduplicator.process(
        img_dir=sample_dir,
        duplication_mode=DuplicationMode.Fastest,
        save_file_mode=SaveFileMode.SaveBigger,
        override=True,
    )

    # 验证返回路径是原目录
    assert output_path == sample_dir

    # 验证原目录的文件数量减少
    assert len(list(sample_dir.iterdir())) < 8

    # 确认体积较大的文件被保留
    assert (sample_dir / "image3_large.png").exists()
    assert not (sample_dir / "image3_small.png").exists()


def test_save_last_strategy(sample_dir):
    """测试SaveLast策略"""
    deduplicator = Duplication()
    deduplicator.process(
        img_dir=sample_dir,
        duplication_mode=DuplicationMode.Best,
        save_file_mode=SaveFileMode.SaveLast,
        override=True,
    )

    # 验证按文件名排序后较后的文件被保留
    assert (sample_dir / "zeta_last.png").exists()
    assert not (sample_dir / "alpha_first.png").exists()


def test_empty_directory(tmp_path):
    """测试空目录处理"""
    empty_dir = tmp_path / "empty_dir"
    empty_dir.mkdir()

    deduplicator = Duplication()
    output_path = deduplicator.process(
        img_dir=empty_dir,
        override=False,
    )

    # 验证创建了输出目录
    assert output_path.exists()
    assert output_path.name == f"{empty_dir.name}_deduplicated"
    assert len(list(output_path.iterdir())) == 0


def test_invalid_directory():
    """测试无效目录处理"""
    invalid_dir = Path("/nonexistent/directory")
    deduplicator = Duplication()

    with pytest.raises(ValueError) as excinfo:
        deduplicator.process(img_dir=invalid_dir)

    assert "不是一个有效的目录" in str(excinfo.value)


def test_save_smaller_strategy(sample_dir):
    """测试SaveSmaller策略"""
    deduplicator = Duplication()
    deduplicator.process(
        img_dir=sample_dir,
        duplication_mode=DuplicationMode.Normal,
        save_file_mode=SaveFileMode.SaveSmaller,
        override=True,
    )

    # 验证体积较小的文件被保留
    assert (sample_dir / "image3_small.png").exists()
    assert not (sample_dir / "image3_large.png").exists()


def test_process_dir(sample_dir):
    """测试批量处理目录"""
    deduplicator = Duplication()
    output_path = deduplicator.process(
        img_dir=sample_dir,
        duplication_mode=DuplicationMode.Normal,
        save_file_mode=SaveFileMode.SaveFirst,
        override=False,
    )

    # 验证输出目录存在
    assert output_path.exists()

    # 验证输出目录中的文件数量减少（去除了重复）
    assert len(list(output_path.iterdir())) < 8

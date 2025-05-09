import multiprocessing
from pathlib import Path
from typing import Optional, Iterator

from src.core import constants


class IOuitls:
    @staticmethod
    def get_img_paths_by_dir(
        dir_path: Path, recursion: bool = True, suffix: Optional[tuple[str, ...]] = None
    ) -> list[Path]:
        """
        获取目录下所有图片文件的路径列表。

        Args:
            dir_path (Path): 目录路径。
            recursion (bool): 是否递归查找子目录中的图片文件。
            suffix (tuple[str, ...], optional): 允许的图片文件后缀名列表。
                如果为 None，则使用默认的常见图片后缀名。

        Returns:
            list[Path]: 图片文件路径列表。
        """
        img_paths = []
        img_generator = dir_path.glob("*") if not recursion else dir_path.rglob("*")
        suffix_allowed = suffix if suffix else constants.COMMON_IMAGE_SUFFIXES
        for img_path in img_generator:
            if img_path.is_file() and img_path.suffix.lower() in suffix_allowed:
                img_paths.append(img_path)
        return img_paths

    @staticmethod
    def get_optimal_process_count() -> int:
        """获取适合的进程数量"""
        # 获取系统中的CPU核心数量
        cpu_count = multiprocessing.cpu_count()
        # 计算适合的进程数量，约占80%的性能
        optimal_process_count = max(1, int(cpu_count * 0.8))
        return optimal_process_count

    @staticmethod
    def detect_new_files(directory_path: str | Path) -> Iterator[list[Path] | None]:
        """
        使用 yield 实现文件差值检测。

        第一次迭代生成器时，它会记录目录中的初始文件集并 yield None。
        第二次迭代生成器时，它会 yield 一个列表，包含新添加到目录中的文件的绝对路径。

        参数:
            directory_path (str): 要监控的文件夹路径。

        Yields:
            None: 第一次迭代时。
            list[str]: 第二次迭代时，返回新增文件的路径列表。

        Raises:
            ValueError: 如果提供的路径不是一个有效的目录。
        """
        path_obj = Path(directory_path)
        if not path_obj.is_dir():
            raise ValueError(f"提供的路径 '{directory_path}' 不是一个有效的目录。")

        # 第一次调用 next() 时执行: 记录初始文件状态
        # 使用 resolve() 获取绝对路径，确保一致性
        # glob('*') 只查找目录直属文件，不包括子目录中的文件
        initial_files = set(p.resolve() for p in path_obj.glob("*") if p.is_file())

        # 第一次 yield
        yield None

        # 第二次调用 next() 时执行: 重新获取文件列表并找出新增文件
        current_files = set(p.resolve() for p in path_obj.glob("*") if p.is_file())

        newly_added_files_paths = [f for f in (current_files - initial_files)]

        # 第二次 yield
        yield newly_added_files_paths


if __name__ == "__main__":
    io_utils = IOuitls()
    print(io_utils.get_optimal_process_count())

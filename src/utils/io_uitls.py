from pathlib import Path
from src.core import constants
from typing import Optional

class IOuitls:
    @staticmethod
    def get_img_paths_by_dir(dir_path: Path, recursion: bool = True, suffix: Optional[tuple[str, ...]] = None) -> list[Path]:
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
            if (
                img_path.is_file()
                and img_path.suffix.lower() in suffix_allowed
            ):
                img_paths.append(img_path)
        return img_paths
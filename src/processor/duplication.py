import shutil
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional, Set

import loguru
from imagededup.methods import CNN as CNNHasher
from imagededup.methods import AHash, PHash, WHash
from tqdm import tqdm

from src.core.enums import DuplicationMode, SaveFileMode
from src.processor import BaseProcessor
from src.utils.io_uitls import IOuitls

# 使用Python 3.10的语法糖
HASHER_TYPE = AHash | PHash | WHash | CNNHasher


class Duplication(BaseProcessor):
    def process_dir(
        self,
        img_dir_path: Path | str,
        duplication_mode: DuplicationMode = DuplicationMode.Normal,
        save_file_mode: SaveFileMode = SaveFileMode.SaveFirst,
        thread_num: Optional[int] = None,
        override: bool = True,
    ) -> Path:
        """批量处理图片去重

        Args:
            img_dir_path: 需要处理的图片的目录
            duplication_mode: 选择去重算法的模式，默认为 Normal (WHash)
            save_file_mode: 决定保留哪些重复图片的规则，默认为 SaveFirst
            thread_num: 处理器数量 (进程池大小)
            override: 是否直接在原图目录中删除重复图片，默认为 True

        Returns:
            处理后图片所在的目录路径列表
        """
        img_dir_path = Path(img_dir_path)
        if not img_dir_path.exists() or not img_dir_path.is_dir():
            raise ValueError(f"提供的路径 '{img_dir_path}' 不是一个有效的目录。")

        return self.process(img_dir_path, duplication_mode, save_file_mode, override)

    def process(
        self,
        img_dir: Path | str,
        duplication_mode: DuplicationMode = DuplicationMode.Normal,
        save_file_mode: SaveFileMode = SaveFileMode.SaveFirst,
        override: bool = True,
    ) -> Path:
        """图片去重处理

        Args:
            img_dir (Path): 包含图片的目录路径。
            duplication_mode (DuplicationMode): 选择去重算法的模式。
                                               默认为 DuplicationMode.Normal (WHash)。
            save_file_mode (SaveFileMode): 当检测到重复图片时，决定保留哪一个的规则。
                                           默认为 SaveFileMode.SaveFirst。
            override (bool): 是否直接在原图目录中删除重复图片。
                             True: 直接删除，修改原目录。
                             False: 不修改原目录，而是创建一个新的目录 (例如 img_dir_deduplicated)
                                    存放去重后的图片。默认为 True。

        Returns:
            Path: 处理后图片所在的目录路径。
                  如果 override 为 True，则返回原始的 img_dir。
                  如果 override 为 False，则返回新创建的去重图片目录的路径。

        Raises:
            ValueError: 如果 img_dir 不是一个有效的目录。
        """
        img_dir = Path(img_dir)
        if not img_dir.is_dir():
            raise ValueError(f"提供的路径 '{img_dir}' 不是一个有效的目录。")

        hasher = self._get_hasher(duplication_mode)

        # 编码图片
        encodings = hasher.encode_images(image_dir=str(img_dir))

        if not encodings:
            # 如果没有图片或无法编码图片
            if not override:
                # 如果不覆盖且没有图片，创建一个空的 "_deduplicated" 文件夹
                output_path = img_dir.parent / f"{img_dir.name}_deduplicated"
                output_path.mkdir(parents=True, exist_ok=True)
                return output_path
            return img_dir  # 如果覆盖且无图片，原目录不变

        # 查找重复项
        raw_duplicates = hasher.find_duplicates(encoding_map=encodings)

        if not raw_duplicates:
            # 没有找到重复项
            if not override:
                # 没有重复项，但需要复制到新目录
                output_path = img_dir.parent / f"{img_dir.name}_deduplicated"
                if output_path.exists():  # 如果目标目录已存在，先清空
                    shutil.rmtree(output_path)
                shutil.copytree(img_dir, output_path)  # 复制整个目录树
                return output_path
            return img_dir  # 无重复，覆盖模式，原目录不变

        # 处理重复项
        files_to_remove_set = self._resolve_duplicates(
            img_dir, raw_duplicates, save_file_mode
        )

        if override:
            # 直接删除原目录中的重复文件
            for file_to_delete in files_to_remove_set:
                if file_to_delete.exists():
                    try:
                        file_to_delete.unlink()
                    except OSError as e:
                        raise OSError(f"删除文件 {file_to_delete.name} 失败: {e}")
            return img_dir
        else:
            # 创建新目录并复制非重复文件
            final_output_path = img_dir.parent / f"{img_dir.name}_deduplicated"

            if final_output_path.exists():
                shutil.rmtree(final_output_path)
            final_output_path.mkdir(parents=True, exist_ok=True)

            # 批量复制非重复文件（性能优化：减少单文件复制次数）
            file_list = [
                item
                for item in img_dir.iterdir()
                if item.is_file() and item not in files_to_remove_set
            ]

            for item in file_list:
                try:
                    shutil.copy2(item, final_output_path / item.name)
                except shutil.Error as e:
                    raise OSError(f"复制文件 {item.name} 时出错: {e}")

            return final_output_path

    def _get_hasher(self, duplication_mode: DuplicationMode) -> HASHER_TYPE:
        """
        根据去重模式获取对应的哈希器实例。
        私有方法。
        """
        # match语句是Python 3.10的新特性
        match duplication_mode:
            case DuplicationMode.Fastest:
                return AHash(verbose=False)
            case DuplicationMode.Normal:
                return WHash(verbose=False)
            case DuplicationMode.Best:
                return PHash(verbose=False)
            case DuplicationMode.CNN:
                return CNNHasher(verbose=False)
            case _:
                raise ValueError(f"未知的去重模式: {duplication_mode}")

    def _resolve_duplicates(
        self,
        img_dir: Path,
        raw_duplicates: Dict[str, List[str]],
        save_file_mode: SaveFileMode,
    ) -> Set[Path]:
        """
        根据指定的保存模式，在每个检测到的重复组中确定要保留的文件，
        并返回一个包含所有应删除文件的集合。

        Args:
            img_dir: 图片所在的目录。
            raw_duplicates: imagededup库找到的重复项字典。
                           键是作为"基准"的文件名，值是其重复文件名列表。
            save_file_mode: 文件保存模式。

        Returns:
            一个包含应被删除的图片文件绝对路径的集合。
        """
        files_to_delete_final: Set[Path] = set()

        for main_file_rel_path, duplicate_files_rel_paths in raw_duplicates.items():
            # 构建此重复组中所有文件的完整路径列表
            current_group_paths = [img_dir / main_file_rel_path] + [
                img_dir / rel_path for rel_path in duplicate_files_rel_paths
            ]

            # 确保所有路径都实际存在且为文件
            current_group_paths = [
                p for p in current_group_paths if p.exists() and p.is_file()
            ]

            if not current_group_paths:
                continue  # 如果组为空或文件不存在，则跳过

            # 初始化一个列表来保存要保留的文件
            files_to_keep: List[Path] = []

            # 使用match语句选择保留文件的策略
            match save_file_mode:
                case SaveFileMode.SaveFirst:
                    files_to_keep = [
                        sorted(current_group_paths, key=lambda p: p.name)[0]
                    ]
                case SaveFileMode.SaveLast:
                    files_to_keep = [
                        sorted(current_group_paths, key=lambda p: p.name)[-1]
                    ]
                case SaveFileMode.SaveFirstAndLast:
                    sorted_files = sorted(current_group_paths, key=lambda p: p.name)
                    # 如果只有一个文件，就只保留它
                    if len(sorted_files) == 1:
                        files_to_keep = [sorted_files[0]]
                    else:
                        files_to_keep = [sorted_files[0], sorted_files[-1]]
                case SaveFileMode.SaveBigger:
                    files_to_keep = [
                        max(current_group_paths, key=lambda p: p.stat().st_size)
                    ]
                case SaveFileMode.SaveSmaller:
                    files_to_keep = [
                        min(current_group_paths, key=lambda p: p.stat().st_size)
                    ]
                case _:
                    raise ValueError(f"未知的保存文件模式: {save_file_mode}")

            # 将组内除了要保留的文件之外的所有其他文件添加到待删除集合
            files_to_delete_final.update(
                file_path
                for file_path in current_group_paths
                if file_path not in files_to_keep  # 使用 not in 而不是 !=
            )

        return files_to_delete_final


if __name__ == "__main__":
    d = Duplication()
    d.process(
        r"G:\CrawlData\kemono\urethra insert\[Zerodo-Degree123]_Modification_of_common_sense_(Lize_Helesta)",
        DuplicationMode.Fastest,
        override=False,
    )

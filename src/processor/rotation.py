import shutil
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Optional, Tuple

from PIL import Image
from src.core.enums import Orientation, RotationMode
from src.processor import BaseProcessor
from src.utils.io_uitls import IOuitls
from tqdm import tqdm


class Rotation(BaseProcessor):
    """
    一个用于根据指定的方向和模式旋转图片的类。
    """

    def process_dir(
        self,
        img_dir_path: Path | str,
        orientation: Orientation,
        rotation_mode: RotationMode = RotationMode.Clockwise,
        thread_num: Optional[int] = None,
        recursion: bool = True,
        suffix: Optional[tuple[str, ...]] = None,
        override: bool = True,
    ) -> Path:
        """批量旋转图片"""
        img_dir_path = Path(img_dir_path)
        thread_num = thread_num if thread_num else IOuitls.get_optimal_process_count()

        if not img_dir_path.exists() or not img_dir_path.is_dir():
            raise ValueError(f"图片目录 '{img_dir_path}' 不存在或不是一个目录。")

        # 获取目录下所有图片文件路径
        img_paths = IOuitls.get_img_paths_by_dir(img_dir_path, recursion, suffix)

        # 确定输出目录
        output_dir = (
            img_dir_path
            if override
            else img_dir_path.with_name(f"{img_dir_path.stem}_{orientation.value}")
        )

        # 如果不是覆盖模式，需要预先创建输出目录结构
        if not override:
            output_dir.mkdir(exist_ok=True)
            # 复制子目录结构
            if recursion:
                for img_path in img_paths:
                    # 计算相对路径，保持目录结构
                    rel_path = img_path.relative_to(img_dir_path)
                    # 确保目标目录的父目录存在
                    target_dir = output_dir / rel_path.parent
                    target_dir.mkdir(parents=True, exist_ok=True)

        # 使用线程池而不是进程池（避免序列化问题）
        from concurrent.futures import ThreadPoolExecutor

        results = []
        with ThreadPoolExecutor(max_workers=thread_num) as executor:
            # 准备任务参数列表
            tasks = []
            for img_path in img_paths:
                if not override:
                    rel_path = img_path.relative_to(img_dir_path)
                    target_path = output_dir / rel_path
                    tasks.append((img_path, target_path))
                else:
                    tasks.append((img_path, None))

            # 创建任务并提交
            futures = []
            for img_path, target_path in tasks:
                future = executor.submit(
                    self._process_single_image,
                    img_path=img_path,
                    orientation=orientation,
                    rotation_mode=rotation_mode,
                    override=override,
                    output_path=target_path,
                )
                futures.append(future)

            # 使用tqdm显示进度
            for future in tqdm(
                as_completed(futures), total=len(futures), desc="旋转图片", unit="张"
            ):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    print(f"处理图片时出错: {e}")

        return output_dir

    def _process_single_image(
        self,
        img_path: Path,
        orientation: Orientation,
        rotation_mode: RotationMode,
        override: bool,
        output_path: Optional[Path] = None,
    ):
        """处理单个图片（用于并行处理）"""
        try:
            return self.process(
                img_path,
                orientation=orientation,
                rotation_mode=rotation_mode,
                override=override,
                output_path=output_path,
            )
        except Exception as e:
            return f"Error processing {img_path}: {e}"

    def process(
        self,
        img_path: Path | str,
        orientation: Orientation,  # 目标方向
        rotation_mode: RotationMode = RotationMode.Clockwise,
        override: bool = True,
        output_path: Optional[Path] = None,
    ) -> Optional[Path]:
        """旋转图片

        Args:
            img_path: 图片路径。
            orientation: 目标旋转方向 (Vertical 或 Horizontal)。
            rotation_mode: 旋转模式 (Clockwise 或 CounterClockwise)。
            override: 是否覆盖原图 (True 则修改原图，False 则保存为带 `_out` 后缀的新文件)。
            output_path: 指定输出路径（当递归处理目录时使用）

        Returns:
            处理后的图片路径；如果处理成功。

        Raises:
            FileNotFoundError: 如果图片文件不存在。
            ValueError: 如果提供的路径不是文件。
            Exception: 如果处理过程中出现其他错误。
        """
        img_path = Path(img_path)
        if not img_path.exists():
            raise FileNotFoundError(f"图片路径 '{img_path}' 不存在。")
        if not img_path.is_file():
            raise ValueError(f"提供的路径 '{img_path}' 不是一个文件。")

        # 获取图片尺寸
        width, height = self._get_image_dimensions(img_path)

        # 根据严格不等判断当前朝向
        is_currently_horizontal = width > height
        is_currently_vertical = height > width
        # 正方形图片 (width == height) 在此定义下既不是严格横向也不是严格纵向。

        needs_rotation = False
        match orientation:
            case Orientation.Horizontal:
                # 如果目标是横向 且 当前是严格纵向，则需要旋转
                if is_currently_vertical:
                    needs_rotation = True
            case Orientation.Vertical:
                # 如果目标是纵向 且 当前是严格横向，则需要旋转
                if is_currently_horizontal:
                    needs_rotation = True

        final_path: Path
        if override:
            final_path = img_path
        else:
            # 如果指定了输出路径，则使用指定路径
            if output_path:
                final_path = output_path
            else:
                # 在扩展名之前创建带有 "_out" 后缀的新路径
                new_stem = img_path.stem + "_out"
                final_path = img_path.with_stem(new_stem)  # pathlib 会正确处理后缀

        if needs_rotation:
            success = self._perform_rotation_and_save(
                img_path, final_path, rotation_mode
            )
            if not success:
                raise RuntimeError(f"旋转并保存图片 '{img_path}' 失败。")
            return final_path
        else:
            # 不需要旋转
            if override:
                # 如果覆盖且不需要旋转，则原文件保持不变，即为结果。
                return img_path
            else:
                # 如果不覆盖且不需要旋转，则将原文件复制到新的路径。
                success = self._copy_file(img_path, final_path)
                if not success:
                    raise RuntimeError(f"复制 '{img_path}' 到 '{final_path}' 失败。")
                return final_path

    def _get_image_dimensions(self, img_path: Path) -> Tuple[int, int]:
        """
        私有方法：加载图片并获取其尺寸。

        Args:
            img_path: 图片文件的路径。

        Returns:
            一个包含 (宽度, 高度) 的元组。

        Raises:
            FileNotFoundError: 如果文件不存在。
            Exception: 如果无法处理图片。
        """
        with Image.open(img_path) as img:
            return img.width, img.height

    def _perform_rotation_and_save(
        self,
        original_img_path: Path,
        target_save_path: Path,
        rotation_mode: RotationMode,
    ) -> bool:
        """
        私有方法：执行图片旋转并保存。

        Args:
            original_img_path: 原始图片的路径。
            target_save_path: 旋转后图片应保存的路径。
            rotation_mode: 旋转模式 (顺时针或逆时针)。

        Returns:
            如果旋转和保存成功则返回 True，否则返回 False。

        Raises:
            FileNotFoundError: 如果原始文件不存在。
            Exception: 如果旋转或保存过程中出现错误。
        """
        with Image.open(original_img_path) as img:
            rotated_img: Optional[Image.Image] = None
            match rotation_mode:
                case RotationMode.Clockwise:
                    # Pillow的 transpose(Image.Transpose.ROTATE_270) 是顺时针旋转90度
                    rotated_img = img.transpose(Image.Transpose.ROTATE_270)
                case RotationMode.CounterClockwise:
                    # Pillow的 transpose(Image.Transpose.ROTATE_90) 是逆时针旋转90度
                    rotated_img = img.transpose(Image.Transpose.ROTATE_90)

            if rotated_img:
                # 确保图片模式适合保存 (例如，JPEG不支持alpha通道)
                # 如果目标是JPEG且图像有Alpha通道(RGBA)或调色板透明(P)，则转换为RGB
                save_suffix_lower = target_save_path.suffix.lower()
                if save_suffix_lower in [".jpg", ".jpeg"]:
                    if rotated_img.mode == "RGBA" or (
                        rotated_img.mode == "P" and "transparency" in rotated_img.info
                    ):
                        rotated_img = rotated_img.convert("RGB")

                # 为了确保目录存在
                target_save_path.parent.mkdir(parents=True, exist_ok=True)
                rotated_img.save(target_save_path)
                return True
            return False  # 如果图片未能成功打开或处理

    def _copy_file(self, source_path: Path, destination_path: Path) -> bool:
        """
        私有方法：复制文件。

        Args:
            source_path: 源文件的路径。
            destination_path: 目标文件的路径。

        Returns:
            如果复制成功则返回 True，否则返回 False。

        Raises:
            Exception: 如果文件复制过程出现任何错误。
        """
        # 为了确保目录存在
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination_path)  # copy2 会保留元数据
        return True


if __name__ == "__main__":
    r = Rotation()
    print(
        r.process(
            Path(r"G:\CrawlData\kemono\RoundsChen\PIC2024.02\0011.jpg"),
            Orientation.Vertical,
        )
    )

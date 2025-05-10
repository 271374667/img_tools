from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from PIL import Image, UnidentifiedImageError
from tqdm import tqdm

from src.core.enums import CompressionMode
from src.processor import BaseProcessor
from src.utils.io_uitls import IOuitls


class Compression(BaseProcessor):
    # 新增的辅助方法，替代原先的嵌套函数
    def process_dir(
        self,
        img_dir_path: Path | str,
        compression: CompressionMode = CompressionMode.Best,
        thread_num: Optional[int] = None,
        recursion: bool = True,
        suffix: Optional[tuple[str, ...]] = None,
        override: bool = True,
    ) -> Path:
        """批量压缩图片

        Args:
            img_dir_path: 图片文件夹路径列表
            compression: 压缩模式
            thread_num: 处理器数量 (进程池大小)
            recursion: 是否递归查找子目录中的图片文件
            suffix: 允许的图片文件后缀名列表(不填则使用默认的常见图片后缀名)
            override: 是否覆盖原图(True 则修改原图，False 则保存为带 `_out` 后缀的新文件)

        Returns:
            处理后的图片所在目录路径
        """
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
            else img_dir_path.with_name(img_dir_path.stem + f"_{compression.value}")
        )

        # 如果不覆盖原文件，则创建输出目录(若已存在则先删除)
        if not override:
            import shutil

            if output_dir.exists():
                shutil.rmtree(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

            # 记录一下原图片路径
            detect_new_file_generator = IOuitls.detect_new_files(img_dir_path)
            next(detect_new_file_generator)  # 第一次迭代，记录初始文件集

        with ProcessPoolExecutor(max_workers=thread_num) as executor:
            # 提交所有任务到进程池，传递输出目录参数
            futures = [
                executor.submit(
                    Compression._process_wrapper,
                    img_path,
                    compression,
                    override,
                    output_dir
                    if not override
                    else None,  # 只在非覆盖模式下传递输出目录
                )
                for img_path in img_paths
            ]

            # 使用tqdm创建进度条
            results = []
            for future in tqdm(
                as_completed(futures), total=len(futures), desc="压缩图片", unit="张"
            ):
                result = future.result()
                # 如果结果是错误消息，则打印出来
                if isinstance(result, str) and result.startswith("Error"):
                    print(result)
                results.append(result)

        return output_dir

    def process(
        self,
        img_path: Path | str,
        compression: CompressionMode = CompressionMode.Best,
        override: bool = True,
    ) -> Optional[Path]:
        """压缩图片

        Args:
            img_path: 图片路径
            compression: 压缩模式
            override: 是否覆盖原图
        Returns:
            压缩后的图片路径
        """
        img_path = Path(img_path)

        if not img_path.exists() or not img_path.is_file():
            raise FileNotFoundError(f"图片未找到: {img_path}")

        try:
            img = Image.open(img_path)
            img.load()  # 确保图像数据已加载以访问格式和模式

            original_format = img.format  # 获取格式的最可靠方式
            if not original_format:  # 如果Pillow无法确定格式则使用后备方案
                original_format = img_path.suffix[1:].upper()

            if not original_format:  # 如果仍然没有格式，无法继续
                img.close()
                raise ValueError(f"无法确定图像格式: {img_path}")

        except (IOError, UnidentifiedImageError) as e:
            raise ValueError(f"无法打开或读取图像文件: {img_path}. 错误: {e}")

        # 处理图像副本以避免更改原始PIL Image对象
        current_img = img.copy()

        output_path, target_format = self._determine_target_format_and_path(
            current_img, img_path, original_format, compression, override
        )

        prepared_img = self._prepare_image_for_saving(current_img, target_format)

        save_options = self._get_save_options(
            prepared_img, target_format, compression, original_format
        )

        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            prepared_img.save(output_path, format=target_format, **save_options)
        except Exception as e:
            # 如果主要保存尝试失败，则使用后备策略
            try:
                # 从原始加载的图像创建新副本用于后备
                fallback_img = img.copy()
                has_alpha_fallback = fallback_img.mode in ("RGBA", "LA") or (
                    fallback_img.mode == "P" and "transparency" in fallback_img.info
                )

                # 根据图像是否有透明通道选择后备格式和配置
                if has_alpha_fallback:
                    # 如果图像有透明度，则后备到PNG
                    fallback_target_format = "PNG"
                    fallback_output_path = output_path.with_suffix(".png")
                    if fallback_img.mode not in ["RGBA", "LA"]:  # 确保模式合适
                        fallback_img = fallback_img.convert("RGBA")
                    # 对后备PNG使用"Best"模式选项
                    fallback_options = self._get_save_options(
                        fallback_img,
                        fallback_target_format,
                        CompressionMode.Best,
                        original_format,
                    )
                else:
                    # 如果没有透明度，则后备到JPEG
                    fallback_target_format = "JPEG"
                    fallback_output_path = output_path.with_suffix(".jpg")
                    if fallback_img.mode != "RGB":
                        fallback_img = fallback_img.convert("RGB")
                    # 对后备JPEG使用"Best"模式选项
                    fallback_options = self._get_save_options(
                        fallback_img,
                        fallback_target_format,
                        CompressionMode.Best,
                        original_format,
                    )

                fallback_output_path.parent.mkdir(parents=True, exist_ok=True)
                fallback_img.save(
                    fallback_output_path,
                    format=fallback_target_format,
                    **fallback_options,
                )
                output_path = fallback_output_path  # 更新为成功的路径
            except Exception as e_fallback:
                # 如果所有尝试都失败，关闭原始图像
                img.close()
                raise IOError(
                    f"保存图像失败 {img_path} (目标格式: {target_format}, 选项: {save_options}). "
                    f"后备尝试也失败: {e_fallback}"
                ) from e
        finally:
            # 确保原始打开的图像已关闭
            img.close()
            # 副本(current_img, prepared_img)将被垃圾回收
            return output_path

    def _process_single_image(
        self, img_path, compression=CompressionMode.Best, override=True, output_dir=None
    ):
        try:
            img_path = Path(img_path)
            if override:
                return self.process(
                    img_path, compression=compression, override=override
                )
            else:
                # 如果提供了输出目录，计算相对于原始目录的路径
                if output_dir:
                    # 计算目标路径保持原始相对路径结构
                    rel_path = img_path.name  # 只保留文件名
                    target_path = output_dir / rel_path

                    # 处理图片
                    result = self.process(
                        img_path, compression=compression, override=False
                    )

                    # 确保目标目录存在
                    target_path.parent.mkdir(parents=True, exist_ok=True)

                    # 移动处理后的文件到目标位置
                    import shutil

                    shutil.copy2(result, target_path)
                    # 删除临时文件
                    if result.exists():
                        result.unlink()

                    return target_path
                else:
                    return self.process(
                        img_path, compression=compression, override=False
                    )
        except Exception as e:
            return f"Error processing {img_path}: {e}"

    @staticmethod
    def _process_wrapper(
        img_path, compression=CompressionMode.Best, override=True, output_dir=None
    ):
        # 创建新实例确保线程安全
        processor = Compression()
        return processor._process_single_image(img_path, compression, override, output_dir)


    def _determine_target_format_and_path(
        self,
        img: Image.Image,  # PIL Image对象
        img_path: Path,  # 原始图像路径
        original_format: str,  # 确定的原始格式（如"JPEG"、"PNG"）
        compression: CompressionMode,
        override: bool,
    ) -> Tuple[Path, str]:
        """
        根据压缩模式确定目标图像格式和输出路径。
        对于"Smallest"模式，如果有益，可能会将格式更改为WebP。
        """
        target_format = original_format

        # 对于"Smallest"模式，考虑将PNG/JPEG/BMP/TIFF转换为WebP
        # 前提是图像模式适合WebP（RGB, RGBA, L）
        if (
            compression == CompressionMode.Smallest
            and original_format in ["PNG", "JPEG", "BMP", "TIFF"]
            and img.mode in ["RGB", "RGBA", "L"]
        ):
            target_format = "WEBP"

        # 确定输出路径
        if override:
            output_path = img_path
            # 如果因优化而更改格式（例如，更改为WebP）并且覆盖原始文件，
            # 则更新原始路径的后缀。
            if target_format.lower() != original_format.lower():
                output_path = img_path.with_suffix(f".{target_format.lower()}")
        else:
            # 用"_compressed"和目标格式的后缀创建新名称。
            output_path = img_path.with_name(
                f"{img_path.stem}_compressed.{target_format.lower()}"
            )

        return output_path, target_format.upper()

    def _prepare_image_for_saving(
        self, img: Image.Image, target_format: str
    ) -> Image.Image:
        """
        准备保存图像，主要处理模式转换
        （例如，如果保存为JPEG，则将RGBA转换为RGB）。
        """
        # 使用match语句处理不同格式的转换逻辑
        match target_format:
            case "JPEG":
                # 处理透明度：如果保存为JPEG，则将RGBA/P转换为RGB
                if img.mode == "RGBA" or (
                    img.mode == "P" and "transparency" in img.info
                ):
                    return img.convert("RGB")

            case "PNG" | "WEBP":
                # 如果图像是调色板(P模式)并且有透明度，
                # 且目标格式是PNG或WEBP，则转换为RGBA以保留透明度
                if img.mode == "P" and "transparency" in img.info:
                    return img.convert("RGBA")

        return img  # 如果不需要转换，则返回原始图像

    def _get_save_options(
        self,
        img: Image.Image,  # 图像对象（可能在_prepare_image_for_saving之后）
        target_format: str,
        compression: CompressionMode,
        original_format: str,  # 输入文件的格式，用于WebP无损决策
    ) -> Dict[str, Any]:
        """
        根据目标格式、压缩模式和原始图像特性，
        确定Pillow的save()方法的保存选项字典。
        """
        # 使用字典查表优化各格式的基本设置
        format_base_options: Dict[str, Dict[str, Any]] = {
            "JPEG": {"optimize": True},
            "PNG": {"optimize": True},
            "TIFF": {"compression": "tiff_lzw"},
        }

        # 为不同格式和压缩模式创建配置表
        format_compression_options: Dict[str, Dict[CompressionMode, Dict[str, Any]]] = {
            "JPEG": {
                CompressionMode.Fastest: {"quality": 85},
                CompressionMode.Smallest: {"quality": 60, "progressive": True},
                CompressionMode.Best: {"quality": 75, "progressive": True},
            },
            "PNG": {
                CompressionMode.Fastest: {"compress_level": 1},
                CompressionMode.Smallest: {"compress_level": 9},
                CompressionMode.Best: {"compress_level": 7},
            },
        }

        # 初始化基本选项
        options = format_base_options.get(target_format, {}).copy()

        # 如果有特定压缩模式的选项，添加它们
        if target_format in format_compression_options:
            options.update(format_compression_options[target_format][compression])

        # WebP需要特殊处理，因为选项取决于图像模式和原始格式
        if target_format == "WEBP":
            options.update(self._get_webp_options(img, compression, original_format))

        return options

    def _get_webp_options(
        self, img: Image.Image, compression: CompressionMode, original_format: str
    ) -> Dict[str, Any]:
        """为WebP格式获取最佳保存选项"""
        has_alpha = img.mode == "RGBA" or (
            img.mode == "P" and "transparency" in img.info
        )

        if has_alpha:
            # 有透明通道的WebP基本设置
            options = {"lossless": False, "exact": True, "alpha_quality": 85}

            # 根据压缩模式应用不同配置
            match compression:
                case CompressionMode.Fastest:
                    options.update({"quality": 85, "method": 0, "alpha_quality": 90})
                case CompressionMode.Smallest:
                    options.update({"quality": 70, "method": 6, "alpha_quality": 70})
                case CompressionMode.Best:
                    options.update({"quality": 80, "method": 4, "alpha_quality": 85})
        else:
            # 无透明通道时，根据原格式决定是否使用无损WebP
            use_lossless = (
                original_format == "PNG" and compression != CompressionMode.Smallest
            )

            if use_lossless:
                options = {"lossless": True, "method": 4}
                if compression == CompressionMode.Fastest:
                    options["method"] = 0
            else:
                options = {"lossless": False, "quality": 80, "method": 4}
                match compression:
                    case CompressionMode.Fastest:
                        options.update({"quality": 85, "method": 0})
                    case CompressionMode.Smallest:
                        options.update({"quality": 70, "method": 6})

        return options


if __name__ == "__main__":
    c = Compression()
    # print(c.process(Path(r"G:\CrawlData\kemono\RoundsChen\PIC2024.02\dif_01.jpg")))
    print(c.process_dir(r"G:\CrawlData\kemono\RoundsChen\PIC2024.02", override=False))

from pathlib import Path
from typing import Literal, Final
from PIL import Image
from src.processor import BaseProcessor

# 定义支持的图片格式和对应的 Pillow 内部格式名称的映射
# Pillow 对于 JPEG 格式通常使用 'JPEG'，无论后缀是 'jpg' 还是 'jpeg'
# 对于其他格式，Pillow 通常能从文件后缀推断，但显式指定更安全
_FORMAT_MAP: Final[dict[str, str]] = {
    "jpg": "JPEG",
    "jpeg": "JPEG",
    "png": "PNG",
    "bmp": "BMP",
    "webp": "WEBP",
    "svg": "SVG",  # Pillow 对 SVG 的支持可能有限，特别是从栅格到矢量的转换
}


class FormatConversion(BaseProcessor):
    """将图片转换为指定格式的类"""

    def process(
        self,
        img_path: Path | str,
        target_format: Literal["jpg", "jpeg", "png", "bmp", "webp", "svg"],
        override: bool = True,
    ) -> Path:
        """将图片转换为指定格式

        Args:
            img_path: 图片路径。
            target_format: 目标格式 (jpg, jpeg, png, bmp, webp, svg)。
            override: 是否覆盖原图 (True 则修改原图，False 则保存为带 `_out` 后缀的新文件)。

        Returns:
            处理后的图片路径。

        Raises:
            FileNotFoundError: 如果图片文件不存在。
            ValueError: 如果提供的路径不是文件或格式不支持。
            UnidentifiedImageError: 如果无法识别的图片文件或格式损坏。
            IOError: 如果读写图片时发生IO错误。
            Exception: 如果处理过程中出现其他错误。
        """
        img_path = Path(img_path)
        if not img_path.exists():
            raise FileNotFoundError(f"图片文件 {img_path} 不存在。")
        if not img_path.is_file():
            raise ValueError(f"提供的路径 {img_path} 不是一个文件。")

        # 获取 Pillow 使用的格式名称
        pillow_format = _FORMAT_MAP.get(target_format.lower())
        if not pillow_format:
            # 理论上 Literal 类型会限制输入，但作为防御性编程
            raise ValueError(f"不支持的目标格式 {target_format}。")

        # 打开图片
        img = Image.open(img_path)

        # 对于某些格式，如PNG转JPG，可能需要处理透明度
        if (pillow_format == "JPEG" or pillow_format == "BMP") and img.mode in (
            "RGBA",
            "LA",
            "P",
        ):
            # 如果图像有 alpha 通道或调色板模式，转换为 RGB
            # JPEG 和 BMP 不支持透明度，BMP通常也不支持索引色直接保存

            # 创建一个白色背景的图像
            background = Image.new("RGB", img.size, (255, 255, 255))

            # 将原图粘贴到背景上（如果原图有alpha通道）
            # 对于P模式，先转RGBA再处理，或者直接转RGB
            if img.mode == "P" and "transparency" in img.info:
                img = img.convert("RGBA")  # 确保调色板透明度被正确处理

            if img.mode == "RGBA" or img.mode == "LA":
                background.paste(img, mask=img.split()[-1])  # 使用alpha通道作为mask
                img = background
            else:  # P模式（无透明度）或其他可以直接转RGB的模式
                img = img.convert("RGB")

        # 确定输出路径
        output_path: Path = self._determine_output_path(
            img_path, target_format, override
        )

        # 确保输出目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 保存图片
        if pillow_format == "WEBP":
            img.save(
                output_path, format=pillow_format, quality=90
            )  # WebP默认使用90%质量
        else:
            img.save(output_path, format=pillow_format)

        return output_path

    def _determine_output_path(
        self, img_path: Path, target_format: str, override: bool = True
    ) -> Path:
        """内部方法：根据 override 参数确定输出路径。

        Args:
            img_path: 原始图片路径。
            target_format: 目标格式字符串。
            override: 是否覆盖原图。

        Returns:
            处理后的图片输出路径。
        """
        if override:
            # 覆盖原图，但修改后缀为目标格式
            return img_path.with_suffix(f".{target_format.lower()}")
        else:
            # 不覆盖原图，在原文件名基础上添加 _out 后缀，并修改为目标格式后缀
            return img_path.with_name(f"{img_path.stem}_out.{target_format.lower()}")


if __name__ == "__main__":
    # 测试代码
    converter = FormatConversion()
    input_path = Path(r"G:\CrawlData\kemono\RoundsChen\PIC2024.02\dif_01.jpg")
    output_path = converter.process(input_path, "webp", override=False)
    print(f"Converted image saved at: {output_path}")

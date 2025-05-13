from typing import Final
import textwrap
from enum import Enum
from src.core.enums import (
    CompressionMode,
    DuplicationMode,
    Orientation,
    RotationMode,
    SaveFileMode,
    SuperResolutionModel,
    ImageFormat,
)

ASCII_LOGO = textwrap.dedent("""
 _____                     _____           _     
|_   _|                   |_   _|         | |    
  | | _ __ ___   __ _       | | ___   ___ | |___ 
  | || '_ ` _ \ / _` |      | |/ _ \ / _ \| / __|
 _| || | | | | | (_| |      | | (_) | (_) | \__ \\
 \___/_| |_| |_|\__, |      \_/\___/ \___/|_|___/
                 __/ |                           
                |___/                            
    """)

COMMON_IMAGE_SUFFIXES: Final[tuple[str, ...]] = (
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".bmp",
    ".webp",
)

ARGS_EXPLAIN: Final[dict[str, str]] = {
    "img_dir_path": "图片目录路径(目录)",
    "img_path": "图片文件路径(单个文件)",
    "suffix": "图片后缀名列表",
    "thread_num": "处理器数量",
    "recursion": "是否递归查找子目录中的图片文件",
    "override": "是否覆盖原图",
    "compression": "压缩模式",
    "rotation_mode": "旋转模式",
    "orientation": "目标方向",
    "duplication_mode": "去重模式",
    "save_file_mode": "文件保存模式",
    "target_format": "目标格式",
    "noise": "降噪等级",
    "scale": "放大倍数",
    "model": "超分模型",
}

ENUM_DESCRIPTION: Final[dict[Enum, str]] = {
    CompressionMode.Fastest: "最快速度，适中压缩率",
    CompressionMode.Best: "平衡速度与压缩率",
    CompressionMode.Smallest: "最高压缩率，较慢速度",
    RotationMode.Clockwise: "顺时针旋转",
    RotationMode.CounterClockwise: "逆时针旋转",
    Orientation.Vertical: "垂直方向",
    Orientation.Horizontal: "水平方向",
    DuplicationMode.Fastest: "最快速度，适中准确率",
    DuplicationMode.Normal: "平衡速度与准确率",
    DuplicationMode.Best: "最高准确率，较慢速度",
    DuplicationMode.CNN: "基于CNN的高精度检测",
    SaveFileMode.SaveFirst: "保留每组重复中的第一个文件",
    SaveFileMode.SaveLast: "保留每组重复中的最后一个文件",
    SaveFileMode.SaveFirstAndLast: "保留每组重复中的第一个和最后一个文件",
    SaveFileMode.SaveBigger: "保留每组重复中最大的文件",
    SaveFileMode.SaveSmaller: "保留每组重复中最小的文件",
    SuperResolutionModel.UpconvAnime: "适合动漫图片的模型",
    SuperResolutionModel.UpconvPhoto: "适合照片的模型",
    SuperResolutionModel.Cunet: "高质量通用模型，速度较慢",
    ImageFormat.JPG: "JPEG格式，有损压缩，较小体积",
    ImageFormat.JPEG: "JPEG格式，有损压缩，较小体积",
    ImageFormat.PNG: "PNG格式，无损压缩，支持透明度",
    ImageFormat.BMP: "BMP格式，无损且无压缩",
    ImageFormat.WEBP: "WebP格式，谷歌开发，有损/无损，高压缩率",
}
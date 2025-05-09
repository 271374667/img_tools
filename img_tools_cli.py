import sys
import time
from enum import Enum
from pathlib import Path
from typing import Optional
import loguru
import typer

from src.core.enums import (
    CompressionMode,
    DuplicationMode,
    Orientation,
    RotationMode,
    SaveFileMode,
    SuperResolutionModel,
)
from src.core.constants import ASCII_LOGO
from rich.panel import Panel
from rich.table import Table
from rich.console import Console
from rich.prompt import IntPrompt, Confirm
from rich.prompt import Prompt

# 配置日志记录器
logger = loguru.logger
logger.remove()
logger.add(sys.stderr, level="INFO")

# 创建富文本控制台对象
console = Console()

# 创建主应用
app = typer.Typer(help="图片工具集 - 提供多种图片处理功能")

# 为不同功能创建子命令
compression_app = typer.Typer(help="图片压缩功能")
rotation_app = typer.Typer(help="图片旋转功能")
format_app = typer.Typer(help="图片格式转换功能")
duplication_app = typer.Typer(help="图片去重功能")
super_resolution_app = typer.Typer(help="图片超分辨率功能")

# 注册子命令
app.add_typer(compression_app, name="compress", help="压缩图片大小")
app.add_typer(rotation_app, name="rotate", help="旋转图片方向")
app.add_typer(format_app, name="convert", help="转换图片格式")
app.add_typer(duplication_app, name="dedup", help="检测并删除重复图片")
app.add_typer(super_resolution_app, name="upscale", help="提高图片分辨率")


# 用于格式转换的格式枚举
class ImageFormat(str, Enum):
    JPG = "jpg"
    JPEG = "jpeg"
    PNG = "png"
    BMP = "bmp"
    WEBP = "webp"


@compression_app.command("dir")
def compress_directory(
    img_dir: Path = typer.Argument(
        ...,
        help="包含需要压缩图片的目录路径",
        exists=True,
        dir_okay=True,
        file_okay=False,
    ),
    mode: CompressionMode = typer.Option(
        CompressionMode.Best,
        "--mode",
        "-m",
        help="压缩模式: fastest (最快), best (最佳), smallest (最小)",
    ),
    threads: Optional[int] = typer.Option(
        None, "--threads", "-t", help="处理线程数量, 默认使用系统优化值"
    ),
    recursion: bool = typer.Option(
        True, "--recursion/--no-recursion", help="是否递归处理子目录", show_default=True
    ),
    override: bool = typer.Option(
        True, "--override/--no-override", help="是否覆盖原始图片", show_default=True
    ),
):
    """
    压缩指定目录中的所有图片。

    示例：img_tools_cli compress dir ./images --mode best --no-override
    """
    logger.info(f"开始压缩图片目录: {img_dir}")
    logger.info(f"压缩模式: {mode.value}")
    logger.info(f"是否覆盖: {override}")

    try:
        from src.processor.compression import Compression

        processor = Compression()
        result_dir = processor.process_dir(
            img_dir_path=img_dir,
            compression=mode,
            thread_num=threads,
            recursion=recursion,
            override=override,
        )
        logger.success(f"图片压缩完成! 结果保存在: {result_dir}")
    except Exception as e:
        logger.error(f"压缩过程中发生错误: {e}")
        raise typer.Exit(code=1)


@compression_app.command("file")
def compress_file(
    img_path: Path = typer.Argument(
        ..., help="需要压缩的图片文件路径", exists=True, dir_okay=False, file_okay=True
    ),
    mode: CompressionMode = typer.Option(
        CompressionMode.Best,
        "--mode",
        "-m",
        help="压缩模式: fastest (最快), best (最佳), smallest (最小)",
    ),
    override: bool = typer.Option(
        True, "--override/--no-override", help="是否覆盖原始图片", show_default=True
    ),
):
    """
    压缩单个图片文件。

    示例：img_tools_cli compress file ./images/photo.jpg --mode smallest --no-override
    """
    logger.info(f"开始压缩图片: {img_path}")
    logger.info(f"压缩模式: {mode.value}")
    logger.info(f"是否覆盖: {override}")

    try:
        from src.processor.compression import Compression

        processor = Compression()
        result_path = processor.process(
            img_path=img_path, compression=mode, override=override
        )
        logger.success(f"图片压缩完成! 结果保存在: {result_path}")
    except Exception as e:
        logger.error(f"压缩过程中发生错误: {e}")
        raise typer.Exit(code=1)


@rotation_app.command("dir")
def rotate_directory(
    img_dir: Path = typer.Argument(
        ...,
        help="包含需要旋转图片的目录路径",
        exists=True,
        dir_okay=True,
        file_okay=False,
    ),
    orientation: Orientation = typer.Option(
        Orientation.Vertical,
        "--orientation",
        "-o",
        help="目标方向: vertical (垂直), horizontal (水平)",
    ),
    mode: RotationMode = typer.Option(
        RotationMode.Clockwise,
        "--mode",
        "-m",
        help="旋转方向: clockwise (顺时针), counterclockwise (逆时针)",
    ),
    threads: Optional[int] = typer.Option(
        None, "--threads", "-t", help="处理线程数量, 默认使用系统优化值"
    ),
    recursion: bool = typer.Option(
        True, "--recursion/--no-recursion", help="是否递归处理子目录", show_default=True
    ),
    override: bool = typer.Option(
        True, "--override/--no-override", help="是否覆盖原始图片", show_default=True
    ),
):
    """
    旋转指定目录中的所有图片到指定方向。

    示例：img_tools_cli rotate dir ./images --orientation horizontal --mode clockwise
    """
    logger.info(f"开始旋转图片目录: {img_dir}")
    logger.info(f"目标方向: {orientation.value}")
    logger.info(f"旋转模式: {mode.value}")
    logger.info(f"是否覆盖: {override}")

    try:
        from src.processor.rotation import Rotation

        processor = Rotation()
        result_dir = processor.process_dir(
            img_dir_path=img_dir,
            orientation=orientation,
            rotation_mode=mode,
            thread_num=threads,
            recursion=recursion,
            override=override,
        )
        logger.success(f"图片旋转完成! 结果保存在: {result_dir}")
    except Exception as e:
        logger.error(f"旋转过程中发生错误: {e}")
        raise typer.Exit(code=1)


@rotation_app.command("file")
def rotate_file(
    img_path: Path = typer.Argument(
        ..., help="需要旋转的图片文件路径", exists=True, dir_okay=False, file_okay=True
    ),
    orientation: Orientation = typer.Option(
        Orientation.Vertical,
        "--orientation",
        "-o",
        help="目标方向: vertical (垂直), horizontal (水平)",
    ),
    mode: RotationMode = typer.Option(
        RotationMode.Clockwise,
        "--mode",
        "-m",
        help="旋转方向: clockwise (顺时针), counterclockwise (逆时针)",
    ),
    override: bool = typer.Option(
        True, "--override/--no-override", help="是否覆盖原始图片", show_default=True
    ),
):
    """
    旋转单个图片文件到指定方向。

    示例：img_tools_cli rotate file ./images/photo.jpg --orientation vertical
    """
    logger.info(f"开始旋转图片: {img_path}")
    logger.info(f"目标方向: {orientation.value}")
    logger.info(f"旋转模式: {mode.value}")
    logger.info(f"是否覆盖: {override}")

    try:
        from src.processor.rotation import Rotation

        processor = Rotation()
        result_path = processor.process(
            img_path=img_path,
            orientation=orientation,
            rotation_mode=mode,
            override=override,
        )
        logger.success(f"图片旋转完成! 结果保存在: {result_path}")
    except Exception as e:
        logger.error(f"旋转过程中发生错误: {e}")
        raise typer.Exit(code=1)


@format_app.command("dir")
def convert_directory(
    img_dir: Path = typer.Argument(
        ...,
        help="包含需要转换格式图片的目录路径",
        exists=True,
        dir_okay=True,
        file_okay=False,
    ),
    format: ImageFormat = typer.Option(
        ..., "--format", "-f", help="目标格式: jpg, jpeg, png, bmp, webp"
    ),
    threads: Optional[int] = typer.Option(
        None, "--threads", "-t", help="处理线程数量, 默认使用系统优化值"
    ),
    recursion: bool = typer.Option(
        True, "--recursion/--no-recursion", help="是否递归处理子目录", show_default=True
    ),
    override: bool = typer.Option(
        True, "--override/--no-override", help="是否覆盖原始图片", show_default=True
    ),
):
    """
    转换指定目录中所有图片的格式。

    示例：img_tools_cli convert dir ./images --format webp --no-override
    """
    logger.info(f"开始转换图片目录: {img_dir}")
    logger.info(f"目标格式: {format.value}")
    logger.info(f"是否覆盖: {override}")

    try:
        from src.processor.format_conversion import FormatConversion

        processor = FormatConversion()
        result_dir = processor.process_dir(
            img_dir_path=img_dir,
            target_format=format.value,
            thread_num=threads,
            recursion=recursion,
            override=override,
        )
        logger.success(f"图片格式转换完成! 结果保存在: {result_dir}")
    except Exception as e:
        logger.error(f"格式转换过程中发生错误: {e}")
        raise typer.Exit(code=1)


@format_app.command("file")
def convert_file(
    img_path: Path = typer.Argument(
        ...,
        help="需要转换格式的图片文件路径",
        exists=True,
        dir_okay=False,
        file_okay=True,
    ),
    format: ImageFormat = typer.Option(
        ..., "--format", "-f", help="目标格式: jpg, jpeg, png, bmp, webp"
    ),
    override: bool = typer.Option(
        True, "--override/--no-override", help="是否覆盖原始图片", show_default=True
    ),
):
    """
    转换单个图片文件的格式。

    示例：img_tools_cli convert file ./images/photo.jpg --format png --no-override
    """
    logger.info(f"开始转换图片: {img_path}")
    logger.info(f"目标格式: {format.value}")
    logger.info(f"是否覆盖: {override}")

    try:
        from src.processor.format_conversion import FormatConversion

        processor = FormatConversion()
        result_path = processor.process(
            img_path=img_path, target_format=format.value, override=override
        )
        logger.success(f"图片格式转换完成! 结果保存在: {result_path}")
    except Exception as e:
        logger.error(f"格式转换过程中发生错误: {e}")
        raise typer.Exit(code=1)


@duplication_app.command("dir")
def deduplicate_directory(
    img_dir: Path = typer.Argument(
        ...,
        help="包含需要去重图片的目录路径",
        exists=True,
        dir_okay=True,
        file_okay=False,
    ),
    mode: DuplicationMode = typer.Option(
        DuplicationMode.Normal,
        "--mode",
        "-m",
        help="去重模式: fastest (最快), normal (普通), best (最佳), cnn (CNN)",
    ),
    save_mode: SaveFileMode = typer.Option(
        SaveFileMode.SaveFirst,
        "--save-mode",
        "-s",
        help="保存模式: save_first (保留首个), save_last (保留最后), save_first_and_last (保留首尾), save_bigger (保留较大), save_smaller (保留较小)",
    ),
    threads: Optional[int] = typer.Option(
        None, "--threads", "-t", help="处理线程数量, 默认使用系统优化值"
    ),
    override: bool = typer.Option(
        True,
        "--override/--no-override",
        help="是否在原目录中删除重复图片",
        show_default=True,
    ),
):
    """
    检测并删除指定目录中的重复图片。

    示例：img_tools_cli dedup dir ./images --mode best --save-mode save_bigger --no-override
    """
    logger.info(f"开始检测重复图片: {img_dir}")
    logger.info(f"去重模式: {mode.value}")
    logger.info(f"保存模式: {save_mode.value}")
    logger.info(f"是否在原目录删除: {override}")

    try:
        from src.processor.duplication import Duplication

        processor = Duplication()
        result_dir = processor.process_dir(
            img_dir_path=img_dir,
            duplication_mode=mode,
            save_file_mode=save_mode,
            override=override,
            thread_num=threads,
        )
        logger.success(f"图片去重完成! 结果保存在: {result_dir}")
    except Exception as e:
        logger.error(f"去重过程中发生错误: {e}")
        raise typer.Exit(code=1)


@super_resolution_app.command("dir")
def upscale_directory(
    img_dir: Path = typer.Argument(
        ...,
        help="包含需要超分辨率处理图片的目录路径",
        exists=True,
        dir_okay=True,
        file_okay=False,
    ),
    noise: int = typer.Option(
        0, "--noise", "-n", help="降噪等级 (-1, 0, 1, 2, 3)", min=-1, max=3
    ),
    scale: int = typer.Option(
        2, "--scale", "-s", help="放大倍数 (1, 2, 3, 4)", min=1, max=4
    ),
    model: SuperResolutionModel = typer.Option(
        SuperResolutionModel.UpconvAnime,
        "--model",
        "-m",
        help="超分模型: upconv_7_anime (动漫优化), upconv_7_photo (照片优化), cunet (高质量)",
    ),
    threads: Optional[int] = typer.Option(
        None, "--threads", "-t", help="处理线程数量, 默认使用系统优化值"
    ),
    recursion: bool = typer.Option(
        True, "--recursion/--no-recursion", help="是否递归处理子目录", show_default=True
    ),
    override: bool = typer.Option(
        True, "--override/--no-override", help="是否覆盖原始图片", show_default=True
    ),
):
    """
    对指定目录中的所有图片进行超分辨率处理。

    示例：img_tools_cli upscale dir ./images --scale 2 --noise 1 --model upconv_7_anime
    """
    logger.info(f"开始超分辨率处理图片目录: {img_dir}")
    logger.info(f"放大倍数: {scale}")
    logger.info(f"降噪等级: {noise}")
    logger.info(f"使用模型: {model.value}")
    logger.info(f"是否覆盖: {override}")

    try:
        from src.processor.super_resolution import SuperResolution

        processor = SuperResolution()
        result_dir = processor.process_dir(
            img_dir_path=img_dir,
            noise=noise,
            scale=scale,
            model=model,
            thread_num=threads,
            recursion=recursion,
            override=override,
        )
        logger.success(f"图片超分辨率处理完成! 结果保存在: {result_dir}")
    except Exception as e:
        logger.error(f"超分辨率处理过程中发生错误: {e}")
        raise typer.Exit(code=1)


@super_resolution_app.command("file")
def upscale_file(
    img_path: Path = typer.Argument(
        ...,
        help="需要超分辨率处理的图片文件路径",
        exists=True,
        dir_okay=False,
        file_okay=True,
    ),
    noise: int = typer.Option(
        0, "--noise", "-n", help="降噪等级 (-1, 0, 1, 2, 3)", min=-1, max=3
    ),
    scale: int = typer.Option(
        2, "--scale", "-s", help="放大倍数 (1, 2, 3, 4)", min=1, max=4
    ),
    model: SuperResolutionModel = typer.Option(
        SuperResolutionModel.UpconvAnime,
        "--model",
        "-m",
        help="超分模型: upconv_7_anime (动漫优化), upconv_7_photo (照片优化), cunet (高质量)",
    ),
    override: bool = typer.Option(
        True, "--override/--no-override", help="是否覆盖原始图片", show_default=True
    ),
):
    """
    对单个图片文件进行超分辨率处理。

    示例：img_tools_cli upscale file ./images/photo.jpg --scale 3 --noise 2 --model cunet
    """
    logger.info(f"开始超分辨率处理图片: {img_path}")
    logger.info(f"放大倍数: {scale}")
    logger.info(f"降噪等级: {noise}")
    logger.info(f"使用模型: {model.value}")
    logger.info(f"是否覆盖: {override}")

    try:
        from src.processor.super_resolution import SuperResolution

        processor = SuperResolution()
        result_path = processor.process(
            img_path=img_path, noise=noise, scale=scale, model=model, override=override
        )
        logger.success(f"图片超分辨率处理完成! 结果保存在: {result_path}")
    except Exception as e:
        logger.error(f"超分辨率处理过程中发生错误: {e}")
        raise typer.Exit(code=1)


@app.command("info")
def show_info():
    """
    显示工具功能介绍和使用方法概览。

    示例：img_tools_cli info
    """

    table = Table(title="图片工具集功能概览")

    table.add_column("命令", style="cyan", no_wrap=True)
    table.add_column("功能", style="magenta")
    table.add_column("使用示例", style="green")

    table.add_row(
        "compress",
        "图片压缩 - 减小图片文件大小",
        "img_tools_cli compress dir ./images --mode best",
    )
    table.add_row(
        "rotate",
        "图片旋转 - 将图片旋转到指定方向",
        "img_tools_cli rotate dir ./images --orientation vertical",
    )
    table.add_row(
        "convert",
        "格式转换 - 将图片转换为指定格式",
        "img_tools_cli convert dir ./images --format webp",
    )
    table.add_row(
        "dedup",
        "图片去重 - 检测并删除重复图片",
        "img_tools_cli dedup dir ./images --mode normal",
    )
    table.add_row(
        "upscale",
        "超分辨率 - 提高图片分辨率与清晰度",
        "img_tools_cli upscale dir ./images --scale 2 --noise 1",
    )

    console.print(table)

    typer.echo("\n每个命令都支持 --help 查看详细帮助信息，例如:")
    typer.echo("  img_tools_cli compress --help")
    typer.echo("  img_tools_cli compress dir --help")


class InteractionTUI:
    @staticmethod
    def show_ascii_logo():
        console.print(
            Panel(
                ASCII_LOGO,
                border_style="cyan",
                expand=False,
                title="欢迎使用图片工具集",
            ),
        )

    @staticmethod
    def show_main_menu():
        table = Table(
            title="请选择要使用的功能", show_header=True, header_style="bold magenta"
        )
        table.add_column("选项", style="cyan", justify="center")
        table.add_column("功能", style="green")
        table.add_column("说明", style="yellow")

        table.add_row("1", "图片压缩", "减小图片文件大小，支持多种压缩模式")
        table.add_row("2", "图片旋转", "将图片旋转到指定方向")
        table.add_row("3", "格式转换", "将图片转换为其他格式(jpg/png/webp等)")
        table.add_row("4", "图片去重", "检测并删除重复图片")
        table.add_row("5", "超分辨率", "提高图片分辨率与清晰度")
        table.add_row("0", "退出程序", "结束程序运行")

        console.print(table)

    @staticmethod
    def get_valid_path(
        prompt_text: str, dir_only: bool = False, file_only: bool = False
    ) -> Path:
        """获取并验证有效的文件或目录路径"""
        while True:
            path_str = Prompt.ask(prompt_text)
            if not path_str:
                console.print("[bold red]错误: 输入不能为空，请重新输入[/bold red]")
                continue

            path = Path(path_str)

            if not path.exists():
                console.print(
                    f"[bold red]错误: 路径 '{path}' 不存在，请重新输入[/bold red]"
                )
                continue

            if dir_only and not path.is_dir():
                console.print(
                    f"[bold red]错误: '{path}' 不是一个目录，请重新输入[/bold red]"
                )
                continue

            if file_only and not path.is_file():
                console.print(
                    f"[bold red]错误: '{path}' 不是一个文件，请重新输入[/bold red]"
                )
                continue
            console.log(f"[bold green]选择的路径: {path}[/bold green]")
            return path

    @staticmethod
    def get_enum_choice(enum_class, prompt_text: str, default=None):
        """获取枚举类型选择"""
        table = Table(
            title=f"{prompt_text} (选择一个选项)", show_header=True, header_style="bold"
        )
        table.add_column("选项", style="cyan", justify="center")
        table.add_column("值", style="green")
        table.add_column("说明", style="yellow")

        enum_dict = {}
        default_option = None

        for i, option in enumerate(enum_class, 1):
            option_name = option.name
            option_value = option.value
            description = InteractionTUI.get_enum_description(enum_class, option)
            table.add_row(str(i), option_value, description)
            enum_dict[i] = option
            if default and option == default:
                default_option = i

        console.print(table)

        default_prompt = f"[默认: {default_option}]" if default_option else ""

        while True:
            choice = IntPrompt.ask(
                f"请选择一个选项 {default_prompt}", default=default_option
            )
            if choice in enum_dict:
                console.print(
                    f"[bold green]选择的值: {enum_dict[choice].value}[/bold green]"
                )
                return enum_dict[choice]
            else:
                console.print(
                    f"[bold red]错误: 无效的选择，请输入1-{len(enum_dict)}之间的数字[/bold red]"
                )

    @staticmethod
    def get_enum_description(enum_class, option):
        """获取枚举选项的描述信息"""
        descriptions = {
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

        return descriptions.get(option, "无描述")

    @staticmethod
    def get_int_input(prompt_text: str, default=None, min_value=None, max_value=None):
        """获取整数输入"""
        from src.utils.io_uitls import IOuitls

        default_prompt = f"[默认: {default}]" if default is not None else ""

        constraint_text = ""
        if min_value is not None and max_value is not None:
            constraint_text = f"({min_value}-{max_value})"
        elif min_value is not None:
            constraint_text = f"(最小: {min_value})"
        elif max_value is not None:
            constraint_text = f"(最大: {max_value})"

        while True:
            value = IntPrompt.ask(
                f"{prompt_text} {constraint_text} {default_prompt}", default=default
            )

            if min_value is not None and value < min_value:
                console.print(f"[bold red]错误: 值不能小于 {min_value}[/bold red]")
                continue

            if max_value is not None and value > max_value:
                console.print(f"[bold red]错误: 值不能大于 {max_value}[/bold red]")
                continue

            if "线程" in prompt_text:
                value = IOuitls.get_optimal_process_count() if value is None else value
            console.print(f"[bold green]选择的值: {value}[/bold green]")
            return value

    @staticmethod
    def get_bool_input(prompt_text: str, default=True) -> bool:
        """获取布尔输入"""
        result = Confirm.ask(
            f"{prompt_text} [默认: {'是' if default else '否'}]", default=default
        )
        console.print(f"[bold green]选择的值: {'是' if result else '否'}[/bold green]")
        return result

    @staticmethod
    def compress_mode():
        """图片压缩交互模式"""
        from src.utils.sound_utils import SoundUtils

        console.print(Panel("图片压缩功能", style="cyan"))

        # 选择处理单个文件还是目录
        process_type = Prompt.ask(
            "请选择处理类型", choices=["file", "dir"], default="dir"
        )

        if process_type == "dir":
            img_dir = InteractionTUI.get_valid_path("请输入图片目录路径", dir_only=True)
            mode = InteractionTUI.get_enum_choice(
                CompressionMode, "选择压缩模式", default=CompressionMode.Best
            )
            threads = InteractionTUI.get_int_input(
                "处理线程数 (留空使用系统优化值)", default=None
            )
            recursion = InteractionTUI.get_bool_input(
                "是否递归处理子目录?", default=True
            )
            override = InteractionTUI.get_bool_input("是否覆盖原始图片?", default=True)

            start_time = time.time()
            try:
                from src.processor.compression import Compression

                processor = Compression()
                console.print("[bold yellow]开始压缩图片目录...[/bold yellow]")
                result_dir = processor.process_dir(
                    img_dir_path=img_dir,
                    compression=mode,
                    thread_num=threads,
                    recursion=recursion,
                    override=override,
                )
                elapsed = time.time() - start_time
                console.print(
                    f"[bold green]图片压缩完成! 结果保存在: {result_dir}[/bold green]"
                )
                console.print(f"[bold blue]处理用时: {elapsed:.2f}秒[/bold blue]")
                SoundUtils.beep()
            except Exception as e:
                console.print(f"[bold red]压缩过程中发生错误: {e}[/bold red]")
                input("按Enter键返回主菜单...")
                return
        else:
            img_path = InteractionTUI.get_valid_path(
                "请输入图片文件路径", file_only=True
            )
            mode = InteractionTUI.get_enum_choice(
                CompressionMode, "选择压缩模式", default=CompressionMode.Best
            )
            override = InteractionTUI.get_bool_input("是否覆盖原始图片?", default=True)

            start_time = time.time()
            try:
                from src.processor.compression import Compression

                processor = Compression()
                console.print("[bold yellow]开始压缩图片...[/bold yellow]")
                result_path = processor.process(
                    img_path=img_path, compression=mode, override=override
                )
                elapsed = time.time() - start_time
                console.print(
                    f"[bold green]图片压缩完成! 结果保存在: {result_path}[/bold green]"
                )
                console.print(f"[bold blue]处理用时: {elapsed:.2f}秒[/bold blue]")
                SoundUtils.beep()  # 完成提示音
            except Exception as e:
                console.print(f"[bold red]压缩过程中发生错误: {e}[/bold red]")
                input("按Enter键返回主菜单...")
                return

    @staticmethod
    def rotate_mode():
        """图片旋转交互模式"""
        from src.utils.sound_utils import SoundUtils

        console.print(Panel("图片旋转功能", style="cyan"))

        # 选择处理单个文件还是目录
        process_type = Prompt.ask(
            "请选择处理类型", choices=["file", "dir"], default="dir"
        )

        if process_type == "dir":
            img_dir = InteractionTUI.get_valid_path("请输入图片目录路径", dir_only=True)
            orientation = InteractionTUI.get_enum_choice(
                Orientation, "选择目标方向", default=Orientation.Vertical
            )
            mode = InteractionTUI.get_enum_choice(
                RotationMode, "选择旋转方向", default=RotationMode.Clockwise
            )
            threads = InteractionTUI.get_int_input(
                "处理线程数 (留空使用系统优化值)", default=None
            )
            recursion = InteractionTUI.get_bool_input(
                "是否递归处理子目录?", default=True
            )
            override = InteractionTUI.get_bool_input("是否覆盖原始图片?", default=True)

            start_time = time.time()
            try:
                from src.processor.rotation import Rotation

                processor = Rotation()
                console.print("[bold yellow]开始旋转图片目录...[/bold yellow]")
                result_dir = processor.process_dir(
                    img_dir_path=img_dir,
                    orientation=orientation,
                    rotation_mode=mode,
                    thread_num=threads,
                    recursion=recursion,
                    override=override,
                )
                elapsed = time.time() - start_time
                console.print(
                    f"[bold green]图片旋转完成! 结果保存在: {result_dir}[/bold green]"
                )
                console.print(f"[bold blue]处理用时: {elapsed:.2f}秒[/bold blue]")
                SoundUtils.beep()  # 完成提示音
            except Exception as e:
                console.print(f"[bold red]旋转过程中发生错误: {e}[/bold red]")
                input("按Enter键返回主菜单...")
                return
        else:
            img_path = InteractionTUI.get_valid_path(
                "请输入图片文件路径", file_only=True
            )
            orientation = InteractionTUI.get_enum_choice(
                Orientation, "选择目标方向", default=Orientation.Vertical
            )
            mode = InteractionTUI.get_enum_choice(
                RotationMode, "选择旋转方向", default=RotationMode.Clockwise
            )
            override = InteractionTUI.get_bool_input("是否覆盖原始图片?", default=True)

            start_time = time.time()
            try:
                from src.processor.rotation import Rotation

                processor = Rotation()
                console.print("[bold yellow]开始旋转图片...[/bold yellow]")
                result_path = processor.process(
                    img_path=img_path,
                    orientation=orientation,
                    rotation_mode=mode,
                    override=override,
                )
                elapsed = time.time() - start_time
                console.print(
                    f"[bold green]图片旋转完成! 结果保存在: {result_path}[/bold green]"
                )
                console.print(f"[bold blue]处理用时: {elapsed:.2f}秒[/bold blue]")
                SoundUtils.beep()  # 完成提示音
            except Exception as e:
                console.print(f"[bold red]旋转过程中发生错误: {e}[/bold red]")
                input("按Enter键返回主菜单...")
                return

    @staticmethod
    def convert_mode():
        """图片格式转换交互模式"""
        from src.utils.sound_utils import SoundUtils

        console.print(Panel("图片格式转换功能", style="cyan"))

        # 选择处理单个文件还是目录
        process_type = Prompt.ask(
            "请选择处理类型", choices=["file", "dir"], default="dir"
        )

        if process_type == "dir":
            img_dir = InteractionTUI.get_valid_path("请输入图片目录路径", dir_only=True)
            format = InteractionTUI.get_enum_choice(
                ImageFormat, "选择目标格式", default=ImageFormat.PNG
            )
            threads = InteractionTUI.get_int_input(
                "处理线程数 (留空使用系统优化值)", default=None
            )
            recursion = InteractionTUI.get_bool_input(
                "是否递归处理子目录?", default=True
            )
            override = InteractionTUI.get_bool_input("是否覆盖原始图片?", default=True)

            start_time = time.time()
            try:
                from src.processor.format_conversion import FormatConversion

                processor = FormatConversion()
                console.print("[bold yellow]开始转换图片格式...[/bold yellow]")
                result_dir = processor.process_dir(
                    img_dir_path=img_dir,
                    target_format=format.value,
                    thread_num=threads,
                    recursion=recursion,
                    override=override,
                )
                elapsed = time.time() - start_time
                console.print(
                    f"[bold green]图片格式转换完成! 结果保存在: {result_dir}[/bold green]"
                )
                console.print(f"[bold blue]处理用时: {elapsed:.2f}秒[/bold blue]")
                SoundUtils.beep()  # 完成提示音
            except Exception as e:
                console.print(f"[bold red]格式转换过程中发生错误: {e}[/bold red]")
                input("按Enter键返回主菜单...")
                return
        else:
            img_path = InteractionTUI.get_valid_path(
                "请输入图片文件路径", file_only=True
            )
            format = InteractionTUI.get_enum_choice(
                ImageFormat, "选择目标格式", default=ImageFormat.PNG
            )
            override = InteractionTUI.get_bool_input("是否覆盖原始图片?", default=True)

            start_time = time.time()
            try:
                from src.processor.format_conversion import FormatConversion

                processor = FormatConversion()
                console.print("[bold yellow]开始转换图片格式...[/bold yellow]")
                result_path = processor.process(
                    img_path=img_path, target_format=format.value, override=override
                )
                elapsed = time.time() - start_time
                console.print(
                    f"[bold green]图片格式转换完成! 结果保存在: {result_path}[/bold green]"
                )
                console.print(f"[bold blue]处理用时: {elapsed:.2f}秒[/bold blue]")
                SoundUtils.beep()  # 完成提示音
            except Exception as e:
                console.print(f"[bold red]格式转换过程中发生错误: {e}[/bold red]")
                input("按Enter键返回主菜单...")
                return

    @staticmethod
    def dedup_mode():
        """图片去重交互模式"""
        from src.utils.sound_utils import SoundUtils

        console.print(Panel("图片去重功能", style="cyan"))

        img_dir = InteractionTUI.get_valid_path("请输入图片目录路径", dir_only=True)
        mode = InteractionTUI.get_enum_choice(
            DuplicationMode, "选择去重模式", default=DuplicationMode.Normal
        )
        save_mode = InteractionTUI.get_enum_choice(
            SaveFileMode, "选择文件保存模式", default=SaveFileMode.SaveFirst
        )
        threads = InteractionTUI.get_int_input(
            "处理线程数 (留空使用系统优化值)", default=None
        )
        override = InteractionTUI.get_bool_input(
            "是否在原目录中删除重复图片?", default=True
        )

        start_time = time.time()
        try:
            from src.processor.duplication import Duplication

            processor = Duplication()
            console.print("[bold yellow]开始检测重复图片...[/bold yellow]")
            result_dir = processor.process_dir(
                img_dir_path=img_dir,
                duplication_mode=mode,
                save_file_mode=save_mode,
                override=override,
                thread_num=threads,
            )
            elapsed = time.time() - start_time
            console.print(
                f"[bold green]图片去重完成! 结果保存在: {result_dir}[/bold green]"
            )
            console.print(f"[bold blue]处理用时: {elapsed:.2f}秒[/bold blue]")
            SoundUtils.beep()  # 完成提示音
        except Exception as e:
            console.print(f"[bold red]去重过程中发生错误: {e}[/bold red]")
            input("按Enter键返回主菜单...")
            return

    @staticmethod
    def upscale_mode():
        """图片超分辨率交互模式"""
        from src.utils.sound_utils import SoundUtils

        console.print(Panel("图片超分辨率功能", style="cyan"))

        # 选择处理单个文件还是目录
        process_type = Prompt.ask(
            "请选择处理类型", choices=["file", "dir"], default="dir"
        )

        if process_type == "dir":
            img_dir = InteractionTUI.get_valid_path("请输入图片目录路径", dir_only=True)
            noise = InteractionTUI.get_int_input(
                "降噪等级", default=0, min_value=-1, max_value=3
            )
            scale = InteractionTUI.get_int_input(
                "放大倍数", default=2, min_value=1, max_value=4
            )
            model = InteractionTUI.get_enum_choice(
                SuperResolutionModel,
                "选择超分模型",
                default=SuperResolutionModel.UpconvAnime,
            )
            threads = InteractionTUI.get_int_input(
                "处理线程数 (留空使用系统优化值)", default=None
            )
            recursion = InteractionTUI.get_bool_input(
                "是否递归处理子目录?", default=True
            )
            override = InteractionTUI.get_bool_input("是否覆盖原始图片?", default=True)

            start_time = time.time()
            try:
                from src.processor.super_resolution import SuperResolution

                processor = SuperResolution()
                console.print("[bold yellow]开始超分辨率处理图片目录...[/bold yellow]")
                result_dir = processor.process_dir(
                    img_dir_path=img_dir,
                    noise=noise,
                    scale=scale,
                    model=model,
                    thread_num=threads,
                    recursion=recursion,
                    override=override,
                )
                elapsed = time.time() - start_time
                console.print(
                    f"[bold green]图片超分辨率处理完成! 结果保存在: {result_dir}[/bold green]"
                )
                console.print(f"[bold blue]处理用时: {elapsed:.2f}秒[/bold blue]")
                SoundUtils.beep()  # 完成提示音
            except Exception as e:
                console.print(f"[bold red]超分辨率处理过程中发生错误: {e}[/bold red]")
                input("按Enter键返回主菜单...")
                return
        else:
            img_path = InteractionTUI.get_valid_path(
                "请输入图片文件路径", file_only=True
            )
            noise = InteractionTUI.get_int_input(
                "降噪等级", default=0, min_value=-1, max_value=3
            )
            scale = InteractionTUI.get_int_input(
                "放大倍数", default=2, min_value=1, max_value=4
            )
            model = InteractionTUI.get_enum_choice(
                SuperResolutionModel,
                "选择超分模型",
                default=SuperResolutionModel.UpconvAnime,
            )
            override = InteractionTUI.get_bool_input("是否覆盖原始图片?", default=True)

            start_time = time.time()
            try:
                from src.processor.super_resolution import SuperResolution

                processor = SuperResolution()
                console.print("[bold yellow]开始超分辨率处理图片...[/bold yellow]")
                result_path = processor.process(
                    img_path=img_path,
                    noise=noise,
                    scale=scale,
                    model=model,
                    override=override,
                )
                elapsed = time.time() - start_time
                console.print(
                    f"[bold green]图片超分辨率处理完成! 结果保存在: {result_path}[/bold green]"
                )
                console.print(f"[bold blue]处理用时: {elapsed:.2f}秒[/bold blue]")
                SoundUtils.beep()  # 完成提示音
            except Exception as e:
                console.print(f"[bold red]超分辨率处理过程中发生错误: {e}[/bold red]")
                input("按Enter键返回主菜单...")
                return

    @staticmethod
    def interactive_cli():
        """交互式命令行主函数"""
        console.clear()

        while True:
            console.clear()
            InteractionTUI.show_ascii_logo()
            InteractionTUI.show_main_menu()

            choice = Prompt.ask(
                "请选择功能",
                choices=["0", "1", "2", "3", "4", "5"],
                default="1",
            )

            if choice == "0":
                console.print("[bold blue]感谢使用，再见！[/bold blue]")
                break
            elif choice == "1":
                InteractionTUI.compress_mode()
            elif choice == "2":
                InteractionTUI.rotate_mode()
            elif choice == "3":
                InteractionTUI.convert_mode()
            elif choice == "4":
                InteractionTUI.dedup_mode()
            elif choice == "5":
                InteractionTUI.upscale_mode()

            # 每次处理完操作后暂停，让用户可以查看结果
            input("\n按Enter键继续...")

if __name__ == "__main__":
    try:
        # 如果有传入选项那么直接执行命令行操作
        if len(sys.argv) > 1:
            app()
        else:
            # 否则进入交互式命令行
            InteractionTUI.interactive_cli()
    except KeyboardInterrupt:
        console.print("\n[bold red]程序被用户中断[/bold red]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[bold red]发生未预期的错误: {e}[/bold red]")
        sys.exit(1)
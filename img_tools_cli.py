import sys
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
    ImageFormat,
)
from rich.table import Table
from rich.console import Console


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


if __name__ == "__main__":
    from PIL import Image

    Image.MAX_IMAGE_PIXELS = None

    try:
        # 如果有传入选项那么直接执行命令行操作
        if len(sys.argv) > 1:
            app()
        else:
            from interaction_tui import InteractionTUI

            # 否则进入交互式命令行
            InteractionTUI.interactive_cli()
    except KeyboardInterrupt:
        console.print("\n[bold red]程序被用户中断[/bold red]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[bold red]发生未预期的错误: {e}[/bold red]")
        sys.exit(1)

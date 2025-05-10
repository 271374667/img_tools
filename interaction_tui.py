import sys
import time
from pathlib import Path
from typing import Optional
import loguru

from src.core.enums import (
    CompressionMode,
    DuplicationMode,
    Orientation,
    RotationMode,
    SaveFileMode,
    SuperResolutionModel,
    ImageFormat,
)
from src.core.constants import ASCII_LOGO, COMMON_IMAGE_SUFFIXES
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


class ChinesePrompt(Prompt):
    validate_error_message = "[prompt.invalid]请输入一个有效的选项！"
    illegal_choice_message = "[prompt.invalid]无效的选项，请重新输入！"

    def process_response(self, value: str) -> str:
        """在返回结果前输出用户选择的值"""
        value = super().process_response(value)  # 调用父类方法进行验证和处理
        self.console.log(f"[bold green]用户选择: {value}[/bold green]")
        return value


class InteractionTUI:
    suffix: Optional[tuple[str, ...]] = None
    thread_num: Optional[int] = None

    args_explain: Optional[dict] = {
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
        table.add_row("9", "全局设置", "设置全局参数(线程数/图片后缀等)")
        table.add_row("0", "退出程序", "结束程序运行")

        console.print(table)

    @staticmethod
    def show_args_menu(**kwargs):
        """在开始之前显示参数设置"""
        table = Table(
            title="当前参数设置", show_header=True, header_style="bold magenta"
        )
        table.add_column("参数", style="cyan", justify="center")
        table.add_column("说明", style="yellow")
        table.add_column("值", style="green")

        for key, value in kwargs.items():
            table.add_row(
                key, InteractionTUI.args_explain.get(key, "无说明"), str(value)
            )

        console.print(table)

    @staticmethod
    def get_valid_path(
        prompt_text: str, dir_only: bool = False, file_only: bool = False
    ) -> Path:
        """获取并验证有效的文件或目录路径"""
        while True:
            path_str = ChinesePrompt.ask(prompt_text)
            if not path_str:
                console.print("[bold red]错误: 输入不能为空，请重新输入[/bold red]")
                continue

            # 删掉开头和结尾的"和空格还有'
            path_str = path_str.strip().strip('"').strip("'")
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
            option_value = option.value
            description = InteractionTUI.get_enum_description(option)
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
    def get_enum_description(option):
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
            return value

    @staticmethod
    def get_bool_input(prompt_text: str, default=True) -> bool:
        """获取布尔输入"""
        result = Confirm.ask(
            f"{prompt_text} [默认: {'是' if default else '否'}]", default=default
        )
        return result

    @staticmethod
    def compress_mode():
        """图片压缩交互模式"""
        from src.utils.sound_utils import SoundUtils

        console.print(Panel("图片压缩功能", style="cyan"))

        # 选择处理单个文件还是目录
        process_type = ChinesePrompt.ask(
            "请选择处理类型", choices=["file", "dir"], default="dir"
        )

        if process_type == "dir":
            img_dir = InteractionTUI.get_valid_path("请输入图片目录路径", dir_only=True)
            mode = InteractionTUI.get_enum_choice(
                CompressionMode, "选择压缩模式", default=CompressionMode.Best
            )
            if not InteractionTUI.thread_num:
                threads = InteractionTUI.get_int_input(
                    "处理线程数 (留空使用系统优化值)", default=None
                )
            else:
                threads = InteractionTUI.thread_num
            recursion = InteractionTUI.get_bool_input(
                "是否递归处理子目录?", default=True
            )
            override = InteractionTUI.get_bool_input("是否覆盖原始图片?", default=True)

            InteractionTUI.show_args_menu(
                img_dir_path=img_dir,
                compression=mode,
                thread_num=threads,
                recursion=recursion,
                override=override,
                suffix=InteractionTUI.suffix
                if InteractionTUI.suffix
                else COMMON_IMAGE_SUFFIXES,
            )

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
                    suffix=InteractionTUI.suffix if InteractionTUI.suffix else None,
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
        process_type = ChinesePrompt.ask(
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
            if not InteractionTUI.thread_num:
                threads = InteractionTUI.get_int_input(
                    "处理线程数 (留空使用系统优化值)", default=None
                )
            else:
                threads = InteractionTUI.thread_num
            recursion = InteractionTUI.get_bool_input(
                "是否递归处理子目录?", default=True
            )
            override = InteractionTUI.get_bool_input("是否覆盖原始图片?", default=True)

            InteractionTUI.show_args_menu(
                img_dir_path=img_dir,
                orientation=orientation,
                rotation_mode=mode,
                thread_num=threads,
                recursion=recursion,
                override=override,
                suffix=InteractionTUI.suffix
                if InteractionTUI.suffix
                else COMMON_IMAGE_SUFFIXES,
            )

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
                    suffix=InteractionTUI.suffix
                    if InteractionTUI.suffix
                    else COMMON_IMAGE_SUFFIXES,
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
        process_type = ChinesePrompt.ask(
            "请选择处理类型", choices=["file", "dir"], default="dir"
        )

        if process_type == "dir":
            img_dir = InteractionTUI.get_valid_path("请输入图片目录路径", dir_only=True)
            format = InteractionTUI.get_enum_choice(
                ImageFormat, "选择目标格式", default=ImageFormat.PNG
            )
            if not InteractionTUI.thread_num:
                threads = InteractionTUI.get_int_input(
                    "处理线程数 (留空使用系统优化值)", default=None
                )
            else:
                threads = InteractionTUI.thread_num
            recursion = InteractionTUI.get_bool_input(
                "是否递归处理子目录?", default=True
            )
            override = InteractionTUI.get_bool_input("是否覆盖原始图片?", default=True)

            InteractionTUI.show_args_menu(
                img_dir_path=img_dir,
                target_format=format.value,
                thread_num=threads,
                recursion=recursion,
                override=override,
                suffix=InteractionTUI.suffix
                if InteractionTUI.suffix
                else COMMON_IMAGE_SUFFIXES,
            )

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
                    suffix=InteractionTUI.suffix
                    if InteractionTUI.suffix
                    else COMMON_IMAGE_SUFFIXES,
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
        if not InteractionTUI.thread_num:
            threads = InteractionTUI.get_int_input(
                "处理线程数 (留空使用系统优化值)", default=None
            )
        else:
            threads = InteractionTUI.thread_num
        override = InteractionTUI.get_bool_input(
            "是否在原目录中删除重复图片?", default=True
        )

        InteractionTUI.show_args_menu(
            img_dir_path=img_dir,
            duplication_mode=mode,
            save_file_mode=save_mode,
            override=override,
            thread_num=threads,
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
        process_type = ChinesePrompt.ask(
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
            if not InteractionTUI.thread_num:
                threads = InteractionTUI.get_int_input(
                    "处理线程数 (留空使用系统优化值)", default=None
                )
            else:
                threads = InteractionTUI.thread_num
            recursion = InteractionTUI.get_bool_input(
                "是否递归处理子目录?", default=True
            )
            override = InteractionTUI.get_bool_input("是否覆盖原始图片?", default=True)

            InteractionTUI.show_args_menu(
                img_dir_path=img_dir,
                noise=noise,
                scale=scale,
                model=model,
                thread_num=threads,
                recursion=recursion,
                override=override,
                suffix=InteractionTUI.suffix
                if InteractionTUI.suffix
                else COMMON_IMAGE_SUFFIXES,
            )

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
                    suffix=InteractionTUI.suffix
                    if InteractionTUI.suffix
                    else COMMON_IMAGE_SUFFIXES,
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
    def settings_mode():
        """全局设置模式"""
        console.print(Panel("全局设置模式", style="cyan"))

        table = Table(
            title="请选择要设置的内容", show_header=True, header_style="bold magenta"
        )
        table.add_column("选项", style="cyan", justify="center")
        table.add_column("功能", style="green")
        table.add_column("说明", style="yellow")

        table.add_row("0", "返回", "返回主菜单")
        table.add_row(
            "1", "设置图片后缀", "设置搜索图片的文件后缀，多个用逗号分隔,例如: jpg,png"
        )
        table.add_row(
            "2", "设置线程/进程数量", "设置处理图片的线程数，默认使用系统优化值"
        )

        console.print(table)

        # 选择处理单个文件还是目录
        process_type = ChinesePrompt.ask(
            "请选择处理类型", choices=["0", "1", "2"], default="0"
        )

        match process_type:
            case "0":
                return
            case "1":
                suffix = ChinesePrompt.ask(
                    "请输入图片后缀（多个用逗号分隔）",
                    default="jpg,jpeg,png,gif,bmp,webp",
                )
                suffix = tuple(suffix.split(","))
                InteractionTUI.suffix = suffix
                console.print(f"[bold green]设置成功: {suffix}[/bold green]")
            case "2":
                thread_num = InteractionTUI.get_int_input(
                    "请输入线程数 (留空使用系统优化值)", default=None
                )
                InteractionTUI.thread_num = thread_num
                console.print(f"[bold green]设置成功: {thread_num}[/bold green]")

    @staticmethod
    def interactive_cli():
        """交互式命令行主函数"""

        console.clear()

        while True:
            console.clear()
            InteractionTUI.show_ascii_logo()
            InteractionTUI.show_main_menu()

            choice = ChinesePrompt.ask(
                "请选择功能",
                choices=["0", "1", "2", "3", "4", "5", "9"],
                default="1",
            )

            match choice:
                case "0":
                    console.print("[bold blue]感谢使用，再见！[/bold blue]")
                    break
                case "1":
                    InteractionTUI.compress_mode()
                case "2":
                    InteractionTUI.rotate_mode()
                case "3":
                    InteractionTUI.convert_mode()
                case "4":
                    InteractionTUI.dedup_mode()
                case "5":
                    InteractionTUI.upscale_mode()
                case "9":
                    InteractionTUI.settings_mode()

            # 每次处理完操作后暂停，让用户可以查看结果
            input("\n按Enter键继续...")

if __name__ == '__main__':
    from PIL import Image

    Image.MAX_IMAGE_PIXELS = None

    try:
        InteractionTUI.interactive_cli()
    except KeyboardInterrupt:
        console.print("\n[bold red]程序被用户中断[/bold red]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[bold red]发生未预期的错误: {e}[/bold red]")
        sys.exit(1)
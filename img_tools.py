import sys
import loguru
from pathlib import Path

# 配置日志记录器(保存一份到本地log.log)
loguru.logger.add(
    Path(__file__).resolve().parent / "log.log",
    rotation="1 MB",
    retention="7 days",
    level="DEBUG",
)

# TODO: 图片水印
# TODO: 图片上色
if __name__ == "__main__":
    try:
        if len(sys.argv) > 1:
            from img_tools_cli import app

            app()
        else:
            from interaction_tui import InteractionTUI

            InteractionTUI.interactive_cli()
    except Exception as e:
        loguru.logger.error(f"发生错误: {e}")


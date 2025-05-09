import subprocess
import time
import loguru
import os

os.chdir(r"E:\load\python\Tools\img_tools\dist")

command = r'pyinstaller --noconfirm --onedir --console  "E:\load\python\Tools\img_tools\img_tools_cli.py"'

start_time = time.time()
subprocess.run(command, shell=True, check=True)
loguru.logger.success(f"打包完成，耗时 {time.time() - start_time:.2f} 秒")

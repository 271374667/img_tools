import subprocess
import time
import loguru
import os
import shutil
from pathlib import Path

dist_path = Path(r"E:\load\python\Tools\img_tools\dist")

if dist_path.exists():
    shutil.rmtree(dist_path)
    loguru.logger.info(f"删除 dist 目录: {dist_path}")
dist_path.mkdir(parents=True, exist_ok=True)

os.chdir(dist_path)

command = r'pyinstaller --noconfirm --onedir --console  "E:\load\python\Tools\img_tools\img_tools.py"'

start_time = time.time()
subprocess.run(command, shell=True, check=True)
loguru.logger.success(f"打包完成，耗时 {time.time() - start_time:.2f} 秒")

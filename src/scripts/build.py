import subprocess
import time
import loguru
import os
import shutil
from pathlib import Path
import winsound

dist_path = Path(r"E:\load\python\Tools\img_tools\dist")

if dist_path.exists():
    shutil.rmtree(dist_path)
    loguru.logger.info(f"删除 dist 目录: {dist_path}")
dist_path.mkdir(parents=True, exist_ok=True)
start_time = time.time()

os.chdir(dist_path)


def pyinstaller_build():
    command = r'pyinstaller --noconfirm --onedir --console --hidden-import=numpy --hidden-import=opencv-python "E:\load\python\Tools\img_tools\img_tools.py"'

    subprocess.run(command, shell=True, check=True)


def nuitka_build():
    command = r'"E:\load\python\Tools\img_tools\.venv\Scripts\python.exe" -m nuitka --standalone --show-progress --show-memory --mingw64 --disable-ccache --assume-yes-for-downloads --warn-implicit-exceptions --output-dir="E:\load\python\Tools\img_tools\dist" --main="E:\load\python\Tools\img_tools\img_tools.py" --windows-icon-from-ico="E:\load\python\Project\NuitkaGUI\dependence\logo.ico" --enable-plugins=upx,no-qt,matplotlib --include-package=torch --include-module=torch'
    subprocess.run(command, shell=True, check=True)


if __name__ == "__main__":
    # nuitka_build()
    pyinstaller_build()

    loguru.logger.success(f"打包完成，耗时 {time.time() - start_time:.2f} 秒")
    winsound.Beep(1000, 10000)  # 发出提示音
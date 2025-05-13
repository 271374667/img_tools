import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Literal, Optional

import GPUtil
import loguru
from PIL import Image
from tqdm import tqdm
from waifu2x_ncnn_py import Waifu2x

from src.core import constants
from src.core.enums import SuperResolutionModel
from src.utils.io_uitls import IOuitls


class SuperResolution:
    def process_dir(
        self,
        img_dir_path: Path | str,
        noise: Literal[-1, 0, 1, 2, 3] = 0,
        scale: Literal[1, 2, 3, 4] = 2,
        model: SuperResolutionModel = SuperResolutionModel.UpconvAnime,
        thread_num: Optional[int] = None,
        recursion: bool = True,
        suffix: Optional[tuple[str, ...]] = None,
        override: bool = True,
    ) -> Path:
        """批量超分辨率处理图片

        Args:
            img_dir_path: 图片文件夹路径
            noise: 降噪等级 (-1, 0, 1, 2, 3)
            scale: 放大倍数 (1, 2, 3, 4)
            model: 超分模型
            thread_num: 处理器数量 (线程池大小)
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
            else img_dir_path.with_name(f"{img_dir_path.stem}_sr{scale}x")
        )

        # 创建输出目录(如果不覆盖原图)
        if not override:
            if output_dir.exists():
                shutil.rmtree(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

            # 记录一下原图片路径
            detect_new_file_generator = IOuitls.detect_new_files(img_dir_path)
            next(detect_new_file_generator)  # 第一次迭代，记录初始文件集

        # 使用ThreadPoolExecutor进行多线程处理
        with ThreadPoolExecutor(max_workers=thread_num) as executor:
            # 提交所有任务到线程池
            futures = [
                executor.submit(
                    self._process_single_image,
                    img_path,
                    noise,
                    scale,
                    model,
                    override,
                )
                for img_path in img_paths
            ]

            # 使用tqdm创建进度条
            results = []
            desc = f"超分辨率处理(放大{scale}倍，降噪{noise})"
            for future in tqdm(
                as_completed(futures), total=len(futures), desc=desc, unit="张"
            ):
                result = future.result()
                # 如果结果是错误消息，则打印出来
                if isinstance(result, str) and result.startswith("Error"):
                    loguru.logger.error(result)
                results.append(result)

        if not override:
            # 第二次迭代，获取新增文件
            new_files = next(detect_new_file_generator)
            if new_files:
                for new_file in new_files:
                    # 移动文件
                    print(new_file.name.removesuffix("_out"))
                    shutil.move(new_file, output_dir / new_file.name)

            for i in output_dir.glob("**/*_out*"):
                i.rename(i.with_stem(i.stem.removesuffix("_out")))

        return output_dir

    def process(
        self,
        img_path: Path | str,
        noise: Literal[-1, 0, 1, 2, 3] = 0,
        scale: Literal[1, 2, 3, 4] = 2,
        model: SuperResolutionModel = SuperResolutionModel.UpconvAnime,
        override: bool = True,
    ) -> Path:
        """图片超分辨率处理

        Args:
            img_path (Path, str): 图片路径
            noise (Literal[-1, 0, 1, 2, 3]): 降噪等级
            scale (Literal[1, 2, 3, 4], optional): 放大倍数. Defaults to 2.
            model (SuperResolutionModel, optional): 超分模型. Defaults to SuperResolutionModel.UpconvAnime.
            override (bool, optional): 是否覆盖原图. Defaults to True.

        Returns:
            输出图片路径
        """
        img_path = Path(img_path)
        if not img_path.exists():
            raise FileNotFoundError(f"File {img_path} not found.")

        input_img_suffix = img_path.suffix.lower()
        if input_img_suffix not in constants.COMMON_IMAGE_SUFFIXES:
            raise ValueError(f"Unsupported image format: {input_img_suffix}")

        gpu_id = GPUtil.getFirstAvailable()[0] if GPUtil.getFirstAvailable() else -1
        waifu2x = Waifu2x(gpuid=gpu_id, scale=scale, noise=noise, model=model.value)
        with Image.open(str(img_path)) as image:
            image = waifu2x.process_pil(image)
            if override:
                output_img_path = img_path
                image.save(str(output_img_path), quality=95)
            else:
                output_img_path = img_path.with_stem(f"{img_path.stem}_out")
                image.save(str(output_img_path), quality=95)
            return output_img_path

    # 用于多线程处理的方法
    def _process_single_image(
        self,
        img_path,
        noise=0,
        scale=2,
        model=SuperResolutionModel.UpconvAnime,
        override=True,
    ):
        try:
            return self.process(
                img_path, noise=noise, scale=scale, model=model, override=override
            )
        except Exception as e:
            return f"Error processing {img_path}: {e}"


if __name__ == "__main__":
    s = SuperResolution()
    # print(s.thread_num)
    # print(GPUtil.getFirstAvailable())
    # print(s.process(r"E:\load\python\Tools\img_tools\测试\megasig.png", noise=3, model=SuperResolutionModel.UpconvPhoto))
    print(
        s.process_dir(
            r"E:\load\python\Tools\img_tools\测试",
            noise=3,
            model=SuperResolutionModel.UpconvPhoto,
        )
    )

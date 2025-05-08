from pathlib import Path
from typing import Literal, Optional
import multiprocessing
import GPUtil
from waifu2x_ncnn_py import Waifu2x
from PIL import Image
from src.core import constants
from src.core.enums import SuperResolutionModel


class SuperResolution:
    def __init__(self, thread_num: Optional[int] = None):
        self.thread_num = (
            max(1, multiprocessing.cpu_count() // 2) if not thread_num else thread_num
        )
        available_gpus = GPUtil.getFirstAvailable()
        self._gpu_id = available_gpus[0] if available_gpus else -1

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

        waifu2x = Waifu2x(
            gpuid=self._gpu_id, scale=scale, noise=noise, model=model.value
        )
        with Image.open(str(img_path)) as image:
            image = waifu2x.process_pil(image)
            if override:
                output_img_path = img_path
                image.save(str(output_img_path), quality=95)
            else:
                output_img_path = img_path.with_stem(f"{img_path.stem}_out")
                image.save(str(output_img_path), quality=95)
            return output_img_path


if __name__ == "__main__":
    s = SuperResolution()
    # print(s.thread_num)
    # print(GPUtil.getFirstAvailable())
    print(s.process(r"E:\load\python\Tools\img_tools\测试\megasig.png", noise=3, model=SuperResolutionModel.UpconvPhoto))

from enum import Enum

# 用于格式转换的格式枚举
class ImageFormat(str, Enum):
    JPG = "jpg"
    JPEG = "jpeg"
    PNG = "png"
    BMP = "bmp"
    WEBP = "webp"

# 下面是图片旋转的模式
class Orientation(Enum):
    Vertical = "vertical"  # 竖向
    Horizontal = "horizontal"  # 横向


class RotationMode(Enum):
    Clockwise = "clockwise"  # 顺时针
    CounterClockwise = "counterclockwise"  # 逆时针


# 下面是图片压缩的模式
class CompressionMode(Enum):
    Fastest = "fastest"  # 最快
    Smallest = "smallest"  # 最小
    Best = "best"  # 最好


# 下面是图片去重的模式
class SaveFileMode(Enum):
    SaveFirst = "save_first"  # 保存第一张 (按文件名排序)
    SaveLast = "save_last"  # 保存最后一张 (按文件名排序)
    SaveFirstAndLast = "save_first_and_last"  # 保存第一张和最后一张 (按文件名排序)
    SaveBigger = "save_bigger"  # 保存图片文件体积更大的
    SaveSmaller = "save_smaller"  # 保存图片文件体积更小的


class DuplicationMode(Enum):
    Fastest = "AHash"  # 最快 (Average Hash)
    Normal = "WHash"  # 均衡 (Wavelet Hash)
    Best = "PHash"  # 最好 (Perceptual Hash)
    CNN = "CNN"  # 使用深度学习模型进行去重 (卷积神经网络，通常最准确但最慢)


# 下面是超分模型选择
class SuperResolutionModel(Enum):
    Cunet = "models-cunet"  # Cunet 模型
    UpconvAnime = "models-upconv_7_anime_style_art_rgb"  # 动漫模型
    UpconvPhoto = "models-upconv_7_photo"  # 真实照片模型

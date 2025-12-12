import cv2
import numpy as np
from skimage.morphology import skeletonize
from skimage.util import invert

# 读取图像
image = cv2.imread(r'C:\szuPython\LLMtoNetlist\001.png', cv2.IMREAD_GRAYSCALE)

# 二值化处理
_, binary = cv2.threshold(image, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

# 转换为scikit-image需要的格式（0=背景,1=前景）
binary = np.where(binary == 0, 1, 0)  # 反转并转换为0/1

# 使用scikit-image骨架化
skeleton = skeletonize(binary)

# 转换回OpenCV格式
skeleton_image = skeleton.astype(np.uint8) * 255

cv2.imwrite('final.png', skeleton_image)
import cv2
# 读取图像
# 读取彩色图像变为灰度图
image = cv2.imread(r'C:\szuPython\LLMtoNetlist\001.png', cv2.IMREAD_GRAYSCALE)

thinned_image = cv2.ximgproc.thinning(image)
# 显示图像
cv2.imshow('Original Image', image)
cv2.imshow('Thinned Image', thinned_image)
cv2.waitKey(0)
cv2.destroyAllWindows()
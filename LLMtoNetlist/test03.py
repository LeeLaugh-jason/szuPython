import cv2
import numpy as np


def keep_largest_connected_component(image_path):
    # 读取图像
    img = cv2.imread(image_path)
    if img is None:
        print("无法读取图像，请检查路径是否正确")
        return

    # 转换为灰度图像
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 二值化（根据图像特性调整阈值）
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

    # 连通域分析
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary, connectivity=8)

    # 忽略背景（索引0是背景）
    if num_labels <= 1:
        print("未检测到连通域")
        return img

    # 找到最大连通域（排除背景）
    max_label = 1
    max_size = stats[1, cv2.CC_STAT_AREA]

    for label in range(2, num_labels):
        if stats[label, cv2.CC_STAT_AREA] > max_size:
            max_size = stats[label, cv2.CC_STAT_AREA]
            max_label = label

    # 创建黑色背景
    result = np.zeros_like(img)

    # 提取最大连通域并保留原始颜色
    result[labels == max_label] = img[labels == max_label]

    inverted_img = cv2.bitwise_not(result)

    return inverted_img


# 使用示例
if __name__ == "__main__":
    input_path = r"/LLMtoNetlist/final.png"  # 替换为你的输入图片路径
    output_path = "output.png"  # 输出图片路径

    result_image = keep_largest_connected_component(input_path)

    if result_image is not None:
        cv2.imwrite(output_path, result_image)
        print(f"处理完成，结果已保存至: {output_path}")
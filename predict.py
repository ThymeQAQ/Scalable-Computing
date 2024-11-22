from ultralytics import YOLO
import os

# 加载YOLO模型
model = YOLO("yolov8n.pt")  # 请确保你使用正确的模型文件路径

# 输入图片路径
image_path = r"D:\Scalable Computing\Project3\pic\humantest.jpg"  # 替换为你自己的图片路径

# 确保结果保存目录存在
output_folder = r"D:\Scalable Computing\Project3\ml"
os.makedirs(output_folder, exist_ok=True)

# 预测并保存结果到指定目录
results = model(image_path, save=True, project=r"D:\Scalable Computing\Project3", name="ml")

# 输出保存路径的提示信息
print(f"Results saved in: D:\\Scalable Computing\\Project3\\ml")

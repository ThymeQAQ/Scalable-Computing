from ultralytics import YOLO
import os


model = YOLO(".model//yolov8n.pt") 

image_path = "./pic/humantest.jpg" 

output_folder = "./output/ml"
os.makedirs(output_folder, exist_ok=True)

results = model(image_path, save=True, project="./output", name="ml")

print("Results saved in: ./output/ml")


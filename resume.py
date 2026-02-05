from ultralytics import YOLO

model = YOLO('runs/detect/stonka_model4/weights/last.pt')

results = model.train(resume=True)
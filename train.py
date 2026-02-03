from ultralytics import YOLO

# Load a pre-trained Nano model to start with
model = YOLO('yolov8n.pt') 

# Train the model
results = model.train(
    data='stonka_dataset/data.yaml', 
    epochs=50, 
    imgsz=640, 
    batch=16, 
    name='stonka_model'
)
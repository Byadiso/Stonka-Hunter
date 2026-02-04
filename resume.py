from ultralytics import YOLO

# Load the partially trained model
# Note: Point this to the 'last.pt' file in your most recent run folder
model = YOLO('runs/detect/stonka_model4/weights/last.pt')

# Resume the training
results = model.train(resume=True)
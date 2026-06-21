from ultralytics import YOLO
import torch

# Confirming CUDA acceleration before starting
device = 0 if torch.cuda.is_available() else 'cpu'
print(f"--- HARDWARE TARGET UNLOCKED: {torch.cuda.get_device_name(0) if device == 0 else 'CPU'} ---")

# 1. Load the heavier YOLOv8 Medium model for deep feature extraction
model = YOLO('yolov8m.pt')

# 2. Production-Grade Training Parameterization
model.train(
    data='data.yaml',       # Path to your dataset map
    epochs=150,             # Increased from 50 to 150 to let the deeper model truly mature
    batch=16,               # Safe batch processing size for a 4GB/6GB laptop GPU layout
    imgsz=640,              # Target input architecture
    device=device,          # Explicitly binds training directly to your RTX 3050 GPU
    patience=20,            # Early Stopping Guardrail: If accuracy doesn't improve for 20 epochs, stop automatically
    optimizer='AdamW',      # High-performance optimizer for precision object localization
    lr0=0.01,               # Initial learning rate
    cos_lr=True,            # Adjusts learning rate over time using a cosine curve for a smoother convergence
    val=True,               # Runs deep validation checking at the end of every single epoch
    save=True,              # Automatically caches checkpoint weights throughout the run
    plots=True              # Compiles detailed analytical precision-recall curves
)

print("\n--- Training Complete! Best weights are saved inside: runs/detect/train/weights/best.pt ---")

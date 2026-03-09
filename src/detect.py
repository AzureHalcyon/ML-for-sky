from ultralytics import YOLO
import cv2
import numpy as np
from typing import List, Optional
import os


class CandleDetector:
    def __init__(self, model_path: str = "models/candle.pt", conf: float = 0.7):
        self.model_path = model_path
        self.conf = conf
        self.model = None
        
        if os.path.exists(model_path):
            self.model = YOLO(model_path)
    
    def load(self, model_path: str):
        self.model = YOLO(model_path)
    
    def train(self, data_yaml: str, epochs: int = 100, imgsz: int = 640):
        if self.model is None:
            self.model = YOLO("yolov8n.pt")
        
        self.model.train(data=data_yaml, epochs=epochs, imgsz=imgsz, device=0)
        self.model.save("models/candle.pt")
    
    def detect(self, frame: np.ndarray) -> List[dict]:
        if self.model is None:
            raise ValueError("模型未加载")
        
        results = self.model(frame, conf=self.conf, verbose=False)
        detections = []
        
        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue
            
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                conf = float(box.conf[0].cpu().numpy())
                detections.append({
                    "bbox": [x1, y1, x2, y2],
                    "confidence": conf,
                    "center": [(x1 + x2) / 2, (y1 + y2) / 2]
                })
        
        return detections
    
    def get_nearest(self, detections: List[dict], w: int, h: int) -> Optional[dict]:
        if not detections:
            return None
        
        cx, cy = w / 2, h / 2
        nearest = min(detections, key=lambda d: ((d["center"][0]-cx)**2 + (d["center"][1]-cy)**2)**0.5)
        return nearest

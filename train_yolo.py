"""
训练 YOLOv8 蜡烛检测模型
"""

from ultralytics import YOLO


def train():
    print("开始训练 YOLOv8...")
    print("使用 GPU: RTX 4060")
    
    # 加载预训练模型
    model = YOLO("yolov8n.pt")
    
    # 训练
    results = model.train(
        data="data/candles.yaml",
        epochs=50,
        imgsz=640,
        batch=8,
        device=0,  # GPU
        workers=2
    )
    
    # 保存
    model.save("models/candle.pt")
    
    print("\n训练完成!")
    print("模型保存至：models/candle.pt")


if __name__ == "__main__":
    train()

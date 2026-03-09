"""
测试 YOLOv8 蜡烛检测模型效果
"""

from ultralytics import YOLO
import os


def test_image(model, image_path):
    """测试单张图片"""
    print(f"\n测试图片：{image_path}")
    results = model.predict(image_path, save=True, conf=0.25)
    result = results[0]
    
    # 打印检测结果
    print(f"检测框数量：{len(result.boxes)}")
    for box in result.boxes:
        cls = int(box.cls[0])
        conf = float(box.conf[0])
        name = model.names[cls]
        print(f"  - {name}: {conf:.2%}")
    
    return result


def test_folder(model, folder_path, max_images=10):
    """测试文件夹中的所有图片"""
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
    images = [f for f in os.listdir(folder_path) 
              if os.path.splitext(f)[1].lower() in image_extensions]
    
    print(f"\n找到 {len(images)} 张图片，测试前 {min(len(images), max_images)} 张")
    
    for img in images[:max_images]:
        test_image(model, os.path.join(folder_path, img))


def test_video(model, video_path):
    """测试视频"""
    print(f"\n测试视频：{video_path}")
    results = model.predict(video_path, save=True, conf=0.25)
    print("视频处理完成，结果保存在 runs/detect/predict/")


def find_latest_model():
    """查找最新的训练模型"""
    base_dir = "runs/detect"
    if not os.path.exists(base_dir):
        return None
    
    runs = []
    for name in os.listdir(base_dir):
        model_path = os.path.join(base_dir, name, "weights", "best.pt")
        if os.path.exists(model_path):
            mtime = os.path.getmtime(model_path)
            runs.append((model_path, mtime))
    
    if not runs:
        return None
    
    runs.sort(key=lambda x: x[1], reverse=True)
    return runs[0][0]


def main():
    # 加载最佳模型
    model_path = find_latest_model()
    
    if not model_path:
        print("错误：未找到训练完成的模型")
        print("请确认训练已完成")
        return
    
    print(f"加载模型：{model_path}")
    model = YOLO(model_path)
    
    # 选择测试方式
    print("\n=== 选择测试方式 ===")
    print("1. 测试验证集图片")
    print("2. 测试单张图片")
    print("3. 测试文件夹")
    print("4. 测试视频")
    print("5. 运行验证集评估")
    
    choice = input("\n请输入选项 (1-5): ").strip()
    
    if choice == "1":
        val_path = "data/candles/images/val"
        if os.path.exists(val_path):
            test_folder(model, val_path)
        else:
            print(f"验证集目录不存在：{val_path}")
    
    elif choice == "2":
        img_path = input("请输入图片路径：").strip()
        if os.path.exists(img_path):
            test_image(model, img_path)
        else:
            print("图片不存在")
    
    elif choice == "3":
        folder_path = input("请输入文件夹路径：").strip()
        if os.path.exists(folder_path):
            test_folder(model, folder_path)
        else:
            print("文件夹不存在")
    
    elif choice == "4":
        video_path = input("请输入视频路径：").strip()
        if os.path.exists(video_path):
            test_video(model, video_path)
        else:
            print("视频不存在")
    
    elif choice == "5":
        print("\n运行验证集评估...")
        metrics = model.val(data="data/candles.yaml")
        print(f"\nmAP50: {metrics.box.map50:.4f}")
        print(f"mAP50-95: {metrics.box.map:.4f}")
    
    else:
        print("无效选项")


if __name__ == "__main__":
    main()

"""
划分训练集和验证集
"""

import os
import random
import shutil


def split_dataset(train_ratio: float = 0.9):
    images_dir = "data/images"
    labels_dir = "data/labels"
    
    # 获取所有图片
    images = [f for f in os.listdir(images_dir) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
    images.sort()
    
    # 只保留有标注的图片
    images_with_labels = []
    for img in images:
        base = os.path.splitext(img)[0]
        if os.path.exists(os.path.join(labels_dir, f"{base}.txt")):
            images_with_labels.append(img)
    
    print(f"总图片数：{len(images)}")
    print(f"已标注：{len(images_with_labels)}")
    
    if not images_with_labels:
        print("错误：没有已标注的图片")
        return
    
    # 打乱顺序
    random.seed(42)
    random.shuffle(images_with_labels)
    
    # 划分
    split_idx = int(len(images_with_labels) * train_ratio)
    train_images = images_with_labels[:split_idx]
    val_images = images_with_labels[split_idx:]
    
    # 创建目录
    dirs = [
        "data/candles/images/train",
        "data/candles/images/val",
        "data/candles/labels/train",
        "data/candles/labels/val"
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
    
    # 复制训练集
    for img in train_images:
        base = os.path.splitext(img)[0]
        shutil.copy(os.path.join(images_dir, img), f"data/candles/images/train/{img}")
        shutil.copy(os.path.join(labels_dir, f"{base}.txt"), f"data/candles/labels/train/{base}.txt")
    
    # 复制验证集
    for img in val_images:
        base = os.path.splitext(img)[0]
        shutil.copy(os.path.join(images_dir, img), f"data/candles/images/val/{img}")
        shutil.copy(os.path.join(labels_dir, f"{base}.txt"), f"data/candles/labels/val/{base}.txt")
    
    print(f"\n划分完成:")
    print(f"  训练集：{len(train_images)} 张")
    print(f"  验证集：{len(val_images)} 张")
    print(f"\n目录：data/candles/")


if __name__ == "__main__":
    split_dataset()

# 光遇自动收集蜡烛 AI

## 环境要求
- Python 3.10+
- Windows 10/11
- 网易版光遇 PC 端
- **CUDA 12.x**

### 1. 采集蜡烛图片
```bash
python tools/collect.py
```
- **空格键** 截图
- 目标：200+ 张

### 2. 标注
```bash
python tools/label.py
```
- **鼠标左键** 画框
- **1** 小蜡烛 / **2** 大蜡烛
- **S** 保存 / **X** 删除
- **A/D** 切换图片

### 3. 划分数据集
```bash
python tools/split_dataset.py
```

### 4. 训练 YOLOv8
```bash
python train_yolo.py
```
- GPU 训练约 10-20 分钟
- 模型保存至：`models/candle.pt`

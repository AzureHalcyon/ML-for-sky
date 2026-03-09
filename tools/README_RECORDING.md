# 光遇录制工具

录制游戏画面并同步记录键鼠操作，用于模仿学习训练。

## 使用方法

以管理员身份运行 PowerShell：
```powershell
python tools/record.py
```

## 热键

| 按键 | 功能 |
|------|------|
| `F1` | 开始/停止录制 |
| `F2` | 暂停/继续 |
| `F3` | 退出程序 |

## 输出

```
data/recordings/
└── rec_001/
    ├── video_seg_001.mp4    # 视频 (30 FPS)
    ├── events_seg_001.jsonl # 键鼠事件
    └── metadata.json        # 元数据
```

## 事件格式

```json
{"t": 0.016, "type": "key", "key": "w", "event": "down"}
{"t": 0.032, "type": "mouse", "dx": 5, "dy": -3}
{"t": 0.048, "type": "mouse", "button": "left", "event": "click"}
```

## 说明

1. **帧率**：30 FPS（1280x764 窗口）
2. **时间同步**：视频时长与实际录制时间基本一致（误差<0.5 秒）
3. **按键打印**：录制时会在终端打印按键操作
4. **自动分段**：每 10 分钟自动保存为新片段

"""
实时检测光遇游戏中的蜡烛
自动检测游戏窗口并分析画面中的蜡烛
"""

import sys
sys.path.insert(0, 'D:\\Works\\workplace\\ML-for-sky')

from src.capture import ScreenCapture
from src.detect import CandleDetector
import cv2
import numpy as np
import time


def draw_detections(frame, detections, w, h):
    """在画面上绘制检测结果"""
    for i, det in enumerate(detections):
        x1, y1, x2, y2 = map(int, det["bbox"])
        conf = det["confidence"]
        
        # 绘制检测框
        color = (0, 255, 0) if conf > 0.7 else (0, 255, 255)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        
        # 绘制标签
        label = f"{conf:.2%}"
        cv2.putText(frame, label, (x1, y1 - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        # 绘制中心点
        cx, cy = map(int, det["center"])
        cv2.circle(frame, (cx, cy), 5, (255, 0, 0), -1)
    
    # 绘制屏幕中心
    cv2.circle(frame, (w // 2, h // 2), 8, (0, 0, 255), -1)
    
    # 显示统计信息
    cv2.putText(frame, f"Candles: {len(detections)}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    return frame


def find_latest_model():
    """查找最新的训练模型"""
    import os
    base_dir = "runs/detect"
    if not os.path.exists(base_dir):
        return "models/candle.pt"
    
    runs = []
    for name in os.listdir(base_dir):
        model_path = os.path.join(base_dir, name, "weights", "best.pt")
        if os.path.exists(model_path):
            mtime = os.path.getmtime(model_path)
            runs.append((model_path, mtime))
    
    if not runs:
        return "models/candle.pt"
    
    runs.sort(key=lambda x: x[1], reverse=True)
    return runs[0][0]


def main():
    print("=== 光遇蜡烛实时检测 ===")
    print("正在初始化...")
    
    # 加载模型
    model_path = find_latest_model()
    print(f"加载模型：{model_path}")
    detector = CandleDetector(model_path=model_path, conf=0.5)
    
    if detector.model is None:
        print("错误：无法加载模型")
        return
    
    # 初始化截屏
    capture = ScreenCapture(window_title="光·遇")
    
    print("\n正在查找光遇窗口...")
    print("提示：如果未找到窗口，请确保游戏已打开且窗口标题包含'光·遇'")
    
    last_capture_time = 0
    capture_interval = 0.02  # 检测间隔（秒）
    
    while True:
        # 查找窗口
        hwnd = capture.find_window()
        
        if not hwnd:
            print("\r未找到光遇窗口，继续查找...", end="", flush=True)
            time.sleep(1)
            continue
        
        print(f"\r已找到窗口，开始检测... (按 Q 退出)")
        
        # 主检测循环
        while True:
            current_time = time.time()
            
            # 按指定间隔检测
            if current_time - last_capture_time >= capture_interval:
                frame = capture.capture()
                
                if frame is None:
                    print("\r窗口已关闭，重新查找...")
                    break
                
                h, w = frame.shape[:2]
                
                # 检测蜡烛
                detections = detector.detect(frame)
                
                # 获取最近的蜡烛
                nearest = detector.get_nearest(detections, w, h)
                if nearest:
                    det_center = nearest["center"]
                    screen_center = (w / 2, h / 2)
                    dx = det_center[0] - screen_center[0]
                    dy = det_center[1] - screen_center[1]
                    distance = (dx * dx + dy * dy) ** 0.5
                    direction = ""
                    if det_center[0] < screen_center[0] - 50:
                        direction = "← 左"
                    elif det_center[0] > screen_center[0] + 50:
                        direction = "右 →"
                    elif det_center[1] < screen_center[1] - 50:
                        direction = "↑ 上"
                    elif det_center[1] > screen_center[1] + 50:
                        direction = "↓ 下"
                    else:
                        direction = "★ 中心"
                    
                    # 在画面显示最近蜡烛信息
                    info_text = f"最近：{direction} ({distance:.0f}px)"
                    cv2.putText(frame, info_text, (10, h - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                
                # 绘制检测结果
                frame = draw_detections(frame, detections, w, h)
                
                # 显示画面
                cv2.imshow("Candle Detection", frame)
                
                last_capture_time = current_time
            
            # 检测按键
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == ord('Q'):
                print("\n退出检测")
                cv2.destroyAllWindows()
                return
            elif key == ord(' '):
                # 空格键暂停/继续
                capture_interval = 10 if capture_interval < 1 else 0.5
                status = "已暂停" if capture_interval > 1 else "继续检测"
                print(f"\r{status}")
    
    cv2.destroyAllWindows()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n中断退出")
        cv2.destroyAllWindows()

"""
蜡烛图片采集工具

使用方法:
1. 打开光遇游戏 (窗口标题：光·遇)
2. 运行：python tools/collect.py
3. 按 空格键 截图，ESC 退出
4. 图片保存到 data/images/
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2
from src.capture import ScreenCapture


def collect(num_samples: int = 9999):
    capture = ScreenCapture("光·遇")
    
    print("=" * 50)
    print("蜡烛图片采集工具")
    print("=" * 50)
    print("操作说明:")
    print("  空格键 - 截图保存")
    print("  ESC    - 退出")
    print(f"目标：{num_samples} 张")
    print("=" * 50)
    
    os.makedirs("data/images", exist_ok=True)
    count = 0
    
    try:
        while count < num_samples:
            frame = capture.capture()
            
            if frame is None:
                print("\r未找到游戏窗口，请启动游戏...", end="", flush=True)
                time.sleep(1)
                continue
            
            # 在画面上显示计数
            info_text = f"Count: {count}"
            cv2.putText(frame, info_text, (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            # 显示操作提示
            hint_text = "SPACE: Save | ESC: Exit"
            cv2.putText(frame, hint_text, (10, frame.shape[0] - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            cv2.imshow("Collect", frame)
            
            # 增加等待时间，确保按键能被捕获
            key = cv2.waitKey(10) & 0xFF
            
            if key == 32:  # 空格键
                count += 1
                filepath = f"data/images/{count:04d}.jpg"
                cv2.imwrite(filepath, frame)
                
                # 显示保存成功提示
                print(f"\r已保存：{count} 张 -> {filepath}")
                
                # 在画面上显示保存成功
                save_frame = frame.copy()
                cv2.putText(save_frame, "SAVED!", (10, 70),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                cv2.imshow("Collect", save_frame)
                cv2.waitKey(100)
                
            elif key == 27:  # ESC
                print("\n退出")
                break
    except KeyboardInterrupt:
        print("\n中断")
    finally:
        cv2.destroyAllWindows()
        print(f"\n完成，共采集 {count} 张图片")
        print(f"保存目录：{os.path.abspath('data/images')}")


if __name__ == "__main__":
    collect()

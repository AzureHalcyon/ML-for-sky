"""
录制数据回放工具
验证录制的视频和键鼠事件同步性

使用方法:
    python tools/playback.py data/recordings/rec_001/
"""

import sys
import os
import json
import time
import cv2
from pathlib import Path
from typing import List, Dict, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load_events(events_path: Path) -> List[Dict[str, Any]]:
    """加载事件文件"""
    events = []
    with open(events_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                events.append(json.loads(line))
    return events


def load_metadata(metadata_path: Path) -> Dict[str, Any]:
    """加载元数据"""
    with open(metadata_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def format_time(seconds: float) -> str:
    """格式化时间"""
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"


def draw_keys(frame, pressed_keys: set):
    """在画面上绘制当前按下的键"""
    if not pressed_keys:
        return frame
    
    # 绘制按键区域
    keys_text = " + ".join(sorted(pressed_keys))
    cv2.rectangle(frame, (10, frame.shape[0] - 50), (200, frame.shape[0] - 10), 
                  (0, 0, 0), -1)
    cv2.putText(frame, f"Keys: {keys_text}", (15, frame.shape[0] - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    return frame


def draw_mouse(frame, mouse_info: Dict[str, Any]):
    """在画面上绘制鼠标信息"""
    if not mouse_info:
        return frame
    
    y_offset = 60
    x_start = 10
    
    if 'dx' in mouse_info or 'dy' in mouse_info:
        dx = mouse_info.get('dx', 0)
        dy = mouse_info.get('dy', 0)
        mouse_text = f"Mouse: dx={dx:+d}, dy={dy:+d}"
        cv2.putText(frame, mouse_text, (x_start, frame.shape[0] - y_offset),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
    
    if 'button' in mouse_info:
        button = mouse_info.get('button', '')
        event = mouse_info.get('event', '')
        click_text = f"Click: {button} {event}"
        cv2.putText(frame, click_text, (x_start, frame.shape[0] - y_offset - 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
    
    return frame


def playback_recording(recording_dir: str, speed: float = 1.0):
    """回放录制数据"""
    recording_path = Path(recording_dir)
    
    if not recording_path.exists():
        print(f"错误：目录不存在 {recording_dir}")
        return
    
    # 加载元数据
    metadata_path = recording_path / "metadata.json"
    if not metadata_path.exists():
        print(f"错误：未找到 metadata.json")
        return
    
    metadata = load_metadata(metadata_path)
    print(f"\n=== 回放录制数据 ===")
    print(f"录制 ID: {metadata['recording_id']}")
    print(f"时间：{metadata['start_time']}")
    print(f"时长：{format_time(metadata['total_duration'])}")
    print(f"片段数：{metadata['segments']}")
    print(f"帧率：{metadata['fps']} FPS")
    print(f"分辨率：{metadata['resolution'][0]}x{metadata['resolution'][1]}")
    print(f"总事件数：{metadata['total_events']}")
    print("=" * 50)
    
    # 选择片段
    segment_num = 1
    if metadata['segments'] > 1:
        print(f"\n可用片段：1 - {metadata['segments']}")
        try:
            segment_num = int(input(f"选择片段 (默认 1): ") or "1")
            segment_num = max(1, min(segment_num, metadata['segments']))
        except ValueError:
            segment_num = 1
    
    # 加载视频
    video_path = recording_path / f"video_seg_{segment_num:03d}.mp4"
    if not video_path.exists():
        print(f"错误：视频文件不存在 {video_path.name}")
        return
    
    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print(f"\n播放片段 {segment_num}")
    print(f"视频帧数：{total_frames}")
    print(f"视频 FPS: {fps}")
    print(f"播放速度：{speed}x")
    print("-" * 50)
    print("控制:")
    print("  SPACE  - 暂停/继续")
    print("  ←/→    - 快退/快进 5 秒")
    print("  ↑/↓    - 调整播放速度")
    print("  ESC    - 退出")
    print("=" * 50)
    
    # 加载事件
    events_path = recording_path / f"events_seg_{segment_num:03d}.jsonl"
    events = []
    if events_path.exists():
        events = load_events(events_path)
        print(f"加载事件：{len(events)} 条")
    else:
        print("警告：未找到事件文件")
    
    # 回放
    pressed_keys = set()
    mouse_info = {}
    event_index = 0
    paused = False
    current_time = 0
    
    while True:
        frame_pos = int(current_time * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
        ret, frame = cap.read()
        
        if not ret:
            print("\n播放结束")
            break
        
        # 计算当前时间
        current_time = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
        
        # 处理当前时间点的事件
        while event_index < len(events) and events[event_index]["t"] <= current_time:
            event = events[event_index]
            
            if event["type"] == "key":
                key = event["key"]
                if event["event"] == "down":
                    pressed_keys.add(key)
                else:
                    pressed_keys.discard(key)
            
            elif event["type"] == "mouse":
                if "dx" in event or "dy" in event:
                    mouse_info = {"dx": event.get("dx", 0), "dy": event.get("dy", 0)}
                elif "button" in event:
                    mouse_info = {
                        "button": event["button"],
                        "event": event["event"]
                    }
            
            event_index += 1
        
        # 绘制信息
        frame = draw_keys(frame, pressed_keys)
        frame = draw_mouse(frame, mouse_info)
        
        # 绘制时间戳
        time_str = format_time(current_time)
        total_str = format_time(metadata['total_duration'])
        cv2.putText(frame, f"{time_str} / {total_str}", 
                    (frame.shape[1] - 200, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # 显示
        cv2.imshow("Playback", frame)
        
        # 按键控制
        key = cv2.waitKey(int(1000 / fps / speed)) & 0xFF
        
        if key == 27:  # ESC
            print("\n退出回放")
            break
        elif key == 32:  # SPACE
            paused = not paused
            while paused:
                cv2.putText(frame, "[PAUSED]", (frame.shape[1] // 2 - 50, frame.shape[0] // 2),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 3)
                cv2.imshow("Playback", frame)
                key = cv2.waitKey(100) & 0xFF
                if key == 32 or key == 27:
                    paused = False
                    if key == 27:
                        break
        elif key == 81 or key == 2424832:  # ←
            current_time = max(0, current_time - 5)
        elif key == 83 or key == 2555904:  # →
            current_time = min(metadata['total_duration'], current_time + 5)
        elif key == 82 or key == 2490368:  # ↑
            speed = min(4.0, speed * 1.5)
            print(f"\r速度：{speed:.1f}x", end="", flush=True)
        elif key == 84 or key == 2621440:  # ↓
            speed = max(0.25, speed / 1.5)
            print(f"\r速度：{speed:.1f}x", end="", flush=True)
    
    cap.release()
    cv2.destroyAllWindows()


def main():
    if len(sys.argv) < 2:
        print("使用方法：python tools/playback.py <recording_dir>")
        print("\n示例:")
        print("  python tools/playback.py data/recordings/rec_001/")
        print("\n查找可用的录制:")
        
        recordings_dir = Path("data/recordings")
        if recordings_dir.exists():
            recordings = list(recordings_dir.glob("rec_*"))
            if recordings:
                print("\n可用录制:")
                for rec in recordings:
                    metadata_path = rec / "metadata.json"
                    if metadata_path.exists():
                        with open(metadata_path, 'r') as f:
                            meta = json.load(f)
                        print(f"  {rec.name} - {meta['total_frames']} 帧，{meta['total_events']} 事件")
            else:
                print("  暂无录制数据")
        return
    
    recording_dir = sys.argv[1]
    
    # 支持速度参数
    speed = 1.0
    if len(sys.argv) > 2:
        try:
            speed = float(sys.argv[2])
        except ValueError:
            print(f"警告：无效的速度参数 {sys.argv[2]}，使用默认速度 1.0x")
    
    playback_recording(recording_dir, speed)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n中断退出")
    except Exception as e:
        print(f"\n错误：{e}")
        import traceback
        traceback.print_exc()

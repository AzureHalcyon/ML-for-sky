"""
光遇录制工具
管理员运行，F1 开始/停止，F2 暂停，ESC 退出
"""

import sys
import os
import time
import json
import cv2
import numpy as np
import mss
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from pynput.keyboard import Listener as KeyboardListener, Key
from pynput.mouse import Listener as MouseListener

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.capture import ScreenCapture


class Recorder:
    FPS = 30  # 1280x764 窗口约 50 FPS，设置 30 保证稳定
    SEGMENT_DURATION = 600  # 10 分钟
    
    def __init__(self, output_dir: str = "data/recordings"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.capture = ScreenCapture("光·遇")
        self.sct = mss.mss()
        
        self.is_recording = False
        self.is_paused = False
        self.start_time = 0.0
        self.segment_start_time = 0.0
        self.segment_index = 1
        self.recording_id = ""
        
        self.video_writer: Optional[cv2.VideoWriter] = None
        self.resolution = (0, 0)
        self.frame_count = 0
        self.actual_duration = 0.0  # 实际录制时长
        
        self.events: List[Dict[str, Any]] = []
        self.last_mouse_pos: Optional[tuple] = None
        
        self.total_frames = 0
        self.total_events = 0
    
    def _new_recording_id(self) -> str:
        existing = list(self.output_dir.glob("rec_*"))
        return f"rec_{len(existing) + 1:03d}"
    
    def _init_segment(self):
        seg_dir = self.output_dir / self.recording_id
        seg_dir.mkdir(parents=True, exist_ok=True)
        
        print("Finding game window...")
        while True:
            hwnd = self.capture.find_window()
            if hwnd:
                break
            time.sleep(0.5)
            print(".", end="", flush=True)
        
        rect = self.capture.get_window_rect()
        if not rect:
            raise RuntimeError("Cannot get window size")
        
        self.resolution = (rect[2] - rect[0], rect[3] - rect[1])
        print(f"\nWindow found: {self.resolution[0]}x{self.resolution[1]}")
        
        self.video_writer = cv2.VideoWriter(
            str(seg_dir / f"video_seg_{self.segment_index:03d}.mp4"),
            cv2.VideoWriter_fourcc(*'mp4v'),
            self.FPS,
            self.resolution
        )
        
        self._add_event({"type": "seg_start", "seg": self.segment_index})
        self.segment_start_time = time.perf_counter()
        self.frame_count = 0
    
    def _close_segment(self):
        self._add_event({"type": "seg_end", "seg": self.segment_index})
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None
        self._save_events()
        print(f"Segment {self.segment_index} saved")
    
    def _save_events(self):
        seg_dir = self.output_dir / self.recording_id
        with open(seg_dir / f"events_seg_{self.segment_index:03d}.jsonl", 'w') as f:
            for e in self.events:
                f.write(json.dumps(e) + '\n')
    
    def _add_event(self, event: Dict[str, Any]):
        if self.is_recording:
            event["t"] = round(time.perf_counter() - self.start_time, 6)
            self.events.append(event)
            self.total_events += 1
    
    def _on_key(self, key, is_press: bool):
        if not self.is_recording or self.is_paused:
            return
        try:
            k = key.char
        except AttributeError:
            k = str(key).replace('Key.', '')
        event_type = "down" if is_press else "up"
        self._add_event({"type": "key", "key": k, "event": event_type})
        # 打印按键操作
        action = "PRESS" if is_press else "RELEASE"
        print(f"[KEY {action}] {k}")
    
    def _on_mouse_move(self, x, y):
        if not self.is_recording or self.is_paused:
            return
        if self.last_mouse_pos:
            dx = x - self.last_mouse_pos[0]
            dy = y - self.last_mouse_pos[1]
            if dx != 0 or dy != 0:
                self._add_event({"type": "mouse", "dx": dx, "dy": dy})
        self.last_mouse_pos = (x, y)
    
    def _on_mouse_click(self, x, y, button, pressed):
        if not self.is_recording or self.is_paused:
            return
        btn = str(button).replace('Button.', '')
        self._add_event({"type": "mouse", "button": btn, "event": "click" if pressed else "release"})
    
    def start(self):
        if self.is_recording:
            return
        
        self.recording_id = self._new_recording_id()
        print(f"\n=== Start Recording: {self.recording_id} ===")
        
        self.is_recording = True
        self.is_paused = False
        self.start_time = time.perf_counter()
        self.segment_start_time = self.start_time
        self.segment_index = 1
        self.events = []
        self.total_frames = 0
        self.total_events = 0
        self.actual_duration = 0.0
        self.last_mouse_pos = None
        
        self._init_segment()
        print("Recording... (F1: Stop, F2: Pause, ESC: Exit)")
    
    def stop(self):
        if not self.is_recording:
            return
        
        self.actual_duration = time.perf_counter() - self.start_time
        
        print("\n=== Stop Recording ===")
        self.is_recording = False
        
        self._close_segment()
        
        # Save metadata
        meta = {
            "recording_id": self.recording_id,
            "start_time": datetime.now().isoformat(),
            "duration": round(self.actual_duration, 2),
            "segments": self.segment_index,
            "fps": self.FPS,
            "resolution": list(self.resolution),
            "frames": self.total_frames,
            "events": self.total_events
        }
        with open(self.output_dir / self.recording_id / "metadata.json", 'w') as f:
            json.dump(meta, f, indent=2)
        
        print(f"Saved: {self.recording_id}")
        print(f"Duration: {self.actual_duration:.2f}s, Frames: {self.total_frames}, Events: {self.total_events}")
    
    def toggle_pause(self):
        if not self.is_recording:
            return
        self.is_paused = not self.is_paused
        print(f"[{'Paused' if self.is_paused else 'Resumed'}]")
    
    def capture_frame(self, frame_time: float) -> Optional[np.ndarray]:
        """
        捕获帧并写入视频
        frame_time: 当前帧的时间戳（相对于 segment_start_time）
        """
        if not self.is_recording or self.is_paused:
            return None
        
        rect = self.capture.get_window_rect()
        if not rect:
            return None
        
        monitor = {
            "left": rect[0], "top": rect[1],
            "right": rect[2], "bottom": rect[3],
            "width": rect[2] - rect[0], "height": rect[3] - rect[1]
        }
        
        try:
            frame = cv2.cvtColor(np.array(self.sct.grab(monitor)), cv2.COLOR_BGRA2BGR)
            if self.video_writer:
                self.video_writer.write(frame)
                self.frame_count += 1
                self.total_frames += 1
            return frame
        except Exception:
            return None
    
    def check_segment(self):
        if time.perf_counter() - self.segment_start_time >= self.SEGMENT_DURATION:
            print(f"\nAuto-switch to segment {self.segment_index + 1}")
            self._close_segment()
            self.segment_index += 1
            self.events = []
            self._init_segment()
            return True  # 表示切换了片段
        return False


class App:
    def __init__(self):
        self.recorder = Recorder()
        self.running = True
        self.last_frame = None
        
        # Keyboard listener
        def on_press(key):
            if key == Key.f3:
                self.running = False
                return False
            elif key == Key.f1:
                if self.recorder.is_recording:
                    self.recorder.stop()
                else:
                    self.recorder.start()
            elif key == Key.f2:
                self.recorder.toggle_pause()
            else:
                self.recorder._on_key(key, True)
        
        def on_release(key):
            self.recorder._on_key(key, False)
        
        def on_move(x, y):
            self.recorder._on_mouse_move(x, y)
        
        def on_click(x, y, button, pressed):
            self.recorder._on_mouse_click(x, y, button, pressed)
        
        self.kbd_listener = KeyboardListener(on_press=on_press, on_release=on_release)
        self.mse_listener = MouseListener(on_move=on_move, on_click=on_click)
        self.kbd_listener.start()
        self.mse_listener.start()
    
    def draw_status(self, frame):
        h, w = frame.shape[:2]
        s = self.recorder
        
        # Status bar
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 70), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        if not s.is_recording:
            text, color = "READY - F1 to start", (0, 255, 0)
        elif s.is_paused:
            text, color = "PAUSED", (0, 165, 255)
        else:
            elapsed = int(time.perf_counter() - s.segment_start_time)
            text, color = f"REC {elapsed//60:02d}:{elapsed%60:02d}", (0, 0, 255)
        
        cv2.putText(frame, text, (15, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        cv2.putText(frame, f"Frames: {s.total_frames} Events: {s.total_events}", (15, 55),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 2)
        
        return frame
    
    def run(self):
        print("\n" + "=" * 50)
        print("  GuangYu Recording Tool")
        print("=" * 50)
        print("\n  F1     - Start/Stop recording")
        print("  F2     - Pause/Resume")
        print("  F3     - Exit")
        print("=" * 50)
        print("\nWaiting for game window...")
        
        frame_interval = 1.0 / self.recorder.FPS
        frames_since_segment_start = 0
        last_recording_state = False
        
        while self.running:
            now = time.perf_counter()
            
            # 检测录制状态变化
            if self.recorder.is_recording and not last_recording_state:
                frames_since_segment_start = 0  # 新录制开始，重置计数
            last_recording_state = self.recorder.is_recording
            
            if self.recorder.is_recording and not self.recorder.is_paused:
                if self.recorder.check_segment():
                    frames_since_segment_start = 0  # 自动分段，重置计数
                
                # 计算相对于 segment 开始的时间
                elapsed = now - self.recorder.segment_start_time
                
                # 按固定帧率捕获
                expected_frames = int(elapsed / frame_interval)
                if frames_since_segment_start < expected_frames:
                    frame = self.recorder.capture_frame(elapsed)
                    if frame is not None:
                        self.last_frame = frame
                        frames_since_segment_start += 1
            
            # Show preview
            if self.last_frame is not None:
                display = self.draw_status(self.last_frame.copy())
                cv2.imshow("Recording (F3 to exit)", display)
                cv2.waitKey(1)
            
            time.sleep(0.001)
        
        # Cleanup
        if self.recorder.is_recording:
            self.recorder.stop()
        cv2.destroyAllWindows()
        self.kbd_listener.stop()
        self.mse_listener.stop()
        print("\nExited")


if __name__ == "__main__":
    try:
        App().run()
    except KeyboardInterrupt:
        print("\nInterrupted")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

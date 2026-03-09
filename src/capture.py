import mss
import win32gui
import win32con
import numpy as np
import cv2
from typing import Optional, Tuple


class ScreenCapture:
    def __init__(self, window_title: str = "光·遇"):
        self.window_title = window_title
        self.hwnd: Optional[int] = None
        self.sct = mss.mss()
        
    def find_window(self) -> Optional[int]:
        def callback(hwnd, extra):
            if win32gui.IsWindowVisible(hwnd):
                if self.window_title in win32gui.GetWindowText(hwnd):
                    windows.append(hwnd)
            return True
        
        windows = []
        win32gui.EnumWindows(callback, None)
        
        if windows:
            self.hwnd = windows[0]
            return self.hwnd
        return None
    
    def get_window_rect(self) -> Optional[Tuple[int, int, int, int]]:
        if not self.hwnd:
            self.find_window()
        if not self.hwnd:
            return None
        return win32gui.GetWindowRect(self.hwnd)
    
    def capture(self) -> Optional[np.ndarray]:
        if not self.hwnd:
            self.find_window()
        if not self.hwnd:
            return None
        
        rect = self.get_window_rect()
        if not rect:
            return None
        
        monitor = {
            "left": rect[0],
            "top": rect[1],
            "right": rect[2],
            "bottom": rect[3],
            "width": rect[2] - rect[0],
            "height": rect[3] - rect[1]
        }
        screenshot = self.sct.grab(monitor)
        img = np.array(screenshot)
        return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

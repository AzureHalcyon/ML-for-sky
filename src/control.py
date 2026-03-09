from pynput.keyboard import Controller
from typing import Set


class KeyboardControl:
    def __init__(self):
        self.keyboard = Controller()
        self.pressed: Set[str] = set()
        self.action_map = {
            0: ["w"], 1: ["s"], 2: ["a"], 3: ["d"],
            4: ["w", "a"], 5: ["w", "d"], 6: ["s", "a"], 7: ["s", "d"]
        }
    
    def press(self, keys):
        for k in keys:
            if k not in self.pressed:
                self.keyboard.press(k)
                self.pressed.add(k)
    
    def release_all(self):
        for k in self.pressed:
            self.keyboard.release(k)
        self.pressed.clear()
    
    def action(self, act: int, duration: float = 0.1):
        import time
        self.release_all()
        self.press(self.action_map[act])
        time.sleep(duration)
        self.release_all()
    
    def stop(self):
        self.release_all()

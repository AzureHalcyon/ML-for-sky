"""
蜡烛标注工具
标注文件保存为 YOLO 格式
"""

import sys
import os
import cv2
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class LabelTool:
    def __init__(self, image_dir: str, label_dir: str):
        self.image_dir = image_dir
        self.label_dir = label_dir
        
        os.makedirs(label_dir, exist_ok=True)
        
        # 获取所有图片
        self.images = [f for f in os.listdir(image_dir) 
                      if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
        self.images.sort()
        
        if not self.images:
            print(f"错误：目录 {image_dir} 中没有图片")
            exit(1)
        
        self.current_idx = 0
        self.current_img = None
        self.drawing = False
        self.pt1 = None
        self.pt2 = None
        self.boxes = {}  # {img_name: [(x1, y1, x2, y2, class_name), ...]}
        
        # 类别配置
        self.classes = {
            '1': 'candle_small',
            '2': 'candle_big'
        }
        self.current_class = '1'
        
        # 颜色配置
        self.colors = {
            'candle_small': (0, 255, 0),   # 绿色
            'candle_big': (0, 0, 255)      # 红色
        }
        
        # 加载所有标注
        self.load_all_labels()
        
        # 创建窗口
        cv2.namedWindow('Label', cv2.WINDOW_NORMAL)
        cv2.setMouseCallback('Label', self.mouse_callback)
        
        print("=" * 50)
        print("蜡烛标注工具")
        print("=" * 50)
        print("操作说明:")
        print("  鼠标左键 - 拖动画框")
        print("  1 - 小蜡烛 (绿色)")
        print("  2 - 大蜡烛 (红色)")
        print("  S - 保存标注")
        print("  X - 删除最后一个框")
        print("  A - 上一张")
        print("  D - 下一张")
        print("  ESC - 退出")
        print("=" * 50)
        print(f"图片总数：{len(self.images)}")
        print(f"当前进度：{self.current_idx + 1}/{len(self.images)}")
        print("=" * 50)
    
    def load_all_labels(self):
        """加载所有已存在的标注文件"""
        for img_name in self.images:
            base_name = os.path.splitext(img_name)[0]
            label_path = os.path.join(self.label_dir, f"{base_name}.txt")
            
            if os.path.exists(label_path):
                self.boxes[img_name] = self.load_label_file(label_path, img_name)
            else:
                self.boxes[img_name] = []
    
    def load_label_file(self, label_path: str, img_name: str) -> list:
        """从 YOLO 格式文件加载标注"""
        boxes = []
        h, w = self.get_image_shape(img_name)
        
        with open(label_path, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) != 5:
                    continue
                
                cls_id = int(parts[0])
                x_center = float(parts[1]) * w
                y_center = float(parts[2]) * h
                box_w = float(parts[3]) * w
                box_h = float(parts[4]) * h
                
                x1 = int(x_center - box_w / 2)
                y1 = int(y_center - box_h / 2)
                x2 = int(x_center + box_w / 2)
                y2 = int(y_center + box_h / 2)
                
                class_name = list(self.classes.values())[cls_id]
                boxes.append((x1, y1, x2, y2, class_name))
        
        return boxes
    
    def get_image_shape(self, img_name: str) -> tuple:
        """获取图片宽高"""
        img_path = os.path.join(self.image_dir, img_name)
        img = cv2.imread(img_path)
        if img is not None:
            return img.shape[:2]
        return (480, 640)
    
    def mouse_callback(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.drawing = True
            self.pt1 = (x, y)
        elif event == cv2.EVENT_MOUSEMOVE:
            if self.drawing:
                self.pt2 = (x, y)
        elif event == cv2.EVENT_LBUTTONUP:
            self.drawing = False
            self.pt2 = (x, y)
            
            if self.pt1 and self.pt2:
                x1, y1 = self.pt1
                x2, y2 = self.pt2
                
                x1, x2 = min(x1, x2), max(x1, x2)
                y1, y2 = min(y1, y2), max(y1, y2)
                
                if x2 - x1 > 10 and y2 - y1 > 10:
                    img_name = self.images[self.current_idx]
                    if img_name not in self.boxes:
                        self.boxes[img_name] = []
                    
                    class_name = self.classes[self.current_class]
                    self.boxes[img_name].append((x1, y1, x2, y2, class_name))
        
        self.draw_image()
    
    def draw_image(self):
        if self.current_img is None:
            return
        
        img = self.current_img.copy()
        img_name = self.images[self.current_idx]
        current_boxes = self.boxes.get(img_name, [])
        
        # 绘制已保存的框
        for x1, y1, x2, y2, class_name in current_boxes:
            color = self.colors.get(class_name, (0, 255, 0))
            cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
            cv2.putText(img, class_name, (x1, y1 - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        # 绘制正在画的框
        if self.drawing and self.pt1 and self.pt2:
            x1, y1 = self.pt1
            x2, y2 = self.pt2
            x1, x2 = min(x1, x2), max(x1, x2)
            y1, y2 = min(y1, y2), max(y1, y2)
            
            color = self.colors.get(self.classes[self.current_class], (0, 255, 0))
            cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
        
        # 显示信息
        img_name = self.images[self.current_idx]
        current_boxes = self.boxes.get(img_name, [])
        info = f"{self.current_idx + 1}/{len(self.images)} | Type: {self.current_class} | Boxes: {len(current_boxes)}"
        cv2.putText(img, info, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        cv2.imshow('Label', img)
    
    def save_labels(self):
        """保存标注为 YOLO 格式"""
        if self.current_img is None:
            print("错误：当前没有图片")
            return
        
        img_name = self.images[self.current_idx]
        base_name = os.path.splitext(img_name)[0]
        label_path = os.path.join(self.label_dir, f"{base_name}.txt")
        
        h, w = self.current_img.shape[:2]
        current_boxes = self.boxes.get(img_name, [])
        
        try:
            with open(label_path, 'w', encoding='utf-8') as f:
                for x1, y1, x2, y2, class_name in current_boxes:
                    cls_id = list(self.classes.values()).index(class_name)
                    x_center = (x1 + x2) / 2 / w
                    y_center = (y1 + y2) / 2 / h
                    box_w = (x2 - x1) / w
                    box_h = (y2 - y1) / h
                    
                    f.write(f"{cls_id} {x_center:.6f} {y_center:.6f} {box_w:.6f} {box_h:.6f}\n")
            
            print(f"\n[OK] 已保存：{label_path} ({len(current_boxes)} 个框)")
        except Exception as e:
            print(f"\n[ERROR] 保存失败：{e}")
    
    def next_image(self):
        if self.current_idx < len(self.images) - 1:
            self.current_idx += 1
            self.load_current_image()
    
    def prev_image(self):
        if self.current_idx > 0:
            self.current_idx -= 1
            self.load_current_image()
    
    def load_current_image(self):
        img_name = self.images[self.current_idx]
        img_path = os.path.join(self.image_dir, img_name)
        self.current_img = cv2.imread(img_path)
        
        # 加载该图片的标注
        if img_name not in self.boxes:
            self.boxes[img_name] = []
        
        self.draw_image()
        print(f"\r加载：{img_name} | 进度：{self.current_idx + 1}/{len(self.images)} | 标注：{len(self.boxes[img_name])}", end="", flush=True)
    
    def delete_last_box(self):
        img_name = self.images[self.current_idx]
        if img_name in self.boxes and self.boxes[img_name]:
            self.boxes[img_name].pop()
            self.draw_image()
    
    def run(self):
        self.load_current_image()
        
        while True:
            key = cv2.waitKey(10) & 0xFF
            
            if key == 27:  # ESC
                print("\n退出")
                break
            elif key == ord('s') or key == ord('S'):  # 保存
                self.save_labels()
            elif key == ord('x') or key == ord('X'):  # 删除
                self.delete_last_box()
            elif key == ord('a') or key == ord('A'):  # 上一张
                self.prev_image()
            elif key == ord('d') or key == ord('D'):  # 下一张
                self.next_image()
            elif key == ord('1'):  # 小蜡烛
                self.current_class = '1'
                self.draw_image()
            elif key == ord('2'):  # 大蜡烛
                self.current_class = '2'
                self.draw_image()
        
        cv2.destroyAllWindows()
        print(f"\n标注完成，共 {len(self.images)} 张图片")


def main():
    image_dir = "data/images"
    label_dir = "data/labels"
    
    if not os.path.exists(image_dir):
        print(f"错误：图片目录 {image_dir} 不存在")
        print("请先运行采集工具采集图片")
        return
    
    tool = LabelTool(image_dir, label_dir)
    tool.run()


if __name__ == "__main__":
    main()

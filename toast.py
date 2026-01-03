import threading
import time
import tkinter as tk
from queue import Queue
import ctypes

ctypes.windll.shcore.SetProcessDpiAwareness(1)

class ToastWindow:
    def __init__(self, parent_root, text, font_size, bg, duration):
        """创建浮动消息窗口"""
        self.parent_root = parent_root
        self.window = tk.Toplevel(parent_root)
        self.window.hang_on = False
        
        # 设置窗口属性
        self.window.overrideredirect(True)
        self.window.attributes('-topmost', True)
        self.window.configure(bg=bg)

        # 绑定可拖动
        self.window.bind('<ButtonPress-1>', self._on_drag_start)
        self.window.bind('<ButtonRelease-1>', self._on_drag_stop)
        self.window.bind('<B1-Motion>', self._on_drag_motion)
        self.window.bind('<Escape>', self._destroy_window)
        
        # 创建文字标签
        label = tk.Label(
            self.window,
            text=text,
            font=('Microsoft YaHei', font_size),
            fg='white',
            bg=bg,
            justify=tk.LEFT,
            wraplength=1200
        )
        label.pack(padx=20, pady=15)
        
        # 更新窗口以确保获取正确的尺寸
        self.window.update_idletasks()
        
        # 设置窗口位置
        self._set_window_position()
        
        # 显示窗口
        self.window.deiconify()
        
        # 设置定时器，在指定时间后销毁窗口
        self.pause = False
        self.window.after(duration, self._destroy_window)
    
    def _set_window_position(self):
        """设置窗口位置"""
        try:
            screen_width = self.window.winfo_screenwidth()
            screen_height = self.window.winfo_screenheight()
            
            window_width = self.window.winfo_width()
            window_height = self.window.winfo_height()
            
            x = (screen_width - window_width) // 2
            y = screen_height // 10 * 8
            
            self.window.geometry(f'+{x}+{y}')
        except:
            pass
    
    def _on_drag_start(self, event):
        self.pause = True
        self.x = event.x
        self.y = event.y

    def _on_drag_stop(self, event):
        self.pause = False

    def _on_drag_motion(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.window.winfo_x() + deltax
        y = self.window.winfo_y() + deltay
        self.window.geometry(f"+{x}+{y}")
    
    def _destroy_window(self, event=None):
        """销毁窗口"""
        try:
            if self.pause:
                # 如果窗口被暂停（拖动），延迟销毁
                self.window.after(100, self._destroy_window)
            else:
                self.window.destroy()  # 销毁窗口
        except:
            pass


class ToastMessageManager:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance.initialized = False
            return cls._instance
    
    def __init__(self):
        if not self.initialized:
            self.message_queue = Queue()
            self.is_running = False
            self.initialized = True
            self.active_windows = []  # 跟踪活动窗口
            
            # 在子线程中启动 Tkinter
            self.manager_thread = threading.Thread(target=self._run_manager)
            self.manager_thread.daemon = True
            self.manager_thread.start()
    
    def _run_manager(self):
        """在子线程中运行 Tkinter 主循环"""
        # 创建隐藏的主窗口
        self.root = tk.Tk()
        self.root.withdraw()  # 隐藏主窗口
        self.root.tk.call('tk', 'scaling', 2)
        
        # 设置窗口关闭时的行为
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # 开始处理队列
        self.is_running = True
        self._process_queue()
        
        # 启动 Tkinter 主循环
        self.root.mainloop()
    
    def _on_close(self):
        """关闭所有窗口并退出"""
        self.is_running = False
        for window in self.active_windows[:]:
            try:
                window.window.destroy()
            except:
                pass
        self.active_windows.clear()
        self.root.quit()
    
    def _process_queue(self):
        """处理队列中的消息"""
        try:
            # 检查是否有新消息
            if not self.message_queue.empty():
                text, font_size, bg, duration = self.message_queue.get_nowait()
                
                # 创建新窗口
                toast_window = ToastWindow(self.root, text, font_size, bg, duration)
                self.active_windows.append(toast_window)
                
                # 设置窗口销毁时的回调
                toast_window.window.bind('<Destroy>', 
                    lambda e, w=toast_window: self._remove_window(w))
            
            # 清理已销毁的窗口
            self.active_windows = [w for w in self.active_windows 
                                 if w.window.winfo_exists()]
            
        except Exception as e:
            # 忽略队列空异常等
            pass
        
        # 继续处理队列
        if self.is_running:
            self.root.after(100, self._process_queue)
    
    def _remove_window(self, window):
        """从活动窗口列表中移除窗口"""
        if window in self.active_windows:
            self.active_windows.remove(window)
    
    def add_message(self, text, font_size, bg, duration):
        """添加消息到队列"""
        self.message_queue.put((text, font_size, bg, duration))


def toast(text, font_size=14, bg="#C41529", duration=2000):
    """显示浮动消息的便捷函数"""
    manager = ToastMessageManager()
    manager.add_message(text, font_size, bg, duration)


# 使用示例
if __name__ == "__main__":
    message_text = """21:14:13 【国际航协：中国四大航空公司加入航班数据交互项目】 财联社11月14日电，从国际航协获悉，中国东方航空公司宣布加入国际航协航班计划数据交互项目（SDEP）。至此，该计划已涵盖中国四大航空公司——中国国际航空公司、中国东方航空公司、中国南方航空公司和海南航空公司，标志着该计划在中国市场的推进迈出了重要一步。随着中国四大航空公司加入航班计划数据交互项目，该项目目前涵盖了中国民航75%以上的运力。 (证券时报)"""
    
    # 测试多个消息
    toast(message_text, bg="#075077", duration=3000)
    time.sleep(4)
    toast(message_text, bg="#C41529", duration=2000)
    time.sleep(4)
    toast(message_text, bg="#008000", duration=1000)
    
    # 保持主线程运行
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("程序退出")

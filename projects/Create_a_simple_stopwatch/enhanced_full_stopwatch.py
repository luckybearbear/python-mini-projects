import time
import tkinter as tk
from tkinter import ttk
from typing import Optional, List
import pystray
from PIL import Image


class StopWatch:
    # ====================== 常量配置区（统一调整UI参数） ======================
    WINDOW_TITLE = "简易秒表"
    WINDOW_SIZE = "520x320"
    REFRESH_INTERVAL_MS = 10  # 界面刷新间隔(毫秒)
    FONT_FAMILY = "Consolas"
    TIME_FONT_SIZE = 36
    BUTTON_FONT_SIZE = 10
    BUTTON_WIDTH = 8

    PAD_X_BUTTON = 4
    PAD_Y_LABEL = 15
    PAD_Y_FRAME = 10

    # 按钮配色
    COLOR_START = "#34a853"
    COLOR_STOP = "#fbbc05"
    COLOR_RESET = "#ea4335"
    COLOR_LAP = "#4285f4"
    COLOR_HOVER_OFFSET = 15  # hover提亮

    def __init__(self, root: tk.Tk):
        """
        秒表初始化
        :param root: tk顶层主窗口实例
        """
        self.root: tk.Tk = root
        self.root.title(self.WINDOW_TITLE)
        self.root.geometry(self.WINDOW_SIZE)
        self.root.resizable(width=False, height=False)

        # 计时状态
        self.running: bool = False
        self.start_time: float = 0.0
        self.elapsed: float = 0.0
        self.after_task_id: Optional[str] = None

        # Lap计次记录
        self.lap_list: List[float] = []
        self.lap_index = 1

        # 托盘相关
        self.tray_icon: Optional[pystray.Icon] = None
        self.is_quitting = False  # 防止重复执行退出逻辑

        # 拦截窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self._on_window_close)

        # 构建界面控件
        self._build_widgets()
        self.sync_btn_state()
        self.update_display()

        # 绑定全局快捷键
        self._bind_hotkey()

    def _build_widgets(self) -> None:
        """UI构建：时间显示、按钮、计次列表"""
        # 主时间标签
        self.time_label = tk.Label(
            self.root,
            text="00:00:00.000",
            font=(self.FONT_FAMILY, self.TIME_FONT_SIZE)
        )
        self.time_label.pack(pady=self.PAD_Y_LABEL)

        # 按钮容器
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=self.PAD_Y_FRAME)

        # 开始按钮
        self.btn_start = tk.Button(
            btn_frame, text="开始", width=self.BUTTON_WIDTH, font=(None, self.BUTTON_FONT_SIZE),
            bg=self.COLOR_START, command=self.start
        )
        self.btn_start.grid(row=0, column=0, padx=self.PAD_X_BUTTON)
        self._bind_button_hover(self.btn_start, self.COLOR_START)

        # 停止按钮
        self.btn_stop = tk.Button(
            btn_frame, text="停止", width=self.BUTTON_WIDTH, font=(None, self.BUTTON_FONT_SIZE),
            bg=self.COLOR_STOP, command=self.stop
        )
        self.btn_stop.grid(row=0, column=1, padx=self.PAD_X_BUTTON)
        self._bind_button_hover(self.btn_stop, self.COLOR_STOP)

        # Lap计次按钮
        self.btn_lap = tk.Button(
            btn_frame, text="计次(Lap)", width=self.BUTTON_WIDTH + 2, font=(None, self.BUTTON_FONT_SIZE),
            bg=self.COLOR_LAP, command=self.lap
        )
        self.btn_lap.grid(row=0, column=2, padx=self.PAD_X_BUTTON)
        self._bind_button_hover(self.btn_lap, self.COLOR_LAP)

        # 重置按钮
        self.btn_reset = tk.Button(
            btn_frame, text="重置", width=self.BUTTON_WIDTH, font=(None, self.BUTTON_FONT_SIZE),
            bg=self.COLOR_RESET, command=self.reset
        )
        self.btn_reset.grid(row=0, column=3, padx=self.PAD_X_BUTTON)
        self._bind_button_hover(self.btn_reset, self.COLOR_RESET)

        # Lap记录列表容器
        lap_frame = tk.Frame(self.root)
        lap_frame.pack(pady=10, fill=tk.BOTH, expand=True)

        # 滚动条 + Listbox展示计次
        scroll_bar = ttk.Scrollbar(lap_frame)
        scroll_bar.pack(side=tk.RIGHT, fill=tk.Y)
        self.lap_box = tk.Listbox(
            lap_frame, yscrollcommand=scroll_bar.set,
            font=(self.FONT_FAMILY, 11)
        )
        scroll_bar.config(command=self.lap_box.yview)
        self.lap_box.pack(fill=tk.BOTH, expand=True)

    def _bind_button_hover(self, btn: tk.Button, base_color: str):
        """绑定按钮hover变色效果"""
        r = int(base_color[1:3], 16)
        g = int(base_color[3:5], 16)
        b = int(base_color[5:7], 16)

        # 简单提亮
        hr = min(r + self.COLOR_HOVER_OFFSET, 255)
        hg = min(g + self.COLOR_HOVER_OFFSET, 255)
        hb = min(b + self.COLOR_HOVER_OFFSET, 255)
        hover_color = f"#{hr:02X}{hg:02X}{hb:02X}"

        def enter(_):
            if btn["state"] == tk.NORMAL:
                btn.config(bg=hover_color)

        def leave(_):
            if btn["state"] == tk.NORMAL:
                btn.config(bg=base_color)

        btn.bind("<Enter>", enter)
        btn.bind("<Leave>", leave)

    def _bind_hotkey(self):
        """绑定全局快捷键
        空格：开始/暂停
        R：重置
        """
        self.root.bind("<space>", self._toggle_start_stop)
        self.root.bind("<Key-r>", lambda e: self.reset())
        self.root.bind("<Key-R>", lambda e: self.reset())

    def _toggle_start_stop(self, event):
        """空格触发：运行则暂停，暂停则继续"""
        if self.running:
            self.stop()
        else:
            self.start()

    def format_time(self, sec_total: float) -> str:
        """秒数格式化 HH:MM:SS.000"""
        hours = int(sec_total // 3600)
        mins = int((sec_total % 3600) // 60)
        secs = sec_total % 60
        return f"{hours:02d}:{mins:02d}:{secs:06.3f}"

    def start(self) -> None:
        """启动/继续计时"""
        if not self.running:
            self.running = True
            self.start_time = time.time() - self.elapsed
            self.sync_btn_state()
            self._tick()

    def stop(self) -> None:
        """暂停计时"""
        self.running = False
        self.sync_btn_state()

    def reset(self) -> None:
        """重置秒表，清空计时与计次记录"""
        self.running = False
        self.elapsed = 0.0
        self.lap_list.clear()
        self.lap_index = 1
        self.lap_box.delete(0, tk.END)
        self.time_label.config(text="00:00:00.000")
        self.sync_btn_state()

    def lap(self) -> None:
        """保存一段计次记录"""
        record = self.elapsed
        self.lap_list.append(record)
        text = f"Lap {self.lap_index:02d} | {self.format_time(record)}"
        self.lap_box.insert(tk.END, text)
        self.lap_box.see(tk.END)
        self.lap_index += 1

    def _tick(self) -> None:
        """定时刷新计时"""
        if not self.running:
            return
        self.elapsed = time.time() - self.start_time
        self.update_display()
        self.after_task_id = self.root.after(self.REFRESH_INTERVAL_MS, self._tick)

    def sync_btn_state(self) -> None:
        """统一控制按钮启用/置灰"""
        if self.running:
            # 计时中：停止、计次可用
            self.btn_start.config(state=tk.DISABLED)
            self.btn_stop.config(state=tk.NORMAL)
            self.btn_lap.config(state=tk.NORMAL)
            self.btn_reset.config(state=tk.DISABLED)
        elif self.elapsed > 0:
            # 暂停状态：开始、重置可用
            self.btn_start.config(state=tk.NORMAL)
            self.btn_stop.config(state=tk.DISABLED)
            self.btn_lap.config(state=tk.DISABLED)
            self.btn_reset.config(state=tk.NORMAL)
        else:
            # 初始清零：仅开始可用
            self.btn_start.config(state=tk.NORMAL)
            self.btn_stop.config(state=tk.DISABLED)
            self.btn_lap.config(state=tk.DISABLED)
            self.btn_reset.config(state=tk.DISABLED)

    def update_display(self) -> None:
        """刷新主时间文本"""
        self.time_label.config(text=self.format_time(self.elapsed))

    def _create_tray_icon(self):
        """创建托盘图标，无图标文件则生成简易图片"""
        if self.tray_icon is not None:
            return
        image = Image.new("RGB", (64, 64), color="#4285f4")
        menu = pystray.Menu(
            pystray.MenuItem("显示窗口", self._show_window),
            pystray.MenuItem("退出程序", self._quit_app)
        )
        self.tray_icon = pystray.Icon("stopwatch", image, self.WINDOW_TITLE, menu)

    def _hide_to_tray(self):
        """隐藏窗口，最小化到托盘"""
        if self.is_quitting:
            return
        self.root.withdraw()
        self._create_tray_icon()
        self.tray_icon.run_detached()

    def _show_window(self):
        """从托盘恢复窗口（投递至tk主线程）"""
        self.root.after(0, self.root.deiconify)

    def _quit_app(self):
        """托盘菜单触发退出入口（运行在pystray子线程）"""
        if self.is_quitting:
            return
        self.is_quitting = True
        # 跨线程禁止直接操作tk，交给主线程调度执行
        self.root.after(0, self._safe_exit)

    def _safe_exit(self):
        """在tk主线程执行真正资源释放与退出"""
        # 停止托盘
        if self.tray_icon:
            self.tray_icon.stop()
        # 取消定时刷新任务
        if self.after_task_id is not None:
            self.root.after_cancel(self.after_task_id)
        # 销毁窗口，终止mainloop
        self.root.destroy()

    def _on_window_close(self):
        """点击窗口右上角X：最小化托盘，不直接退出"""
        if self.is_quitting:
            return
        self._hide_to_tray()


if __name__ == "__main__":
    root = tk.Tk()
    app = StopWatch(root)
    root.mainloop()
import time
import tkinter as tk
from typing import Optional


class StopWatch:
    # ====================== 常量配置区（统一调整UI参数） ======================
    WINDOW_TITLE = "简易秒表"
    WINDOW_SIZE = "380x180"
    REFRESH_INTERVAL_MS = 10  # 界面刷新间隔(毫秒)
    FONT_FAMILY = "Consolas"
    FONT_SIZE = 36
    BUTTON_WIDTH = 8
    PAD_X_BUTTON = 6
    PAD_X_RESET = 8
    PAD_Y_LABEL = 20
    PAD_Y_FRAME = 10

    def __init__(self, root: tk.Tk):
        """
        秒表初始化
        :param root: tk顶层主窗口实例
        """
        self.root: tk.Tk = root
        self.root.title(self.WINDOW_TITLE)
        self.root.geometry(self.WINDOW_SIZE)
        # 禁止窗口自由缩放，防止布局错乱
        self.root.resizable(width=False, height=False)

        # 计时运行标记：True=正在计时；False=暂停/初始状态
        self.running: bool = False
        # 计时基准起始时间戳
        self.start_time: float = 0.0
        # 累计已计时总秒数
        self.elapsed: float = 0.0
        # after定时任务ID，用于销毁窗口时取消排队回调，避免内存残留
        self.after_task_id: Optional[str] = None

        # 构建所有界面控件
        self._build_widgets()
        # 同步按钮启用/置灰状态
        self.sync_btn_state()
        # 初始化时间文本显示
        self.update_display()

        # 拦截窗口关闭事件，执行资源清理后再销毁窗口
        self.root.protocol("WM_DELETE_WINDOW", self._on_window_close)

    def _build_widgets(self) -> None:
        """UI构建方法，界面代码与业务计时逻辑分离"""
        # 时间显示标签
        self.time_label = tk.Label(
            self.root,
            text="00:00:00.000",
            font=(self.FONT_FAMILY, self.FONT_SIZE)
        )
        self.time_label.pack(pady=self.PAD_Y_LABEL)

        # 创建按钮容器Frame，统一管理三个按钮布局
        frame = tk.Frame(self.root)
        frame.pack(pady=self.PAD_Y_FRAME)

        # 开始按钮
        self.btn_start = tk.Button(
            frame, text="开始", width=self.BUTTON_WIDTH, command=self.start
        )
        self.btn_start.grid(row=0, column=0, padx=self.PAD_X_BUTTON)

        # 停止按钮
        self.btn_stop = tk.Button(
            frame, text="停止", width=self.BUTTON_WIDTH, command=self.stop
        )
        self.btn_stop.grid(row=0, column=1, padx=self.PAD_X_BUTTON)

        # 重置按钮
        self.btn_reset = tk.Button(
            frame, text="重置", width=self.BUTTON_WIDTH, command=self.reset
        )
        self.btn_reset.grid(row=0, column=2, padx=self.PAD_X_RESET)

    def start(self) -> None:
        """启动/继续计时"""
        if not self.running:
            self.running = True
            # 支持暂停后续跑：当前时间 - 已消耗时间 = 新基准起点
            self.start_time = time.time() - self.elapsed
            self.sync_btn_state()
            self._tick()

    def stop(self) -> None:
        """暂停计时"""
        self.running = False
        self.sync_btn_state()

    def reset(self) -> None:
        """重置秒表，清零所有计时数据"""
        self.running = False
        self.elapsed = 0.0
        self.time_label.config(text="00:00:00.000")
        self.sync_btn_state()

    def _tick(self) -> None:
        """定时回调，持续计算流逝时间"""
        # 如果已经暂停，终止后续递归调度
        if not self.running:
            return

        # 实时计算从基准起点到当前一共流逝多少秒
        self.elapsed = time.time() - self.start_time
        self.update_display()
        # 注册下一轮刷新任务，保存任务id用于后续取消
        self.after_task_id = self.root.after(self.REFRESH_INTERVAL_MS, self._tick)

    def sync_btn_state(self) -> None:
        """统一管理按钮启用/置灰逻辑，防止出现非法操作"""
        if self.running:
            # 计时中：仅停止按钮可用
            self.btn_start.config(state=tk.DISABLED)
            self.btn_stop.config(state=tk.NORMAL)
            self.btn_reset.config(state=tk.DISABLED)
        elif self.elapsed > 0:
            # 已暂停、存在计时数据：可以继续计时或者重置
            self.btn_start.config(state=tk.NORMAL)
            self.btn_stop.config(state=tk.DISABLED)
            self.btn_reset.config(state=tk.NORMAL)
        else:
            # 初始清零状态：仅允许点击开始
            self.btn_start.config(state=tk.NORMAL)
            self.btn_stop.config(state=tk.DISABLED)
            self.btn_reset.config(state=tk.DISABLED)

    def update_display(self) -> None:
        """将总秒数格式化为 HH:MM:SS.毫秒 并更新界面文本"""
        sec_total = self.elapsed
        hours = int(sec_total // 3600)
        mins = int((sec_total % 3600) // 60)
        secs = sec_total % 60
        self.time_label.config(text=f"{hours:02d}:{mins:02d}:{secs:06.3f}")

    def _on_window_close(self) -> None:
        """窗口关闭回调：清理定时任务，释放资源"""
        # 取消还在排队的after定时回调
        if self.after_task_id is not None:
            self.root.after_cancel(self.after_task_id)
        # 销毁主窗口
        self.root.destroy()


if __name__ == "__main__":
    # 程序入口
    root = tk.Tk()
    app = StopWatch(root)
    # 启动tk消息循环
    root.mainloop()
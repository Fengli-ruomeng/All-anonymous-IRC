import asyncio
import queue
import sys
import threading
import tkinter as tk
from tkinter import scrolledtext

# --- 配置 ---
HOST = '127.0.0.1'
PORT = 6667
# --------------

class IRCClientGUI:

    def __init__(self, root):
        self.root = root
        self.root.title("KaguyaIRC 客户端")
        self.root.geometry("800x600")

        self.message_queue = queue.Queue()
        self.command_queue = None # Will be created within the asyncio thread
        self.current_channel = None
        self.connection_active = False
        self.thread = None

        self._setup_gui()

        self.running = True
        self.root.after(100, self._process_message_queue)
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

        self.insert_message("欢迎来到 KaguyaIRC!\n", "system")
        self.insert_message("使用 /chelp 查看可用命令。\n", "system")
        
        # 自动连接
        self._start_connection()


    def _start_connection(self):
        """启动一个新的网络线程来连接服务器。"""
        if self.thread and self.thread.is_alive():
            self.insert_message("错误: 已经有一个活动的连接。\n", "error")
            return

        self.connection_active = True
        self.thread = threading.Thread(target=self._run_asyncio_loop, daemon=True)
        self.thread.start()

    def _disconnect(self):
        """断开与服务器的连接。"""
        if not self.connection_active:
            self.insert_message("提示: 当前没有活动的连接。\n", "info")
            return
        
        # 礼貌地发送QUIT命令
        if hasattr(self, 'loop') and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(self.command_queue.put("QUIT :Client disconnected\r\n"), self.loop)
        
        self.connection_active = False
        self.insert_message("正在断开连接...\n", "system")

    def _setup_gui(self):
        """设置UI组件"""
        bg_color = "#000000"
        fg_color = "#ECEFF4"
        font_spec = ("JetBrains Mono", 13)

        self.root.configure(bg=bg_color)

        # --- Frame for input and button at the bottom ---
        input_frame = tk.Frame(self.root, bg=bg_color)
        input_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(5, 10))

        self.input_entry = tk.Entry(
            input_frame, font=font_spec, bg=bg_color, fg=fg_color,
            insertbackground=fg_color, relief=tk.FLAT
        )
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5)
        self.input_entry.bind("<Return>", self._on_enter_pressed)
        self.input_entry.focus_set()

        send_button = tk.Button(
            input_frame, text="发送", font=("Microsoft YaHei", 12),
            command=self._send_input, bg="#262626", fg=fg_color,
            activebackground="#5E81AC", activeforeground=fg_color,
            relief=tk.FLAT, padx=10
        )
        send_button.pack(side=tk.RIGHT, padx=(5, 0))
        
        # --- ScrolledText for messages, fills the rest of the space ---
        self.text_area = scrolledtext.ScrolledText(
            self.root, wrap=tk.WORD, state='disabled', font=font_spec,
            bg=bg_color, fg=fg_color, insertbackground=fg_color, relief=tk.FLAT,
            borderwidth=0, highlightthickness=0
        )
        self.text_area.pack(padx=10, pady=(10, 0), fill=tk.BOTH, expand=True)

        self.text_area.tag_config('server', foreground='#8FBCBB')
        self.text_area.tag_config('user_input', foreground='#EBCB8B')
        self.text_area.tag_config('system', foreground='#D08770')
        self.text_area.tag_config('error', foreground='#BF616A', font=font_spec)
        self.text_area.tag_config('info', foreground='#81A1C1')
        self.text_area.tag_config('privmsg', foreground=fg_color)

    def _send_input(self):
        """处理输入框的文本发送"""
        text = self.input_entry.get().strip()
        if not text:
            return
            
        self.input_entry.delete(0, tk.END)
        self.insert_message(f"> {text}\n", "user_input")

        if text.startswith('/'):
            command_with_args = text[1:]
            parts = command_with_args.split(" ", 1)
            command = parts[0].upper()
            args = parts[1] if len(parts) > 1 else ""

            # 纯客户端命令
            if command == "CONNECT":
                self._start_connection()
                return
            if command == "DISCONNECT":
                self._disconnect()
                return
            if command == "CHELP":
                self.insert_message("--- 客户端命令 ---\n", "info")
                self.insert_message("/connect - 连接到服务器\n", "info")
                self.insert_message("/disconnect - 从服务器断开\n", "info")
                self.insert_message("/help - 显示此帮助信息\n", "info")
                self.insert_message("--- 服务器命令 (需要连接) ---\n", "info")
                self.insert_message("/NICK <nickname> - 注册或更改昵称\n", "info")
                self.insert_message("/JOIN <#channel> - 加入频道\n", "info")
                self.insert_message("/PART <#channel> - 离开频道\n", "info")
                self.insert_message("/LIST - 列出所有可用频道\n", "info")
                return

            # 需要连接的服务器命令
            if not self.connection_active:
                self.insert_message("错误: 发送命令前请先连接到服务器 (/connect)\n", "error")
                return

            if command == "JOIN":
                if args:
                    channel = args.split()[0]
                    if channel.startswith("#"):
                        self.current_channel = channel # 跟踪当前频道
                    asyncio.run_coroutine_threadsafe(self.command_queue.put(f"JOIN {args}\r\n"), self.loop)
                else:
                    self.insert_message("用法: /JOIN <#channel> [key]\n", "error")
            elif command == "NICK":
                 if args:
                    nickname = args.split()[0]
                    asyncio.run_coroutine_threadsafe(self.command_queue.put(f"NICK {nickname}\r\n"), self.loop)
                    # IRC 协议要求 NICK 和 USER 一起发送以进行初始注册
                    asyncio.run_coroutine_threadsafe(self.command_queue.put(f"USER {nickname} 0 * :{nickname}\r\n"), self.loop)
                 else:
                    self.insert_message("用法: /NICK <nickname>\n", "error")
            else:
                asyncio.run_coroutine_threadsafe(self.command_queue.put(command_with_args + "\r\n"), self.loop)
        else:
            if not self.connection_active:
                self.insert_message("错误: 发送消息前请先连接到服务器 (/connect)\n", "error")
                return

            if self.current_channel:
                message_to_send = f"PRIVMSG {self.current_channel} :{text}\r\n"
                asyncio.run_coroutine_threadsafe(self.command_queue.put(message_to_send), self.loop)
            else:
                self.insert_message("错误: 您当前不在任何频道中。请使用 /join #频道名 加入一个频道。\n", "error")

    def _on_enter_pressed(self, event):
        """处理输入框的回车事件"""
        self._send_input()

    def _process_message_queue(self):
        """从队列中获取消息并显示在UI上"""
        try:
            while True:
                line, tag = self.message_queue.get_nowait()
                self.insert_message(line, tag)
        except queue.Empty:
            pass
        
        if self.running:
            self.root.after(100, self._process_message_queue)

    def insert_message(self, message: str, tag: str):
        """向文本区域插入消息"""
        self.text_area.config(state='normal')
        self.text_area.insert(tk.END, message, tag)
        self.text_area.config(state='disabled')
        self.text_area.see(tk.END)

    def _on_closing(self):
        """处理窗口关闭"""
        self.running = False
        if self.connection_active:
            self._disconnect()
        # 等待一小段时间让消息发送
        self.root.after(200, self.root.destroy)

    def _run_asyncio_loop(self):
        """在后台线程中运行asyncio事件循环"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.command_queue = asyncio.Queue() 
        try:
            self.loop.run_until_complete(self.irc_main())
        except Exception as e:
            self.message_queue.put((f"网络线程错误: {e}\n", "error"))

    async def irc_main(self):
        """IRC网络通信主函数"""
        try:
            self.message_queue.put((f"正在连接到 {HOST}:{PORT}...\n", "info"))
            reader, writer = await asyncio.open_connection(HOST, PORT)
            self.message_queue.put((f"成功连接到服务器。\n", "info"))
        except ConnectionRefusedError:
            self.message_queue.put((f"!!! 连接失败: 服务器拒绝连接。\n", "error"))
            self.connection_active = False
            return
        except Exception as e:
            self.message_queue.put((f"!!! 连接失败: {e}\n", "error"))
            self.connection_active = False
            return

        read_task = asyncio.create_task(self.read_from_server(reader))
        write_task = asyncio.create_task(self.write_to_server(writer))
        
        # 等待任一任务完成 (表示断开)
        done, pending = await asyncio.wait([read_task, write_task], return_when=asyncio.FIRST_COMPLETED)

        for task in pending:
            task.cancel() # 确保另一个任务也被取消

        # 清理writer
        if writer.can_write_eof():
            writer.write_eof()
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass # 忽略关闭时的错误

        self.connection_active = False
        self.message_queue.put(("!!! 连接已关闭。使用 /connect 重新连接。\n", "system"))


    async def read_from_server(self, reader: asyncio.StreamReader):
        """持续从服务器读取消息"""
        while self.connection_active:
            try:
                data = await reader.readline()
                if not data:
                    break
                line = data.decode('utf-8', 'ignore').strip()
                if line:
                    if line.startswith("PING"):
                        response = f"PONG :{line.split(':', 1)[1]}\r\n"
                        asyncio.run_coroutine_threadsafe(self.command_queue.put(response), self.loop)
                        self.message_queue.put((f"<-- {line}\n", "server"))
                    else:
                        self.message_queue.put((f"<-- {line}\n", "privmsg"))
            except (ConnectionResetError, asyncio.CancelledError):
                break
            except Exception as e:
                 self.message_queue.put((f"!!! 读取时出错: {e}\n", "error"))
                 break
        self.connection_active = False


    async def write_to_server(self, writer: asyncio.StreamWriter):
        """持续从命令队列中获取命令并发送到服务器"""
        while self.connection_active:
            try:
                # 使用超时来定期检查 self.connection_active 状态
                command = await asyncio.wait_for(self.command_queue.get(), timeout=1.0)
                writer.write(command.encode('utf-8'))
                await writer.drain()
            except asyncio.TimeoutError:
                continue # 没有命令，继续循环
            except (asyncio.CancelledError, ConnectionResetError):
                break
            except Exception as e:
                 self.message_queue.put((f"!!! 发送时出错: {e}\n", "error"))
                 break
        self.connection_active = False


if __name__ == "__main__":
    app_root = tk.Tk()
    client_gui = IRCClientGUI(app_root)
    app_root.mainloop()
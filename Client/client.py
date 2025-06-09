import asyncio
import sys

# --- 配置 ---
# 如果服务器运行在另一台机器上，请将 HOST 修改为服务器的 IP 地址
HOST = '154.37.215.134'
PORT = 6667
# --------------

async def handle_server_message(line: str, writer: asyncio.StreamWriter):
    """解析并处理来自服务器的单行消息。"""
    print(f"\r<-- {line.strip()}", flush=True)
    print("> ", end="", flush=True) # 重新显示输入提示符

    parts = line.split()
    if not parts:
        return

    # 自动响应服务器的 PING 请求以保持连接
    if parts[0].upper() == "PING":
        response = f"PONG :{parts[1] if len(parts) > 1 else ''}\r\n"
        writer.write(response.encode())
        await writer.drain()
        # 我们可以选择不打印 PONG 消息，以保持界面清洁
        # print(f"--> PONG", flush=True)

async def read_from_server(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    """持续监听来自服务器的消息。"""
    while not reader.at_eof():
        try:
            data = await reader.readline()
            if not data:
                print("\r!!! 与服务器的连接已断开。", flush=True)
                break
            line = data.decode('utf-8', errors='ignore').strip()
            if line:
                await handle_server_message(line, writer)
        except ConnectionResetError:
            print("\r!!! 连接被重置。", flush=True)
            break
        except Exception as e:
            print(f"\r!!! 读取服务器消息时出错: {e}", flush=True)
            break

async def read_from_input(writer: asyncio.StreamWriter):
    """持续监听用户的键盘输入。"""
    current_channel = ""
    loop = asyncio.get_running_loop()

    while True:
        print("> ", end="", flush=True)
        try:
            # 使用 to_thread 在不阻塞事件循环的情况下读取 stdin
            line = await loop.run_in_executor(None, sys.stdin.readline)
            line = line.strip()
        except asyncio.CancelledError:
            break

        if not line:
            continue

        if line.startswith("/"):
            # 以 / 开头的输入被视为命令
            parts = line.split(" ", 1)
            command = parts[0][1:].upper()
            args = parts[1] if len(parts) > 1 else ""

            if command == "JOIN" and args:
                # 跟踪当前频道，以便发送裸消息
                current_channel = args.split()[0]
                message = f"JOIN {args}\r\n"
            elif command == "QUIT":
                message = f"QUIT :{args or '客户端关闭'}\r\n"
                writer.write(message.encode())
                await writer.drain()
                break # 退出循环，关闭客户端
            else:
                message = f"{command} {args}\r\n"
        else:
            # 裸消息被发送到当前频道
            if current_channel:
                message = f"PRIVMSG {current_channel} :{line}\r\n"
            else:
                print("!!! 您当前不在任何频道中。请使用 /join #channel_name 加入一个频道。", flush=True)
                continue
        
        writer.write(message.encode())
        await writer.drain()

async def main():
    print("--- KaguyaIRC 客户端 ---")
    try:
        reader, writer = await asyncio.open_connection(HOST, PORT)
    except ConnectionRefusedError:
        print(f"!!! 无法连接到 {HOST}:{PORT}。服务器是否正在运行？")
        return
    except Exception as e:
        print(f"!!! 连接失败: {e}")
        return

    # 从用户处获取昵称
    nickname = ""
    while not nickname:
        nickname = input("请输入您的昵称[此昵称不可更改]: ").strip()

    # 发送 NICK 和 USER 命令进行注册
    writer.write(f"NICK {nickname}\r\n".encode())
    writer.write(f"USER {nickname} 0 * :{nickname}\r\n".encode())
    await writer.drain()

    print(f"--- 已作为 {nickname} 连接。输入 /join #channel 加入频道。---")

    # 创建并发任务来处理服务器消息和用户输入
    server_task = asyncio.create_task(read_from_server(reader, writer))
    input_task = asyncio.create_task(read_from_input(writer))

    # 等待任一任务完成（例如用户输入 /quit 或服务器断开连接）
    done, pending = await asyncio.wait(
        [server_task, input_task],
        return_when=asyncio.FIRST_COMPLETED
    )

    for task in pending:
        task.cancel()
    
    writer.close()
    await writer.wait_closed()
    print("--- 连接已关闭。 ---")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n客户端已关闭。") 
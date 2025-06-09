import asyncio
import logging
from pydoc import Helper
from re import A
from typing import Dict, Set, Optional, List

import config

# 配置日志记录
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(config.LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class Client:
    """代表一个连接到服务器的客户端"""
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self.reader = reader
        self.writer = writer
        self.nickname: Optional[str] = None
        self.username: Optional[str] = None
        self.realname: Optional[str] = None
        self.is_operator = False
        self.channels: Set['Channel'] = set()
        self.ip, self.port = writer.get_extra_info('peername')

    async def send(self, message: str):
        """向客户端发送一条消息"""
        if not message.endswith("\r\n"):
            message += "\r\n"
        try:
            self.writer.write(message.encode('utf-8'))
            await self.writer.drain()
        except ConnectionResetError:
            logging.warning(f"尝试向已断开的客户端 {self.nickname or self.ip} 发送消息失败。")

    def get_prefix(self) -> str:
        """获取客户端的 IRC 前缀"""
        if self.nickname and self.username:
            return f"{self.nickname}!{self.username}@{self.ip}"
        return config.SERVER_NAME

class Channel:
    """代表一个 IRC 频道"""
    def __init__(self, name: str, server: 'Server'):
        self.name = name
        self.server = server
        self.clients: Set[Client] = set()
        self.topic: Optional[str] = None
        self.password: Optional[str] = None

    async def broadcast(self, message: str, sender_to_exclude: Optional[Client] = None):
        """向频道中的所有客户端广播消息，可选择排除一个发送者。"""
        # 创建一个副本以安全地迭代，以防在广播期间有客户端加入/离开
        clients_to_send = list(self.clients)
        for client in clients_to_send:
            if client != sender_to_exclude:
                await client.send(message)

    def add_client(self, client: Client):
        """将客户端添加到频道"""
        self.clients.add(client)
        client.channels.add(self)

    def remove_client(self, client: Client):
        """从频道移除客户端"""
        if client in self.clients:
            self.clients.remove(client)
            client.channels.remove(self)

class Server:
    """IRC 服务器主类"""
    def __init__(self):
        self.clients: Set[Client] = set()
        self.channels: Dict[str, Channel] = {}
        self.nicknames: Dict[str, Client] = {}

    async def handle_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """处理新的客户端连接"""
        client = Client(reader, writer)
        self.clients.add(client)
        logging.info(f"接受来自 {client.ip}:{client.port} 的新连接。")

        try:
            while not reader.at_eof():
                data = await reader.readline()
                if not data:
                    break
                
                line = data.decode('utf-8', errors='ignore').strip()
                if not line:
                    continue
                
                logging.info(f"[RECV] 来自 {client.nickname or client.ip}: {line}")
                
                parts = line.split(' ', 1)
                command = parts[0].upper()
                args = parts[1] if len(parts) > 1 else ""

                handler = getattr(self, f"handle_{command.lower()}", None)
                if handler:
                    await handler(client, args.split())
                else:
                    logging.warning(f"未知命令: {command} from {client.nickname or client.ip}")
                    # 可以选择向客户端发送一个未知命令的数字回复
                    await client.send(f":{config.SERVER_NAME} 421 {client.nickname or '*'} {command} :Unknown command")

        except (ConnectionResetError, BrokenPipeError):
            logging.info(f"客户端 {client.nickname or client.ip} 意外断开连接。")
        finally:
            await self.disconnect_client(client, "Connection closed")

    async def disconnect_client(self, client: Client, reason: str):
        """处理客户端断开连接"""
        if client not in self.clients:
            return

        logging.info(f"客户端 {client.nickname or client.ip} 断开连接: {reason}")

        # 从所有频道中移除
        for channel in list(client.channels):
            channel.remove_client(client)
            await channel.broadcast(f":{client.get_prefix()} PART {channel.name} :{reason}")

        # 从服务器移除
        if client.nickname and client.nickname in self.nicknames:
            del self.nicknames[client.nickname]
        self.clients.remove(client)

        try:
            client.writer.close()
            await client.writer.wait_closed()
        except Exception as e:
            logging.error(f"关闭客户端 {client.nickname} 的 writer 时出错: {e}")

    # --- IRC 命令处理函数 ---

    async def _check_registration(self, client: Client):
        """检查客户端是否已通过发送 NICK 和 USER 完成注册"""
        if client.nickname and client.username and not client.realname: # realname is set here for logic simplicity
            client.realname = "registered" # Mark as registered
            # 001: Welcome message
            await client.send(f":{config.SERVER_NAME} 001 {client.nickname} :欢迎来到 {config.SERVER_NAME} IRC 服务器")
            # 002: Your host is...
            await client.send(f":{config.SERVER_NAME} 002 {client.nickname} :你的主机是 {config.SERVER_NAME}, 运行版本 {config.SERVER_VERSION}")
            # 003: This server was created...
            await client.send(f":{config.SERVER_NAME} 003 {client.nickname} :该服务器创建于一个晴朗的日子")
            # 004: Server info
            await client.send(f":{config.SERVER_NAME} 004 {client.nickname} {config.SERVER_NAME} {config.SERVER_VERSION} i o")
            logging.info(f"客户端 {client.ip} 完成注册，昵称为 {client.nickname}")

    async def handle_nick(self, client: Client, args: List[str]):
        """处理 NICK 命令"""
        if not args:
            await client.send(f":{config.SERVER_NAME} 431 {client.nickname or '*'} :No nickname given")
            return

        new_nick = args[0]
        if new_nick in self.nicknames and self.nicknames[new_nick] != client:
            await client.send(f":{config.SERVER_NAME} 433 {client.nickname or '*'} {new_nick} :Nickname is already in use")
            return

        old_prefix = client.get_prefix()
        if client.nickname and client.nickname in self.nicknames:
            del self.nicknames[client.nickname]
        
        self.nicknames[new_nick] = client
        client.nickname = new_nick
        
        # 如果用户已经注册，通知所有相关频道昵称已更改
        if client.realname: # Check if registered
            notification = f":{old_prefix} NICK :{new_nick}"
            await client.send(notification)
            for channel in client.channels:
                await channel.broadcast(notification, sender_to_exclude=client)

        await self._check_registration(client)

    async def handle_user(self, client: Client, args: List[str]):
        """处理 USER 命令"""
        if len(args) < 4:
            await client.send(f":{config.SERVER_NAME} 461 {client.nickname or '*'} USER :Not enough parameters")
            return
        if client.username:
            await client.send(f":{config.SERVER_NAME} 462 {client.nickname or '*'} :You may not reregister")
            return
        
        client.username = args[0]
        # args[1] 和 args[2] (host 和 server) 通常被忽略
        client.realname = args[3].lstrip(':')

        await client.send(f":{config.SERVER_NAME} 001 :Welcome to {config.SERVER_NAME} , Version {config.SERVER_VERSION}")

        if config.IS_TESTING:
            await client.send(f":{config.SERVER_NAME} 999 :Hey {client.nickname} , Dieser IRC-Server befindet sich noch in der Testphase. Bitte hinterlassen Sie keine vertraulichen Informationen!")
        
        await self._check_registration(client)

    async def handle_ping(self, client: Client, args: List[str]):
        """处理 PING 命令"""
        payload = args[0] if args else config.SERVER_NAME
        await client.send(f"PONG :{payload}")

    async def handle_quit(self, client: Client, args: List[str]):
        """处理 QUIT 命令"""
        reason = args[0] if args else "Client quit"
        await self.disconnect_client(client, reason)

    async def handle_join(self, client: Client, args: List[str]):
        """处理 JOIN 命令，增加对带密码频道的功能支持。"""
        if not client.realname: # Not registered
            await client.send(f":{config.SERVER_NAME} 451 {client.nickname or '*'} :You have not registered")
            return
        if not args:
            await client.send(f":{config.SERVER_NAME} 461 {client.nickname or '*'} JOIN :Not enough parameters. Usage: /join <#channel_name> [key]")
            return

        channel_name = args[0]
        key = args[1] if len(args) > 1 else None # <-- 新增：获取用户提供的密码 (key)

        if channel_name not in self.channels:
            # 在旧版本中，这里是直接拒绝。现在我们允许管理员创建频道，但普通用户只能加入已存在的。
            # 这部分逻辑保持不变，因为创建是由 /create 命令完成的。
            await client.send(f":{config.SERVER_NAME} 403 {client.nickname} {channel_name} :No such channel, it must be created by an operator first.")
            return

        channel = self.channels[channel_name]
        if client in channel.clients:
            return # Already in channel

        # --- 核心改动：密码检查 ---
        if channel.password:
            if not key or key != channel.password:
                # 475 ERR_BADCHANNELKEY 是 IRC 中密码错误的 标准数字回复
                await client.send(f":{config.SERVER_NAME} 475 {client.nickname} {channel_name} :Cannot join channel (+k) - incorrect password")
                return # 密码错误，终止加入流程

        # --- 密码检查结束 ---

        channel.add_client(client)
        logging.info(f"客户端 {client.nickname} 加入频道 {channel_name}")
        
        join_msg = f":{client.get_prefix()} JOIN {channel_name}"
        await channel.broadcast(join_msg)

        nicks_in_channel = ' '.join([c.nickname for c in channel.clients])
        await client.send(f":{config.SERVER_NAME} 353 {client.nickname} = {channel_name} :{nicks_in_channel}")
        await client.send(f":{config.SERVER_NAME} 366 {client.nickname} {channel_name} :End of /NAMES list.")

    async def handle_part(self, client: Client, args: List[str]):
        """处理 PART 命令"""
        if not args:
            await client.send(f":{config.SERVER_NAME} 461 {client.nickname} PART :Not enough parameters")
            return
            
        channel_name = args[0]
        reason = ' '.join(args[1:]).lstrip(':') if len(args) > 1 else "Leaving"

        if channel_name not in self.channels or client not in self.channels[channel_name].clients:
            await client.send(f":{config.SERVER_NAME} 442 {client.nickname} {channel_name} :You're not on that channel")
            return

        channel = self.channels[channel_name]
        part_msg = f":{client.get_prefix()} PART {channel_name} :{reason}"
        
        # 广播给包括自己在内的所有人，这样客户端也能收到离开确认
        await channel.broadcast(part_msg)
        
        channel.remove_client(client)
        logging.info(f"客户端 {client.nickname} 离开频道 {channel_name}")

        if not channel.clients:
            logging.info(f"频道 {channel_name} 为空，正在移除。")
            del self.channels[channel_name]
    
    async def handle_privmsg(self, client: Client, args: List[str]):
        """处理 PRIVMSG 命令 (频道消息和私聊)"""
        if not client.realname: # Not registered
            await client.send(f":{config.SERVER_NAME} 451 {client.nickname or '*'} :You have not registered")
            return
        if len(args) < 2:
            await client.send(f":{config.SERVER_NAME} 461 {client.nickname} PRIVMSG :Not enough parameters")
            return

        target, message = args[0], ' '.join(args[1:]).lstrip(':')
        
        full_message = f":{client.get_prefix()} PRIVMSG {target} :{message}"

        if target.startswith('#'):
            # 频道消息
            if target not in self.channels or client not in self.channels[target].clients:
                await client.send(f":{config.SERVER_NAME} 404 {client.nickname} {target} :Cannot send to channel")
                return
            # 广播给包括发送者在内的所有人，以简化客户端逻辑
            await self.channels[target].broadcast(full_message)
        else:
            # 私聊
            if target not in self.nicknames:
                await client.send(f":{config.SERVER_NAME} 401 {client.nickname} {target} :No such nick/channel")
                return
            recipient_client = self.nicknames[target]
            await recipient_client.send(full_message)

    async def handle_topic(self, client: Client, args: List[str]):
        if config.ONLY_ADMIN_CHANGE_TOPIC:
            if not client.is_operator:
                await client.send(f":{config.SERVER_NAME} 481 {client.nickname} :Permission Denied- You're not an IRC operator.")
                return

        if not client.realname:
            await client.send(f":{config.SERVER_NAME} 451 {client.nickname or '*'} :You have not registered")
            return
        
        if(len(args) < 1):
            await client.send(f":{config.SERVER_NAME} 461 {client.nickname} TOPIC :Not enough parameters")
            return

        channel_name = args[0]

        if channel_name not in self.channels:
            await client.send(f":{config.SERVER_NAME} 403 {client.nickname} {channel_name} :No such channel")
            return
        
        channel = self.channels[channel_name]

        if client not in channel.clients:
            await client.send(f":{config.SERVER_NAME} 442 {client.nickname} {channel_name} :You're not on that channel")
            return
        
        if len(args) > 1:
            new_topic = ' '.join(args[1:]).lstrip(':')
            channel.topic = new_topic

            logging.info(f"客户端 {client.nickname} 更新了频道 {channel_name} 的话题为: {new_topic}")
            
            topic_change_msg = f":{client.get_prefix()} TOPIC {channel_name} :{new_topic}"
            await channel.broadcast(topic_change_msg)

        else:
            if channel.topic:
                await client.send(f":{config.SERVER_NAME} 332 {client.nickname} {channel_name} :{channel.topic}")
            else:
                await client.send(f":{config.SERVER_NAME} 331 {client.nickname} {channel_name} :No topic is set")

    async def handle_list(self, client: Client, args: List[str]):
        """处理 LIST 命令，列出所有可用频道"""
        if not client.realname: # Not registered
            await client.send(f":{config.SERVER_NAME} 451 {client.nickname or '*'} :You have not registered")
            return
        
        await client.send(f":{config.SERVER_NAME} 321 {client.nickname} Channel :Users  Name")
        if not self.channels:
            await client.send(f":{config.SERVER_NAME} 322 {client.nickname} * 0 :No channels available.")
        else:
            for name, channel in self.channels.items():
                user_count = len(channel.clients)
                topic = channel.topic or "No topic is set"
                await client.send(f":{config.SERVER_NAME} 322 {client.nickname} {name} {user_count} :{topic}")
        await client.send(f":{config.SERVER_NAME} 323 {client.nickname} :End of /LIST")
    
    async def handle_help(self, client: Client, args: List[str]):
        """处理 HELP 命令"""
        if not client.realname: # 检查是否注册
            await client.send(f":{config.SERVER_NAME} 451 {client.nickname or '*'} :You have not registered")
            return
        help_messages = [
            "--- 可用命令列表 ---",
            "/NICK <新昵称>                  - 更改你的昵称",
            "/JOIN <#频道名> <密码>             - 加入一个频道",
            "/PART [<#频道名>] [原因]          - 离开当前或指定频道",
            "/MSG <昵称> <消息>              - 向指定用户发送私聊消息",
            "/LIST                           - 列出服务器上所有可用的频道",
            "/QUIT [原因]                    - 断开与服务器的连接",
        ]

        if client.is_operator:
            help_messages.append("/CREATE <#频道名>               - 创建一个新的频道")
            help_messages.append("/TOPIC <#频道名> [话题]          - 查看或设置频道话题")

        help_messages.append("--- END OF HELP ---")

        for message in help_messages:
            await client.send(f":{config.SERVER_NAME} NOTICE {client.nickname} :{message}")

    async def handle_create(self, client: Client, args: List[str]):
        """处理 CREATE 命令 (仅限管理员)，可选择性添加密码。"""

        if config.ONLY_ADMIN_CREATE_CHANNEL:
            if not client.is_operator:
                await client.send(f":{config.SERVER_NAME} 481 {client.nickname} :Permission Denied- You're not an IRC operator.")
                return
        
        if not args:
            await client.send(f":{config.SERVER_NAME} 461 {client.nickname} CREATE :Not enough parameters. Usage: /create <#channel_name> [password]")
            return

        channel_name = args[0]
        password = args[1] if len(args) > 1 else None  # <-- 新增：获取可选的密码参数

        if not channel_name.startswith('#'):
            await client.send(f":{config.SERVER_NAME} 403 {client.nickname} {channel_name} :Invalid channel name, must start with #.")
            return

        if channel_name in self.channels:
            await client.send(f":{config.SERVER_NAME} NOTICE {client.nickname} :Channel {channel_name} already exists.")
            return

        # 创建频道并设置密码
        new_channel = Channel(channel_name, self)
        if password:
            new_channel.password = password
        
        self.channels[channel_name] = new_channel
        
        # 根据是否设置密码，发送不同的成功消息
        if password:
            logging.info(f"管理员 {client.nickname} 创建了新的私密频道: {channel_name}")
            await client.send(f":{config.SERVER_NAME} NOTICE {client.nickname} :Private channel {channel_name} has been created successfully.")
        else:
            logging.info(f"管理员 {client.nickname} 创建了新频道: {channel_name}")
            await client.send(f":{config.SERVER_NAME} NOTICE {client.nickname} :Channel {channel_name} has been created successfully.")


    async def handle_oper(self, client: Client, args: List[str]):
        """处理 OPER 命令"""
        if len(args) < 1:
            await client.send(f":{config.SERVER_NAME} 461 {client.nickname} OPER :Not enough parameters")
            return

        password = args[0]
        if password == config.OPERATOR_PASSWORD:
            client.is_operator = True
            await client.send(f":{config.SERVER_NAME} 381 {client.nickname} :You are now an IRC operator")
            logging.info(f"客户端 {client.nickname} ({client.ip}) 成功认证为管理员。")
        else:
            await client.send(f":{config.SERVER_NAME} 464 {client.nickname} :Password incorrect")
            logging.warning(f"客户端 {client.nickname} ({client.ip}) 尝试使用错误密码进行管理员认证。")

async def main():
    server = Server()
    try:
        server_instance = await asyncio.start_server(
            server.handle_connection, config.HOST, config.PORT)

        addr = server_instance.sockets[0].getsockname()
        logging.info(f"服务器正在 {addr} 上运行...")

        async with server_instance:
            await server_instance.serve_forever()
    except OSError as e:
        logging.error(f"无法启动服务器: {e}. 端口 {config.PORT} 是否已被占用？")
    except Exception as e:
        logging.error(f"服务器遇到致命错误: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("服务器正在关闭。") 
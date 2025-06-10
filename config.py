# config.py

# 服务器配置
HOST = "0.0.0.0"  # 监听所有网络接口
PORT = 6667        # 标准的 IRC 端口

# 服务器信息
SERVER_NAME = "KaguyaIRC"
SERVER_VERSION = "0.7.0"

#2025-06-10 Version 0.6.0
# 添加默认频道 #global
# 添加MSG命令

#2025-06-11 Version 0.7.0
#准备更新内容->
#第一个创建频道的人将会获得一串随机生成的密钥（这串密钥会被连续发送5次)。使用/CHANNEL <密钥> 可以获得此频道的所有权
#密钥在频道被移除之前永远无法更改,且当你下线重新登陆后仍然还需要密钥来重新获得权限。
#频道所有者可以更改频道主题,密码(非隐私频道无法更改),从频道中移除角色(在当前频道中使用/KICK)封禁角色(/BAN <用户名>,且通常是封禁该用户名对应的IP,以及/UNBAN <IP>)
#/OPER获得的管理员默认有所有频道的相关操作权限,以及有着全服务器的/ALLKICK和/ALLBAN <IP/USERNAME>(/UNALLBAN <IP>)权限
#/LISTALLBAN可以查看所有被封禁的IP（他到底是在封禁谁我们不在乎）
#同样的，CONFIG.py中ONLY_ADMIN_CHANGE_TOPIC将会被移除

IS_TESTING = True

ONLY_ADMIN_CREATE_CHANNEL = False

# 管理员密码
# 用户可以通过发送 /OPER <password> 来获取管理员权限
OPERATOR_PASSWORD = "admin"

# 日志文件
LOG_FILE = "irc.log" 

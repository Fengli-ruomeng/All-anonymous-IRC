# config.py

# 服务器配置
HOST = "0.0.0.0"  # 监听所有网络接口
PORT = 6667        # 标准的 IRC 端口

# 服务器信息
SERVER_NAME = "KaguyaIRC"
SERVER_VERSION = "0.3.0"

IS_TESTING = True

ONLY_ADMIN_CREATE_CHANNEL = False
ONLY_ADMIN_CHANGE_TOPIC = False

# 管理员密码
# 用户可以通过发送 /OPER <password> 来获取管理员权限
OPERATOR_PASSWORD = "admin"

# 日志文件
LOG_FILE = "irc.log" 
"""
tiger_client.py

作用：
1. 初始化 Tiger OpenAPI 客户端配置
2. 显式读取本地 PEM 私钥
3. 提供行情客户端 QuoteClient
"""

# 导入 Tiger OpenAPI 的基础配置对象
from tigeropen.tiger_open_config import TigerOpenClientConfig

# 导入 Tiger 行情客户端
from tigeropen.quote.quote_client import QuoteClient

# 导入 Tiger SDK 的私钥读取工具
from tigeropen.common.util.signature_utils import read_private_key

# 从配置文件中读取账户信息和私钥路径
from config.settings import TIGER_ID, ACCOUNT, PRIVATE_KEY_PATH


def get_client_config():
    """
    创建 Tiger API 客户端配置
    """
    config = TigerOpenClientConfig()

    # 开发者 ID
    config.tiger_id = TIGER_ID

    # 账户
    config.account = ACCOUNT

    # 私钥文件路径（保留，方便排查）
    config.private_key_path = PRIVATE_KEY_PATH

    # 关键：显式读取 PEM 私钥内容
    config.private_key = read_private_key(PRIVATE_KEY_PATH)

    # 语言设置
    config.language = "en_US"

    return config


def get_quote_client():
    """
    创建并返回 Tiger 行情客户端
    """
    config = get_client_config()
    quote_client = QuoteClient(config)
    return quote_client
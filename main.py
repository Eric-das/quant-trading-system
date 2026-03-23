"""
main.py

作用：
测试 Tiger 客户端是否能成功初始化
"""

from broker.tiger_client import get_client_config


def mask(value):
    """
    隐藏敏感字段
    """
    if not value:
        return "None"

    if len(value) <= 4:
        return "****"

    return value[:4] + "****"


def main():
    """
    初始化 Tiger client config，并打印非敏感信息
    """
    client_config = get_client_config()

    print("Tiger client config initialized successfully")
    print("Tiger ID:", mask(client_config.tiger_id))
    print("Account:", mask(client_config.account))
    print("Private key loaded:", client_config.private_key is not None)


if __name__ == "__main__":
    main()
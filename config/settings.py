"""
tiger_config.py

作用：
1. 读取 Tiger OpenAPI 的 properties 配置文件
2. 提取关键字段（tiger_id / account / env / license / private_key_pk1）
3. 把 private_key_pk1 写入本地 PEM 文件，供 Tiger SDK 使用

说明：
Tiger Python SDK 官方示例通常使用 read_private_key('pem文件路径') 来读取私钥。
因此这里我们把 properties 里的 private_key_pk1 落地为本地文件。
"""

from pathlib import Path

# -----------------------------
# 路径配置
# -----------------------------
# 当前项目里 Tiger 配置文件的位置
CONFIG_FILE = Path("config/tiger_openapi_config.properties")

# 生成本地私钥文件的位置
PRIVATE_KEY_FILE = Path("config/tiger_private_key.pem")


def load_properties(file_path):
    """
    读取 .properties 文件
    格式示例：
        key=value

    返回：
        dict
    """
    props = {}

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            # 跳过空行
            if not line:
                continue

            # 跳过注释行
            if line.startswith("#"):
                continue

            # 解析 key=value
            if "=" in line:
                key, value = line.split("=", 1)
                props[key.strip()] = value.strip()

    return props


def write_private_key_pem(private_key_str, output_path):
    """
    把 properties 里的 PKCS#1 私钥字符串写成 PEM 文件

    Tiger Python SDK 使用 PKCS#1 私钥，
    SDK 示例一般通过 read_private_key('path') 读取本地私钥文件。
    """
    if not private_key_str:
        raise ValueError("private_key_pk1 is missing in properties file")

    # 如果文件已经存在，就不重复生成
    if output_path.exists():
        return

    pem_text = (
        "-----BEGIN RSA PRIVATE KEY-----\n"
        + private_key_str
        + "\n-----END RSA PRIVATE KEY-----\n"
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(pem_text)


# -----------------------------
# 加载配置
# -----------------------------
CONFIG = load_properties(CONFIG_FILE)

# -----------------------------
# 提取字段
# -----------------------------
TIGER_ID = CONFIG.get("tiger_id")
ACCOUNT = CONFIG.get("account")
ENV = CONFIG.get("env")
LICENSE = CONFIG.get("license")

# Python SDK 优先使用 PKCS#1
PRIVATE_KEY_PK1 = CONFIG.get("private_key_pk1")

# Tiger client 要读取的私钥文件路径
PRIVATE_KEY_PATH = str(PRIVATE_KEY_FILE)

# -----------------------------
# 基础校验
# -----------------------------
if not TIGER_ID:
    raise ValueError("Missing tiger_id in properties file")

if not ACCOUNT:
    raise ValueError("Missing account in properties file")

if not ENV:
    raise ValueError("Missing env in properties file")

if not PRIVATE_KEY_PK1:
    raise ValueError("Missing private_key_pk1 in properties file")

# -----------------------------
# 生成 PEM 私钥文件
# -----------------------------
write_private_key_pem(PRIVATE_KEY_PK1, PRIVATE_KEY_FILE)
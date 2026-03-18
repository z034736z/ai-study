# 后端配置
import os

# MiniMax API配置（阿里DashScope兼容Anthropic API）
ANTHROPIC_AUTH_TOKEN = "sk-sp-88e5c7898eb545f4b56b9d96df06a13d"
ANTHROPIC_BASE_URL = "https://coding.dashscope.aliyuncs.com/apps/anthropic"
ANTHROPIC_MODEL = "MiniMax-M2.5"

# 数据文件路径
DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "带量采购数据.xlsx")

# Flask配置
HOST = "0.0.0.0"
PORT = 5000
DEBUG = True
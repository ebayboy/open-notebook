import os
from openai import OpenAI
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# 从环境变量读取配置
api_key = os.getenv("OPENAI_COMPATIBLE_API_KEY")
base_url = os.getenv("OPENAI_COMPATIBLE_BASE_URL", "https://api.openai.com/v1")

print("api_key:", api_key)
print("base_url:", base_url)

# 初始化客户端
client = OpenAI(api_key=api_key, base_url=base_url)

# 调用模型
response = client.chat.completions.create(
    model="Qwen3-30B-A3B-GPTQ-Int4",
    messages=[{"role": "user", "content": "Hello, world!"}],
)

print(response.choices[0].message.content)

from utils.logging_config import configure_sync_logging, configure_async_logging
from quart import Quart, render_template, request, jsonify
import openai
import os
import asyncio
import logging

# Prometheus metrics
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from prometheus_client.exposition import start_http_server

# 创建 Quart 应用实例
app = Quart(__name__)

# 获取环境变量中的 API 密钥
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable not set.")

# 创建 OpenAI 客户端实例
client = openai.AsyncClient(api_key=api_key)

# 配置同步和异步日志
sync_logger = configure_sync_logging()
async_logger = configure_async_logging()

# 指标
request_counter = Counter('chatgpt_requests', 'Number of requests to ChatGPT')
request_latency = Histogram('chatgpt_request_latency_seconds', 'Request latency in seconds')
request_in_progress = Gauge('chatgpt_requests_in_progress', 'Requests currently in progress')

@app.route("/", methods=["GET", "POST"])
async def index():
    if request.method == "POST":
        # 计数器 +1
        request_counter.inc()
        
        # 使用上下文管理器记录请求的开始和结束
        with request_latency.time():
            # 正在处理的请求数 +1
            request_in_progress.inc()
            
            # 使用 await 正确获取 JSON 数据
            data = await request.get_json()
            user_input = data.get("user_input")
            
            # 记录收到请求的日志（同步和异步）
            sync_logger.info(f"Received input: {user_input}")
            await async_logger.info(f"Received input: {user_input}")
            # 调用 OpenAI API 获取回复
            response = await get_chatgpt_response(user_input)
            
            # 正在处理的请求数 -1
            request_in_progress.dec()
            
            # 返回 JSON 格式的响应
            return jsonify({"response": response})
    
    # 渲染 HTML 模板（GET 请求）
    return await render_template("index.html")

async def get_chatgpt_response(prompt):
    """
    调用 OpenAI API 获取响应的辅助函数
    """
    try:
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",  # 使用 GPT-3.5 Turbo 模型
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,             # 返回的最大 token 数量
            temperature=0.7             # 控制生成文本的随机性
        )
        
        # 提取并返回 GPT-3.5 Turbo 生成的文本
        result = response.choices[0].message.content.strip()
        
    # 记录成功的API调用日志
        sync_logger.info(f"OpenAI API call successful: {result}")
        await async_logger.info(f"OpenAI API call successful: {result}")
        return result
    except openai.OpenAIError as e:
        return f"OpenAI API returned an error: {str(e)}"
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"

# 启动 Prometheus 指标服务
@app.route('/metrics')
async def metrics():
    return generate_latest()

# 启动 Quart 应用
if __name__ == "__main__":
    start_http_server(8000)  # 启动 Prometheus 指标服务
    app.run(host="0.0.0.0", port=5000, debug=True)


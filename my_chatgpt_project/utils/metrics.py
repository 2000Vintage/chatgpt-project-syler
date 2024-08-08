#/metrics.py

from prometheus_client import Counter, Histogram, generate_latest
from quart import Response
import time

# 定义请求计数器
REQUEST_COUNT = Counter('request_count', 'Total number of requests', ['method', 'endpoint', 'status_code'])

# 定义请求时长的直方图
REQUEST_LATENCY = Histogram('request_latency_seconds', 'Request latency', ['endpoint'])

def track_request_metrics(endpoint: str):
    """跟踪请求的计数和时长"""
    def increment_counter(method: str, status_code: int):
        """增加请求计数"""
        REQUEST_COUNT.labels(method, endpoint, status_code).inc()

    class Timer:
        def __enter__(self):
            self.start_time = time.time()
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            duration = time.time() - self.start_time
            REQUEST_LATENCY.labels(endpoint).observe(duration)

    return Timer, increment_counter

async def metrics():
    """导出 Prometheus 格式的指标"""
    return Response(generate_latest(), mimetype='text/plain')


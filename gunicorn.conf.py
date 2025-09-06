# gunicorn.conf.py
import os
import multiprocessing

# 포트는 환경변수 PORT와 동기화 (Dockerfile의 ENV PORT=8000 참고)
bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"

# 워커/스레드 기본값: 코어*2+1, 스레드 2
workers = int(os.getenv("GUNICORN_WORKERS", (multiprocessing.cpu_count() * 2) + 1))
threads = int(os.getenv("GUNICORN_THREADS", 2))

# 타임아웃/로그
timeout = int(os.getenv("GUNICORN_TIMEOUT", 120))
graceful_timeout = int(os.getenv("GUNICORN_GRACEFUL_TIMEOUT", 30))
keepalive = int(os.getenv("GUNICORN_KEEPALIVE", 5))
accesslog = "-"   # stdout
errorlog = "-"    # stderr

# 동시성 모델: 기본 gthread. (비동기/ASGI면 uvicorn.worker 고려)
worker_class = os.getenv("GUNICORN_WORKER_CLASS", "gthread")

# 요청/응답 제한 (필요 시)
limit_request_line = int(os.getenv("GUNICORN_LIMIT_REQUEST_LINE", 4094))
limit_request_fields = int(os.getenv("GUNICORN_LIMIT_REQUEST_FIELDS", 100))
limit_request_field_size = int(os.getenv("GUNICORN_LIMIT_REQUEST_FIELD_SIZE", 8190))

# 헤더, proxy 옵션 (리버스프록시/Nginx 뒤에 둘 때 추천)
forwarded_allow_ips = os.getenv("GUNICORN_FORWARDED_ALLOW_IPS", "*")
proxy_protocol = os.getenv("GUNICORN_PROXY_PROTOCOL", "False").lower() == "true"

# preload_app: 메모리 절감/시작속도 trade-off. True면 초기화 시점에 앱 로드
preload_app = os.getenv("GUNICORN_PRELOAD", "False").lower() == "true"

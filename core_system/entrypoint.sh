#!/usr/bin/env bash
set -euo pipefail
# -e: 에러 즉시 종료, -u: 미정의 변수 사용시 에러, -o pipefail: 파이프 중간에러 감지

# ── 0) 선택: Django 모듈 기본값(원하시면 제거해도 됨)
: "${DJANGO_SETTINGS_MODULE:=config.settings}"

# ── 1) DB 연결 대기
DB_WAIT_SECONDS="${DB_WAIT_SECONDS:-60}"
echo "[entrypoint] Waiting for database (timeout: ${DB_WAIT_SECONDS}s)..."
python - <<PY
import os, sys, time
import psycopg2

def need(k, allow_empty=False):
    v = os.environ.get(k)
    if v is None or (not allow_empty and v == ""):
        print(f"[entrypoint][FATAL] Missing env: {k}", flush=True)
        sys.exit(1)
    return v

host = need("DATABASES_HOST")
port = int(need("DATABASES_PORT"))
name = need("DATABASES_NAME")
user = need("DATABASES_USER")
password = os.environ.get("DATABASES_PASSWORD", "")  # 빈값 허용 가능

timeout = int(os.environ.get("DB_WAIT_SECONDS","60"))
start = time.time()
while time.time() - start < timeout:
    try:
        conn = psycopg2.connect(host=host, port=port, dbname=name, user=user, password=password)
        conn.close()
        print("[entrypoint] Database is ready", flush=True)
        sys.exit(0)
    except Exception as e:
        time.sleep(1)

print("[entrypoint][FATAL] Database not reachable within timeout", flush=True)
sys.exit(1)
PY

# ── 2) 마이그레이션
echo "[entrypoint] Running migrations..."
python manage.py migrate --noinput

# ── 3) 선택: 운영에서만 정적 파일 수집
if [ "${COLLECTSTATIC:-0}" = "1" ]; then
  echo "[entrypoint] Collecting static files..."
  python manage.py collectstatic --noinput
fi

# ── 4) 실행 (Gunicorn / runserver)
if [ "${GUNICORN_ENABLE:-0}" = "1" ]; then
  : "${WSGI_MODULE?}[FATAL] WSGI_MODULE is required when GUNICORN_ENABLE=1"
  : "${GUNICORN_BIND?}[FATAL] GUNICORN_BIND is required when GUNICORN_ENABLE=1"
  : "${GUNICORN_WORKERS?}[FATAL] GUNICORN_WORKERS is required when GUNICORN_ENABLE=1"
  : "${GUNICORN_TIMEOUT?}[FATAL] GUNICORN_TIMEOUT is required when GUNICORN_ENABLE=1"
  echo "[entrypoint] Starting Gunicorn..."
  exec gunicorn "${WSGI_MODULE}" \
    --bind "${GUNICORN_BIND}" \
    --workers "${GUNICORN_WORKERS}" \
    --timeout "${GUNICORN_TIMEOUT}"
else
  : "${DJANGO_HOST?}[FATAL] DJANGO_HOST is required for runserver mode"
  : "${DJANGO_PORT?}[FATAL] DJANGO_PORT is required for runserver mode"
  echo "[entrypoint] Starting Django runserver..."
  exec python manage.py runserver "${DJANGO_HOST}:${DJANGO_PORT}"
fi

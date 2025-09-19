# django_server
Saas 기능 구현 및 기능 관리

---
## 📦 요구 사항
- Python 3.13+
- pip


## 🛠 설치
```bash
# 1) 저장소 클론
git clone https://github.com/jeonghyeon0329/django_server.git

# 2) 가상환경 & 패키지 설치 (pip)
python -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

✨ 주요 기능

멀티 테넌시(Multi-Tenancy)
- 요청 헤더의 테넌트 식별자(X-Tenant-ID)를 통해 데이터/권한을 분리
- 예외 경로 설정(TENANT_EXEMPT_PATHS)로 특정 엔드포인트는 테넌트 검증 스킵 가능

멱등성(Idempotency) 미들웨어
- Idempotency-Key 헤더를 통해 중복 요청 방지/응답 재사용
- 4xx~5xx 응답은 캐시하지 않음
- TTL(예: 60초) 이후 캐시 무효화(옵션)
- 멱등키가 없는 경우 400에러

파일시스템(MinIO)
- s3 api 기준 : 추후 AWS S3/Wasabi 등으로 엔드포인트 교체
- 대용량에 강함 : 클라이언트와 스토리지 직접 전송(서버는 서명만)
- docker & docker-compose를 활용하여 진행

pytest 기반 테스트
- 미들웨어 동작 및 회귀 테스트
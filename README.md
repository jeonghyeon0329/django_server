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

## ✨ 기능 요약
- 멀티테넌트 적용(api에 테넌트 info 추가하여 별도 관리)

## 🛠 pytest 실험
- 멀티테넌트 pytest 진행(TenantMiddleware,IdempotencyMiddleware)

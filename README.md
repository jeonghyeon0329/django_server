# django_server
회사 전사 프로그램 설계 및 구현

---
## 📦 요구 사항
- Python 3.13+

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

1. core_system : 멱등성, 테넌트 검증
2. hr_system : 인사관리팀
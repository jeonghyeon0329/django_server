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
```bash
# 1) pytest -q : pytest.ini에 따라 test로 시작하는 python파일 모두 실행
pytest -q
# 2) pytest -s : test로 시작하는 python파일에서 print 확인하는 방법
pytest -s
```

## 🛠 멀티테넌트 생성 방법
```bash
http://localhost:8000/admin/ 추가(테넌트: 추가)
```



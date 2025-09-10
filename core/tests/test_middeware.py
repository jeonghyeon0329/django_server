import json
import hashlib
import pytest
from django.http import JsonResponse

@pytest.mark.django_db
class TestTenantMiddleware:
    def test_header_sets_tenant(self, rf, tenant):
        from core.middleware import TenantMiddleware
        req = rf.get("/anything", HTTP_X_TENANT_ID=tenant.code)
        mw = TenantMiddleware(lambda r: JsonResponse({"ok": True}))
        mw.process_request(req)
        assert getattr(req, "tenant", None) == tenant

    # def test_query_param_sets_tenant(self, rf, tenant):
    #     from core.middleware import TenantMiddleware
    #     req = rf.get(f"/anything?tenant={tenant.code}")
    #     mw = TenantMiddleware(lambda r: JsonResponse({"ok": True}))
    #     mw.process_request(req)
    #     assert req.tenant == tenant

    # def test_unknown_tenant_keeps_none(self, rf):
    #     from core.middleware import TenantMiddleware
    #     req = rf.get("/anything", HTTP_X_TENANT_ID="no-such")
    #     mw = TenantMiddleware(lambda r: JsonResponse({"ok": True}))
    #     mw.process_request(req)
    #     assert getattr(req, "tenant", None) is None


# @pytest.mark.django_db
# class TestIdempotencyMiddleware:
#     def _mw_with_counting_view(self):
#         """
#         호출 횟수를 기록하는 뷰와 래핑된 미들웨어를 돌려준다.
#         """
#         from core.middleware import IdempotencyMiddleware
#         calls = {"count": 0}
#         def view(req):
#             calls["count"] += 1
#             return JsonResponse({"ok": True, "n": calls["count"]}, status=201)
#         return IdempotencyMiddleware(view), calls

#     def test_post_with_same_key_and_body_uses_cached_response(self, rf, db):
#         from core.models import IdempotencyKey
#         mw, calls = self._mw_with_counting_view()

#         payload = {"x": 1}
#         body1 = json.dumps(payload)

#         # 1차 호출: 저장 + 실제 뷰 실행
#         req1 = rf.post("/echo", data=body1, content_type="application/json", HTTP_IDEMPOTENCY_KEY="k1")
#         resp1 = mw(req1)
#         assert resp1.status_code == 201
#         assert calls["count"] == 1

#         # DB 저장 확인
#         h1 = hashlib.sha256(body1.encode("utf-8")).hexdigest()
#         row = IdempotencyKey.objects.get(key="k1")
#         assert row.request_hash == h1
#         assert row.status_code == 201
#         assert '"ok": true' in row.response_body

#         # 2차 호출 (동일 바디/키): 캐시 재사용, 뷰 미호출
#         req2 = rf.post("/echo", data=body1, content_type="application/json", HTTP_IDEMPOTENCY_KEY="k1")
#         resp2 = mw(req2)
#         assert resp2.status_code == 201
#         assert calls["count"] == 1  # 증가하지 않음 (캐시 히트)
#         # assert resp2.json()["ok"] is True
#         data = json.loads(resp2.content.decode("utf-8"))
#         assert data["ok"] is True

#     def test_post_with_same_key_but_different_body_does_not_reuse(self, rf, db):
#         """
#         현재 모델에서 key가 unique=True라서,
#         같은 키에 다른 바디를 보내면 새 레코드가 저장되지 못하고(무결성 오류 -> except로 넘어가며 무시됨),
#         결과적으로 '멱등성 캐시'는 첫 바디 기준으로만 남는다.
#         => 이 동작을 테스트로 명시해 둔다.
#         """
#         from core.models import IdempotencyKey
#         mw, calls = self._mw_with_counting_view()

#         body1 = json.dumps({"x": 1})
#         body2 = json.dumps({"x": 2})

#         # 최초 요청
#         req1 = rf.post("/echo", data=body1, content_type="application/json", HTTP_IDEMPOTENCY_KEY="k2")
#         resp1 = mw(req1)
#         assert resp1.status_code == 201
#         assert calls["count"] == 1

#         # 다른 바디지만 같은 키
#         req2 = rf.post("/echo", data=body2, content_type="application/json", HTTP_IDEMPOTENCY_KEY="k2")
#         resp2 = mw(req2)
#         assert resp2.status_code == 201
#         assert calls["count"] == 2  # 캐시 미적용, 실제 뷰 재호출

#         # 여전히 레코드는 1개(첫 바디 hash만 저장됨)
#         assert IdempotencyKey.objects.filter(key="k2").count() == 1

#     def test_safe_methods_are_ignored(self, rf, db):
#         mw, calls = self._mw_with_counting_view()
#         # GET은 미들웨어 스킵
#         req = rf.get("/echo", HTTP_IDEMPOTENCY_KEY="k3")
#         resp = mw(req)
#         assert resp.status_code == 201
#         assert calls["count"] == 1

#     def test_no_key_header_behaves_normally(self, rf, db):
#         mw, calls = self._mw_with_counting_view()
#         req = rf.post("/echo", data=json.dumps({"a": 1}), content_type="application/json")
#         resp = mw(req)
#         assert resp.status_code == 201
#         assert calls["count"] == 1

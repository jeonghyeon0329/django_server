import json
import hashlib
import pytest
from django.http import JsonResponse

@pytest.mark.django_db
class TestTenantMiddleware:
    """
        tenant정보가 헤더에 있는 경우(정상처리)
    """
    def test_header_sets_tenant(self, rf, tenant):
        from core.middleware import TenantMiddleware
        req = rf.get("/anything", HTTP_X_TENANT_ID=tenant.code)
        mw = TenantMiddleware(lambda r: JsonResponse({"ok": True}))
        resp = mw(req)
        assert resp.status_code == 200
        assert getattr(req, "tenant", None) == tenant

    """
        tenant정보가 쿼리에 있는 경우(tenant 정보 외부 노출)
    """
    def test_query_param_sets_tenant(self, rf, tenant):
        from core.middleware import TenantMiddleware
        req = rf.get(f"/anything?tenant={tenant.code}")
        mw = TenantMiddleware(lambda r: JsonResponse({"ok": True}))
        resp = mw(req)
        assert resp.status_code == 400

    """
        tenant정보가 없는 경우(unmatched)
    """
    def test_unknown_tenant_keeps_none(self, rf):
        from core.middleware import TenantMiddleware
        req = rf.get("/anything", HTTP_X_TENANT_ID="no-such")
        mw = TenantMiddleware(lambda r: JsonResponse({"ok": True}))
        resp = mw(req)        
        assert resp.status_code == 404


@pytest.mark.django_db
class TestIdempotencyMiddleware:
    def _mw_with_counting_view(self):
        """
            호출 횟수를 기록하는 뷰와 래핑된 미들웨어를 돌려준다.
        """
        from core.middleware import IdempotencyMiddleware
        calls = {"count": 0}
        def view(req):
            calls["count"] += 1
            return JsonResponse({"ok": True, "n": calls["count"]}, status=201)
        return IdempotencyMiddleware(view), calls

    def test_post_with_same_key_and_body_uses_cached_response(self, rf, db):
        """
            API를 2번 호출했을때 COUNT가 변화하는지 검사한다.
        """
        from core.models import IdempotencyKey
        mw, calls = self._mw_with_counting_view()

        payload = {"x": 1}
        body1 = json.dumps(payload)

        # 1차 호출: 저장 + 실제 뷰 실행(RequestFactory의 HTTP_ 기능 활용 - 헤더변환)
        req1 = rf.post("/echo", data=body1, content_type="application/json", HTTP_IDEMPOTENCY_KEY="k1")
        resp1 = mw(req1)
        ## 캐시 미스(return None인 경우 뷰를 계속 진행, JsonResponse이면 뷰 미진행)
        assert resp1.status_code == 201
        assert calls["count"] == 1
        
        # DB 저장 확인
        h1 = hashlib.sha256(body1.encode("utf-8")).hexdigest()
        row = IdempotencyKey.objects.get(key="k1")
        assert row.request_hash == h1
        assert row.status_code == 201
        assert '"ok": true' in row.response_body

        # 2차 호출 (동일 바디/키): 캐시 재사용, 뷰 미호출
        req2 = rf.post("/echo", data=body1, content_type="application/json", HTTP_IDEMPOTENCY_KEY="k1")
        resp2 = mw(req2)
        assert resp2.status_code == 201
        assert calls["count"] == 1  # 증가하지 않음 (캐시 히트)
        data = json.loads(resp2.content.decode("utf-8"))
        assert data["ok"] is True

    def test_post_with_same_key_but_different_body_does_not_reuse(self, rf, db):
        """
            key가 unique=True 임으로 '멱등성 캐시'는 첫 바디 기준으로만 남는다.
        """
        from core.models import IdempotencyKey
        mw, calls = self._mw_with_counting_view()

        body1 = json.dumps({"x": 1})
        body2 = json.dumps({"x": 2})

        # 최초 요청
        req1 = rf.post("/echo", data=body1, content_type="application/json", HTTP_IDEMPOTENCY_KEY="k2")
        resp1 = mw(req1)
        assert resp1.status_code == 201
        assert calls["count"] == 1

        # 다른 바디지만 같은 키
        req2 = rf.post("/echo", data=body2, content_type="application/json", HTTP_IDEMPOTENCY_KEY="k2")
        resp2 = mw(req2)
        assert resp2.status_code == 201
        assert calls["count"] == 2  # 캐시 미적용, 실제 뷰 재호출

        assert IdempotencyKey.objects.filter(key="k2").count() == 1

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

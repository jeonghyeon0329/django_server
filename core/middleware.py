import hashlib, json
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.db import transaction, IntegrityError
from django.conf import settings
from django.utils.text import slugify
from .models import Tenant, IdempotencyKey
import re

EXEMPT_PATTERNS = [re.compile(p) for p in getattr(settings, "TENANT_EXEMPT_PATHS", [])]

def _is_exempt(path: str) -> bool:
    return any(p.match(path) for p in EXEMPT_PATTERNS)

class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if _is_exempt(request.path_info):
            return self.get_response(request)
        
        raw = (request.headers.get(getattr(settings, "TENANT_HEADER_NAME", "X-Tenant-ID"))
               or (request.GET.get("tenant") if getattr(settings, "TENANT_ALLOW_QUERY_PARAM", False) else None)
               or (request.POST.get("tenant") if getattr(settings, "TENANT_ALLOW_QUERY_PARAM", False) else None))
    
        code = raw.strip() if raw else None

        if not code:
            return JsonResponse(
                {"detail": "X-Tenant-ID is required."},
                status=400
            )

        else: 
            norm = slugify(code) 
            if norm != code:
                return JsonResponse(
                    {"detail": "Invalid tenant code format."}, 
                    status=400
                )
            code = norm

        tenant = Tenant.objects.filter(code=code).first()
        if not tenant:
            return JsonResponse(
                {"detail": f"Access denied."},
                status=404
            )

        request.tenant = tenant
        return self.get_response(request)

class IdempotencyMiddleware(MiddlewareMixin):
    SAFE_METHODS = {'GET', 'HEAD', 'OPTIONS'} ## 멱등성이 보장되는 Methods

    def process_request(self, request):
        if request.method in self.SAFE_METHODS:
            return None
        
        try:
            key = request.headers.get('Idempotency-Key')
            if not key:
                return JsonResponse(
                    {"detail": "Idempotency-Key header is required."},
                    status=400
                )
            ## 동일 key를 가짐에도 불구하고 body가 다르면 다른 요청으로 처리
            body_hash = hashlib.sha256(request.body or b'').hexdigest()
        
            existing = IdempotencyKey.objects.filter(key=key).first()
            if existing and existing.request_hash != body_hash:
                return JsonResponse(
                    {"detail": "Idempotency-Key reuse with different request body."},
                    status=409
                )
            if existing and existing.status_code and existing.request_hash == body_hash:
                request._idemp_cache_hit = True
                try:
                    data = json.loads(existing.response_body)
                except Exception:
                    data = {'detail': 'OK'}
                return JsonResponse(data, status=existing.status_code, safe=isinstance(data, dict))

            request._idemp_body_hash = body_hash
            return None

        except Exception as e:
            return JsonResponse(
                    {"detail": "internal server error(idempotency)"},
                    status=500
                )
            

    def process_response(self, request, response):
        try:
            if request.method in self.SAFE_METHODS:
                return response
            
            key = request.headers.get('Idempotency-Key')
            if not key :
                return response
            
            # 이미 캐시로 응답한 경우
            if getattr(request, "_idemp_cache_hit", False):
                return response

            if 400 <= getattr(response, "status_code", 200) <= 599:
                return response

            body_hash = getattr(request, "_idemp_body_hash", None)
            if not body_hash:
                body_hash = hashlib.sha256(request.body or b'').hexdigest()
                with transaction.atomic():
                    try:
                        obj, _ = IdempotencyKey.objects.get_or_create(
                            key=key, request_hash=body_hash
                        )
                    except IntegrityError:
                        obj = IdempotencyKey.objects.select_for_update().get(key=key)

                    # Only store JSON responses
                    if hasattr(response, 'content'):
                        try:
                            payload = response.content.decode('utf-8')
                        except Exception:
                            payload = ''

                        obj.request_hash = body_hash
                        obj.response_body = payload
                        obj.status_code = response.status_code
                        obj.save()
        except Exception:
            """
                TODO logger 추가
                logger.exception("Idempotency persistence failed: %s", e)
            """
            pass
        return response

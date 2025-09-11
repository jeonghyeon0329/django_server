import hashlib, json
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.db import transaction
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
    ## 멱등성이 보장되는 Methods
    SAFE_METHODS = {'GET', 'HEAD', 'OPTIONS'}

    def process_request(self, request):
        if request.method in self.SAFE_METHODS:
            return None
        
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
        elif existing and existing.request_hash == body_hash:
            try:
                data = json.loads(existing.response_body)
            except Exception:
                data = {'detail': 'OK'}
            return JsonResponse(data, status=existing.status_code, safe=isinstance(data, dict))
        
        else:
            return None

    def process_response(self, request, response):
        try:
            if request.method not in self.SAFE_METHODS:
                key = request.headers.get('Idempotency-Key')
                if key and hasattr(request, 'body'):
                    body_hash = hashlib.sha256(request.body or b'').hexdigest()
                    with transaction.atomic():
                        obj, _ = IdempotencyKey.objects.get_or_create(
                            key=key, request_hash=body_hash
                        )
                        # Only store JSON responses
                        if hasattr(response, 'content'):
                            try:
                                payload = response.content.decode('utf-8')
                            except Exception:
                                payload = ''
                            obj.response_body = payload
                            obj.status_code = response.status_code
                            obj.save()
        except Exception:
            print("idempotency persistence failed")
        return response

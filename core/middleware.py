import hashlib, json
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.db import transaction
from django.conf import settings
from .models import Tenant, IdempotencyKey
import re

EXEMPT_PATTERNS = [re.compile(p) for p in getattr(settings, "TENANT_EXEMPT_PATHS", [])]

def _is_exempt(path: str) -> bool:
    return any(p.match(path) for p in EXEMPT_PATTERNS)

class TenantMiddleware(MiddlewareMixin):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if _is_exempt(request.path_info):
            return self.get_response(request)
        
        code = (request.headers.get('X-Tenant-ID')
                or request.GET.get('tenant')
                or request.POST.get('tenant'))
        code = code.strip() if code else None

        if not code:
            return JsonResponse(
                {"detail": "X-Tenant-ID header (or ?tenant=) is required."},
                status=400
            )

        tenant = Tenant.objects.filter(code=code).first()
        if not tenant:
            return JsonResponse(
                {"detail": f"Tenant not found for code={code}"},
                status=404
            )

        request.tenant = tenant
        return self.get_response(request)
    
    def process_request(self, request):
        code = request.headers.get('X-Tenant-ID') or request.GET.get('tenant')
        print("(1)")
        print(code)
        request.tenant = None
        if code:
            try:
                request.tenant = Tenant.objects.get(code=code.strip())
            except Tenant.MultipleObjectsReturned:
                print(f"[TenantMiddleware] multiple tenants for code={code!r}")
                request.tenant = None

class IdempotencyMiddleware(MiddlewareMixin):
    SAFE_METHODS = {'GET', 'HEAD', 'OPTIONS'}

    def process_request(self, request):
        if request.method in self.SAFE_METHODS:
            return None
        key = request.headers.get('Idempotency-Key')
        if not key:
            return None
        body_bytes = request.body or b''
        body_hash = hashlib.sha256(body_bytes).hexdigest()
        found = IdempotencyKey.objects.filter(key=key, request_hash=body_hash).first()
        if found and found.status_code:
            # Return cached response
            try:
                data = json.loads(found.response_body)
            except Exception:
                data = {'detail': 'OK'}
            return JsonResponse(data, status=found.status_code, safe=isinstance(data, dict))

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
            pass
        return response

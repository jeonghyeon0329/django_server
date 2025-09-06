import hashlib, json
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.db import transaction
from .models import Tenant, IdempotencyKey

class TenantMiddleware(MiddlewareMixin):
    def process_request(self, request):
        code = request.headers.get('X-Tenant-ID') or request.GET.get('tenant')
        request.tenant = None
        if code:
            try:
                request.tenant = Tenant.objects.get(code=code)
            except Tenant.DoesNotExist:
                # Allow proceeding; views can enforce if needed
                pass

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

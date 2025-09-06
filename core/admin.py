from django.contrib import admin
from .models import Tenant, IdempotencyKey, Outbox

admin.site.register(Tenant)
admin.site.register(IdempotencyKey)
admin.site.register(Outbox)

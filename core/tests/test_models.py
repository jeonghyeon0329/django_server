import pytest
from django.db import IntegrityError
from django.db.models import ProtectedError

@pytest.mark.django_db
def test_idempotency_status_code_constraint_allows_valid():
    from core.models import IdempotencyKey
    obj = IdempotencyKey.objects.create(
        key="k-ok",
        request_hash="h1",
        status_code=200,
        response_body="{}",
    )
    assert obj.pk is not None

@pytest.mark.django_db
def test_idempotency_status_code_constraint_blocks_invalid():
    from core.models import IdempotencyKey
    with pytest.raises(IntegrityError):
        IdempotencyKey.objects.create(
            key="k-bad",
            request_hash="h1",
            status_code=42,  # 0 또는 100~599만 허용
            response_body="{}",
        )

@pytest.mark.django_db
def test_outbox_defaults_and_protect(tenant):
    from core.models import Outbox, Tenant
    ev = Outbox.objects.create(
        tenant=tenant,
        event_name="user.created",
        payload={"id": 1},
    )
    assert ev.published is False

    # Tenant가 참조되는 동안은 삭제 PROTECT
    with pytest.raises(ProtectedError):
        tenant.delete()

@pytest.mark.django_db
def test_tenant_str_and_indexes(tenant):
    # __str__ 확인 정도
    assert str(tenant) == tenant.code

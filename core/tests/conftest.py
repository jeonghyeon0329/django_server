"""
fixture 사용시 DB트랜잭션을 열고, 끝나면 롤백해 테스트간 격리를 보장
"""
import json
import pytest
from django.test import RequestFactory

@pytest.fixture
def rf():
    return RequestFactory()

@pytest.fixture
def tenant(db):
    from core.models import Tenant
    return Tenant.objects.create(code="acme", name="ACME Inc.")

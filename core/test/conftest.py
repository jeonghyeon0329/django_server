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

from django.db import transaction
from django.utils import timezone
from accounts.models import Membership, Role, User
from core.models import Tenant

DEFAULT_TENANT_CODE = "public"
DEFAULT_ROLE_CODE = "member"

@transaction.atomic
def register_user_and_membership(*, username: str, email: str, password: str) -> User:
    user = User.objects.create_user(
        username=username,
        email=email.lower(),
        password=password,
        is_email_verified=False,
        last_terms_agreed_at=timezone.now(),
    )
    tenant = Tenant.objects.get(code=DEFAULT_TENANT_CODE)
    membership = Membership.objects.create(user=user, tenant=tenant, is_active=True)

    try:
        role = Role.objects.get(tenant=tenant, code=DEFAULT_ROLE_CODE)

        print("\n11111")
        print(role)
        print()
        
        membership.roles.add(role)
    except Role.DoesNotExist:
        pass

    return user

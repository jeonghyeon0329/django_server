from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class User(AbstractUser):
    is_email_verified = models.BooleanField(default=False, db_index=True)
    last_terms_agreed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "사용자"
        verbose_name_plural = "사용자"
        indexes = [
            models.Index(fields=["is_active", "is_email_verified"]),
        ]

    def __str__(self):
        return self.get_username()

class Membership(models.Model):
    """
    한 사용자(User)가 여러 테넌트(Tenant)에 속할 수 있고,
    테넌트별로 다른 역할/상태를 가질 수 있게 하는 연결 테이블.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_index=True)
    tenant = models.ForeignKey("core.Tenant", on_delete=models.PROTECT, db_index=True)

    # 테넌트 스코프의 프로필/정책
    display_name = models.CharField(max_length=150, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)    
    external_id = models.CharField(max_length=150, blank=True) # 테넌트별 고유 식별자(사번/파트너ID 등)

    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    roles = models.ManyToManyField("accounts.Role", through="accounts.MembershipRole", related_name="memberships", blank=True,)

    class Meta:
        verbose_name = "멤버십"
        verbose_name_plural = "멤버십"
        constraints = [
            # 한 유저는 한 테넌트에 한 번만 가입
            models.UniqueConstraint(fields=["user", "tenant"], name="uniq_membership_user_tenant"),
        ]
        indexes = [
            models.Index(fields=["tenant", "code"]),
        ]

    def __str__(self):
        return f"{self.user} @ {self.tenant}"

class Role(models.Model):
    """
    RBAC용 역할(테넌트 스코프). 예: owner, admin, manager, member 등
    """
    tenant = models.ForeignKey("core.Tenant", on_delete=models.PROTECT, db_index=True)
    code = models.CharField(max_length=50)  # 'owner', 'admin' 등
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name = "역할"
        verbose_name_plural = "역할"
        constraints = [
            models.UniqueConstraint(fields=["tenant", "code"], name="uniq_role_tenant_code"),
        ]

    def __str__(self):
        return f"{self.tenant}:{self.code}"


class MembershipRole(models.Model):
    membership = models.ForeignKey("accounts.Membership", on_delete=models.CASCADE, db_index=True)
    role = models.ForeignKey("accounts.Role", on_delete=models.PROTECT, db_index=True)

    class Meta:
        verbose_name = "멤버십-역할"
        verbose_name_plural = "멤버십-역할"
        constraints = [
            models.UniqueConstraint(fields=["membership", "role"], name="uniq_mship_role"),
        ]

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from core.models import Tenant
from .models import Membership, Role
from rest_framework import serializers

User = get_user_model()

class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    tenant_id = serializers.IntegerField(required=False)
    role_codes = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False
    )

    class Meta:
        model = User
        fields = ("username", "email", "password", "tenant_id", "role_codes")

    def validate_password(self, value):
        validate_password(value)
        return value

    @transaction.atomic
    def create(self, validated_data):
        tenant_id = validated_data.pop("tenant_id", "public")
        role_codes = validated_data.pop("role_codes", "member")

        user = User(
            username=validated_data["username"],
            email=validated_data.get("email", ""),
        )
        user.set_password(validated_data["password"])
        user.save()

        if tenant_id:
            tenant = Tenant.objects.select_for_update().get(id=tenant_id)
            membership = Membership.objects.create(user=user, tenant=tenant)
            if role_codes:
                roles = list(Role.objects.filter(tenant=tenant, code__in=role_codes))
                membership.roles.set(roles)

        return user
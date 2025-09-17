from django.contrib import admin
from django.urls import path, include

from accounts.views import signup

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),  # 로그인/로그아웃
    path("accounts/", include("accounts.urls")),             # 회원가입 등 우리가 만든 URL
]
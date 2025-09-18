from django.contrib import admin
from django.urls import path, include

# from accounts.views import signup
from accounts.views import SignupAPIView 
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    # path("accounts/", include("django.contrib.auth.urls")),
    # path("accounts/signup/", signup, name="signup"),
    path("api/accounts/signup/", SignupAPIView.as_view(), name="api-signup"),
    path("api/accounts/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/accounts/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
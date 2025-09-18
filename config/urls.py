from django.contrib import admin
from django.urls import path, include

# from accounts.views import signup
urlpatterns = [
    path("admin/", admin.site.urls),
    # path("accounts/", include("django.contrib.auth.urls")),
    # path("accounts/signup/", signup, name="signup"),
    path("api/accounts/", include("accounts.urls")),
]
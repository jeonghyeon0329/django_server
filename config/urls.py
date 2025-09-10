from django.contrib import admin
from django.urls import path

from django.http import JsonResponse
def test_view(request):
    return JsonResponse({
        "tenant": str(getattr(request, "tenant", None))
    })

urlpatterns = [
    path('admin/', admin.site.urls),
    path("test/", test_view),
]

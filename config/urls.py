from django.contrib import admin
from django.urls import path

from django.http import JsonResponse
def test_view(request):
    return JsonResponse({
        "tenant": str(getattr(request, "tenant", None))
    })

from uuid import uuid4
from django.views.decorators.csrf import csrf_exempt
@csrf_exempt
def test_view2(request):
    # 매 요청마다 달라지는 값(랜덤 UUID)을 응답에 포함
    return JsonResponse({
        "tenant": str(getattr(request, "tenant", None)),
        "request_id": str(uuid4()),
    }, status=201)

urlpatterns = [
    path('admin/', admin.site.urls),
    path("test/", test_view),
    path("test2/", test_view2),
]

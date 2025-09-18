from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.db import IntegrityError
from .serializers import SignupSerializer
from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import SignUpForm
from .services import register_user_and_membership

# def signup(request):
#     if request.method == "POST":
#         form = SignUpForm(request.POST)
#         if form.is_valid():
#             user = register_user_and_membership(
#                 username=form.cleaned_data["username"],
#                 email=form.cleaned_data["email"],
#                 password=form.cleaned_data["password1"],
#             )
#             # login(request, user) # 자동로그인
#             return redirect("home")
#     else:
#         form = SignUpForm()
#     return render(request, "accounts/signup.html", {"form": form})

class SignupAPIView(generics.CreateAPIView):
    """
    회원가입 API
    - 인증 불필요 (AllowAny)
    - POST /api/accounts/signup/
      body: { username, email, password, tenant_id?, role_codes? }
    """
    serializer_class = SignupSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = []  # 회원가입은 보통 비인증 허용

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            user = serializer.save()
        except IntegrityError:
            return Response(
                {"detail": "이미 존재하는 사용자명(또는 이메일)입니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        headers = self.get_success_headers(serializer.data)
        return Response(
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "is_email_verified": getattr(user, "is_email_verified", False),
            },
            status=status.HTTP_201_CREATED,
            headers=headers,
        )
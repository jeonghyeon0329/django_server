from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import SignUpForm
from .services import register_user_and_membership

def signup(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = register_user_and_membership(
                username=form.cleaned_data["username"],
                email=form.cleaned_data["email"],
                password=form.cleaned_data["password1"],
            )
            # login(request, user) # 자동로그인
            return redirect("home")
    else:
        form = SignUpForm()
    return render(request, "accounts/signup.html", {"form": form})

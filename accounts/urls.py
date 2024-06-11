from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegistrationAPIView,
    LoginAPIView,
    ProfileAPIView,
    PasswordUpdateAPIView,
    LogoutAPIView,
    ProfileUpdateAPIView,
)

urlpatterns = [
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    
    path("register/", RegistrationAPIView.as_view(), name="registration"),
    path("login/", LoginAPIView.as_view(), name="login"),
    path("logout/", LogoutAPIView.as_view(), name="logout"),
    
    path("profile/", ProfileAPIView.as_view(), name="profile-details"),
    path("profile/update/", ProfileUpdateAPIView.as_view(), name="profile-update"),
    path("password/update/", PasswordUpdateAPIView.as_view(), name="password-update"),
    
]

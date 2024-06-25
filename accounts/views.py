from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from .models import UserProfile
from .serializers import (
    LoginSerializer,
    RegisterSerializer,
    PasswordUpdateSerializer,
    LogoutSerializer,
    ProfileUpdateSerializer,
    PasswordResetSerializer,
    PasswordResetConfirmSerializer,
)
from django.contrib.auth.models import User
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.utils.html import strip_tags
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
from projectTeams.models import Team

# Registration
class RegistrationAPIView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            response = {"message": "User account created successfully"}
            return Response(response, status=status.HTTP_201_CREATED)
        errors = serializer.errors
        response = {}
        if 'email' in errors:
            response['error'] = errors['email'][0]
        elif 'password' in errors:
            response['error'] = "This password is too short. It must contain at least 8 characters."
        elif 'first_name' in errors:
            response['error'] = "Name must be at least 2 characters long."
        else:
            response['error'] = "Invalid data provided."
        return Response(response, status=status.HTTP_400_BAD_REQUEST)



# Login
class LoginAPIView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data
            refresh = RefreshToken.for_user(user)
            try:
                user_profile = UserProfile.objects.get(user=user)
                if user_profile.profile_image:
                    profile_image_url = request.build_absolute_uri(
                        user_profile.profile_image.url
                    )
                else:
                    profile_image_url = None
            except UserProfile.DoesNotExist:
                profile_image_url = None
                
            team_name = user.first_name
            try:
                team = Team.objects.get(owner=user, name=team_name)
                team_id = team.id
            except Team.DoesNotExist:
                team_id = None

            response = {
                "message": "User login successfully",
                "data": {
                    "user": {
                        "user_id": user.id,
                        "full_name": user.first_name,
                        "email": user.email,
                        "profile_image": profile_image_url,
                        "team_id":team_id
                    },
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
            }
            return Response(response, status=status.HTTP_200_OK)
        errors = serializer.errors
        response = {}
        if 'email' in errors:
            response['error'] = errors['email'][0]
        elif 'non_field_errors' in errors:
            response['error'] =  errors['non_field_errors'][0]
        else:
            response['error'] = serializer.errors
        return Response(response, status=status.HTTP_400_BAD_REQUEST)


# Profile Details
class ProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        try:
            user_profile = UserProfile.objects.get(user=user)
            if user_profile.profile_image:
                profile_image_url = request.build_absolute_uri(
                    user_profile.profile_image.url
                )
            else:
                profile_image_url = None
        except UserProfile.DoesNotExist:
            profile_image_url = None
        team_name = user.first_name
        try:
            team = Team.objects.get(owner=user, name=team_name)
            team_id = team.id
        except Team.DoesNotExist:
            team_id = None
        response = {
            "message": "Profile details fetch successfully",
            "data": {
                "user_id": user.id,
                "full_name": user.first_name,
                "email": user.email,
                "profile_image": profile_image_url,
                "team_id":team_id
            },
        }
        return Response(response, status=status.HTTP_200_OK)


# Profile Update
class ProfileUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        serializer = ProfileUpdateSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            user = request.user
            serializer.update(user, serializer.validated_data)
            profile_image = serializer.validated_data.get("profile_image")
            if profile_image:
                try:
                    user_profile = UserProfile.objects.get(user=user)
                    user_profile.profile_image = profile_image
                    user_profile.save()
                except UserProfile.DoesNotExist:
                    UserProfile.objects.create(user=user, profile_image=profile_image)
            user = request.user
            profile_image_url = None
            user_profile = UserProfile.objects.filter(user=user).first()
            if user_profile and user_profile.profile_image:
                profile_image_url = request.build_absolute_uri(
                    user_profile.profile_image.url
                )
            response = {
                "message": "Profile details updated successfully",
                "data": {
                    "full_name": user.first_name,
                    "email": user.email,
                    "profile_image": profile_image_url,
                },
            }
            return Response(response, status=status.HTTP_200_OK)
        return Response(
            {"error": "Failed to update profile"},
            status=status.HTTP_400_BAD_REQUEST,
        )


# Change Password
class PasswordUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        serializer = PasswordUpdateSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            old_password = serializer.validated_data.get("old_password")
            new_password = serializer.validated_data.get("new_password")
            if not user.check_password(old_password):
                return Response(
                    {"error": "Incorrect old password"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user.set_password(new_password)
            user.save()
            return Response(
                {"message": "Password updated successfully"}, status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"error": "Failed to update password"},
                status=status.HTTP_400_BAD_REQUEST,
            )


# Logout
class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"Logout successfully"}, status=status.HTTP_201_CREATED)
        return Response(
            {"error": "Invalid refresh token. Failed to logout"},
            status=status.HTTP_404_NOT_FOUND,
        )


# Password Reset Request
class PasswordResetRequestView(APIView):
    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            user = User.objects.get(email=email)
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            reset_link = f"{settings.FRONTEND_URL}/api/accounts/password-reset-confirm/{uid}/{token}/"
            print(reset_link)
            subject = "Forget Password Request"
            html_content = render_to_string(
                "password_reset_email.html",
                {
                    "reset_link": reset_link,
                    "user": user,
                },
            )
            text_content = strip_tags(html_content)
            msg = EmailMultiAlternatives(
                subject, text_content, settings.EMAIL_HOST_USER, [email]
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            return Response(
                {"message": "Password reset link sent."}, status=status.HTTP_200_OK
            )
        return Response(
            {"error": "Failed to send reset password link"},
            status=status.HTTP_400_BAD_REQUEST,
        )


class PasswordResetConfirmView(APIView):
    def post(self, request, uidb64, token):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            try:
                uid = force_str(urlsafe_base64_decode(uidb64))
                user = User.objects.get(pk=uid)
                if default_token_generator.check_token(user, token):
                    user.set_password(serializer.validated_data["new_password"])
                    user.save()
                    return Response(
                        {"message": "Password reset successful."},
                        status=status.HTTP_200_OK,
                    )
                else:
                    return Response(
                        {"message": "Invalid token or UID."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            except (TypeError, ValueError, OverflowError, User.DoesNotExist):
                return Response(
                    {"error": "Invalid token or UID."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        return Response(
            {"error": "Your token has been expired."},
            status=status.HTTP_400_BAD_REQUEST,
        )

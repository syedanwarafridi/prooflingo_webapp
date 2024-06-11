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
)


# Registration
class RegistrationAPIView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            response = {
                "message": "User account created successfully"
            }
            return Response(response, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
            response = {
                "message": "User login successfully",
                "data": {
                    "user": {
                        "user_id": user.id,
                        "full_name": user.first_name,
                        "email": user.email,
                        "profile_image": profile_image_url,
                    },
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
            }
            return Response(response, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
        response = {
            "message": "Profile details fetch successfully",
            "data": {
                "user_id": user.id,
                "full_name": user.first_name,
                "email": user.email,
                "profile_image": profile_image_url,
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
            if profile_image:  # Check if profile image is provided
                try:
                    user_profile = UserProfile.objects.get(user=user)
                    user_profile.profile_image = profile_image
                    user_profile.save()
                except UserProfile.DoesNotExist:
                    UserProfile.objects.create(user=user, profile_image=profile_image)
            user = request.user  # Refresh user data
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
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
                    {"detail": "Incorrect old password"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user.set_password(new_password)
            user.save()
            return Response(
                {"detail": "Password updated successfully"}, status=status.HTTP_200_OK
            )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Logout
class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"Logout successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

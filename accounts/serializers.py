from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.core.validators import validate_email , FileExtensionValidator
from django.core.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from django.contrib.auth.password_validation import validate_password

# Register Serializers
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(max_length=68, write_only=True)
    first_name = serializers.CharField(max_length=30)

    class Meta:
        model = User
        fields = ["first_name", "email", "password"]

    def validate_first_name(self, value):
        if len(value) < 2:
            raise serializers.ValidationError(
                "Name must be at least 4 characters long."
            )
        if not all(char.isalpha() or char.isspace() for char in value):
            raise serializers.ValidationError(
                "Name can only contain alphabetic characters and spaces."
            )
        return value

    def validate_email(self, value):
        value = value.lower()
        validate_email(value)
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Email is already in use.")
        return value

    def validate_password(self, value):
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(str(e))
        return value

    def validate(self, attrs):
        if "first_name" not in attrs:
            raise serializers.ValidationError("Name is required.")
        if "email" not in attrs:
            raise serializers.ValidationError("Email is required.")
        if "password" not in attrs:
            raise serializers.ValidationError("Password is required.")
        return attrs

    def create(self, validated_data):
        validated_data['email'] = validated_data['email'].lower()
        user = User.objects.create_user(
            username=validated_data["email"],
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data["first_name"],
        )
        return user


# Login Serializers
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255, min_length=6, required=True)
    password = serializers.CharField(max_length=68, min_length=8, write_only=True)

    def validate(self, data):
        email = data.get("email").lower()
        password = data.get("password")
        if email and password:
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                raise serializers.ValidationError("No registered user found against your email address")
            user = authenticate(username=user.username, password=password)
            if user and user.is_active:
                return user
            raise serializers.ValidationError("Incorrect password, please try again")
        else:
            raise serializers.ValidationError("Must include both email and password")


# Logout Serializers
class LogoutSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()

    def validate(self, attrs):
        self.token = attrs["refresh_token"]
        return attrs

    def save(self, **kwargs):
        try:
            RefreshToken(self.token).blacklist()
        except TokenError:
            raise serializers.ValidationError("Invalid refresh token")


# Password field Update Serializer
class PasswordUpdateSerializer(serializers.Serializer):
    old_password = serializers.CharField(max_length=68, min_length=8, write_only=True)
    new_password = serializers.CharField(max_length=68, min_length=8, write_only=True)

    def validate_new_password(self, value):
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(str(e))
        return value

    def validate(self, data):
        old_password = data.get("old_password")
        new_password = data.get("new_password")

        if old_password == new_password:
            raise serializers.ValidationError(
                "New password must be different from old password"
            )

        return data


# Profile username and email update Serializer
class ProfileUpdateSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255, min_length=6, required=True)
    full_name = serializers.CharField(max_length=150, min_length=5, required=True)
    profile_image = serializers.ImageField(required=False, validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'gif'])])
    
    def validate_full_name(self, value):
        if len(value) < 2:
            raise serializers.ValidationError(
                "Name must be at least 2 characters long."
            )
        if not all(char.isalpha() or char.isspace() for char in value):
            raise serializers.ValidationError(
                "Name can only contain alphabetic characters and spaces."
            )
        return value

    def validate_email(self, value):
        validate_email(value)
        user = self.context['request'].user
        if User.objects.filter(email=value).exclude(id=user.id).exists():
            raise serializers.ValidationError("Email is already in use.")
        return value

    def update(self, instance, validated_data):
        instance.email = validated_data.get('email', instance.email)
        instance.first_name = validated_data.get('full_name', instance.first_name)
        instance.save()
        return instance
 

# Forget Password Serializer
class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is not registered.")
        return value

# Password Reset Confirm Serializer
class PasswordResetConfirmSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True)
    token = serializers.CharField(write_only=True)
    uidb64 = serializers.CharField(write_only=True)
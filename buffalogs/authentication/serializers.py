from django.contrib import auth
from django.contrib.auth import logout
from rest_framework import serializers as rfs
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import TokenError

from .models import User


class RegisterSerializer(rfs.ModelSerializer):
    password = rfs.CharField(max_length=68, min_length=6, write_only=True)

    default_error_messages = {
        "username": "The username should only contain alphanumeric characters"
    }

    class Meta:
        model = User
        fields = ["email", "username", "password"]

    def validate(self, attrs):
        email = attrs.get("email", "")
        username = attrs.get("username", "")

        user_filtered_by_email = User.objects.filter(email=email).first()
        if user_filtered_by_email:
            raise rfs.ValidationError("User with that email already exists")

        user_filtered_by_username = User.objects.filter(username=username).first()
        if user_filtered_by_username:
            raise rfs.ValidationError("User with that username already exists")

        if not username.isalnum():
            raise rfs.ValidationError(self.default_error_messages)
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class LoginSerializer(rfs.ModelSerializer):
    email = rfs.EmailField(max_length=255, min_length=3)
    password = rfs.CharField(max_length=68, min_length=6, write_only=True)

    tokens = rfs.SerializerMethodField()

    def get_tokens(self, obj):
        user = User.objects.get(email=obj["email"])

        return {"refresh": user.tokens()["refresh"], "access": user.tokens()["access"]}

    class Meta:
        model = User
        fields = [
            "email",
            "password",
            "tokens",
        ]

    def validate(self, attrs):
        email = attrs.get("email", "")
        password = attrs.get("password", "")


        user = auth.authenticate(email=email, password=password)

        if not user:
            raise AuthenticationFailed("Invalid credentials, try again")

        return {"email": user.email, "username": user.username, "tokens": user.tokens}


class LogoutSerializer(rfs.Serializer):
    default_error_message = {"bad_token": ("Token is expired or invalid")}

    def validate(self, attrs):
        user = self.context["request"].user
        self.tokens = user.tokens()
        return attrs

    def save(self):
        try:
            logout(self.context["request"])
        except TokenError:
            self.fail("bad_token")


class UserSerializer(rfs.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "created_at",
            "updated_at",
            "avatar",
            "is_staff",
        )
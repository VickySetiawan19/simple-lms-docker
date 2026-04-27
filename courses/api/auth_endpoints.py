from ninja import Router
from ninja.errors import HttpError
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
import jwt
import datetime as dt
from django.conf import settings

from courses.models import UserProfile
from courses.api.schemas import (
    RegisterIn, LoginIn, TokenOut, RefreshIn, AccessTokenOut,
    ProfileUpdateIn, UserOut,
)
from courses.api.auth import generate_tokens, decode_token, jwt_auth

router = Router(tags=["Auth"])


@router.post("/register", response={201: UserOut}, auth=None)
def register(request, data: RegisterIn):
    """Register pengguna baru. Role: student | instructor | admin"""
    if User.objects.filter(username=data.username).exists():
        raise HttpError(400, "Username sudah digunakan")
    if User.objects.filter(email=data.email).exists():
        raise HttpError(400, "Email sudah digunakan")

    valid_roles = {"student", "instructor", "admin"}
    if data.role not in valid_roles:
        raise HttpError(400, f"Role tidak valid. Pilih: {', '.join(valid_roles)}")

    user = User.objects.create_user(
        username=data.username,
        email=data.email,
        password=data.password,
        first_name=data.first_name,
        last_name=data.last_name,
    )
    UserProfile.objects.create(user=user, role=data.role)
    return 201, user


@router.post("/login", response=TokenOut, auth=None)
def login(request, data: LoginIn):
    """Login dan dapatkan JWT access + refresh token."""
    user = authenticate(username=data.username, password=data.password)
    if user is None:
        raise HttpError(401, "Username atau password salah")
    if not user.is_active:
        raise HttpError(401, "Akun tidak aktif")
    return generate_tokens(user)


@router.post("/refresh", response=AccessTokenOut, auth=None)
def refresh_token(request, data: RefreshIn):
    """Gunakan refresh token untuk mendapatkan access token baru."""
    payload = decode_token(data.refresh, expected_type="refresh")
    try:
        user = User.objects.get(pk=payload["user_id"])
    except User.DoesNotExist:
        raise HttpError(401, "User tidak ditemukan")

    now = dt.datetime.now(dt.timezone.utc)
    access_payload = {
        "user_id": user.id,
        "username": user.username,
        "type": "access",
        "iat": now,
        "exp": now + dt.timedelta(minutes=15),
    }
    access_token = jwt.encode(access_payload, settings.SECRET_KEY, algorithm="HS256")
    return {"access": access_token}


@router.get("/me", response=UserOut, auth=jwt_auth)
def get_me(request):
    """Dapatkan data profil user yang sedang login."""
    return request.auth


@router.put("/me", response=UserOut, auth=jwt_auth)
def update_me(request, data: ProfileUpdateIn):
    """Update profil user yang sedang login."""
    user = request.auth

    if data.first_name is not None:
        user.first_name = data.first_name
    if data.last_name is not None:
        user.last_name = data.last_name
    if data.email is not None:
        if User.objects.exclude(pk=user.pk).filter(email=data.email).exists():
            raise HttpError(400, "Email sudah digunakan oleh user lain")
        user.email = data.email
    user.save()

    if data.bio is not None:
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.bio = data.bio
        profile.save()

    return user
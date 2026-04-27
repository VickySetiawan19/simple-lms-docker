import jwt
import functools
from datetime import datetime, timedelta, timezone

from django.conf import settings
from django.contrib.auth.models import User
from ninja.security import HttpBearer
from ninja.errors import HttpError

from courses.models import UserProfile


# ─── Token Generation ───────────────────────────────────

def generate_tokens(user):
    now = datetime.now(timezone.utc)

    access_payload = {
        "user_id": user.id,
        "username": user.username,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=15),
    }
    refresh_payload = {
        "user_id": user.id,
        "type": "refresh",
        "iat": now,
        "exp": now + timedelta(days=7),
    }

    access_token = jwt.encode(access_payload, settings.SECRET_KEY, algorithm="HS256")
    refresh_token = jwt.encode(refresh_payload, settings.SECRET_KEY, algorithm="HS256")

    return {"access": access_token, "refresh": refresh_token}


def decode_token(token, expected_type="access"):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HttpError(401, "Token telah kadaluarsa")
    except jwt.InvalidTokenError:
        raise HttpError(401, "Token tidak valid")

    if payload.get("type") != expected_type:
        raise HttpError(401, f"Token type harus '{expected_type}'")

    return payload


# ─── Ninja Auth Backend ──────────────────────────────────

class JWTAuth(HttpBearer):
    def authenticate(self, request, token):
        payload = decode_token(token, expected_type="access")
        try:
            user = User.objects.select_related("profile").get(pk=payload["user_id"])
        except User.DoesNotExist:
            raise HttpError(401, "User tidak ditemukan")
        return user


jwt_auth = JWTAuth()


# ─── Helper Role ─────────────────────────────────────────

def get_role(user):
    try:
        return user.profile.role
    except UserProfile.DoesNotExist:
        return "student"


# ─── Role Decorators (RBAC) ──────────────────────────────

def _require_role(*roles):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(request, *args, **kwargs):
            user = request.auth
            if get_role(user) not in roles:
                raise HttpError(403, f"Akses ditolak. Role dibutuhkan: {', '.join(roles)}")
            return func(request, *args, **kwargs)
        return wrapper
    return decorator


def is_admin(func):
    return _require_role("admin")(func)


def is_instructor(func):
    return _require_role("instructor", "admin")(func)


def is_student(func):
    return _require_role("student", "admin")(func)
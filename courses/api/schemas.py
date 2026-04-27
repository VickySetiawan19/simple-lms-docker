from ninja import Schema
from typing import Optional, List
from datetime import datetime


# ─── Auth Schemas ────────────────────────────────────────

class RegisterIn(Schema):
    username: str
    email: str
    password: str
    first_name: str = ""
    last_name: str = ""
    role: str = "student"


class LoginIn(Schema):
    username: str
    password: str


class TokenOut(Schema):
    access: str
    refresh: str


class RefreshIn(Schema):
    refresh: str


class AccessTokenOut(Schema):
    access: str


class ProfileUpdateIn(Schema):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    bio: Optional[str] = None


# ─── User Schemas ────────────────────────────────────────

class UserOut(Schema):
    id: int
    username: str
    first_name: str
    last_name: str
    email: str
    role: Optional[str] = "student"

    @staticmethod
    def resolve_role(obj):
        try:
            return obj.profile.role
        except Exception:
            return "student"


# ─── Course Schemas ──────────────────────────────────────

class CourseIn(Schema):
    title: str
    description: str
    category_id: Optional[int] = None
    is_published: bool = True


class CoursePatchIn(Schema):
    title: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    is_published: Optional[bool] = None


class LessonTitleOut(Schema):
    id: int
    title: str
    order: int


class CourseOut(Schema):
    id: int
    title: str
    description: str
    is_published: bool
    instructor: UserOut
    created_at: datetime
    updated_at: datetime


class CourseDetailOut(CourseOut):
    lessons: List[LessonTitleOut] = []

    @staticmethod
    def resolve_lessons(obj):
        return list(obj.lessons.all())


class PaginatedCourseOut(Schema):
    total: int
    page: int
    page_size: int
    results: List[CourseOut]


# ─── Enrollment Schemas ──────────────────────────────────

class EnrollmentIn(Schema):
    course_id: int


class EnrollmentOut(Schema):
    id: int
    course: CourseOut
    enrolled_at: datetime


class ProgressIn(Schema):
    lesson_id: int
    is_completed: bool = True


class ProgressOut(Schema):
    id: int
    lesson_id: int
    lesson_title: str
    is_completed: bool
    completed_at: Optional[datetime] = None

    @staticmethod
    def resolve_lesson_title(obj):
        return obj.lesson.title


# ─── Generic ─────────────────────────────────────────────

class MessageOut(Schema):
    message: str
from ninja import Router
from ninja.errors import HttpError
from typing import List

from courses.models import Course, Lesson
from courses.api.schemas import LessonIn, LessonOut
from courses.api.auth import jwt_auth, is_instructor, is_admin, get_role

router = Router(tags=["Lessons"])


# ─── PUBLIC ──────────────────────────────────────────────

@router.get("/{course_id}", response=List[LessonOut], auth=None)
def list_lessons(request, course_id: int):
    """Daftar semua lesson dalam satu course."""
    try:
        course = Course.objects.get(pk=course_id, is_published=True)
    except Course.DoesNotExist:
        raise HttpError(404, "Course tidak ditemukan")

    lessons = Lesson.objects.filter(course=course).order_by("order")
    return list(lessons)


# ─── PROTECTED ───────────────────────────────────────────

@router.post("/{course_id}", response={201: LessonOut}, auth=jwt_auth)
@is_instructor
def create_lesson(request, course_id: int, data: LessonIn):
    """Buat lesson baru di course. Hanya pemilik course atau Admin."""
    try:
        course = Course.objects.get(pk=course_id)
    except Course.DoesNotExist:
        raise HttpError(404, "Course tidak ditemukan")

    user = request.auth
    role = get_role(user)
    if role != "admin" and course.instructor_id != user.pk:
        raise HttpError(403, "Anda bukan pemilik course ini")

    lesson = Lesson.objects.create(
        course=course,
        title=data.title,
        content=data.content,
        order=data.order,
    )
    return 201, lesson


@router.patch("/{lesson_id}/update", response=LessonOut, auth=jwt_auth)
@is_instructor
def update_lesson(request, lesson_id: int, data: LessonIn):
    """Update lesson. Hanya pemilik course atau Admin."""
    try:
        lesson = Lesson.objects.select_related("course").get(pk=lesson_id)
    except Lesson.DoesNotExist:
        raise HttpError(404, "Lesson tidak ditemukan")

    user = request.auth
    role = get_role(user)
    if role != "admin" and lesson.course.instructor_id != user.pk:
        raise HttpError(403, "Anda bukan pemilik course ini")

    if data.title is not None:
        lesson.title = data.title
    if data.content is not None:
        lesson.content = data.content
    if data.order is not None:
        lesson.order = data.order
    lesson.save()

    return lesson


@router.delete("/{lesson_id}/delete", response={204: None}, auth=jwt_auth)
@is_admin
def delete_lesson(request, lesson_id: int):
    """Hapus lesson. Hanya Admin."""
    try:
        lesson = Lesson.objects.get(pk=lesson_id)
    except Lesson.DoesNotExist:
        raise HttpError(404, "Lesson tidak ditemukan")

    lesson.delete()
    return 204, None

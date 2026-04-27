from ninja import Router
from ninja.errors import HttpError
from django.db import IntegrityError
from django.utils import timezone
from typing import List

from courses.models import Course, Enrollment, Lesson, Progress
from courses.api.schemas import (
    EnrollmentIn, EnrollmentOut, ProgressIn, ProgressOut,
)
from courses.api.auth import jwt_auth, is_student

router = Router(tags=["Enrollments"])


@router.post("", response={201: EnrollmentOut}, auth=jwt_auth)
@is_student
def enroll_course(request, data: EnrollmentIn):
    """Daftar ke course. Hanya Student dan Admin."""
    try:
        course = Course.objects.get(pk=data.course_id, is_published=True)
    except Course.DoesNotExist:
        raise HttpError(404, "Course tidak ditemukan")

    try:
        enrollment = Enrollment.objects.create(
            student=request.auth,
            course=course
        )
    except IntegrityError:
        raise HttpError(409, "Anda sudah terdaftar di course ini")

    enrollment = Enrollment.objects.select_related(
        "course", "course__instructor", "course__instructor__profile"
    ).get(pk=enrollment.pk)
    return 201, enrollment


@router.get("/my-courses", response=List[EnrollmentOut], auth=jwt_auth)
def my_courses(request):
    """Daftar semua course yang sudah diikuti."""
    enrollments = Enrollment.objects.select_related(
        "course", "course__instructor", "course__instructor__profile"
    ).filter(student=request.auth).order_by("-enrolled_at")
    return list(enrollments)


@router.post("/{enrollment_id}/progress", response={201: ProgressOut}, auth=jwt_auth)
def mark_progress(request, enrollment_id: int, data: ProgressIn):
    """Tandai lesson sebagai selesai atau belum selesai."""
    try:
        enrollment = Enrollment.objects.select_related("course").get(
            pk=enrollment_id, student=request.auth
        )
    except Enrollment.DoesNotExist:
        raise HttpError(404, "Enrollment tidak ditemukan")

    try:
        lesson = Lesson.objects.get(pk=data.lesson_id, course=enrollment.course)
    except Lesson.DoesNotExist:
        raise HttpError(404, "Lesson tidak ditemukan dalam course ini")

    progress, created = Progress.objects.get_or_create(
        student=request.auth,
        lesson=lesson,
    )
    progress.is_completed = data.is_completed
    if data.is_completed:
        progress.completed_at = timezone.now()
    else:
        progress.completed_at = None
    progress.save()

    return 201, progress
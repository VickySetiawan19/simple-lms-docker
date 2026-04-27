from ninja import Router
from ninja.errors import HttpError
from typing import Optional

from courses.models import Course
from courses.api.schemas import (
    CourseIn, CoursePatchIn, CourseOut, CourseDetailOut,
    PaginatedCourseOut,
)
from courses.api.auth import jwt_auth, is_instructor, is_admin, get_role

router = Router(tags=["Courses"])


# ─── PUBLIC ──────────────────────────────────────────────

@router.get("", response=PaginatedCourseOut, auth=None)
def list_courses(
    request,
    search: Optional[str] = None,
    category_id: Optional[int] = None,
    instructor_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 10,
):
    """Daftar semua course. Mendukung pagination dan filter."""
    qs = Course.objects.select_related(
        "instructor", "instructor__profile", "category"
    ).filter(is_published=True)

    if search:
        qs = qs.filter(title__icontains=search)
    if category_id:
        qs = qs.filter(category_id=category_id)
    if instructor_id:
        qs = qs.filter(instructor_id=instructor_id)

    qs = qs.order_by("-created_at")
    total = qs.count()
    offset = (page - 1) * page_size
    results = list(qs[offset: offset + page_size])

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "results": results,
    }


@router.get("/{course_id}", response=CourseDetailOut, auth=None)
def get_course(request, course_id: int):
    """Detail course beserta daftar lesson."""
    try:
        course = Course.objects.select_related(
            "instructor", "instructor__profile", "category"
        ).prefetch_related("lessons").get(pk=course_id, is_published=True)
    except Course.DoesNotExist:
        raise HttpError(404, "Course tidak ditemukan")
    return course


# ─── PROTECTED ───────────────────────────────────────────

@router.post("", response={201: CourseOut}, auth=jwt_auth)
@is_instructor
def create_course(request, data: CourseIn):
    """Buat course baru. Hanya Instructor dan Admin."""
    course = Course.objects.create(
        instructor=request.auth,
        **data.dict(),
    )
    course = Course.objects.select_related(
        "instructor", "instructor__profile"
    ).get(pk=course.pk)
    return 201, course


@router.patch("/{course_id}", response=CourseOut, auth=jwt_auth)
def update_course(request, course_id: int, data: CoursePatchIn):
    """Update sebagian field course. Hanya pemilik atau Admin."""
    try:
        course = Course.objects.select_related(
            "instructor", "instructor__profile"
        ).get(pk=course_id)
    except Course.DoesNotExist:
        raise HttpError(404, "Course tidak ditemukan")

    user = request.auth
    role = get_role(user)

    if role != "admin" and course.instructor_id != user.pk:
        raise HttpError(403, "Anda bukan pemilik course ini")

    for field, value in data.dict(exclude_unset=True).items():
        setattr(course, field, value)
    course.save()

    return course


@router.delete("/{course_id}", response={204: None}, auth=jwt_auth)
@is_admin
def delete_course(request, course_id: int):
    """Hapus course. Hanya Admin."""
    try:
        course = Course.objects.get(pk=course_id)
    except Course.DoesNotExist:
        raise HttpError(404, "Course tidak ditemukan")

    course.delete()
    return 204, None
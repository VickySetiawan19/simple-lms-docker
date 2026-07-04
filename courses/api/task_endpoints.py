from ninja import Router
from ninja.errors import HttpError
from celery.result import AsyncResult

from courses.api.schemas import TaskTriggerOut, TaskStatusOut
from courses.api.auth import jwt_auth, is_admin, is_instructor

router = Router(tags=["Tasks"])


# ─── TRIGGER ASYNC TASKS ─────────────────────────────────

@router.post("/export-report", response=TaskTriggerOut, auth=jwt_auth)
@is_admin
def trigger_export_report(request, course_id: int = None):
    """
    Trigger async task untuk generate CSV report enrollment.
    Hanya Admin. Mengembalikan task_id untuk tracking status.
    """
    from courses.tasks import export_course_report

    task = export_course_report.delay(
        course_id=course_id,
        requested_by_user_id=request.auth.id,
    )

    return {
        "task_id": task.id,
        "status": "PENDING",
        "message": "Report sedang diproses. Gunakan task_id untuk cek status.",
    }


@router.post("/generate-certificate", response=TaskTriggerOut, auth=jwt_auth)
@is_instructor
def trigger_generate_certificate(request, user_id: int, course_id: int):
    """
    Trigger async task untuk generate certificate.
    Instructor/Admin bisa trigger manual.
    """
    from courses.tasks import generate_certificate
    from django.contrib.auth.models import User
    from courses.models import Course

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        raise HttpError(404, "User tidak ditemukan")

    try:
        course = Course.objects.get(pk=course_id)
    except Course.DoesNotExist:
        raise HttpError(404, "Course tidak ditemukan")

    task = generate_certificate.delay(
        user_id=user.id,
        user_name=user.get_full_name() or user.username,
        course_id=course.id,
        course_title=course.title,
    )

    return {
        "task_id": task.id,
        "status": "PENDING",
        "message": f"Certificate untuk {user.username} - {course.title} sedang diproses.",
    }


# ─── TASK STATUS ──────────────────────────────────────────

@router.get("/{task_id}/status", response=TaskStatusOut, auth=jwt_auth)
def get_task_status(request, task_id: str):
    """
    Cek status task berdasarkan task_id.
    Status: PENDING, STARTED, SUCCESS, FAILURE, RETRY.
    """
    result = AsyncResult(task_id)

    response = {
        "task_id": task_id,
        "status": result.status,
        "result": None,
    }

    if result.ready():
        if result.successful():
            response["result"] = result.result
        else:
            response["result"] = {"error": str(result.result)}

    return response

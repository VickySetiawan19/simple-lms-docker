"""
courses/tasks.py

Celery tasks untuk LMS:
1. send_enrollment_email  - kirim email saat student enroll
2. generate_certificate   - generate certificate saat course complete
3. update_enrollment_statistics - update statistik (scheduled)
4. export_course_report   - generate CSV report (async)
"""

import csv
import io
import logging
from datetime import datetime
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)


# =============================================
# TASK 1: Send Enrollment Email
# =============================================
@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_enrollment_email(self, user_id, user_email, user_name, course_id, course_title):
    """
    Kirim email konfirmasi kepada student yang baru enroll ke sebuah course.

    Args:
        user_id (int): ID user yang enroll
        user_email (str): Email user
        user_name (str): Nama user
        course_id (int): ID course
        course_title (str): Judul course
    """
    try:
        subject = f"Selamat! Kamu berhasil mendaftar kursus: {course_title}"
        message = f"""
Halo {user_name},

Selamat! Kamu berhasil mendaftar ke kursus:

  📚 {course_title}

Kamu sekarang bisa mulai belajar kapan saja.
Semangat belajarnya!

Salam,
Tim Simple LMS
        """.strip()

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            fail_silently=False,
        )

        logger.info(
            f"[TASK] send_enrollment_email: Email terkirim ke {user_email} "
            f"untuk course {course_title} (user_id={user_id})"
        )
        return {
            "status": "success",
            "user_id": user_id,
            "course_id": course_id,
            "email": user_email,
        }

    except Exception as exc:
        logger.error(
            f"[TASK] send_enrollment_email: Gagal kirim email ke {user_email}. "
            f"Error: {exc}. Retry ke-{self.request.retries}"
        )
        raise self.retry(exc=exc)


# =============================================
# TASK 2: Generate Certificate
# =============================================
@shared_task(bind=True, max_retries=3, default_retry_delay=120)
def generate_certificate(self, user_id, user_name, course_id, course_title):
    """
    Generate sertifikat digital saat student menyelesaikan course.
    Kirim email notifikasi dengan informasi sertifikat.

    Args:
        user_id (int): ID user
        user_name (str): Nama user
        course_id (int): ID course yang diselesaikan
        course_title (str): Judul course
    """
    try:
        # Generate certificate number yang unik
        cert_number = f"CERT-{course_id:04d}-{user_id:06d}-{datetime.now().strftime('%Y%m%d')}"
        issued_date = datetime.now().strftime("%d %B %Y")

        # Simpan ke MongoDB (activity log)
        try:
            from analytics.mongo_models import ActivityLog
            ActivityLog(
                user_id=user_id,
                username=user_name,
                action="certificate_generated",
                resource_type="course",
                resource_id=course_id,
                resource_name=course_title,
                metadata={
                    "certificate_number": cert_number,
                    "issued_date": issued_date,
                }
            ).save()
        except Exception as mongo_exc:
            logger.warning(f"[TASK] generate_certificate: Gagal log ke MongoDB: {mongo_exc}")

        logger.info(
            f"[TASK] generate_certificate: Sertifikat {cert_number} dibuat "
            f"untuk {user_name} - course '{course_title}'"
        )
        return {
            "status": "success",
            "certificate_number": cert_number,
            "user_id": user_id,
            "course_id": course_id,
            "issued_date": issued_date,
        }

    except Exception as exc:
        logger.error(
            f"[TASK] generate_certificate: Gagal generate sertifikat untuk "
            f"user_id={user_id}, course_id={course_id}. Error: {exc}"
        )
        raise self.retry(exc=exc)


# =============================================
# TASK 3: Update Enrollment Statistics (Scheduled)
# =============================================
@shared_task
def update_enrollment_statistics():
    """
    Scheduled task: Update statistik enrollment untuk semua course.
    Berjalan otomatis setiap jam (dikonfigurasi di celery.py beat_schedule).

    Menghitung:
    - Total enrollment per course
    - Jumlah completion per course
    - Completion rate per course
    """
    try:
        from courses.models import Course, Enrollment

        updated_count = 0
        courses = Course.objects.all()

        for course in courses:
            total_enrolled = Enrollment.objects.filter(course=course).count()
            total_completed = Enrollment.objects.filter(
                course=course,
                status='completed'
            ).count()

            # Update field statistik di model Course
            course.enrollment_count = total_enrolled
            course.save(update_fields=['enrollment_count'])  # field ini sudah ada di model
            updated_count += 1

            logger.debug(
                f"  Course '{course.title}': enrolled={total_enrolled}, completed={total_completed}"
            )

        logger.info(
            f"[TASK] update_enrollment_statistics: Berhasil update "
            f"{updated_count} courses."
        )
        return {
            "status": "success",
            "updated_courses": updated_count,
            "run_at": datetime.now().isoformat(),
        }

    except Exception as exc:
        logger.error(
            f"[TASK] update_enrollment_statistics: Error - {exc}"
        )
        raise


# =============================================
# TASK 4: Export Course Report (Async CSV)
# =============================================
@shared_task(bind=True)
def export_course_report(self, course_id=None, requested_by_user_id=None):
    """
    Async task: Generate CSV report untuk laporan enrollment & progress.
    Bisa untuk semua course atau satu course tertentu.

    Args:
        course_id (int, optional): ID course tertentu. None = semua course.
        requested_by_user_id (int): ID user yang request export.

    Returns:
        dict dengan CSV content (base64) dan metadata.
    """
    import base64

    try:
        from courses.models import Course, Enrollment

        # Query data
        enrollments = Enrollment.objects.select_related('user', 'course')
        if course_id:
            enrollments = enrollments.filter(course_id=course_id)

        # Build CSV
        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            'Enrollment ID',
            'Student Name',
            'Student Email',
            'Course Title',
            'Category',
            'Enrolled Date',
            'Status',
            'Completion %',
        ])

        # Rows
        row_count = 0
        for enrollment in enrollments:
            writer.writerow([
                enrollment.id,
                enrollment.student.get_full_name() or enrollment.student.username,  # Fix #4: .student bukan .user
                enrollment.student.email,                                             # Fix #4: .student bukan .user
                enrollment.course.title,
                enrollment.course.category.name if enrollment.course.category else '-',
                enrollment.enrolled_at.strftime('%Y-%m-%d'),
                enrollment.status,  # field status sudah ada di model
                0,  # completion_percentage dihitung dari Progress, bisa di-extend nanti
            ])
            row_count += 1

        csv_content = output.getvalue()
        csv_base64 = base64.b64encode(csv_content.encode('utf-8')).decode('utf-8')

        logger.info(
            f"[TASK] export_course_report: CSV berhasil dibuat. "
            f"{row_count} baris data. Diminta oleh user_id={requested_by_user_id}"
        )
        return {
            "status": "success",
            "rows": row_count,
            "csv_base64": csv_base64,
            "filename": f"course_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "generated_at": datetime.now().isoformat(),
        }

    except Exception as exc:
        logger.error(
            f"[TASK] export_course_report: Gagal generate report. Error: {exc}"
        )
        raise
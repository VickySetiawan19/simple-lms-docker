# Generated manually - Fix #3 & Fix #6
# Menambahkan:
#   - Course.enrollment_count  → dipakai oleh Celery task update_enrollment_statistics
#   - Enrollment.status        → dipakai oleh Celery task update_enrollment_statistics & export_course_report

# pyrefly: ignore [missing-import]
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0002_course_created_at_course_is_published_and_more'),
    ]

    operations = [
        # Fix #3: tambah enrollment_count ke Course
        migrations.AddField(
            model_name='course',
            name='enrollment_count',
            field=models.PositiveIntegerField(default=0),
        ),
        # Fix #6: tambah status ke Enrollment
        migrations.AddField(
            model_name='enrollment',
            name='status',
            field=models.CharField(
                choices=[
                    ('active', 'Active'),
                    ('completed', 'Completed'),
                    ('dropped', 'Dropped'),
                ],
                default='active',
                max_length=20,
            ),
        ),
    ]

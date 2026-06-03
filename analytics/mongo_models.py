"""
analytics/mongo_models.py

MongoDB document models menggunakan MongoEngine.
Menyimpan activity logs dan learning analytics.
"""

import mongoengine as me
from datetime import datetime


class ActivityLog(me.Document):
    """
    Activity Log collection.
    Menyimpan setiap aksi user di platform LMS.
    """
    user_id = me.IntField(required=True)
    username = me.StringField(required=True, max_length=150)
    action = me.StringField(required=True, max_length=100)
    # Contoh action: 'course_view', 'lesson_complete', 'enroll', 'login'

    resource_type = me.StringField(max_length=50)
    # Contoh: 'course', 'lesson', 'enrollment'

    resource_id = me.IntField()
    resource_name = me.StringField(max_length=255)

    metadata = me.DictField()
    # Data tambahan bebas, misal: {"duration_seconds": 120, "device": "mobile"}

    ip_address = me.StringField(max_length=45)
    user_agent = me.StringField()

    timestamp = me.DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'activity_logs',
        'indexes': [
            'user_id',
            'action',
            'timestamp',
            ('user_id', 'timestamp'),   # compound index untuk query per user
            ('action', 'timestamp'),    # compound index untuk query per action
        ],
        'ordering': ['-timestamp'],
    }

    def __str__(self):
        return f"[{self.timestamp}] {self.username} - {self.action}"


class LearningAnalytics(me.Document):
    """
    Learning Analytics collection.
    Menyimpan progress dan statistik belajar per user per course.
    """
    user_id = me.IntField(required=True)
    course_id = me.IntField(required=True)
    course_title = me.StringField(max_length=255)

    # Statistik belajar
    total_lessons = me.IntField(default=0)
    completed_lessons = me.IntField(default=0)
    completion_percentage = me.FloatField(default=0.0)

    total_study_time_seconds = me.IntField(default=0)
    last_activity = me.DateTimeField()
    first_enrolled = me.DateTimeField(default=datetime.utcnow)

    # Sesi belajar harian (list of dict)
    daily_sessions = me.ListField(me.DictField())
    # Contoh: [{"date": "2026-01-01", "duration": 3600, "lessons_done": 2}]

    is_completed = me.BooleanField(default=False)
    completed_at = me.DateTimeField()

    updated_at = me.DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'learning_analytics',
        'indexes': [
            'user_id',
            'course_id',
            ('user_id', 'course_id'),  # unique compound
        ],
    }

    def update_completion(self):
        """Hitung ulang completion percentage."""
        if self.total_lessons > 0:
            self.completion_percentage = (
                self.completed_lessons / self.total_lessons
            ) * 100
        if self.completion_percentage >= 100 and not self.is_completed:
            self.is_completed = True
            self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.save()

    def __str__(self):
        return f"User {self.user_id} - Course {self.course_id} ({self.completion_percentage:.1f}%)"
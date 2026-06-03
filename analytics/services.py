"""
analytics/services.py

Service layer untuk MongoDB aggregation queries.
Digunakan untuk menghasilkan laporan dan statistik LMS.
"""

from datetime import datetime, timedelta
from .mongo_models import ActivityLog, LearningAnalytics


class ActivityLogService:
    """Service untuk menyimpan dan membaca activity logs."""

    @staticmethod
    def log(user_id, username, action, resource_type=None,
            resource_id=None, resource_name=None,
            metadata=None, ip_address=None, user_agent=None):
        """Simpan satu activity log ke MongoDB."""
        ActivityLog(
            user_id=user_id,
            username=username,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            metadata=metadata or {},
            ip_address=ip_address,
            user_agent=user_agent,
        ).save()

    @staticmethod
    def get_user_activity(user_id, days=30, limit=50):
        """Ambil activity log user dalam N hari terakhir."""
        since = datetime.utcnow() - timedelta(days=days)
        return list(
            ActivityLog.objects(
                user_id=user_id,
                timestamp__gte=since
            ).order_by('-timestamp').limit(limit)
        )

    @staticmethod
    def get_recent_activity(limit=100):
        """Ambil activity log terbaru dari semua user."""
        return list(ActivityLog.objects().order_by('-timestamp').limit(limit))


class AnalyticsReportService:
    """Service untuk aggregation queries dan laporan."""

    @staticmethod
    def get_most_active_users(days=7, top_n=10):
        """
        Aggregation: top N user paling aktif dalam N hari terakhir.
        Menghitung jumlah action per user.
        """
        since = datetime.utcnow() - timedelta(days=days)

        pipeline = [
            {"$match": {"timestamp": {"$gte": since}}},
            {"$group": {
                "_id": "$user_id",
                "username": {"$first": "$username"},
                "total_actions": {"$sum": 1},
                "last_active": {"$max": "$timestamp"},
            }},
            {"$sort": {"total_actions": -1}},
            {"$limit": top_n},
            {"$project": {
                "_id": 0,
                "user_id": "$_id",
                "username": 1,
                "total_actions": 1,
                "last_active": 1,
            }}
        ]

        return list(ActivityLog.objects().aggregate(pipeline))

    @staticmethod
    def get_popular_courses(days=30, top_n=10):
        """
        Aggregation: top N course paling sering dilihat/diakses.
        """
        since = datetime.utcnow() - timedelta(days=days)

        pipeline = [
            {"$match": {
                "timestamp": {"$gte": since},
                "resource_type": "course",
                "action": {"$in": ["course_view", "enroll"]},
            }},
            {"$group": {
                "_id": "$resource_id",
                "course_name": {"$first": "$resource_name"},
                "total_views": {"$sum": 1},
                "unique_users": {"$addToSet": "$user_id"},
            }},
            {"$addFields": {
                "unique_user_count": {"$size": "$unique_users"}
            }},
            {"$sort": {"total_views": -1}},
            {"$limit": top_n},
            {"$project": {
                "_id": 0,
                "course_id": "$_id",
                "course_name": 1,
                "total_views": 1,
                "unique_user_count": 1,
            }}
        ]

        return list(ActivityLog.objects().aggregate(pipeline))

    @staticmethod
    def get_daily_activity_summary(days=7):
        """
        Aggregation: ringkasan aktivitas harian dalam N hari terakhir.
        """
        since = datetime.utcnow() - timedelta(days=days)

        pipeline = [
            {"$match": {"timestamp": {"$gte": since}}},
            {"$group": {
                "_id": {
                    "year": {"$year": "$timestamp"},
                    "month": {"$month": "$timestamp"},
                    "day": {"$dayOfMonth": "$timestamp"},
                },
                "total_actions": {"$sum": 1},
                "unique_users": {"$addToSet": "$user_id"},
            }},
            {"$addFields": {
                "unique_user_count": {"$size": "$unique_users"},
                "date": {
                    "$dateToString": {
                        "format": "%Y-%m-%d",
                        "date": {
                            "$dateFromParts": {
                                "year": "$_id.year",
                                "month": "$_id.month",
                                "day": "$_id.day",
                            }
                        }
                    }
                }
            }},
            {"$sort": {"date": 1}},
            {"$project": {
                "_id": 0,
                "date": 1,
                "total_actions": 1,
                "unique_user_count": 1,
            }}
        ]

        return list(ActivityLog.objects().aggregate(pipeline))

    @staticmethod
    def get_enrollment_completion_report():
        """
        Aggregation: laporan tingkat penyelesaian kursus.
        """
        pipeline = [
            {"$group": {
                "_id": "$course_id",
                "course_title": {"$first": "$course_title"},
                "total_enrolled": {"$sum": 1},
                "completed": {
                    "$sum": {"$cond": ["$is_completed", 1, 0]}
                },
                "avg_completion": {"$avg": "$completion_percentage"},
            }},
            {"$addFields": {
                "completion_rate": {
                    "$multiply": [
                        {"$divide": ["$completed", "$total_enrolled"]},
                        100
                    ]
                }
            }},
            {"$sort": {"completion_rate": -1}},
            {"$project": {
                "_id": 0,
                "course_id": "$_id",
                "course_title": 1,
                "total_enrolled": 1,
                "completed": 1,
                "avg_completion": {"$round": ["$avg_completion", 1]},
                "completion_rate": {"$round": ["$completion_rate", 1]},
            }}
        ]

        return list(LearningAnalytics.objects().aggregate(pipeline))
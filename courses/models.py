from django.db import models
from django.contrib.auth.models import User


class CourseManager(models.Manager):
    def for_listing(self):
        return self.select_related('instructor', 'category')


class UserProfile(models.Model):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('instructor', 'Instructor'),
        ('student', 'Student'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    bio = models.TextField(blank=True, default='')  # ← baru


class Category(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey('self', on_delete=models.CASCADE,
                               null=True, blank=True, related_name='subcategories')


class Course(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    instructor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courses')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    enrollment_count = models.PositiveIntegerField(default=0)  # ← Fix #3: diupdate oleh Celery task
    objects = CourseManager()


class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=255)
    content = models.TextField(blank=True, default='')      # ← baru
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)    # ← baru

    class Meta:
        ordering = ['order']


class Enrollment(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('dropped', 'Dropped'),
    ]
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(  # ← Fix #6: diperlukan oleh Celery task statistics
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
    )

    class Meta:
        unique_together = ('student', 'course')


class Progress(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='progress')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='progress')
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)  # ← baru

    class Meta:
        unique_together = ('student', 'lesson')
from django.db import models
from django.contrib.auth.models import User

# --- Custom Manager untuk Optimasi ---
class CourseManager(models.Manager):
    def for_listing(self):
        # Menggunakan select_related agar data instructor & category terambil dalam 1 query (Optimasi N+1)
        return self.select_related('instructor', 'category')

# --- Data Models ---
class UserProfile(models.Model):
    ROLE_CHOICES = (('admin', 'Admin'), ('instructor', 'Instructor'), ('student', 'Student'))
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')

class Category(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')

class Course(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    instructor = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    objects = CourseManager()

class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0)
    class Meta:
        ordering = ['order']

class Enrollment(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    class Meta:
        unique_together = ('student', 'course')

class Progress(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False)
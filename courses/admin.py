from django.contrib import admin
from .models import UserProfile, Category, Course, Lesson, Enrollment

class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'instructor', 'category')
    inlines = [LessonInline]

admin.site.register(UserProfile)
admin.site.register(Category)
admin.site.register(Enrollment)
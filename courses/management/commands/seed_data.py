"""
Management command untuk membuat demo/seed data.
Idempotent: bisa dijalankan berulang tanpa duplikasi.

Usage:
    docker-compose exec web python manage.py seed_data
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from courses.models import UserProfile, Category, Course, Lesson, Enrollment, Progress
from django.utils import timezone


class Command(BaseCommand):
    help = 'Seed database dengan data demo untuk testing'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('\n🌱 Memulai seed data...\n'))

        # ─── 1. AKUN DEMO ──────────────────────────────────
        demo_users = [
            {
                'username': 'admin',
                'email': 'admin@lms.test',
                'password': 'admin123',
                'first_name': 'Admin',
                'last_name': 'LMS',
                'role': 'admin',
                'is_staff': True,
                'is_superuser': True,
            },
            {
                'username': 'instructor1',
                'email': 'instructor1@lms.test',
                'password': 'instructor123',
                'first_name': 'Budi',
                'last_name': 'Santoso',
                'role': 'instructor',
            },
            {
                'username': 'instructor2',
                'email': 'instructor2@lms.test',
                'password': 'instructor123',
                'first_name': 'Siti',
                'last_name': 'Rahayu',
                'role': 'instructor',
            },
            {
                'username': 'student1',
                'email': 'student1@lms.test',
                'password': 'student123',
                'first_name': 'Andi',
                'last_name': 'Pratama',
                'role': 'student',
            },
            {
                'username': 'student2',
                'email': 'student2@lms.test',
                'password': 'student123',
                'first_name': 'Dewi',
                'last_name': 'Lestari',
                'role': 'student',
            },
        ]

        created_users = {}
        for u_data in demo_users:
            user, created = User.objects.get_or_create(
                username=u_data['username'],
                defaults={
                    'email': u_data['email'],
                    'first_name': u_data['first_name'],
                    'last_name': u_data['last_name'],
                    'is_staff': u_data.get('is_staff', False),
                    'is_superuser': u_data.get('is_superuser', False),
                }
            )
            if created:
                user.set_password(u_data['password'])
                user.save()
                self.stdout.write(self.style.SUCCESS(
                    f"  ✅ User '{user.username}' (role: {u_data['role']}) dibuat"
                ))
            else:
                self.stdout.write(f"  ⏭️  User '{user.username}' sudah ada, skip")

            # Selalu pastikan UserProfile ada (fix: profile juga dibuat untuk user yang sudah ada)
            UserProfile.objects.get_or_create(
                user=user, defaults={'role': u_data['role']}
            )
            created_users[u_data['username']] = user

        # ─── 2. CATEGORIES ─────────────────────────────────
        category_names = [
            'Programming',
            'Data Science',
            'Web Development',
            'Mobile Development',
            'DevOps',
        ]

        created_categories = {}
        for name in category_names:
            cat, created = Category.objects.get_or_create(name=name)
            created_categories[name] = cat
            if created:
                self.stdout.write(self.style.SUCCESS(f"  ✅ Category '{name}' dibuat"))

        # ─── 3. COURSES ────────────────────────────────────
        courses_data = [
            {
                'title': 'Python Fundamentals',
                'description': 'Belajar dasar-dasar Python dari nol. Cocok untuk pemula yang ingin memulai karir di bidang programming.',
                'instructor': 'instructor1',
                'category': 'Programming',
                'lessons': [
                    ('Pengenalan Python', 'Python adalah bahasa pemrograman yang populer dan mudah dipelajari.', 1),
                    ('Variabel dan Tipe Data', 'Memahami variabel, string, integer, float, dan boolean.', 2),
                    ('Kontrol Alur (If/Else)', 'Penggunaan conditional statement dalam Python.', 3),
                    ('Perulangan (For/While)', 'Memahami loop dan iterasi dalam Python.', 4),
                    ('Fungsi', 'Membuat dan menggunakan fungsi di Python.', 5),
                ],
            },
            {
                'title': 'Django Web Development',
                'description': 'Membangun web application menggunakan Django framework. Dari setup project hingga deployment.',
                'instructor': 'instructor1',
                'category': 'Web Development',
                'lessons': [
                    ('Setup Project Django', 'Instalasi Django dan membuat project pertama.', 1),
                    ('Models dan Database', 'Membuat model dan menjalankan migration.', 2),
                    ('Views dan URLs', 'Routing dan membuat views di Django.', 3),
                    ('Django REST API', 'Membuat REST API menggunakan Django Ninja.', 4),
                ],
            },
            {
                'title': 'Data Science dengan Python',
                'description': 'Analisis data dan machine learning menggunakan Python, Pandas, dan Scikit-learn.',
                'instructor': 'instructor2',
                'category': 'Data Science',
                'lessons': [
                    ('Pengenalan Data Science', 'Apa itu Data Science dan mengapa penting.', 1),
                    ('Pandas DataFrame', 'Manipulasi data menggunakan Pandas.', 2),
                    ('Visualisasi Data', 'Membuat grafik dengan Matplotlib dan Seaborn.', 3),
                ],
            },
            {
                'title': 'Docker & Containerization',
                'description': 'Memahami Docker, container, dan cara deploy aplikasi modern menggunakan Docker Compose.',
                'instructor': 'instructor2',
                'category': 'DevOps',
                'lessons': [
                    ('Apa itu Docker?', 'Konsep container dan perbedaan dengan VM.', 1),
                    ('Dockerfile', 'Membuat Dockerfile untuk aplikasi Python.', 2),
                    ('Docker Compose', 'Menjalankan multi-container dengan Docker Compose.', 3),
                ],
            },
            {
                'title': 'React Native Mobile App',
                'description': 'Belajar membuat aplikasi mobile cross-platform menggunakan React Native.',
                'instructor': 'instructor1',
                'category': 'Mobile Development',
                'lessons': [
                    ('Setup React Native', 'Instalasi dan konfigurasi environment.', 1),
                    ('Komponen Dasar', 'View, Text, Image, dan styling.', 2),
                    ('Navigasi', 'Implementasi navigasi antar screen.', 3),
                ],
            },
        ]

        created_courses = {}
        for c_data in courses_data:
            course, created = Course.objects.get_or_create(
                title=c_data['title'],
                defaults={
                    'description': c_data['description'],
                    'instructor': created_users[c_data['instructor']],
                    'category': created_categories[c_data['category']],
                    'is_published': True,
                }
            )
            created_courses[c_data['title']] = course

            if created:
                self.stdout.write(self.style.SUCCESS(f"  ✅ Course '{course.title}' dibuat"))
                for lesson_title, lesson_content, lesson_order in c_data['lessons']:
                    Lesson.objects.get_or_create(
                        course=course,
                        title=lesson_title,
                        defaults={
                            'content': lesson_content,
                            'order': lesson_order,
                        }
                    )
            else:
                self.stdout.write(f"  ⏭️  Course '{course.title}' sudah ada, skip")

        # ─── 4. ENROLLMENTS ────────────────────────────────
        enrollments_data = [
            ('student1', 'Python Fundamentals'),
            ('student1', 'Django Web Development'),
            ('student1', 'Docker & Containerization'),
            ('student2', 'Python Fundamentals'),
            ('student2', 'Data Science dengan Python'),
        ]

        for student_name, course_title in enrollments_data:
            student = created_users[student_name]
            course = created_courses[course_title]
            enrollment, created = Enrollment.objects.get_or_create(
                student=student,
                course=course,
                defaults={'status': 'active'}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(
                    f"  ✅ Enrollment: {student_name} → {course_title}"
                ))

        # ─── 5. PROGRESS ───────────────────────────────────
        # student1 sudah selesaikan semua lesson Python Fundamentals
        python_course = created_courses['Python Fundamentals']
        student1 = created_users['student1']
        for lesson in Lesson.objects.filter(course=python_course):
            progress, created = Progress.objects.get_or_create(
                student=student1,
                lesson=lesson,
                defaults={
                    'is_completed': True,
                    'completed_at': timezone.now(),
                }
            )

        # student1 selesaikan 2 lesson pertama Django
        django_course = created_courses['Django Web Development']
        django_lessons = Lesson.objects.filter(course=django_course).order_by('order')[:2]
        for lesson in django_lessons:
            Progress.objects.get_or_create(
                student=student1,
                lesson=lesson,
                defaults={
                    'is_completed': True,
                    'completed_at': timezone.now(),
                }
            )

        # ─── SUMMARY ──────────────────────────────────────
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 50))
        self.stdout.write(self.style.SUCCESS('🎉 Seed data selesai!'))
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write('\n📋 Akun Demo:')
        self.stdout.write('  ┌──────────────┬────────────────┬──────────────┐')
        self.stdout.write('  │ Username     │ Password       │ Role         │')
        self.stdout.write('  ├──────────────┼────────────────┼──────────────┤')
        self.stdout.write('  │ admin        │ admin123       │ admin        │')
        self.stdout.write('  │ instructor1  │ instructor123  │ instructor   │')
        self.stdout.write('  │ instructor2  │ instructor123  │ instructor   │')
        self.stdout.write('  │ student1     │ student123     │ student      │')
        self.stdout.write('  │ student2     │ student123     │ student      │')
        self.stdout.write('  └──────────────┴────────────────┴──────────────┘')
        self.stdout.write(f'\n📊 Data: {Category.objects.count()} categories, '
                         f'{Course.objects.count()} courses, '
                         f'{Lesson.objects.count()} lessons, '
                         f'{Enrollment.objects.count()} enrollments, '
                         f'{Progress.objects.count()} progress records\n')

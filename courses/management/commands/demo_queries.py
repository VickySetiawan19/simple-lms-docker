from django.core.management.base import BaseCommand
from django.db import connection, reset_queries
from courses.models import Course

class Command(BaseCommand):
    help = 'Demonstrasi N+1 Problem vs Optimized Query'

    def handle(self, *args, **kwargs):
        # --- SKENARIO 1: N+1 Problem (Tanpa Optimasi) ---
        self.stdout.write(self.style.WARNING('\n--- MENJALANKAN QUERY TANPA OPTIMASI (N+1 PROBLEM) ---'))
        reset_queries() # Mulai hitung query dari 0
        
        # Ambil semua course (hanya query ke tabel Course)
        courses_bad = Course.objects.all()
        for course in courses_bad:
            # Karena instructor dan category tidak di-load di awal, 
            # Django akan melakukan query baru ke database setiap kali loop berputar!
            print(f"Course: {course.title} | Instructor: {course.instructor.username} | Category: {course.category.name if course.category else 'None'}")
        
        bad_query_count = len(connection.queries)
        self.stdout.write(self.style.ERROR(f"Total Database Queries dieksekusi: {bad_query_count}\n"))

        # --- SKENARIO 2: Optimized Query (Solusi) ---
        self.stdout.write(self.style.SUCCESS('--- MENJALANKAN QUERY DENGAN OPTIMASI (select_related) ---'))
        reset_queries() # Reset hitungan query
        
        # Menggunakan custom manager for_listing() yang ada select_related-nya
        courses_good = Course.objects.for_listing()
        for course in courses_good:
            # Data instructor dan category sudah ditarik sekaligus di awal (JOIN SQL), 
            # jadi tidak memicu query tambahan di dalam loop.
            print(f"Course: {course.title} | Instructor: {course.instructor.username} | Category: {course.category.name if course.category else 'None'}")
        
        good_query_count = len(connection.queries)
        self.stdout.write(self.style.SUCCESS(f"Total Database Queries dieksekusi: {good_query_count}\n"))
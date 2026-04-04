# Simple LMS

Project ini adalah inisialisasi environment development untuk aplikasi Simple LMS menggunakan Django dan PostgreSQL yang dijalankan di dalam container Docker.

## Cara Menjalankan Project

Ikuti langkah-langkah berikut untuk menjalankan project ini di komputer lokal Anda:

1. **Clone Repository**
   Buka terminal dan clone repository ini ke komputer Anda:
   ```bash
   git clone https://github.com/VickySetiawan19/simple-lms-docker.git
   cd simple-lms

-dokumentasi
![Screenshot Django Welcome Page](images/screenshot_welcome.png)

## Tugas: Django ORM & Query Optimization

Project ini telah mengimplementasikan Data Models untuk LMS (User, Category, Course, Lesson, Enrollment, Progress) beserta relasi ForeignKey dan OneToOneField. 

**Bukti Optimasi Query (N+1 Problem Solved):**
Membuat custom manager `Course.objects.for_listing()` menggunakan `select_related`. Berikut adalah perbandingan performa query ke database sebelum dan sesudah optimasi:

![Screenshot Optimasi Query](images/screenshot_optimasi.png)
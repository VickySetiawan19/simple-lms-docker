# FINAL PROJECT REPORT

## Identitas

- **Nama:** Vicky Setiawan
- **NIM:** *(isi NIM)*
- **Kelas:** *(isi Kelas)*
- **URL Repository:** [github.com/VickySetiawan19/simple-lms-docker](https://github.com/VickySetiawan19/simple-lms-docker)

---

## Deskripsi Project

Project ini adalah **Simple Learning Management System (LMS)** yang dikembangkan sebagai tugas final project mata kuliah Pemrograman Sisi Server. LMS ini menyediakan REST API untuk manajemen course, lesson, enrollment, dan progress belajar menggunakan Django + Django Ninja.

Project menggunakan arsitektur microservices dengan:
- **Django** sebagai backend utama
- **PostgreSQL** sebagai database relasional
- **Redis** untuk caching
- **MongoDB** untuk activity logging dan analytics
- **Celery + RabbitMQ** untuk background task processing
- **Flower** untuk monitoring task

Semua service dijalankan menggunakan **Docker Compose**.

---

## Fitur Dasar yang Sudah Berjalan

| No | Fitur | Status |
|----|-------|--------|
| 1 | Docker Compose (semua service) | ✅ Berjalan |
| 2 | Database PostgreSQL + migration | ✅ Berjalan |
| 3 | JWT Authentication (login/register/refresh) | ✅ Berjalan |
| 4 | Role-based access control (admin/instructor/student) | ✅ Berjalan |
| 5 | Endpoint course CRUD | ✅ Berjalan |
| 6 | Endpoint lesson CRUD | ✅ Berjalan |
| 7 | Endpoint enrollment | ✅ Berjalan |
| 8 | Endpoint progress | ✅ Berjalan |
| 9 | README lengkap | ✅ Berjalan |
| 10 | Swagger/OpenAPI | ✅ Berjalan |
| 11 | Struktur project rapi | ✅ Berjalan |
| 12 | Seed data / akun demo | ✅ Berjalan |

---

## Fitur Tambahan yang Dipilih

**Paket 6 — Async Processing & Notification**

| No | Fitur | Kategori | Poin | Status |
|----|-------|----------|------|--------|
| 1 | Email notification async | F. Celery | 12 | ✅ Selesai |
| 2 | Generate certificate/report async | F. Celery | 18 | ✅ Selesai |
| 3 | Scheduled task (Celery Beat) | F. Celery | 15 | ✅ Selesai |
| 4 | Task status endpoint | F. Celery | 12 | ✅ Selesai |
| 5 | Flower monitoring | F. Celery | 8 | ✅ Selesai |
| | **Total** | | **65** | **(maks dihitung 50)** |

---

## Penjelasan Implementasi Fitur Tambahan

### 1. Email Notification Async (12 Poin)

**File:** `courses/tasks.py` → `send_enrollment_email`
**Integrasi:** `courses/api/enrollment_endpoints.py` → endpoint `enroll_course`

Saat student berhasil enroll ke sebuah course, sistem otomatis mengirim email konfirmasi melalui Celery worker. Email dikirim secara **asynchronous** menggunakan `.delay()` sehingga response API tetap cepat.

```python
send_enrollment_email.delay(
    user_id=user.id,
    user_email=user.email,
    user_name=user.get_full_name(),
    course_id=course.id,
    course_title=course.title,
)
```

Task dilengkapi dengan:
- **Auto-retry** hingga 3 kali jika gagal (`max_retries=3`)
- **Retry delay** 60 detik antar percobaan
- **Logging** untuk tracking keberhasilan/kegagalan

### 2. Generate Certificate/Report Async (18 Poin)

**File:** `courses/tasks.py` → `generate_certificate`, `export_course_report`

**Certificate otomatis:**
Saat student menandai lesson terakhir sebagai selesai (semua lesson completed), sistem:
1. Update status enrollment menjadi `completed`
2. Trigger `generate_certificate.delay()` untuk membuat sertifikat
3. Sertifikat memiliki nomor unik: `CERT-{course_id}-{user_id}-{date}`
4. Log sertifikat disimpan ke MongoDB (ActivityLog)

**Export Report:**
Admin dapat trigger export CSV laporan enrollment melalui:
```
POST /api/tasks/export-report?course_id=1
```
Report diproses secara async dan hasilnya bisa diambil melalui task status endpoint.

### 3. Scheduled Tasks — Celery Beat (15 Poin)

**File:** `config/celery.py` → `app.conf.beat_schedule`

Tiga scheduled tasks dikonfigurasi:

| Task | Jadwal | Fungsi |
|------|--------|--------|
| `update_enrollment_statistics` | Setiap jam | Hitung ulang `enrollment_count` per course |
| `cleanup_expired_data` | Setiap hari 02:00 | Hapus expired sessions dari database |
| `sync_learning_analytics` | Setiap 6 jam | Sync progress dari PostgreSQL ke MongoDB |

Task `sync_learning_analytics` mengambil data enrollment + progress dari PostgreSQL, menghitung completion percentage, lalu menyimpan/mengupdate document di MongoDB collection `learning_analytics`.

### 4. Task Status Endpoint (12 Poin)

**File:** `courses/api/task_endpoints.py`

Endpoint untuk mengecek status background task:
```
GET /api/tasks/{task_id}/status
```

Response:
```json
{
    "task_id": "e9f3c4a2-...",
    "status": "SUCCESS",
    "result": {
        "rows": 25,
        "csv_base64": "...",
        "filename": "course_report_20260630_120000.csv"
    }
}
```

Menggunakan `celery.result.AsyncResult` untuk membaca status task dari Redis result backend.

### 5. Flower Monitoring (8 Poin)

**File:** `docker-compose.yml` → service `flower`

Flower berjalan sebagai service Docker terpisah pada port `5555`. Menyediakan:
- Dashboard real-time worker dan task
- List semua task yang pernah dieksekusi
- Detail per task: arguments, result, duration, retries
- Grafik throughput dan latency

Akses: `http://localhost:5555`

---

## Cara Menjalankan Project

```bash
# 1. Clone repository
git clone https://github.com/VickySetiawan19/simple-lms-docker.git
cd simple-lms

# 2. Copy environment variables
cp .env.example .env

# 3. Build dan jalankan semua services
docker-compose build
docker-compose up -d

# 4. Jalankan migrasi database
docker-compose exec web python manage.py migrate

# 5. Load demo data
docker-compose exec web python manage.py seed_data
```

### Verifikasi Semua Service Berjalan

```bash
docker-compose ps
```

Harus menampilkan 7 service running: `db`, `redis`, `mongodb`, `rabbitmq`, `web`, `celery-worker`, `celery-beat`, `flower`.

---

## Akun Demo

| Username | Password | Role |
|----------|----------|------|
| `admin` | `admin123` | Admin |
| `instructor1` | `instructor123` | Instructor |
| `instructor2` | `instructor123` | Instructor |
| `student1` | `student123` | Student |
| `student2` | `student123` | Student |

---

## Endpoint Penting

| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| POST | `/api/auth/login` | Login |
| POST | `/api/auth/register` | Register |
| GET | `/api/courses` | List courses |
| GET | `/api/courses/{id}` | Detail course |
| POST | `/api/enrollments` | Enroll (trigger email) |
| POST | `/api/enrollments/{id}/progress` | Mark progress (trigger certificate) |
| POST | `/api/tasks/export-report` | Trigger async export |
| GET | `/api/tasks/{task_id}/status` | Cek status task |

Dokumentasi lengkap: `http://localhost:8000/api/docs`

---

## Screenshot / Bukti Pengujian

### Swagger UI
Akses `http://localhost:8000/api/docs` untuk melihat semua endpoint yang tersedia.

### Flower Dashboard
Akses `http://localhost:5555` untuk melihat monitoring Celery tasks.

### RabbitMQ Management
Akses `http://localhost:15672` (guest/guest) untuk melihat message queue.

---

## Kendala dan Solusi

| No | Kendala | Solusi |
|----|---------|--------|
| 1 | MongoDB connection timeout saat pertama kali start | Menambahkan `healthcheck` di docker-compose untuk memastikan MongoDB ready sebelum Django start |
| 2 | Celery task gagal karena Django belum ready | Menggunakan `depends_on` dengan `condition: service_healthy` |
| 3 | Email gagal terkirim di environment development | Menggunakan `try/except` agar enrollment tetap berhasil meskipun email gagal. Email bisa dikonfigurasi via .env |
| 4 | N+1 query problem pada endpoint list course | Menggunakan `select_related` dan `prefetch_related` untuk mengurangi jumlah query |

---

## Kesimpulan

Final project ini memberikan pengalaman yang komprehensif dalam mengembangkan backend yang mendekati production. Beberapa pelajaran penting yang didapat:

1. **Async Processing**: Menggunakan Celery + RabbitMQ untuk memproses task berat di background sangat meningkatkan responsivitas API. User tidak perlu menunggu email terkirim atau report di-generate.

2. **Docker Compose**: Mengelola banyak service (Django, PostgreSQL, Redis, MongoDB, RabbitMQ, Celery Worker, Celery Beat, Flower) dalam satu `docker-compose.yml` membuat deployment menjadi konsisten dan reproducible.

3. **Monitoring**: Flower memberikan visibility yang sangat berguna untuk debugging dan memantau performa background tasks.

4. **Design Pattern**: Memisahkan logic ke service layer (`cache/services.py`, `analytics/services.py`) dan menggunakan Celery tasks untuk operasi berat membuat kode lebih terstruktur dan maintainable.

5. **Error Handling**: Penting untuk menangani kegagalan external service (email, MongoDB) dengan graceful agar tidak menggagalkan operasi utama.

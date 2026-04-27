from ninja import NinjaAPI
from courses.api.auth import jwt_auth
from courses.api.auth_endpoints import router as auth_router
from courses.api.course_endpoints import router as course_router
from courses.api.enrollment_endpoints import router as enrollment_router

api = NinjaAPI(
    title="Simple LMS API",
    version="1.0.0",
    description=(
        "REST API untuk Simple Learning Management System. "
        "Dibuat dengan Django Ninja + JWT Authentication + RBAC.\n\n"
        "**Roles:** `student` | `instructor` | `admin`\n\n"
        "**Cara pakai:** Login dulu di `/api/auth/login`, "
        "copy token `access`, lalu klik tombol **Authorize** "
        "dan masukkan `Bearer <token>`"
    ),
    auth=jwt_auth,
    docs_url="/docs",
)

api.add_router("/auth", auth_router)
api.add_router("/courses", course_router)
api.add_router("/enrollments", enrollment_router)
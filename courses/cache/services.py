"""
courses/cache/services.py

Redis caching service untuk LMS.
Menangani caching course list, course detail, dan cache invalidation.
"""

import json
import logging
from django.core.cache import cache

logger = logging.getLogger(__name__)

# =============================================
# CACHE KEY CONSTANTS
# =============================================
CACHE_KEY_COURSE_LIST = "courses:list:page:{page}:size:{size}"
CACHE_KEY_COURSE_DETAIL = "courses:detail:{course_id}"
CACHE_KEY_COURSE_ALL_KEYS = "courses:all_keys"

CACHE_TTL_COURSE_LIST = 300    # 5 menit
CACHE_TTL_COURSE_DETAIL = 600  # 10 menit


class CourseCacheService:
    """
    Service untuk caching operasi Course.
    Menggunakan Redis via django-redis.
    """

    # ------------------------------------------
    # Course List Caching
    # ------------------------------------------
    @staticmethod
    def get_course_list(page: int = 1, size: int = 10):
        """
        Ambil course list dari cache.
        Return None jika cache miss.
        """
        key = CACHE_KEY_COURSE_LIST.format(page=page, size=size)
        cached = cache.get(key)
        if cached is not None:
            logger.debug(f"[CACHE HIT] course_list page={page}")
            return cached
        logger.debug(f"[CACHE MISS] course_list page={page}")
        return None

    @staticmethod
    def set_course_list(data, page: int = 1, size: int = 10):
        """
        Simpan course list ke cache.
        """
        key = CACHE_KEY_COURSE_LIST.format(page=page, size=size)
        cache.set(key, data, timeout=CACHE_TTL_COURSE_LIST)
        logger.debug(f"[CACHE SET] course_list page={page}")

    # ------------------------------------------
    # Course Detail Caching
    # ------------------------------------------
    @staticmethod
    def get_course_detail(course_id: int):
        """
        Ambil detail course dari cache.
        Return None jika cache miss.
        """
        key = CACHE_KEY_COURSE_DETAIL.format(course_id=course_id)
        cached = cache.get(key)
        if cached is not None:
            logger.debug(f"[CACHE HIT] course_detail id={course_id}")
            return cached
        logger.debug(f"[CACHE MISS] course_detail id={course_id}")
        return None

    @staticmethod
    def set_course_detail(course_id: int, data):
        """
        Simpan detail course ke cache.
        """
        key = CACHE_KEY_COURSE_DETAIL.format(course_id=course_id)
        cache.set(key, data, timeout=CACHE_TTL_COURSE_DETAIL)
        logger.debug(f"[CACHE SET] course_detail id={course_id}")

    # ------------------------------------------
    # Cache Invalidation Strategy
    # ------------------------------------------
    @staticmethod
    def invalidate_course(course_id: int):
        """
        Invalidate cache untuk satu course (detail + semua list pages).
        Dipanggil saat course diupdate atau dihapus.
        """
        # Hapus detail cache
        detail_key = CACHE_KEY_COURSE_DETAIL.format(course_id=course_id)
        cache.delete(detail_key)
        logger.info(f"[CACHE INVALIDATE] course_detail id={course_id}")

        # Hapus semua list cache (karena list bisa berubah)
        CourseCacheService.invalidate_all_lists()

    @staticmethod
    def invalidate_all_lists():
        """
        Invalidate semua cache course list.
        Menggunakan pattern delete dengan prefix 'lms:courses:list:*'.
        """
        # django-redis mendukung delete_pattern
        try:
            from django_redis import get_redis_connection
            redis_conn = get_redis_connection("default")
            # Key prefix "lms" sudah ditambahkan oleh Django cache framework
            pattern = "lms:courses:list:*"
            keys = redis_conn.keys(pattern)
            if keys:
                redis_conn.delete(*keys)
                logger.info(
                    f"[CACHE INVALIDATE] Dihapus {len(keys)} list cache keys"
                )
        except Exception as e:
            logger.warning(f"[CACHE INVALIDATE] Gagal pattern delete: {e}")
            # Fallback: hapus beberapa halaman pertama secara manual
            for page in range(1, 11):
                for size in [10, 20, 50]:
                    key = CACHE_KEY_COURSE_LIST.format(page=page, size=size)
                    cache.delete(key)

    @staticmethod
    def invalidate_all():
        """Hapus seluruh cache LMS (gunakan dengan hati-hati)."""
        cache.clear()
        logger.warning("[CACHE INVALIDATE] Seluruh cache dihapus!")
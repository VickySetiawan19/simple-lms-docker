"""
weather_api.py — Redis Caching Exercise
Modifikasi fungsi get_weather() dengan Redis caching.
"""

# pyrefly: ignore [missing-import]
import redis
import time
import json


# ─── Koneksi ke Redis ────────────────────────────────────────────────────────
r = redis.Redis(
    host='localhost',
    port=6379,
    db=0,
    decode_responses=True,  # agar hasil GET langsung string, bukan bytes
)

CACHE_TTL = 300  # 5 menit dalam detik


def _simulate_api_call(city: str) -> dict:
    """
    Simulasi API call yang lambat ke endpoint cuaca.
    (api.example.com tidak real, jadi data kita buat sendiri)
    """
    time.sleep(2)  # Simulate slow API (2 detik)

    # Data cuaca simulasi berdasarkan nama kota
    weather_data = {
        "Jakarta":   {"temperature": 32, "humidity": 85, "condition": "Partly Cloudy"},
        "Surabaya":  {"temperature": 34, "humidity": 78, "condition": "Sunny"},
        "Bandung":   {"temperature": 24, "humidity": 90, "condition": "Rainy"},
        "Bali":      {"temperature": 30, "humidity": 80, "condition": "Clear"},
    }
    default = {"temperature": 28, "humidity": 75, "condition": "Unknown"}
    data = weather_data.get(city, default)

    return {
        "city": city,
        **data,
        "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }


def get_weather(city: str) -> dict:
    """
    Ambil data cuaca dengan Redis caching.

    Alur:
      1. Cek apakah data ada di Redis cache.
      2. Kalau ADA  → return dari cache (cepat).
      3. Kalau TIDAK → panggil API, simpan ke cache, return data.

    Cache TTL: 300 detik (5 menit).

    Redis commands yang digunakan:
      - GET  : mengambil data dari cache
      - SETEX: menyimpan data + set expiry sekaligus (SET + EXPIRE)
    """
    cache_key = f"weather:{city.lower()}"

    # ── STEP 1: Cek cache ────────────────────────────────────────────────────
    cached_data = r.get(cache_key)          # Redis: GET weather:jakarta

    if cached_data:
        # ── CACHE HIT ────────────────────────────────────────────────────────
        remaining_ttl = r.ttl(cache_key)    # Redis: TTL weather:jakarta
        print(f"  [CACHE HIT]  Key '{cache_key}' ditemukan. "
              f"Sisa TTL: {remaining_ttl} detik")
        return json.loads(cached_data)

    # ── CACHE MISS: panggil API ──────────────────────────────────────────────
    print(f"  [CACHE MISS] Key '{cache_key}' tidak ada. Memanggil API...")
    data = _simulate_api_call(city)

    # ── STEP 2: Simpan ke cache dengan expiry ────────────────────────────────
    r.setex(                                # Redis: SETEX weather:jakarta 300 <json>
        name=cache_key,
        time=CACHE_TTL,
        value=json.dumps(data),
    )
    print(f"  [CACHE SET]  Data disimpan ke Redis. "
          f"Key: '{cache_key}', TTL: {CACHE_TTL}s")

    return data

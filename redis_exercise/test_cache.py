"""
test_cache.py — Testing Script Redis Caching Exercise

Menguji perbedaan response time antara:
  - First call  : data tidak ada di cache → lambat (~2 detik)
  - Second call : data ada di cache       → cepat  (< 0.05 detik)
"""

import time
from weather_api import get_weather, r


def divider(title=""):
    print("\n" + "=" * 55)
    if title:
        print(f"  {title}")
        print("=" * 55)


def run_test():
    divider("REDIS CACHING - WEATHER API TEST")

    city = "Jakarta"

    # ─────────────────────────────────────────────────────────────
    # Pastikan cache bersih sebelum test (opsional, untuk repro)
    # ─────────────────────────────────────────────────────────────
    cache_key = f"weather:{city.lower()}"
    r.delete(cache_key)
    print(f"\n[SETUP] Cache untuk '{city}' dihapus sebelum test.\n")

    # ─────────────────────────────────────────────────────────────
    # CALL 1 — Cache MISS, harus lambat (~2 detik)
    # ─────────────────────────────────────────────────────────────
    divider("CALL #1 — First call (Cache MISS)")
    start = time.time()
    result1 = get_weather(city)
    time1 = time.time() - start

    print(f"\n  Data     : {result1}")
    print(f"  Waktu  : {time1:.3f} detik  <- lambat (hit API)")

    # ─────────────────────────────────────────────────────────────
    # CALL 2 — Cache HIT, harus cepat (< 0.1 detik)
    # ─────────────────────────────────────────────────────────────
    divider("CALL #2 — Second call (Cache HIT)")
    start = time.time()
    result2 = get_weather(city)
    time2 = time.time() - start

    print(f"\n  Data     : {result2}")
    print(f"  Waktu  : {time2:.4f} detik  <- cepat (dari cache)")

    # ─────────────────────────────────────────────────────────────
    # CALL 3 — Kota berbeda, cache MISS lagi
    # ─────────────────────────────────────────────────────────────
    divider("CALL #3 — Kota berbeda: Bandung (Cache MISS)")
    start = time.time()
    result3 = get_weather("Bandung")
    time3 = time.time() - start

    print(f"\n  Data     : {result3}")
    print(f"  Waktu  : {time3:.3f} detik  <- lambat (beda kota)")

    # ─────────────────────────────────────────────────────────────
    # CALL 4 — Bandung lagi, sekarang cache HIT
    # ─────────────────────────────────────────────────────────────
    divider("CALL #4 — Bandung lagi (Cache HIT)")
    start = time.time()
    result4 = get_weather("Bandung")
    time4 = time.time() - start

    print(f"\n  Data     : {result4}")
    print(f"  Waktu  : {time4:.4f} detik  <- cepat (dari cache)")

    # ─────────────────────────────────────────────────────────────
    # SUMMARY
    # ─────────────────────────────────────────────────────────────
    divider("SUMMARY")
    speedup = time1 / time2 if time2 > 0 else float('inf')
    print(f"""
  Kota       | Call    | Waktu       | Status
  -----------+---------+-------------+------------
  Jakarta    | #1      | {time1:>8.3f}s  | CACHE MISS
  Jakarta    | #2      | {time2:>8.4f}s  | CACHE HIT [OK]
  Bandung    | #3      | {time3:>8.3f}s  | CACHE MISS
  Bandung    | #4      | {time4:>8.4f}s  | CACHE HIT [OK]

  Speedup  : {speedup:.0f}x lebih cepat dengan cache!

  Catatan (Call #5 setelah 5 menit):
  Jika dibiarkan 5 menit (300 detik), key akan expired
  otomatis oleh Redis. Call berikutnya akan CACHE MISS lagi
  dan membutuhkan waktu ~2 detik (hit API kembali).
""")
    divider()


if __name__ == "__main__":
    # Pastikan Redis berjalan sebelum menjalankan test!
    # Jalankan Redis dengan Docker: docker run -p 6379:6379 redis:7-alpine
    # Atau gunakan Redis yang sudah ada di docker-compose.yml project ini.

    try:
        r.ping()
        print("[OK] Redis terkoneksi!")
        run_test()
    except Exception as e:
        print(f"[ERROR] Gagal koneksi ke Redis: {e}")
        print("   Pastikan Redis berjalan di localhost:6379")
        print("   Jalankan: docker run -d -p 6379:6379 redis:7-alpine")

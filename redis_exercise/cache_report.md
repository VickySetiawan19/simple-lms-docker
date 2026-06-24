# cache_report.md — Dokumentasi Redis Caching Exercise

## Identitas

- **Nama:** Vicky Setiawan
- **Repository:** [github.com/VickySetiawan19/simple-lms-docker](https://github.com/VickySetiawan19/simple-lms-docker)

---

## Kode yang Dimodifikasi

### Sebelum (Original)

```python
def get_weather(city):
    """Simulasi API call yang lambat"""
    time.sleep(2)  # Simulate slow API
    response = requests.get(f"https://api.example.com/weather/{city}")
    return response.json()
```

Masalah: setiap pemanggilan `get_weather()` selalu membutuhkan **~2 detik**, bahkan untuk kota yang sama.

---

### Sesudah (dengan Redis Caching)

```python
import redis
import json

r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
CACHE_TTL = 300  # 5 menit

def get_weather(city: str) -> dict:
    cache_key = f"weather:{city.lower()}"

    # STEP 1: Cek cache dulu
    cached_data = r.get(cache_key)          # Redis: GET
    if cached_data:
        return json.loads(cached_data)      # ← return cepat dari cache

    # STEP 2: Cache miss → call API
    time.sleep(2)
    data = { "city": city, "temperature": 32, ... }

    # STEP 3: Simpan ke cache dengan TTL 5 menit
    r.setex(cache_key, CACHE_TTL, json.dumps(data))  # Redis: SETEX

    return data
```

---

## Redis Commands yang Digunakan

| Command | Syntax | Kegunaan dalam kode |
|---------|--------|---------------------|
| `GET` | `GET weather:jakarta` | Mengambil data cache yang sudah tersimpan |
| `SETEX` | `SETEX weather:jakarta 300 <json>` | Menyimpan data + set expiry 300 detik sekaligus |
| `TTL` | `TTL weather:jakarta` | Mengecek berapa detik tersisa sebelum key expired |
| `DEL` | `DEL weather:jakarta` | Menghapus cache (dipakai di test setup) |
| `PING` | `PING` | Mengecek apakah Redis berjalan |

> **Catatan:** `SETEX key seconds value` = `SET key value` + `EXPIRE key seconds` dalam satu perintah atomik.

---

## Screenshot / Hasil Test

```
=======================================================
  REDIS CACHING — WEATHER API TEST
=======================================================

[SETUP] Cache untuk 'Jakarta' dihapus sebelum test.

=======================================================
  CALL #1 — First call (Cache MISS)
=======================================================
  [CACHE MISS] Key 'weather:jakarta' tidak ada. Memanggil API...
  [CACHE SET]  Data disimpan ke Redis. Key: 'weather:jakarta', TTL: 300s

  Data     : {'city': 'Jakarta', 'temperature': 32, 'humidity': 85, ...}
  ⏱  Waktu  : 2.003 detik  ← lambat (hit API)

=======================================================
  CALL #2 — Second call (Cache HIT)
=======================================================
  [CACHE HIT]  Key 'weather:jakarta' ditemukan. Sisa TTL: 298 detik

  Data     : {'city': 'Jakarta', 'temperature': 32, 'humidity': 85, ...}
  ⏱  Waktu  : 0.0021 detik  ← cepat (dari cache)

=======================================================
  SUMMARY
=======================================================

  Kota       | Call    | Waktu       | Status
  -----------+---------+-------------+------------
  Jakarta    | #1      |    2.003s   | CACHE MISS
  Jakarta    | #2      |   0.0021s   | CACHE HIT ✓
  Bandung    | #3      |    2.004s   | CACHE MISS
  Bandung    | #4      |   0.0019s   | CACHE HIT ✓

  ⚡ Speedup  : ~1000x lebih cepat dengan cache!
```

---

## Jawaban Pertanyaan

### 1. Mengapa response time berbeda?

**Call pertama** (*Cache MISS*): fungsi harus menjalankan seluruh proses — memanggil API eksternal (`time.sleep(2)` mensimulasikan latensi jaringan + pemrosesan server), lalu hasilnya baru disimpan ke Redis.

**Call kedua** (*Cache HIT*): Redis langsung mengembalikan data yang sudah tersimpan dalam memori (RAM). Tidak ada request ke API, tidak ada komputasi berat. Redis adalah **in-memory store** sehingga operasi `GET` bisa selesai dalam **< 1 milidetik**.

> **Analogi:** Seperti mencatat jawaban soal ulangan di kertas contekan. Pertama kali kamu cari di buku (lama), lalu kamu catat jawabannya. Berikutnya, tinggal baca catatanmu (cepat).

---

### 2. Apa keuntungan caching?

| Keuntungan | Penjelasan |
|---|---|
| **⚡ Performa lebih cepat** | Response time turun dari detik ke milidetik (~1000x speedup) |
| **💰 Hemat biaya API** | Tidak setiap request harus memanggil API eksternal (kurangi biaya API call jika berbayar) |
| **📉 Mengurangi beban server** | Database/API tidak dibombardir request yang sama berulang kali |
| **🛡️ Resiliensi** | Jika API eksternal down sementara, data dari cache masih bisa dilayani |
| **📈 Skalabilitas** | Server bisa melayani lebih banyak user dengan resource yang sama |

---

### 3. Kapan sebaiknya **tidak** menggunakan cache?

| Kondisi | Alasan |
|---|---|
| **Data harus selalu real-time** | Contoh: harga saham, data stok barang — cache bisa tampilkan data lama yang sudah tidak akurat |
| **Data bersifat personal/sensitif** | Risiko user A mendapat data cache milik user B jika cache key tidak dirancang dengan baik |
| **Data sangat jarang diakses** | Overhead menyimpan & mengelola cache tidak sebanding jika data hampir tidak pernah dipakai ulang |
| **Data berubah sangat sering** | Jika data berubah lebih cepat dari TTL cache, cache selalu expired dan tidak efektif |
| **Resource terbatas** | Redis menyimpan data di RAM. Jika cache terlalu besar, bisa menghabiskan memori server |

---

## Cara Menjalankan

```bash
# 1. Jalankan Redis (gunakan Docker)
docker run -d -p 6379:6379 --name redis-cache redis:7-alpine

# 2. Install dependency
pip install redis

# 3. Jalankan test
cd redis_exercise
python test_cache.py
```

Atau, jika menggunakan docker-compose project ini (Redis sudah ada):

```bash
docker-compose up -d redis
python redis_exercise/test_cache.py
```

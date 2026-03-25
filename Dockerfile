# Menggunakan base image Python
FROM python:3.10-slim

# Mencegah Python menulis file .pyc ke disk
ENV PYTHONDONTWRITEBYTECODE=1

# Memastikan output Python langsung dikirim ke terminal
ENV PYTHONUNBUFFERED=1

# Menentukan direktori kerja di dalam container
WORKDIR /app

# Meng-copy file requirements dan menginstal dependency
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Meng-copy seluruh kode project ke dalam container
COPY . /app/
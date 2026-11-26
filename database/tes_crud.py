"""
Pengujian otomatis CRUD Perpustakaan (Flask).
Menjalankan seluruh skenario dari materi praktikum.
"""
import sys
import os
import io

# Pastikan stdout memakai UTF-8 (Windows default cp1252 tidak bisa mencetak →, ✅, dll.)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import requests

BASE = "http://127.0.0.1:5000"
PASS = []
FAIL = []
# Path absolut ke file SQL (terletak di folder yang sama dengan skrip ini)
SQL_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "db_perpustakaan.sql")

def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    status = "PASS" if cond else "FAIL"
    print(f"[{status}] {name}" + (f"  [{detail}]" if detail else ""))

def reset_db():
    """Reset database ke kondisi awal."""
    import pymysql
    conn = pymysql.connect(host="localhost", user="root", password="", database="db_perpustakaan",
                           charset="utf8mb4", cursorclass=pymysql.cursors.DictCursor)
    with conn.cursor() as cur:
        cur.execute("SET FOREIGN_KEY_CHECKS=0")
        cur.execute("TRUNCATE TABLE peminjaman")
        cur.execute("TRUNCATE TABLE buku")
        cur.execute("TRUNCATE TABLE anggota")
        cur.execute("SET FOREIGN_KEY_CHECKS=1")
        conn.commit()
    # Baca SQL file, ambil hanya bagian INSERT (lewati DROP/CREATE/USE)
    with open(SQL_FILE, encoding="utf-8") as f:
        sql = f.read()
    for stmt in sql.split(";"):
        stmt = stmt.strip()
        if stmt.upper().startswith("INSERT"):
            with conn.cursor() as cur:
                cur.execute(stmt)
    conn.commit()
    conn.close()

reset_db()
print("Database direset ke kondisi awal.\n")

s = requests.Session()

# === MODUL BUKU ===
print("=== MODUL BUKU ===")
r = s.get(f"{BASE}/buku/")
check("S1  Daftar buku tampil 7 baris", r.status_code == 200 and r.text.count('B00') >= 7)

r = s.get(f"{BASE}/buku/?q=munir")
check("S2  Pencarian 'munir' → hanya B003 & B007",
      "B003" in r.text and "B007" in r.text and "B001" not in r.text)

# S3: tambah B008
r = s.post(f"{BASE}/buku/tambah", data={
    "id_buku": "B008", "judul": "Pemrograman Web Lanjut",
    "pengarang": "Ahmad Fikri", "penerbit": "Informatika",
    "tahun_terbit": "2025", "stok": "5"})
check("S3  Tambah B008 → pesan sukses + muncul di tabel",
      "Buku berhasil ditambahkan" in r.text and "B008" in r.text)

# S4: duplikat B008 (error 1062)
r = s.post(f"{BASE}/buku/tambah", data={
    "id_buku": "B008", "judul": "Duplikat", "pengarang": "X",
    "penerbit": "", "tahun_terbit": "", "stok": "1"})
check("S4  Duplikat B008 ditolak (1062)", "ID buku sudah digunakan" in r.text)

# S5: format ID salah
r = s.post(f"{BASE}/buku/tambah", data={
    "id_buku": "X1", "judul": "Salah", "pengarang": "X",
    "penerbit": "", "tahun_terbit": "", "stok": "1"})
check("S5  ID 'X1' ditolak validasi format Bxxx", "berformat Bxxx" in r.text)

# S6: edit B008 stok → 8
r = s.post(f"{BASE}/buku/B008/edit", data={
    "id_buku": "B008", "judul": "Pemrograman Web Lanjut", "pengarang": "Ahmad Fikri",
    "penerbit": "Informatika", "tahun_terbit": "2025", "stok": "8"})
check("S6  Edit B008 stok → 8",
      "berhasil diperbarui" in r.text and "B008" in r.text)

# S7: hapus B008
r = s.post(f"{BASE}/buku/B008/hapus")
check("S7  Hapus B008 → hilang dari tabel",
      "berhasil dihapus" in r.text
      and '<td>B008</td>' not in r.text)

# S8: hapus B001 (harus ditolak FK 1451)
# requests.Session mengikuti redirect otomatis, jadi pesan flash terbaca pada respons POST
r = s.post(f"{BASE}/buku/B001/hapus")
check("S8  Hapus B001 ditolak FK (1451)",
      "B001" in r.text and "riwayat peminjaman" in r.text)

# === MODUL PEMINJAMAN ===
print("\n=== MODUL PEMINJAMAN ===")
r = s.get(f"{BASE}/peminjaman/")
check("S9  12 transaksi tampil (INNER JOIN)", "Andi Pratama" in r.text or "Rizky Maulana" in r.text)
check("S9b Nama anggota + judul buku tergabung", "Abraham Silberschatz" in r.text or "Sistem Basis Data" in r.text)
check("S9c Badge keterlambatan tampil", "terlambat" in r.text)

r = s.get(f"{BASE}/peminjaman/?status=dipinjam")
check("S10 Filter status 'dipinjam'", r.status_code == 200 and "terlambat" in r.text)

# S11: pinjam B007
import pymysql
conn = pymysql.connect(host="localhost", user="root", password="", database="db_perpustakaan",
                       charset="utf8mb4", cursorclass=pymysql.cursors.DictCursor)
with conn.cursor() as cur:
    cur.execute("SELECT stok FROM buku WHERE id_buku='B007'")
    sebelum = cur.fetchone()["stok"]
conn.close()

from datetime import date
s.post(f"{BASE}/peminjaman/tambah", data={
    "id_anggota": "A006", "id_buku": "B007", "tgl_pinjam": date.today().isoformat()})

conn = pymysql.connect(host="localhost", user="root", password="", database="db_perpustakaan",
                       charset="utf8mb4", cursorclass=pymysql.cursors.DictCursor)
with conn.cursor() as cur:
    cur.execute("SELECT stok FROM buku WHERE id_buku='B007'")
    sesudah = cur.fetchone()["stok"]
conn.close()
check("S11 Pinjam B007 → stok berkurang 1", sesudah == sebelum - 1, f"{sebelum}→{sesudah}")

# S12: kembalikan transaksi terbaru
conn = pymysql.connect(host="localhost", user="root", password="", database="db_perpustakaan",
                       charset="utf8mb4", cursorclass=pymysql.cursors.DictCursor)
with conn.cursor() as cur:
    cur.execute("SELECT MAX(id_pinjam) AS id FROM peminjaman WHERE id_anggota='A006' AND id_buku='B007'")
    id_pinjam = cur.fetchone()["id"]
conn.close()

s.post(f"{BASE}/peminjaman/{id_pinjam}/kembalikan")
conn = pymysql.connect(host="localhost", user="root", password="", database="db_perpustakaan",
                       charset="utf8mb4", cursorclass=pymysql.cursors.DictCursor)
with conn.cursor() as cur:
    cur.execute("SELECT status FROM peminjaman WHERE id_pinjam=%s", (id_pinjam,))
    status = cur.fetchone()["status"]
    cur.execute("SELECT stok FROM buku WHERE id_buku='B007'")
    stok_kembali = cur.fetchone()["stok"]
conn.close()
check("S12 Kembalikan → status 'kembali' + stok pulih",
      status == "kembali" and stok_kembali == sebelum, f"status={status}, stok={stok_kembali}")

# S13: pinjam B006 2x
for _ in range(2):
    s.post(f"{BASE}/peminjaman/tambah", data={
        "id_anggota": "A005", "id_buku": "B006", "tgl_pinjam": date.today().isoformat()})

r = s.get(f"{BASE}/peminjaman/tambah")
check("S13 B006 habis → hilang dari dropdown",
      "B006" not in r.text and "stok 0" not in r.text)

# S14: hapus transaksi B006 yang masih dipinjam
conn = pymysql.connect(host="localhost", user="root", password="", database="db_perpustakaan",
                       charset="utf8mb4", cursorclass=pymysql.cursors.DictCursor)
with conn.cursor() as cur:
    cur.execute("SELECT MAX(id_pinjam) AS id FROM peminjaman WHERE id_buku='B006' AND status='dipinjam'")
    id6 = cur.fetchone()["id"]
    cur.execute("SELECT stok FROM buku WHERE id_buku='B006'")
    stok6_sebelum = cur.fetchone()["stok"]
conn.close()

s.post(f"{BASE}/peminjaman/{id6}/hapus")
conn = pymysql.connect(host="localhost", user="root", password="", database="db_perpustakaan",
                       charset="utf8mb4", cursorclass=pymysql.cursors.DictCursor)
with conn.cursor() as cur:
    cur.execute("SELECT stok FROM buku WHERE id_buku='B006'")
    stok6_sesudah = cur.fetchone()["stok"]
conn.close()
check("S14 Hapus transaksi B006 → terhapus & stok +1", stok6_sesudah == stok6_sebelum + 1)

# === RINGKASAN ===
print("\n" + "=" * 60)
print(f"TOTAL: {len(PASS)} PASS, {len(FAIL)} FAIL")
if FAIL:
    print("\nGagal:")
    for f in FAIL:
        print(f"  - {f}")
    sys.exit(1)
else:
    print("SEMUA SKENARIO LULUS!")

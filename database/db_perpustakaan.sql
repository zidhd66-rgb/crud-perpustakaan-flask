-- ============================================================
-- Studi Kasus 1 - Sistem Informasi Perpustakaan
-- Mata Kuliah Basis Data | Materi Praktikum CRUD
-- Lampiran A: Skrip Basis Data Kasus 1
-- ============================================================

DROP DATABASE IF EXISTS db_perpustakaan;
CREATE DATABASE db_perpustakaan;
USE db_perpustakaan;

CREATE TABLE anggota (
    id_anggota CHAR(4) PRIMARY KEY,
    nama VARCHAR(50) NOT NULL,
    alamat VARCHAR(100),
    tgl_daftar DATE NOT NULL
) ENGINE=InnoDB;

CREATE TABLE buku (
    id_buku CHAR(4) PRIMARY KEY,
    judul VARCHAR(100) NOT NULL,
    pengarang VARCHAR(50) NOT NULL,
    penerbit VARCHAR(50),
    tahun_terbit INT,
    stok INT NOT NULL DEFAULT 0
) ENGINE=InnoDB;

CREATE TABLE peminjaman (
    id_pinjam INT AUTO_INCREMENT PRIMARY KEY,
    id_anggota CHAR(4) NOT NULL,
    id_buku CHAR(4) NOT NULL,
    tgl_pinjam DATE NOT NULL,
    tgl_kembali DATE,
    status ENUM('dipinjam','kembali') NOT NULL DEFAULT 'dipinjam',
    FOREIGN KEY (id_anggota) REFERENCES anggota(id_anggota),
    FOREIGN KEY (id_buku) REFERENCES buku(id_buku)
) ENGINE=InnoDB;

INSERT INTO anggota VALUES
('A001','Andi Pratama', 'Jl. Kenanga 12', '2025-08-15'),
('A002','Siti Rahmawati', 'Jl. Melati 5', '2025-08-20'),
('A003','Rizky Maulana', 'Jl. Mawar 21', '2025-09-01'),
('A004','Dewi Lestari', 'Jl. Anggrek 7', '2025-09-10'),
('A005','Fajar Nugroho', 'Jl. Dahlia 3', '2026-01-05'),
('A006','Nadia Putri', 'Jl. Flamboyan 9', '2026-02-14');

INSERT INTO buku VALUES
('B001','Sistem Basis Data', 'Abraham Silberschatz','McGraw-Hill',2019,4),
('B002','Pemrograman Python Dasar', 'Budi Raharjo', 'Informatika',2021,6),
('B003','Algoritma dan Struktur Data', 'Rinaldi Munir', 'Informatika',2020,5),
('B004','Rekayasa Perangkat Lunak', 'Roger Pressman', 'McGraw-Hill',2022,3),
('B005','Jaringan Komputer', 'Andrew Tanenbaum', 'Pearson', 2023,4),
('B006','Kecerdasan Buatan', 'Suyanto', 'Informatika',2024,2),
('B007','Matematika Diskrit', 'Rinaldi Munir', 'Informatika',2018,7);

INSERT INTO peminjaman
(id_anggota, id_buku, tgl_pinjam, tgl_kembali, status) VALUES
('A001','B001','2026-01-10','2026-01-17','kembali'),
('A002','B001','2026-02-03','2026-02-09','kembali'),
('A003','B001','2026-03-12','2026-03-18','kembali'),
('A004','B001','2026-05-20','2026-05-27','kembali'),
('A005','B001','2026-10-02','2026-10-08','kembali'),
('A001','B002','2026-03-01','2026-03-08','kembali'),
('A001','B003','2026-06-15','2026-06-22','kembali'),
('A001','B004','2026-10-25', NULL, 'dipinjam'),
('A001','B005','2026-11-08', NULL, 'dipinjam'),
('A002','B003','2026-07-11','2026-07-16','kembali'),
('A003','B006','2026-10-30', NULL, 'dipinjam'),
('A004','B002','2026-11-10', NULL, 'dipinjam');

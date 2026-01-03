CREATE DATABASE IF NOT EXISTS toko_bangunan
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE toko_bangunan;

-- ======================
-- TABEL ADMIN
-- ======================
CREATE TABLE admin (
  id_admin INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(50) UNIQUE,
  password VARCHAR(255)
) ENGINE=InnoDB;

INSERT INTO admin (username, password) VALUES
(1, 'admin', 'scrypt:32768:8:1$vXy... (Hash dibuat di app.py)'),
(2, 'hilmi', 'pbkdf2:sha256:1000000$B6rGlK1CX7Jt5vGF$bdaac0f8e72759f7a63247a76cbfe55db6d1d28abec21527cd237d6d40132ab3');

-- ======================
-- TABEL PELANGGAN
-- ======================
CREATE TABLE pelanggan (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nama_lengkap VARCHAR(100),
  nomor_hp VARCHAR(15) UNIQUE,
  alamat TEXT,
  password VARCHAR(255)
) ENGINE=InnoDB;

INSERT INTO pelanggan (nama_lengkap, nomor_hp, alamat, password) VALUES
('jule', '123456', 'jogja',
'scrypt:32768:8:1$wqzahKWxkWT8ygCd$9a84d1b2468e7c782b0e14ac065f9aa3ff1871950240c2fb7d7b833e44f1c99a55f308e87bf4388e13d01954c6f1cef25fbd44de385171d540145882f5188249');

-- ======================
-- TABEL PRODUK
-- ======================
CREATE TABLE produk (
  id_produk INT AUTO_INCREMENT PRIMARY KEY,
  nama_produk VARCHAR(100),
  harga INT,
  stok INT,
  gambar VARCHAR(255) DEFAULT 'default.jpg',
  status VARCHAR(20) DEFAULT 'aktif'
) ENGINE=InnoDB;

-- ======================
-- TABEL PESANAN
-- ======================
CREATE TABLE pesanan (
  id_pesanan INT AUTO_INCREMENT PRIMARY KEY,
  id_pelanggan INT,
  total_bayar INT,
  status VARCHAR(50) DEFAULT 'Diproses',
  notif_viewed TINYINT(1) DEFAULT 0,
  tanggal_pesanan TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_pesanan_pelanggan
    FOREIGN KEY (id_pelanggan) REFERENCES pelanggan(id)
) ENGINE=InnoDB;

-- ======================
-- TABEL DETAIL PESANAN
-- ======================
CREATE TABLE detail_pesanan (
  id_detail INT AUTO_INCREMENT PRIMARY KEY,
  id_pesanan INT,
  id_produk INT,
  jumlah INT,
  harga_satuan INT,
  CONSTRAINT fk_detail_pesanan
    FOREIGN KEY (id_pesanan) REFERENCES pesanan(id_pesanan) ON DELETE CASCADE,
  CONSTRAINT fk_detail_produk
    FOREIGN KEY (id_produk) REFERENCES produk(id_produk)
) ENGINE=InnoDB;


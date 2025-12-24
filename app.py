from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os

app = Flask(_name_)
app.secret_key = 'maju_jaya_key'

# --- KONFIGURASI DATABASE ---
db_config = {
    'host': 'web-toko-bangunan.mysql.database.azure.com',
    'user': 'punakawan',
    'password': 'Punak4w@n#2025',
    'database': 'toko_bangunan',
    'auth_plugin': 'mysql_native_password'
}

def get_db_connection():
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except Error as e:
        print(f"Gagal koneksi ke Azure: {e}")
        return None

# --- KONFIGURASI UPLOAD GAMBAR ---
UPLOAD_FOLDER = 'static/images'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- HELPER: LOGIN CHECK ---
def is_admin():
    return session.get('admin_ok')

def is_logged_in():
    return 'user_id' in session

# --- ROUTE PELANGGAN ---

@app.route('/')
def index():
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM produk WHERE status = 'aktif'")
    produk = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('index.html', produk=produk)

@app.route('/login', methods=['GET', 'POST'])
def login_pelanggan():
    if request.method == 'POST':
        hp = request.form['hp']
        pw = request.form['password']
        
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM pelanggan WHERE nomor_hp = %s", [hp])
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user and check_password_hash(user['password'], pw):
            session['user_id'] = user['id']
            session['user_name'] = user['nama_lengkap']
            return redirect(url_for('index'))
        else:
            flash("Nomor HP atau Password salah!", "danger")
    return render_template('login_pelanggan.html')

@app.route('/checkout', methods=['POST'])
def checkout():
    if not is_logged_in():
        return jsonify({'status': 'error', 'message': 'Anda harus login dahulu'})
    
    data = request.json
    total = data['total']
    keranjang = data['keranjang'] 
    user_id = session['user_id']

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    try:
        # 1. Simpan ke tabel induk pesanan
        cur.execute("INSERT INTO pesanan (id_pelanggan, total_bayar, status, notif_viewed) VALUES (%s, %s, 'Diproses', 0)", 
                    (user_id, total))
        order_id = cur.lastrowid
        
        # 2. Simpan rincian & Update stok
        for item in keranjang:
            cur.execute("INSERT INTO detail_pesanan (id_pesanan, id_produk, jumlah, harga_satuan) VALUES (%s, %s, %s, %s)",
                        (order_id, item['id_produk'], item['jumlah'], item['harga']))
            cur.execute("UPDATE produk SET stok = stok - %s WHERE id_produk = %s", 
                        (item['jumlah'], item['id_produk']))

        conn.commit()
        return jsonify({'status': 'success'})
    except Error as e:
        conn.rollback()
        return jsonify({'status': 'error', 'message': str(e)})
    finally:
        cur.close()
        conn.close()

# --- ROUTE ADMIN ---

@app.route('/admin/login', methods=['GET', 'POST'])
def login_admin():
    if request.method == 'POST':
        user = request.form['user']
        pw = request.form['pass']
        
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM admin WHERE username = %s", [user])
        adm = cur.fetchone()
        cur.close()
        conn.close()

        if adm and check_password_hash(adm['password'], pw):
            session['admin_ok'] = True
            return redirect(url_for('admin'))
        else:
            flash("Username atau Password Admin salah!", "danger")
    return render_template('login_admin.html')

@app.route('/admin')
def admin():
    if not is_admin(): return redirect(url_for('login_admin'))
    
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT p.*, c.nama_lengkap FROM pesanan p JOIN pelanggan c ON p.id_pelanggan = c.id ORDER BY p.tanggal_pesanan DESC")
    orders = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('admin.html', orders=orders)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if _name_ == '_main_':
    app.run(debug=True)


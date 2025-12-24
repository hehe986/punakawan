from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.secret_key = 'maju_jaya_key'

# --- KONFIGURASI DATABASE ---
app.config['MYSQL_HOST'] = 'web-toko-bangunan.mysql.database.azure.com'
app.config['MYSQL_USER'] = 'punakawan'
app.config['MYSQL_PASSWORD'] = 'Punak4w@n#2025'
app.config['MYSQL_DB'] = 'toko_bangunan'
app.config['MYSQL_PORT'] = '3306'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# --- KONFIGURASI UPLOAD GAMBAR ---
UPLOAD_FOLDER = 'static/images'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

mysql = MySQL(app)

# --- MIDDLEWARE SEDERHANA (Pengecekan Login) ---
def is_admin():
    return session.get('admin_ok')

def is_logged_in():
    return 'user_id' in session

# --- ROUTE PELANGGAN ---

@app.route('/')
def index():
    cur = mysql.connection.cursor()
    # Hanya ambil produk yang statusnya aktif
    cur.execute("SELECT * FROM produk WHERE status = 'aktif'")
    produk = cur.fetchall()
    cur.close()
    return render_template('index.html', produk=produk)

@app.route('/login', methods=['GET', 'POST'])
def login_pelanggan():
    if request.method == 'POST':
        hp = request.form['hp']
        pw = request.form['password']
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM pelanggan WHERE nomor_hp = %s", [hp])
        user = cur.fetchone()
        cur.close()

        if user and check_password_hash(user['password'], pw):
            session['user_id'] = user['id']
            session['user_name'] = user['nama_lengkap']
            return redirect(url_for('index'))
        else:
            flash("Nomor HP atau Password salah!", "danger")
    return render_template('login_pelanggan.html')

@app.route('/daftar', methods=['GET', 'POST'])
def daftar_pelanggan():
    if request.method == 'POST':
        nama = request.form['nama']
        hp = request.form['hp']
        alamat = request.form['alamat']
        password = request.form['password']
        hashed_pw = generate_password_hash(password)
        
        try:
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO pelanggan (nama_lengkap, nomor_hp, alamat, password) VALUES (%s, %s, %s, %s)", 
                        (nama, hp, alamat, hashed_pw))
            mysql.connection.commit()
            cur.close()
            flash("Pendaftaran berhasil, silakan login.", "success")
            return redirect(url_for('login_pelanggan'))
        except Exception as e:
            return f"Error: {str(e)}"
    return render_template('daftar_pelanggan.html')

@app.route('/checkout', methods=['POST'])
def checkout():
    if not is_logged_in():
        return jsonify({'status': 'error', 'message': 'Anda harus login dahulu'})
    
    data = request.json
    total = data['total']
    keranjang = data['keranjang'] 
    user_id = session['user_id']

    try:
        cur = mysql.connection.cursor()
        
        # --- VALIDASI STATUS PRODUK ---
        for item in keranjang:
            cur.execute("SELECT nama_produk, status FROM produk WHERE id_produk = %s", [item['id_produk']])
            produk = cur.fetchone()
            
            if not produk:
                return jsonify({'status': 'error', 'message': f"Produk tidak ditemukan."})
            
            if produk['status'] == 'dihapus':
                return jsonify({
                    'status': 'error', 
                    'message': f"Maaf, produk '{produk['nama_produk']}' sedang tidak tersedia/non-aktif. Mohon hapus dari keranjang."
                })
        # --- END VALIDASI ---

        # 1. Simpan ke tabel induk pesanan
        cur.execute("INSERT INTO pesanan (id_pelanggan, total_bayar, status, notif_viewed) VALUES (%s, %s, 'Diproses', 0)", 
                    (user_id, total))
        order_id = cur.lastrowid
        
        # 2. Simpan rincian barang
        for item in keranjang:
            cur.execute("""
                INSERT INTO detail_pesanan (id_pesanan, id_produk, jumlah, harga_satuan) 
                VALUES (%s, %s, %s, %s)
            """, (order_id, item['id_produk'], item['jumlah'], item['harga']))
            
            # Update Stok
            cur.execute("UPDATE produk SET stok = stok - %s WHERE id_produk = %s", 
                        (item['jumlah'], item['id_produk']))

        mysql.connection.commit()
        cur.close()
        return jsonify({'status': 'success'})
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/histori_pesanan')
def histori_pesanan():
    if not is_logged_in():
        return redirect(url_for('login_pelanggan'))
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM pesanan WHERE id_pelanggan = %s ORDER BY tanggal_pesanan DESC", [session['user_id']])
    orders = cur.fetchall()
    cur.close()
    return render_template('histori_pesanan.html', orders=orders)

# FITUR LIHAT DETAIL PESANAN (SISI PELANGGAN)
@app.route('/pesanan/detail/<int:id>')
def detail_pesanan_pelanggan(id):
    if not is_logged_in():
        return redirect(url_for('login_pelanggan'))
    
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT p.*, c.nama_lengkap 
        FROM pesanan p 
        JOIN pelanggan c ON p.id_pelanggan = c.id 
        WHERE p.id_pesanan = %s AND p.id_pelanggan = %s
    """, (id, session['user_id']))
    pesanan = cur.fetchone()
    
    if not pesanan:
        cur.close()
        flash("Detail pesanan tidak ditemukan atau akses dilarang.", "danger")
        return redirect(url_for('histori_pesanan'))
    
    cur.execute("""
        SELECT d.*, pr.nama_produk 
        FROM detail_pesanan d 
        JOIN produk pr ON d.id_produk = pr.id_produk 
        WHERE d.id_pesanan = %s
    """, [id])
    rincian = cur.fetchall()
    cur.close()
    return render_template('lihat_detail_pelanggan.html', pesanan=pesanan, rincian=rincian)

@app.route('/keranjang')
def keranjang():
    return render_template('keranjang.html')

@app.route('/kalkulator')
def kalkulator():
    return render_template('kalkulator.html')

@app.route('/profil')
def profil():
    if not is_logged_in():
        return redirect(url_for('login_pelanggan'))
    
    cur = mysql.connection.cursor()
    # Pastikan nama kolom 'id' sesuai dengan tabel pelanggan Anda
    cur.execute("SELECT id, nama_lengkap, nomor_hp, alamat FROM pelanggan WHERE id = %s", [session['user_id']])
    user = cur.fetchone()
    cur.close()
    
    if not user:
        flash("Data pengguna tidak ditemukan.", "danger")
        return redirect(url_for('logout'))
        
    return render_template('profil.html', user=user)

@app.route('/profil/update', methods=['POST'])
def update_profil():
    if not is_logged_in():
        return redirect(url_for('login_pelanggan'))

    # Ambil data dari form profil.html
    nama = request.form.get('nama')
    hp = request.form.get('hp')
    alamat = request.form.get('alamat')
    password_baru = request.form.get('password_baru')
    user_id = session['user_id']

    cur = mysql.connection.cursor()
    
    try:
        if password_baru and password_baru.strip() != "":
            # Jika user mengisi password baru, lakukan hashing
            hashed_pw = generate_password_hash(password_baru)
            cur.execute("""
                UPDATE pelanggan 
                SET nama_lengkap = %s, nomor_hp = %s, alamat = %s, password = %s 
                WHERE id = %s
            """, (nama, hp, alamat, hashed_pw, user_id))
        else:
            # Jika password dikosongkan, update data profil saja
            cur.execute("""
                UPDATE pelanggan 
                SET nama_lengkap = %s, nomor_hp = %s, alamat = %s 
                WHERE id = %s
            """, (nama, hp, alamat, user_id))
        
        mysql.connection.commit()
        
        # Update session agar nama di header berubah seketika
        session['user_name'] = nama
        
        flash("Profil berhasil diperbarui!", "success")
    except Exception as e:
        mysql.connection.rollback()
        flash(f"Gagal memperbarui profil: {str(e)}", "danger")
    finally:
        cur.close()

    return redirect(url_for('profil'))

# --- ROUTE LUPA PASSWORD ---

@app.route('/lupa-password', methods=['GET', 'POST'])
def lupa_password():
    if request.method == 'POST':
        query = request.form['search_query']
        cur = mysql.connection.cursor()
        # Mencari berdasarkan nama atau nomor hp
        cur.execute("SELECT id FROM pelanggan WHERE nama_lengkap = %s OR nomor_hp = %s", (query, query))
        user = cur.fetchone()
        cur.close()

        if user:
            # Jika ketemu, arahkan ke halaman reset dengan membawa ID user
            return redirect(url_for('reset_password', user_id=user['id']))
        else:
            flash("Akun tidak ditemukan. Pastikan Nama atau Nomor HP benar.")
            
    return render_template('lupa_password.html')

@app.route('/reset-password/<int:user_id>', methods=['GET', 'POST'])
def reset_password(user_id):
    if request.method == 'POST':
        pw_baru = request.form['password']
        hashed_pw = generate_password_hash(pw_baru)

        cur = mysql.connection.cursor()
        cur.execute("UPDATE pelanggan SET password = %s WHERE id = %s", (hashed_pw, user_id))
        mysql.connection.commit()
        cur.close()

        flash("Password berhasil direset! Silakan login.")
        return redirect(url_for('login_pelanggan'))

    return render_template('reset_password.html', user_id=user_id)

# --- ROUTE ADMIN ---

@app.route('/admin/login', methods=['GET', 'POST'])
def login_admin():
    if request.method == 'POST':
        user = request.form['user']
        pw = request.form['pass']
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM admin WHERE username = %s", [user])
        adm = cur.fetchone()
        cur.close()

        if adm and check_password_hash(adm['password'], pw):
            session['admin_ok'] = True
            return redirect(url_for('admin'))
        else:
            flash("Username atau Password Admin salah!", "danger")
    return render_template('login_admin.html')

@app.route('/admin')
def admin():
    if not is_admin():
        return redirect(url_for('login_admin'))
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT p.*, c.nama_lengkap FROM pesanan p JOIN pelanggan c ON p.id_pelanggan = c.id ORDER BY p.tanggal_pesanan DESC")
    orders = cur.fetchall()
    
    cur.execute("SELECT DATE(tanggal_pesanan) as tgl, SUM(total_bayar) as total FROM pesanan GROUP BY tgl ORDER BY tgl DESC LIMIT 7")
    graph_data = cur.fetchall()
    cur.close()
    
    return render_template('admin.html', orders=orders, graph_data=graph_data)

# FITUR LIHAT DETAIL PESANAN (SISI ADMIN)
@app.route('/admin/detail_pesanan/<int:id>')
def lihat_detail_admin(id):
    if not is_admin():
        return redirect(url_for('login_admin'))
    
    cur = mysql.connection.cursor()
    # Mengambil data pesanan beserta info lengkap pelanggan (nama, hp, alamat)
    cur.execute("""
        SELECT p.*, c.nama_lengkap, c.nomor_hp, c.alamat 
        FROM pesanan p 
        JOIN pelanggan c ON p.id_pelanggan = c.id 
        WHERE p.id_pesanan = %s
    """, [id])
    pesanan = cur.fetchone()
    
    # Mengambil rincian produk yang dipesan
    cur.execute("""
        SELECT d.*, pr.nama_produk 
        FROM detail_pesanan d 
        JOIN produk pr ON d.id_produk = pr.id_produk 
        WHERE d.id_pesanan = %s
    """, [id])
    rincian = cur.fetchall()
    cur.close()
    return render_template('lihat_detail.html', pesanan=pesanan, rincian=rincian)

@app.route('/get_order_count')
def get_order_count():
    if not is_admin():
        return jsonify({'count': 0})

    cur = mysql.connection.cursor()
    cur.execute("SELECT COUNT(*) as total FROM pesanan WHERE notif_viewed = 0")
    result = cur.fetchone()
    count = result['total']
    
    if count > 0:
        cur.execute("UPDATE pesanan SET notif_viewed = 1 WHERE notif_viewed = 0")
        mysql.connection.commit()
        
    cur.close()
    return jsonify({'count': count})

@app.route('/admin/update_status/<int:id>')
def update_status_selesai(id):
    if not is_admin():
        return redirect(url_for('login_admin'))
    
    cur = mysql.connection.cursor()
    cur.execute("UPDATE pesanan SET status = 'Selesai' WHERE id_pesanan = %s", [id])
    mysql.connection.commit()
    cur.close()
    # Redirect kembali ke detail agar admin bisa langsung cetak invoice terbaru
    return redirect(url_for('lihat_detail_admin', id=id))

# ROUTE TAMBAHAN UNTUK MANAJEMEN PRODUK (ADMIN)
@app.route('/admin/produk')
def kelola_produk():
    if not is_admin():
        return redirect(url_for('login_admin'))
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM produk")
    produk = cur.fetchall()
    cur.close()
    return render_template('Kelola_Produk.html', produk=produk)

@app.route('/tambah_produk', methods=['POST'])
def tambah_produk():
    if not is_admin(): return redirect(url_for('login_admin'))
    
    nama = request.form['nama_produk']
    harga = request.form['harga']
    stok = request.form.get('stok', 0)
    file = request.files['gambar']

    if file:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO produk (nama_produk, harga, gambar, stok) VALUES (%s, %s, %s, %s)", 
                    (nama, harga, filename, stok))
        mysql.connection.commit()
        cur.close()
    return redirect(url_for('kelola_produk'))

@app.route('/admin/update_stok/<int:id>', methods=['POST'])
def update_stok(id):
    if not is_admin(): return redirect(url_for('login_admin'))
    stok_baru = request.form['stok_baru']
    cur = mysql.connection.cursor()
    cur.execute("UPDATE produk SET stok = %s WHERE id_produk = %s", (stok_baru, id))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('kelola_produk'))

@app.route('/admin/hapus_produk/<int:id>')
def hapus_produk(id):
    if not is_admin(): return redirect(url_for('login_admin'))
    cur = mysql.connection.cursor()
    # Mengubah status daripada menghapus barisnya
    cur.execute("UPDATE produk SET status = 'dihapus' WHERE id_produk = %s", [id])
    mysql.connection.commit()
    cur.close()
    flash("Produk telah dinonaktifkan!", "success")
    return redirect(url_for('kelola_produk'))

@app.route('/admin/aktifkan_produk/<int:id>')
def aktifkan_produk(id):
    if not is_admin(): return redirect(url_for('login_admin'))
    cur = mysql.connection.cursor()
    cur.execute("UPDATE produk SET status = 'aktif' WHERE id_produk = %s", [id])
    mysql.connection.commit()
    cur.close()
    flash("Produk berhasil diaktifkan kembali!", "success")
    return redirect(url_for('kelola_produk'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':

    app.run(debug=True)

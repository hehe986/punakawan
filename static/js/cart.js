// Di file JavaScript Anda (misal script.js atau cart.js)
function addToCart(id, nama, harga, stok) {
    // 1. Cek apakah stok tersedia
    if (parseInt(stok) <= 0) {
        showToast(`Maaf, stok ${nama} habis!`, "danger");
        return; // Hentikan proses
    }

    // 2. Ambil data keranjang dari localStorage
    let cart = JSON.parse(localStorage.getItem('cart')) || [];

    // 3. Cek apakah barang sudah ada di keranjang
    let found = cart.find(item => item.id === id);
    if (found) {
        // Cek jika penambahan melebihi stok yang ada
        if (found.qty >= parseInt(stok)) {
            showToast(`Gagal! Jumlah di keranjang sudah mencapai batas stok ${nama}.`, "danger");
            return;
        }
        found.qty += 1;
    } else {
        cart.push({
            id: id,
            name: nama,
            price: parseInt(harga),
            qty: 1
        });
    }

    // 4. Simpan kembali
    localStorage.setItem('cart', JSON.stringify(cart));
    
    // 5. Beri feedback sukses
    showToast(`${nama} ditambahkan ke keranjang`, "success");
    
    // Jika ada fungsi update counter di header
    if (typeof updateCartCount === 'function') updateCartCount();
}
function showNotification(message) {
    // 1. Buat elemen div notifikasi
    const notif = document.createElement('div');
    notif.className = 'toast-notif';
    
    // 2. Isi konten dengan ikon dan pesan
    notif.innerHTML = `
        <i class="fas fa-check-circle"></i>
        <span>${message}</span>
    `;

    // 3. Tambahkan ke body dokumen
    document.body.appendChild(notif);

    // 4. Hapus elemen dari DOM setelah animasi selesai (3 detik)
    setTimeout(() => {
        notif.remove();
    }, 3000);
}
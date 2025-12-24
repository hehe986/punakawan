function getCart() { return JSON.parse(localStorage.getItem('cart')) || []; }
function updateCartCount() {
    let count = getCart().reduce((sum, item) => sum + item.qty, 0);
    if(document.getElementById('cart-count')) document.getElementById('cart-count').innerText = count;
}
function addToCart(id, name, price) {
    let cart = getCart();
    let idx = cart.findIndex(i => i.id === id);
    
    if(idx > -1) {
        cart[idx].qty++; 
    } else {
        cart.push({id, name, price, qty: 1});
    }
    
    localStorage.setItem('cart', JSON.stringify(cart));
    updateCartCount();

    // Mengganti alert dengan notifikasi kustom
    showNotification(name + " berhasil ditambahkan ke keranjang!");
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
document.addEventListener('DOMContentLoaded', updateCartCount);

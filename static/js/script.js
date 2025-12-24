function filterProducts() {
    let search = document.getElementById('product-search').value.toLowerCase();
    document.querySelectorAll('.product-card').forEach(card => {
        let name = card.querySelector('h3').innerText.toLowerCase();
        card.style.display = name.includes(search) ? "" : "none";
    });
}
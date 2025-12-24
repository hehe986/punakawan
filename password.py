from werkzeug.security import generate_password_hash

# Membuat hash dengan metode pbkdf2:sha256
password_asli = "123"
hash_baru = generate_password_hash(password_asli, method='pbkdf2:sha256')
print(hash_baru)
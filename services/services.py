import hashlib


# Функция получения хеша
def get_hash(password):
    hash = hashlib.sha256()
    hash.update(password.encode('utf-8'))
    password_hash = hash.hexdigest()
    return password_hash
import hashlib


# Функция получения хеша
def get_hash(password):
    hash = hashlib.sha256()
    hash.update(password.encode('utf-8'))
    password_hash = hash.hexdigest()
    return password_hash


# Возвращает профиль авторизованного пользователя
def get_userprofile(request):
    if request.user.is_authenticated:
        user = request.user
        return user
    else:
        return None
from bcrypt import hashpw, checkpw, gensalt


def get_hash(password: str) -> tuple[str, str]:
    """
    Хеширует пароль с солью и возвращает пароль и соль
    """
    salt = gensalt()
    password_bytes = password.encode('utf-8')
    hashed_password = hashpw(password_bytes, salt)
    
    return hashed_password.decode('utf-8')

def check_pwd(pwd: str, hash_pwd: str):
    pwd_bytes = pwd.encode('utf-8')
    hash_pwd = hash_pwd.encode('utf-8')
    return checkpw(pwd_bytes, hash_pwd)




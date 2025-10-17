"""
Утиліти для хешування паролів
"""
import bcrypt


def hash_password(password: str) -> str:
    """
    Хешує пароль за допомогою bcrypt
    
    Args:
        password: Звичайний текстовий пароль
        
    Returns:
        Хешований пароль (string)
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(password: str, hashed_password: str) -> bool:
    """
    Перевіряє, чи відповідає пароль хешу
    
    Args:
        password: Звичайний текстовий пароль
        hashed_password: Хешований пароль з бази даних
        
    Returns:
        True якщо пароль відповідає хешу, False якщо ні
    """
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

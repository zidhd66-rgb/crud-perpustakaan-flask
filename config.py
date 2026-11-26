import os


class Config:
    # SECRET_KEY wajib diisi agar fitur flash (berbasis session) dapat dipakai
    SECRET_KEY = os.environ.get('SECRET_KEY', 'ganti-dengan-kunci-rahasia')

    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
    DB_NAME = os.environ.get('DB_NAME', 'db_perpustakaan')

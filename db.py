import pymysql
from flask import current_app, g


def get_db():
    """Mengembalikan koneksi untuk request saat ini (dibuat jika belum ada)."""
    if 'db' not in g:
        cfg = current_app.config
        g.db = pymysql.connect(
            host=cfg['DB_HOST'],
            user=cfg['DB_USER'],
            password=cfg['DB_PASSWORD'],
            database=cfg['DB_NAME'],
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,  # hasil berupa dict
            autocommit=False,                        # commit dilakukan manual
        )
    return g.db


def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_app(app):
    app.teardown_appcontext(close_db)

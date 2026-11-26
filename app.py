from flask import Flask, redirect, url_for

import db
from config import Config
from routes.buku import bp as buku_bp
from routes.peminjaman import bp as peminjaman_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    app.register_blueprint(buku_bp)
    app.register_blueprint(peminjaman_bp)

    @app.route('/')
    def index():
        return redirect(url_for('buku.index'))

    return app


app = create_app()

if __name__ == '__main__':
    app.run(debug=True)

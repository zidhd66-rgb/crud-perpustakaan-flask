import re

import pymysql
from flask import Blueprint, flash, redirect, render_template, request, url_for, abort

from db import get_db

bp = Blueprint('buku', __name__, url_prefix='/buku')


def ambil_form():
    f = request.form
    return {
        'id_buku': f.get('id_buku', '').strip().upper(),
        'judul': f.get('judul', '').strip(),
        'pengarang': f.get('pengarang', '').strip(),
        'penerbit': f.get('penerbit', '').strip(),
        'tahun_terbit': f.get('tahun_terbit', '').strip(),
        'stok': f.get('stok', '0').strip(),
    }


def validasi(b):
    err = []
    if not re.fullmatch(r'B\d{3}', b['id_buku']):
        err.append('ID buku harus berformat Bxxx, contoh B008.')
    if not b['judul']:
        err.append('Judul wajib diisi.')
    if not b['pengarang']:
        err.append('Pengarang wajib diisi.')
    if b['tahun_terbit'] and not b['tahun_terbit'].isdigit():
        err.append('Tahun terbit harus berupa angka.')
    if not b['stok'].isdigit():
        err.append('Stok harus bilangan bulat >= 0.')
    return err


def nilai(b):
    """Urutan parameter: judul, pengarang, penerbit, tahun, stok, id_buku."""
    return (
        b['judul'],
        b['pengarang'],
        b['penerbit'] or None,
        int(b['tahun_terbit']) if b['tahun_terbit'] else None,
        int(b['stok']),
        b['id_buku'],
    )


# ---------------- READ ----------------
@bp.route('/')
def index():
    q = request.args.get('q', '').strip()
    with get_db().cursor() as cur:
        if q:
            cur.execute(
                "SELECT * FROM buku WHERE judul LIKE %s OR pengarang LIKE %s "
                "ORDER BY id_buku",
                (f'%{q}%', f'%{q}%'),
            )
        else:
            cur.execute("SELECT * FROM buku ORDER BY id_buku")
        daftar = cur.fetchall()
    return render_template('buku/index.html', daftar=daftar, q=q)


# ---------------- CREATE ----------------
@bp.route('/tambah', methods=['GET', 'POST'])
def tambah():
    buku = {'id_buku': '', 'judul': '', 'pengarang': '',
            'penerbit': '', 'tahun_terbit': '', 'stok': '0'}
    errors = []

    if request.method == 'POST':
        buku = ambil_form()
        errors = validasi(buku)
        if not errors:
            conn = get_db()
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO buku (judul, pengarang, penerbit, tahun_terbit, stok, id_buku) "
                        "VALUES (%s, %s, %s, %s, %s, %s)",
                        nilai(buku),
                    )
                conn.commit()
                flash('Buku berhasil ditambahkan.', 'success')
                return redirect(url_for('buku.index'))
            except pymysql.err.IntegrityError as e:
                conn.rollback()
                if e.args[0] == 1062:
                    errors.append('ID buku sudah digunakan.')
                else:
                    raise

    return render_template('buku/form.html', buku=buku, errors=errors, mode='tambah')


# ---------------- UPDATE ----------------
@bp.route('/<id_buku>/edit', methods=['GET', 'POST'])
def edit(id_buku):
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM buku WHERE id_buku = %s", (id_buku,))
        buku = cur.fetchone()
    if buku is None:
        abort(404)

    errors = []
    if request.method == 'POST':
        buku = ambil_form()
        buku['id_buku'] = id_buku  # ID tidak boleh diubah
        errors = validasi(buku)
        if not errors:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE buku SET judul = %s, pengarang = %s, penerbit = %s, "
                    "tahun_terbit = %s, stok = %s WHERE id_buku = %s",
                    nilai(buku),
                )
            conn.commit()
            flash('Data buku berhasil diperbarui.', 'success')
            return redirect(url_for('buku.index'))

    return render_template('buku/form.html', buku=buku, errors=errors, mode='edit')


# ---------------- DELETE ----------------
@bp.route('/<id_buku>/hapus', methods=['POST'])
def hapus(id_buku):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            jumlah = cur.execute("DELETE FROM buku WHERE id_buku = %s", (id_buku,))
        conn.commit()
        if jumlah:
            flash(f'Buku {id_buku} berhasil dihapus.', 'success')
        else:
            flash('Buku tidak ditemukan.', 'warning')
    except pymysql.err.IntegrityError as e:
        conn.rollback()
        if e.args[0] == 1451:
            flash('Buku tidak dapat dihapus karena memiliki riwayat peminjaman.', 'danger')
        else:
            raise
    return redirect(url_for('buku.index'))

from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, url_for

from db import get_db

bp = Blueprint('peminjaman', __name__, url_prefix='/peminjaman')


class GagalProses(Exception):
    """Pelanggaran aturan bisnis yang pesannya aman ditampilkan ke pengguna."""


SQL_DAFTAR = """
SELECT p.id_pinjam, a.nama, b.judul, p.tgl_pinjam, p.tgl_kembali, p.status,
       CASE WHEN p.status = 'dipinjam'
            THEN GREATEST(DATEDIFF(CURDATE(), p.tgl_pinjam) - 7, 0)
            ELSE 0 END AS hari_terlambat
FROM peminjaman p
INNER JOIN anggota a ON a.id_anggota = p.id_anggota
INNER JOIN buku b ON b.id_buku = p.id_buku
"""


# ---------------- READ ----------------
@bp.route('/')
def index():
    status = request.args.get('status', '')
    sql, params = SQL_DAFTAR, ()
    if status in ('dipinjam', 'kembali'):
        sql += " WHERE p.status = %s"
        params = (status,)
    sql += " ORDER BY p.tgl_pinjam DESC, p.id_pinjam DESC"

    with get_db().cursor() as cur:
        cur.execute(sql, params)
        daftar = cur.fetchall()
    return render_template('peminjaman/index.html', daftar=daftar, status=status)


# ---------------- CREATE ----------------
@bp.route('/tambah', methods=['GET', 'POST'])
def tambah():
    conn = get_db()
    errors = []
    data = {'id_anggota': '', 'id_buku': '', 'tgl_pinjam': date.today().isoformat()}

    if request.method == 'POST':
        data = {k: request.form.get(k, '').strip() for k in data}
        if not data['id_anggota'] or not data['id_buku']:
            errors.append('Anggota dan buku wajib dipilih.')
        try:
            date.fromisoformat(data['tgl_pinjam'])
        except ValueError:
            errors.append('Tanggal pinjam tidak valid.')

        if not errors:
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT stok FROM buku WHERE id_buku = %s FOR UPDATE",
                                (data['id_buku'],))
                    row = cur.fetchone()
                    if row is None or row['stok'] < 1:
                        raise GagalProses('Stok buku habis atau buku tidak ditemukan.')
                    cur.execute(
                        "INSERT INTO peminjaman (id_anggota, id_buku, tgl_pinjam, status) "
                        "VALUES (%s, %s, %s, 'dipinjam')",
                        (data['id_anggota'], data['id_buku'], data['tgl_pinjam']),
                    )
                    cur.execute("UPDATE buku SET stok = stok - 1 WHERE id_buku = %s",
                                (data['id_buku'],))
                conn.commit()
                flash('Peminjaman berhasil dicatat.', 'success')
                return redirect(url_for('peminjaman.index'))
            except GagalProses as ex:
                conn.rollback()
                errors.append(str(ex))
            except Exception:
                conn.rollback()
                raise

    with conn.cursor() as cur:
        cur.execute("SELECT id_anggota, nama FROM anggota ORDER BY id_anggota")
        anggota = cur.fetchall()
        cur.execute("SELECT id_buku, judul, stok FROM buku WHERE stok > 0 ORDER BY judul")
        buku = cur.fetchall()
    return render_template('peminjaman/form.html', data=data, errors=errors,
                           anggota=anggota, buku=buku)


# ---------------- UPDATE (pengembalian) ----------------
@bp.route('/<int:id_pinjam>/kembalikan', methods=['POST'])
def kembalikan(id_pinjam):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id_buku, status FROM peminjaman "
                        "WHERE id_pinjam = %s FOR UPDATE", (id_pinjam,))
            p = cur.fetchone()
            if p is None or p['status'] != 'dipinjam':
                raise GagalProses('Transaksi tidak ditemukan atau sudah dikembalikan.')
            cur.execute("UPDATE peminjaman SET status = 'kembali', tgl_kembali = CURDATE() "
                        "WHERE id_pinjam = %s", (id_pinjam,))
            cur.execute("UPDATE buku SET stok = stok + 1 WHERE id_buku = %s", (p['id_buku'],))
        conn.commit()
        flash('Buku berhasil dikembalikan.', 'success')
    except GagalProses as ex:
        conn.rollback()
        flash(str(ex), 'danger')
    except Exception:
        conn.rollback()
        raise
    return redirect(url_for('peminjaman.index'))


# ---------------- DELETE ----------------
@bp.route('/<int:id_pinjam>/hapus', methods=['POST'])
def hapus(id_pinjam):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id_buku, status FROM peminjaman "
                        "WHERE id_pinjam = %s FOR UPDATE", (id_pinjam,))
            p = cur.fetchone()
            if p is None:
                raise GagalProses('Transaksi tidak ditemukan.')
            if p['status'] == 'dipinjam':
                cur.execute("UPDATE buku SET stok = stok + 1 WHERE id_buku = %s",
                            (p['id_buku'],))
            cur.execute("DELETE FROM peminjaman WHERE id_pinjam = %s", (id_pinjam,))
        conn.commit()
        flash('Transaksi berhasil dihapus.', 'success')
    except GagalProses as ex:
        conn.rollback()
        flash(str(ex), 'danger')
    except Exception:
        conn.rollback()
        raise
    return redirect(url_for('peminjaman.index'))

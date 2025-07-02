import pandas as pd
import streamlit as st
import os
import sqlite3
from datetime import datetime

# Konfigurasi database
DB_FILE = "pengeluaran_kas.db"

# --- Fungsi Database ---
def get_connection():
    return sqlite3.connect(DB_FILE)

def setup_database():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS kas (
            id TEXT,
            tanggal TEXT,
            deskripsi_pekerjaan TEXT,
            deskripsi_pengeluaran TEXT,
            jumlah_barang INTEGER,
            unit TEXT,
            harga_per_satuan INTEGER,
            total_harga INTEGER,
            keterangan TEXT
        )
    """)
    conn.commit()
    conn.close()

setup_database()

# --- Fungsi CRUD ---
def load_data():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM kas", conn)
    df['tanggal'] = pd.to_datetime(df['tanggal'], errors='coerce')
    conn.close()
    return df


def save_data(row):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO kas (id, tanggal, deskripsi_pekerjaan, deskripsi_pengeluaran,
                         jumlah_barang, unit, harga_per_satuan, total_harga, keterangan)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", row)
    conn.commit()
    conn.close()


def delete_data_by_index(index):
    df = load_data()
    if index < len(df):
        id_to_delete = df.iloc[index]['id']
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM kas WHERE id = ?", (id_to_delete,))
        conn.commit()
        conn.close()


def update_data_by_id(data):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE kas SET
            tanggal = ?,
            deskripsi_pekerjaan = ?,
            deskripsi_pengeluaran = ?,
            jumlah_barang = ?,
            unit = ?,
            harga_per_satuan = ?,
            total_harga = ?,
            keterangan = ?
        WHERE id = ?
    """, data)
    conn.commit()
    conn.close()


# --- Fungsi Tambahan ---
def generate_id_transaksi(kode_pelanggan, tanggal, df):
    prefix = kode_pelanggan.upper() if kode_pelanggan else "X1"
    bulan_tahun = tanggal.strftime("%m%y")
    filter_prefix = prefix + bulan_tahun
    df_filtered = df[df['id'].notna() & df['id'].astype(str).str.startswith(filter_prefix)]
    nomor_urut = len(df_filtered) + 1
    nomor_urut_str = f"{nomor_urut:03d}"
    return f"{filter_prefix}{nomor_urut_str}"


def format_rupiah(x):
    try:
        if isinstance(x, (int, float)):
            return f"Rp {x:,.0f}".replace(",", ".")
        return x
    except:
        return x


# --- Fungsi Cetak ---
def print_data(df_to_print, no_voucher, nama_pengeluaran, total_pengeluaran):
    df_to_print = df_to_print.copy()
    df_to_print['harga_per_satuan'] = df_to_print['harga_per_satuan'].apply(format_rupiah)
    df_to_print['total_harga'] = df_to_print['total_harga'].apply(format_rupiah)
    total_pengeluaran_rupiah = format_rupiah(total_pengeluaran)

    html_content = df_to_print.to_html(index=False)

    full_html_page = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Voucher Pengeluaran</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1, h2, h3 {{ text-align: center; }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }}
            th {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        <h1>Voucher Pengeluaran</h1>
        <h3>No Voucher: {no_voucher}</h3>
        <h3>Nama Pengeluaran: {nama_pengeluaran}</h3>
        <h3>Total Pengeluaran: {total_pengeluaran_rupiah}</h3>
        {html_content}
    </body>
    </html>
    """

    html_path = "pengeluaran_kas_print.html"
    try:
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(full_html_page)

        with open(html_path, "r", encoding="utf-8") as f:
            html_data = f.read()

        st.download_button(
            label="📥 Download Voucher (HTML)",
            data=html_data,
            file_name="voucher_pengeluaran.html",
            mime="text/html"
        )

        st.components.v1.html(html_data, height=600, scrolling=True)

        st.success("Laporan berhasil dibuat. Silakan download untuk melihat hasilnya.")
    except Exception as e:
        st.error(f"Gagal membuat atau membuka file HTML: {e}")

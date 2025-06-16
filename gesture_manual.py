# File: gesture_manual.py

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

class ManualWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Manual Penggunaan Gestur")
        self.geometry("500x600")

        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=BOTH, expand=True)
        
        title_label = ttk.Label(main_frame, text="Panduan Gestur", font=("Helvetica", 16, "bold"))
        title_label.pack(pady=10)

        # Anda bisa menambahkan gambar atau teks detail di sini
        text_content = """
        Berikut adalah daftar gestur yang dikenali oleh aplikasi:

        - Play:
          Tunjukkan telapak tangan terbuka (5 jari).

        - Pause:
          Arahkan jempol ke bawah (Thumbs Down).

        - Aktifkan Mode Volume:
          Angkat 3 jari (Telunjuk, Tengah, Manis).
          Mode volume aktif selama 4 detik.

        - Volume Naik (+10):
          Saat mode volume aktif, arahkan jempol ke atas.

        - Volume Turun (-10):
          Saat mode volume aktif, arahkan jempol ke bawah.

        - Lagu Selanjutnya (Next):
          Gunakan gestur 'Peace' (V) dan geser ke kanan.

        - Lagu Sebelumnya (Previous):
          Gunakan gestur 'Peace' (V) dan geser ke kiri.
        """
        
        manual_text = ttk.Label(main_frame, text=text_content, justify=LEFT, font=("Helvetica", 11))
        manual_text.pack(pady=10, anchor='w')
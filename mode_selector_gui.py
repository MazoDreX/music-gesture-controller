# File: mode_selector_gui.py

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import configparser
import os
from gesture_controller_gui import GestureControllerApp
from spotify_gesture_gui import SpotifyGestureApp

class ModeSelectorApp:
    def __init__(self, master, camera_index):
        """Inisialisasi aplikasi pemilih mode."""
        self.master = master
        self.camera_index = camera_index  # Simpan indeks kamera dari GUI sebelumnya
        self.config_file = 'config.ini'
        
        self.master.title("Pilih Mode Kontrol")
        self.master.geometry("700x400")
        self.master.resizable(False, False)
        
        # --- Variabel untuk menyimpan input ---
        self.client_id_var = tk.StringVar()
        self.client_secret_var = tk.StringVar()

        # --- Buat Widget ---
        self._create_widgets()
        
        # Muat kredensial yang tersimpan saat aplikasi dimulai
        self._load_credentials()

    def _create_widgets(self):
        """Membuat semua widget untuk GUI."""
        main_frame = ttk.Frame(self.master, padding=(20, 10))
        main_frame.pack(fill=BOTH, expand=True)

        # Judul Utama
        title_label = ttk.Label(main_frame, text="Pilih Mode Kontrol yang diinginkan", font=("Helvetica", 16, "bold"))
        title_label.pack(pady=(10, 20))

        # Frame untuk dua panel pilihan
        options_frame = ttk.Frame(main_frame)
        options_frame.pack(fill=BOTH, expand=True, pady=10)

        # --- Panel Kiri: Spotify API ---
        spotify_frame = ttk.Labelframe(options_frame, text=" Menggunakan Spotify API ", padding=(20, 10))
        spotify_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 10))

        lbl_client_id = ttk.Label(spotify_frame, text="Client ID", font=("Helvetica", 10))
        lbl_client_id.pack(anchor='w', pady=(10, 2))
        entry_client_id = ttk.Entry(spotify_frame, textvariable=self.client_id_var, width=40)
        entry_client_id.pack(fill='x')

        lbl_client_secret = ttk.Label(spotify_frame, text="Client Secret", font=("Helvetica", 10))
        lbl_client_secret.pack(anchor='w', pady=(10, 2))
        entry_client_secret = ttk.Entry(spotify_frame, textvariable=self.client_secret_var, show="*", width=40)
        entry_client_secret.pack(fill='x')

        btn_start_spotify = ttk.Button(spotify_frame, text="Mulai", command=self._start_spotify_mode, style='primary.TButton')
        btn_start_spotify.pack(side=BOTTOM, pady=(20, 10), fill='x', ipady=5)


        # --- Panel Kanan: Windows Control ---
        windows_frame = ttk.Labelframe(options_frame, text=" Menggunakan Windows Control ", padding=(20, 10))
        windows_frame.pack(side=RIGHT, fill=BOTH, expand=True, padx=(10, 0))
        
        # Tambahkan label deskripsi jika perlu
        lbl_win_desc = ttk.Label(windows_frame, text="Kontrol pemutar musik apa pun\nyang sedang aktif di sistem Anda.", justify=CENTER, wraplength=250)
        lbl_win_desc.pack(pady=(20,0), fill=BOTH, expand=True)

        btn_start_windows = ttk.Button(windows_frame, text="Mulai", command=self._start_windows_mode, style='success.TButton')
        btn_start_windows.pack(side=BOTTOM, pady=(20, 10), fill='x', ipady=5)

    def _load_credentials(self):
        """Memuat Client ID dan Secret dari file config.ini."""
        if not os.path.exists(self.config_file):
            return # Jika file tidak ada, tidak melakukan apa-apa

        config = configparser.ConfigParser()
        config.read(self.config_file)
        
        if 'Spotify' in config:
            client_id = config['Spotify'].get('client_id', '')
            client_secret = config['Spotify'].get('client_secret', '')
            self.client_id_var.set(client_id)
            self.client_secret_var.set(client_secret)

    def _save_credentials(self):
        """Menyimpan Client ID dan Secret ke file config.ini."""
        config = configparser.ConfigParser()
        config['Spotify'] = {
            'client_id': self.client_id_var.get(),
            'client_secret': self.client_secret_var.get()
        }
        with open(self.config_file, 'w') as f:
            config.write(f)
        print(f"Kredensial disimpan ke {self.config_file}")

    def _launch_windows_app(self):
        self.master.withdraw()
        main_app_window = tk.Toplevel(self.master)
        GestureControllerApp(main_app_window, self.camera_index, 'windows')

    def _launch_spotify_app(self):
        client_id = self.client_id_var.get()
        client_secret = self.client_secret_var.get()

        if not client_id or not client_secret:
            from tkinter import messagebox
            messagebox.showerror("Error", "Client ID dan Client Secret tidak boleh kosong untuk mode Spotify.")
            return
        
        print(f"Meluncurkan aplikasi utama dengan mode: spotify")
        self.master.withdraw()
        main_app_window = tk.Toplevel(self.master)
        SpotifyGestureApp(main_app_window, self.camera_index, client_id, client_secret)


    def _start_spotify_mode(self):
        """Aksi saat tombol 'Mulai' untuk Spotify ditekan."""
        self._save_credentials()
        
        print("--- Memulai Aplikasi ---")
        print(f"Mode Kontrol: Spotify API")
        print(f"Kamera yang digunakan: Kamera {self.camera_index}")
        self._launch_spotify_app()
        

    def _start_windows_mode(self):
        """Aksi saat tombol 'Mulai' untuk Windows Control ditekan."""
        print("--- Memulai Aplikasi ---")
        print(f"Mode Kontrol: Windows Control")
        print(f"Kamera yang digunakan: Kamera {self.camera_index}")
        self._launch_windows_app()

# File: camera_selector_gui.py

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import cv2
from PIL import Image, ImageTk
from mode_selector_gui import ModeSelectorApp # <-- IMPORT FILE BARU

class CameraSelectorApp:
    # ... (Semua kode dari __init__ hingga _update_feed tetap sama)
    def __init__(self, master):
        self.master = master
        self.master.title("Pemilih Kamera - Kontrol Gestur")
        self.master.geometry("860x520")
        self.master.resizable(False, False)
        self.cap = None
        self.camera_list = []
        self.is_camera_testing = False
        self.selected_camera_index = tk.IntVar(value=-1)
        self.left_frame = ttk.Frame(self.master, padding=(20, 10))
        self.left_frame.pack(side=LEFT, fill=Y)
        self.right_frame = ttk.Frame(self.master, padding=(10, 10))
        self.right_frame.pack(side=RIGHT, fill=BOTH, expand=True)
        self._find_available_cameras()
        self._create_left_panel_widgets()
        self._create_right_panel_widgets()
        self.master.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _find_available_cameras(self):
        index = 0
        while True:
            cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
            if cap.isOpened():
                self.camera_list.append(f"Kamera {index}")
                cap.release()
                index += 1
            else:
                cap.release()
                break
        if not self.camera_list:
            self.camera_list.append("Tidak ada kamera ditemukan")

    def _create_left_panel_widgets(self):
        lbl_select = ttk.Label(self.left_frame, text="Pilih Kamera", font=("Helvetica", 12, "bold"))
        lbl_select.pack(pady=(10, 5), anchor='w')
        self.combo_camera = ttk.Combobox(self.left_frame, values=self.camera_list, state="readonly", width=25)
        self.combo_camera.pack(pady=5, fill='x')
        if "Tidak ada kamera ditemukan" not in self.camera_list:
            self.combo_camera.current(0)
        self.btn_test = ttk.Button(self.left_frame, text="Tes Kamera", command=self._toggle_camera_test, style='primary.TButton')
        self.btn_test.pack(pady=(20, 10), fill='x', ipady=5)
        self.btn_next = ttk.Button(self.left_frame, text="Selanjutnya", command=self._proceed_to_next, style='success.TButton', state=DISABLED)
        self.btn_next.pack(pady=10, fill='x', ipady=5)
        if "Tidak ada kamera ditemukan" in self.camera_list:
            self.btn_test.config(state=DISABLED)

    def _create_right_panel_widgets(self):
        lbl_camera_title = ttk.Label(self.right_frame, text="Kamera", font=("Helvetica", 12, "bold"))
        lbl_camera_title.pack(pady=(0, 5))
        self.camera_label = ttk.Label(self.right_frame, background="black")
        self.camera_label.pack(fill=BOTH, expand=True)

    def _toggle_camera_test(self):
        if self.is_camera_testing:
            self.is_camera_testing = False
            self.btn_test.config(text="Tes Kamera")
            if self.cap: self.cap.release()
            self.camera_label.config(image='', background="black")
            self.btn_next.config(state=DISABLED)
        else:
            selection = self.combo_camera.get()
            if "Kamera" in selection:
                self.selected_camera_index.set(int(selection.split()[-1]))
                self.cap = cv2.VideoCapture(self.selected_camera_index.get(), cv2.CAP_DSHOW)
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                if self.cap.isOpened():
                    self.is_camera_testing = True
                    self.btn_test.config(text="Hentikan Tes")
                    self.btn_next.config(state=NORMAL)
                    self._update_feed()

    def _update_feed(self):
        if not self.is_camera_testing or not self.cap.isOpened(): return
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.flip(frame, 1)
            cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(cv2image)
            imgtk = ImageTk.PhotoImage(image=img)
            self.camera_label.imgtk = imgtk
            self.camera_label.configure(image=imgtk)
        self.master.after(10, self._update_feed)

    def _proceed_to_next(self):
        """Fungsi untuk melanjutkan ke GUI pemilihan mode."""
        camera_idx = self.selected_camera_index.get()
        print(f"Kamera {camera_idx} dipilih. Melanjutkan ke pemilihan mode...")

        # Hentikan feed kamera saat ini
        if self.is_camera_testing:
            self.is_camera_testing = False
            if self.cap:
                self.cap.release()
        
        # Sembunyikan jendela saat ini
        self.master.withdraw()
        
        # Buat jendela baru untuk pemilihan mode
        mode_window = tk.Toplevel(self.master)
        ModeSelectorApp(mode_window, camera_idx) # Kirim indeks kamera ke GUI baru

    def _on_closing(self):
        """Aksi yang harus dilakukan sebelum jendela ditutup."""
        print("Menutup aplikasi dan melepaskan sumber daya kamera...")
        if self.cap and self.cap.isOpened():
            self.cap.release()
        self.master.destroy()
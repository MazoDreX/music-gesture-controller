# File: gesture_controller_gui.py

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import cv2
from PIL import Image, ImageTk
import time
import numpy as np

# Impor semua modul yang dibutuhkan
import HandTrackingModule as htm
import pyautogui
import pygame
try:
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    PYCAW_AVAILABLE = True
except (ImportError, OSError):
    PYCAW_AVAILABLE = False

# Impor jendela manual
from gesture_manual import ManualWindow

class GestureControllerApp:
    def __init__(self, master, camera_index, mode):
        self.master = master
        self.camera_index = camera_index
        self.mode = mode # 'windows' atau 'spotify'

        self.master.title("Music Gesture Controller")
        self.master.geometry("1024x600")
        
        # --- Inisialisasi Logika dari windows_control.py ---
        self._initialize_logic()

        # --- Buat Widget GUI ---
        self._create_widgets()
        
        # Mulai loop utama untuk update frame
        self._update_frame_and_gestures()
        
        self.master.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _initialize_logic(self):
        """Inisialisasi semua variabel dan objek dari skrip logika."""
        self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        self.cap.set(3, 640)
        self.cap.set(4, 480)
        
        self.detector = htm.handDetector(detectionCon=0.75, maxHands=1)

        # Variabel Status
        self.pTime = 0
        self.last_action_time = 0
        self.ACTION_COOLDOWN = 1.5
        self.hand_center_x_history = []
        self.SWIPE_THRESHOLD = 80
        self.is_volume_mode = False
        self.volume_mode_timeout = 0
        self.VOLUME_MODE_DURATION = 4.0

        # Inisialisasi Volume Control
        self.volume_control_enabled = False
        if PYCAW_AVAILABLE:
            try:
                devices = AudioUtilities.GetSpeakers()
                interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                self.volume = cast(interface, POINTER(IAudioEndpointVolume))
                self.volRange = self.volume.GetVolumeRange()
                self.minVol, self.maxVol = self.volRange[0], self.volRange[1]
                self.volume_control_enabled = True
            except Exception as e:
                print(f"Gagal menginisialisasi Pycaw: {e}")

        # Inisialisasi Suara
        pygame.mixer.init()
        try:
            self.sound_volume = pygame.mixer.Sound("Sounds/sfx-1.wav")
            self.sound_play_pause = pygame.mixer.Sound("Sounds/sfx-2.wav")
            self.sound_next_prev = pygame.mixer.Sound("Sounds/sfx-3.wav")
        except pygame.error:
            class DummySound:
                def play(self): pass
            self.sound_volume = self.sound_play_pause = self.sound_next_prev = DummySound()

    def _create_widgets(self):
        """Membuat semua widget GUI."""
        main_frame = ttk.Frame(self.master, padding=20)
        main_frame.pack(fill=BOTH, expand=True)

        # --- Panel Kiri (Kontrol) ---
        left_panel = ttk.Frame(main_frame)
        left_panel.pack(side=LEFT, fill=Y, padx=(0, 20))

        title_label = ttk.Label(left_panel, text="Music Gesture Controller", font=("Helvetica", 16, "bold"))
        title_label.pack(anchor='w', pady=(0, 20))

        btn_manual = ttk.Button(left_panel, text="Manual", command=self._open_manual_window, style='primary.TButton')
        btn_manual.pack(fill='x', ipady=5, pady=(0, 30))

        recog_label = ttk.Label(left_panel, text="Recognized Gesture", font=("Helvetica", 12, "bold"))
        recog_label.pack(anchor='w', pady=(10, 5))

        self.recognized_gesture_var = tk.StringVar(value="---")
        recog_entry = ttk.Entry(left_panel, textvariable=self.recognized_gesture_var, state="readonly", justify=CENTER, font=("Helvetica", 11))
        recog_entry.pack(fill='x', ipady=5)

        # --- Panel Tengah (Volume Bar) ---
        mid_panel = ttk.Frame(main_frame)
        mid_panel.pack(side=LEFT, fill=Y, padx=(0, 20))

        self.volume_var = tk.DoubleVar()
        volume_bar = ttk.Progressbar(mid_panel, variable=self.volume_var, orient=VERTICAL, length=400, mode='determinate')
        volume_bar.pack(fill=Y, expand=True)
        
        vol_bar_label = ttk.Label(mid_panel, text="Volume Bar")
        vol_bar_label.pack(pady=5)


        # --- Panel Kanan (Kamera) ---
        right_panel = ttk.Frame(main_frame)
        right_panel.pack(side=LEFT, fill=BOTH, expand=True)

        camera_title_label = ttk.Label(right_panel, text="Kamera", font=("Helvetica", 12, "bold"))
        camera_title_label.pack(pady=(0, 5))

        self.camera_label = ttk.Label(right_panel, background="black")
        self.camera_label.pack(fill=BOTH, expand=True)

    def _update_frame_and_gestures(self):
        """Metode ini menggantikan 'while True' dari skrip asli."""
        success, img = self.cap.read()
        if not success:
            self.master.after(15, self._update_frame_and_gestures)
            return

        img = cv2.flip(img, 1)
        img_for_detection = img.copy() # Gunakan copy untuk deteksi agar gambar asli tidak dimodifikasi
        
        img_for_detection = self.detector.findHands(img_for_detection)
        lmList = self.detector.findPosition(img_for_detection, draw=False)

        # --- Logika Gestur (hampir sama seperti windows_control.py) ---
        current_time = time.time()
        action_text = ""

        if self.is_volume_mode and current_time > self.volume_mode_timeout:
            self.is_volume_mode = False
            action_text = "Volume Mode OFF"

        if lmList:
            fingers = self.detector.fingersUp()

            print(f"Finger: {fingers}")
            
            # Deteksi jempol
            thumbs_up = fingers == [1, 0, 0, 0, 0] and lmList[4][2] < lmList[2][2]
            thumbs_down = fingers == [1, 0, 0, 0, 0] and lmList[4][2] > lmList[2][2]
            
            if self.is_volume_mode:
                action_text = "VOL MODE"
                if thumbs_up and (current_time - self.last_action_time > self.ACTION_COOLDOWN):
                    self.set_volume_percentage(self.get_current_volume_percentage() + 10)
                    action_text = "Vol +10"
                    self.sound_volume.play()
                    self.last_action_time = current_time
                    self.volume_mode_timeout = current_time + self.VOLUME_MODE_DURATION
                elif thumbs_down and (current_time - self.last_action_time > self.ACTION_COOLDOWN):
                    self.set_volume_percentage(self.get_current_volume_percentage() - 10)
                    action_text = "Vol -10"
                    self.sound_volume.play()
                    self.last_action_time = current_time
                    self.volume_mode_timeout = current_time + self.VOLUME_MODE_DURATION
            else:
                if fingers == [0, 1, 1, 1, 0] and (current_time - self.last_action_time > self.ACTION_COOLDOWN):
                    self.is_volume_mode = True
                    self.volume_mode_timeout = current_time + self.VOLUME_MODE_DURATION
                    action_text = "Volume Mode ON"
                    self.sound_volume.play()
                    self.last_action_time = current_time
                elif fingers == [0, 0, 0, 0, 0] and (current_time - self.last_action_time > self.ACTION_COOLDOWN): # PLAY GESTURE diubah ke 5 jari
                    action_text = "PLAY"
                    pyautogui.press('playpause')
                    self.sound_play_pause.play()
                    self.last_action_time = current_time
                elif thumbs_down and (current_time - self.last_action_time > self.ACTION_COOLDOWN):
                    action_text = "PAUSE"
                    pyautogui.press('playpause')
                    self.sound_play_pause.play()
                    self.last_action_time = current_time
                elif fingers == [0, 1, 1, 0, 0] and (current_time - self.last_action_time > self.ACTION_COOLDOWN):
                    # ... (logika swipe)
                    hand_center_x = lmList[9][1]; self.hand_center_x_history.append(hand_center_x)
                    if len(self.hand_center_x_history) > 10:
                        dx = self.hand_center_x_history[-1] - self.hand_center_x_history[0]; key = None
                        if dx > self.SWIPE_THRESHOLD: action_text, key = "NEXT TRACK", 'nexttrack'
                        elif dx < -self.SWIPE_THRESHOLD: action_text, key = "PREV TRACK", 'prevtrack'
                        if key: pyautogui.press(key); self.sound_next_prev.play(); self.last_action_time = current_time; self.hand_center_x_history.clear()
                    if not action_text: action_text = "Ready to Swipe"
                else: self.hand_center_x_history.clear()

        # --- Update GUI ---
        if action_text:
            self.recognized_gesture_var.set(action_text)

        # Update Volume Bar
        if self.volume_control_enabled:
            current_vol = self.get_current_volume_percentage()
            self.volume_var.set(current_vol)

        # Update Camera Feed
        cv2image = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(cv2image)
        imgtk = ImageTk.PhotoImage(image=img_pil)


        self.camera_label.imgtk = imgtk
        self.camera_label.configure(image=imgtk)

        # Jadwalkan frame berikutnya
        self.master.after(15, self._update_frame_and_gestures)

    def _open_manual_window(self):
        """Membuka jendela manual."""
        ManualWindow(self.master)

    def _on_closing(self):
        """Aksi sebelum jendela ditutup."""
        print("Menutup aplikasi utama...")
        self.cap.release()
        pygame.mixer.quit()
        self.master.destroy()
        
    # --- Fungsi bantuan dari skrip asli ---
    def get_current_volume_percentage(self):
        if not self.volume_control_enabled: return 0
        current_level = self.volume.GetMasterVolumeLevel()
        return np.interp(current_level, [self.minVol, self.maxVol], [0, 100])

    def set_volume_percentage(self, percentage):
        if not self.volume_control_enabled: return
        percentage = np.clip(percentage, 0, 100)
        level = np.interp(percentage, [0, 100], [self.minVol, self.maxVol])
        self.volume.SetMasterVolumeLevel(level, None)
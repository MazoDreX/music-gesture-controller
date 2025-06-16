import cv2
import time
import numpy as np
import HandTrackingModule as htm
import pyautogui
import pygame
import pycaw

# --- Inisialisasi (tetap sama) ---
# ... (Semua kode inisialisasi tidak berubah)
wCam, hCam = 640, 480
pTime = 0
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
cap.set(3, wCam)
cap.set(4, hCam)
detector = htm.handDetector(detectionCon=0.75, maxHands=1)

pygame.mixer.init()
try:
    sound_volume = pygame.mixer.Sound("Sounds/sfx-1.wav")
    sound_play_pause = pygame.mixer.Sound("Sounds/sfx-2.wav")
    sound_next_prev = pygame.mixer.Sound("Sounds/sfx-3.wav")
except pygame.error as e:
    print(f"Error loading sound files: {e}")
    class DummySound:
        def play(self): pass
    sound_volume = sound_play_pause = sound_next_prev = DummySound()

try:
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))
    volRange = volume.GetVolumeRange()
    minVol, maxVol = volRange[0], volRange[1]
    volume_control_enabled = True
except (ImportError, OSError) as e:
    print(f"Could not initialize volume control: {e}")
    volume_control_enabled = False
# ... (akhir inisialisasi)


# --- Variabel Status (tetap sama) ---
last_action_time = 0
ACTION_COOLDOWN = 1.5
hand_center_x_history = []
SWIPE_THRESHOLD = 80
is_volume_mode = False
volume_mode_timeout = 0
VOLUME_MODE_DURATION = 4.0

# --- Fungsi Bantuan Volume (tetap sama) ---
def get_current_volume_percentage():
    if not volume_control_enabled: return 0
    current_level = volume.GetMasterVolumeLevel()
    return np.interp(current_level, [minVol, maxVol], [0, 100])

def set_volume_percentage(percentage):
    if not volume_control_enabled: return
    percentage = np.clip(percentage, 0, 100)
    level = np.interp(percentage, [0, 100], [minVol, maxVol])
    volume.SetMasterVolumeLevel(level, None)

# --- FUNGSI DETEKSI JEMPOL BARU ---
def is_thumbs_up(fingers, lmList):
    # Kondisi: hanya jempol terangkat DAN ujung jempol (4) di atas pangkalnya (2)
    return fingers == [1, 0, 0, 0, 0] and lmList[4][2] < lmList[2][2]

def is_thumbs_down(fingers, lmList):
    # Kondisi: hanya jempol terangkat DAN ujung jempol (4) di bawah pangkalnya (2)
    return fingers == [1, 0, 0, 0, 0] and lmList[4][2] > lmList[2][2]


# --- Loop Utama ---
while True:
    success, img = cap.read()
    if not success: break
    
    img = cv2.flip(img, 1)
    img = detector.findHands(img)
    lmList = detector.findPosition(img, draw=False)

    current_time = time.time()
    action_text = ""

    if is_volume_mode and current_time > volume_mode_timeout:
        is_volume_mode = False
        action_text = "Volume Mode OFF"

    if lmList:
        fingers = detector.fingersUp()
        print(f"Fingers: {fingers}, Is Thumbs Up: {is_thumbs_up(fingers, lmList)}, Is Thumbs Down: {is_thumbs_down(fingers, lmList)}")
        
        if is_volume_mode:
            action_text = "VOL MODE"
            
            # 1. NAIKKAN VOLUME (Thumbs Up)
            if is_thumbs_up(fingers, lmList) and (current_time - last_action_time > ACTION_COOLDOWN):
                current_vol = get_current_volume_percentage()
                set_volume_percentage(current_vol + 10)
                action_text = "Vol +10"
                sound_volume.play()
                last_action_time = current_time
                volume_mode_timeout = current_time + VOLUME_MODE_DURATION

            # 2. TURUNKAN VOLUME (Thumbs Down)
            elif is_thumbs_down(fingers, lmList) and (current_time - last_action_time > ACTION_COOLDOWN):
                current_vol = get_current_volume_percentage()
                set_volume_percentage(current_vol - 10)
                action_text = "Vol -10"
                sound_volume.play()
                last_action_time = current_time
                volume_mode_timeout = current_time + VOLUME_MODE_DURATION
        
        else: # Jika tidak sedang dalam mode volume
            # 1. AKTIVASI MODE VOLUME (Tiga Jari Tengah)
            if fingers == [0, 1, 1, 1, 0] and (current_time - last_action_time > ACTION_COOLDOWN):
                is_volume_mode = True
                volume_mode_timeout = current_time + VOLUME_MODE_DURATION
                action_text = "Volume Mode ON"
                sound_volume.play()
                last_action_time = current_time

            # 2. GESTUR PLAY
            elif fingers == [0, 0, 0, 0, 0] and (current_time - last_action_time > ACTION_COOLDOWN):
                action_text = "PLAY"
                pyautogui.press('playpause')
                sound_play_pause.play()
                last_action_time = current_time

            # 3. GESTUR PAUSE (Kembali ke Thumbs Down yang andal)
            elif is_thumbs_down(fingers, lmList) and (current_time - last_action_time > ACTION_COOLDOWN):
                 action_text = "PAUSE"
                 pyautogui.press('playpause')
                 sound_play_pause.play()
                 last_action_time = current_time

            # 4. GESTUR SWIPE (Peace Sign)
            elif fingers == [0, 1, 1, 0, 0] and (current_time - last_action_time > ACTION_COOLDOWN):
                # ... (logika swipe tidak berubah)
                hand_center_x = lmList[9][1]
                hand_center_x_history.append(hand_center_x)
                if len(hand_center_x_history) > 10: 
                    start_x, end_x = hand_center_x_history[0], hand_center_x_history[-1]
                    dx = end_x - start_x
                    key = None
                    if dx > SWIPE_THRESHOLD:
                        action_text, key = "NEXT TRACK", 'nexttrack'
                    elif dx < -SWIPE_THRESHOLD:
                        action_text, key = "PREV TRACK", 'prevtrack'
                    if key:
                        pyautogui.press(key)
                        sound_next_prev.play()
                        last_action_time = current_time
                        hand_center_x_history.clear()
                if not action_text: action_text = "Ready to Swipe"
                if len(hand_center_x_history) > 20: hand_center_x_history.pop(0)
            
            else:
                 hand_center_x_history.clear()

    # --- VISUALISASI (Tidak ada perubahan) ---
    # ... (sisa kode visualisasi tetap sama)
    if volume_control_enabled:
        currentVolPer = get_current_volume_percentage()
        volBar = np.interp(currentVolPer, [0, 100], [400, 150])
        cv2.rectangle(img, (50, 150), (85, 400), (255, 0, 0), 3)
        cv2.rectangle(img, (50, int(volBar)), (85, 400), (0, 255, 0), cv2.FILLED)
        cv2.putText(img, f'{int(currentVolPer)} %', (40, 450), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 2)
    if is_volume_mode:
        cv2.putText(img, "VOL MODE ACTIVE", (wCam - 350, 100), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 2)
    if action_text:
        cv2.putText(img, action_text, (50, 100), cv2.FONT_HERSHEY_PLAIN, 3, (255, 0, 0), 3)
    cTime = time.time()
    fps = 1 / (cTime - pTime)
    pTime = cTime
    cv2.putText(img, f'FPS: {int(fps)}', (wCam - 150, 50), cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 0), 2)
    cv2.imshow("Advanced Gesture Control", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
pygame.mixer.quit()
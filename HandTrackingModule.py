import cv2
import mediapipe as mp
import time
import math # Diperlukan untuk kalkulasi jarak

class handDetector():
    def __init__(self, mode=False, maxHands=1, modelComplexity=1, detectionCon=0.5, trackCon=0.5): # maxHands diubah ke 1 untuk konsistensi
        self.mode = mode
        self.maxHands = maxHands
        self.modelComplex = modelComplexity
        self.detectionCon = detectionCon
        self.trackCon = trackCon

        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands(
            static_image_mode=self.mode,
            max_num_hands=self.maxHands,
            model_complexity=self.modelComplex,
            min_detection_confidence=self.detectionCon,
            min_tracking_confidence=self.trackCon)
        self.mpDraw = mp.solutions.drawing_utils

        self.tipIds = [4, 8, 12, 16, 20]
        self.lmList = []

    def findHands(self, img, draw=True):
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(imgRGB)

        if self.results.multi_hand_landmarks:
            for handLms in self.results.multi_hand_landmarks:
                if draw:
                    self.mpDraw.draw_landmarks(img, handLms, self.mpHands.HAND_CONNECTIONS)
        return img

    def findPosition(self, img, handNo=0, draw=True):
        self.lmList = []
        if self.results.multi_hand_landmarks:
            myHand = self.results.multi_hand_landmarks[handNo]
            for id, lm in enumerate(myHand.landmark):
                h, w, c = img.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                self.lmList.append([id, cx, cy])
                if draw:
                    cv2.circle(img, (cx, cy), 7, (255, 0, 0), cv2.FILLED)
        return self.lmList

    # --- FUNGSI fingersUp() YANG SUDAH DIPERBAIKI ---
    def fingersUp(self):
        """
        Mengecek jari mana saja yang terangkat menggunakan logika yang lebih andal.
        Memperhitungkan gambar yang di-flip oleh skrip utama.
        """
        fingers = []
        if not self.lmList:
            return []

        # 1. Jempol (Thumb)
        # Logika untuk jempol yang terentang. Ini hanya langkah pertama.
        # Skrip utama akan memeriksa posisi Y untuk membedakan atas/bawah.
        # Untuk tangan kanan di depan kamera (yang tampak seperti tangan kiri setelah di-flip),
        # ujung jempol akan memiliki koordinat X lebih KECIL dari sendi di bawahnya.
        if self.lmList[self.tipIds[0]][1] < self.lmList[self.tipIds[0] - 1][1]:
            fingers.append(1)
        else:
            fingers.append(0)

        # 2. Empat Jari Lainnya (Telunjuk, Tengah, Manis, Kelingking)
        # Logika ini sudah andal: cek apakah ujung jari berada di atas sendi di bawahnya.
        # Di OpenCV, "di atas" berarti nilai Y lebih kecil.
        for id in range(1, 5):
            if self.lmList[self.tipIds[id]][2] < self.lmList[self.tipIds[id] - 2][2]:
                fingers.append(1)
            else:
                fingers.append(0)

        return fingers

    def findDistance(self, p1_id, p2_id, img, draw=True, r=10, t=2):
        length = 0
        info = []
        if self.lmList:
            x1, y1 = self.lmList[p1_id][1], self.lmList[p1_id][2]
            x2, y2 = self.lmList[p2_id][1], self.lmList[p2_id][2]
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

            if draw:
                cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), t)
                cv2.circle(img, (x1, y1), r, (255, 0, 255), cv2.FILLED)
                cv2.circle(img, (x2, y2), r, (255, 0, 255), cv2.FILLED)
                cv2.circle(img, (cx, cy), r, (0, 0, 255), cv2.FILLED)

            length = math.hypot(x2 - x1, y2 - y1)
            info = [x1, y1, x2, y2, cx, cy]
        
        return length, img, info

# Fungsi main untuk testing modul secara mandiri
def main():
    pTime = 0
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    detector = handDetector(detectionCon=0.7)

    while True:
        success, img = cap.read()
        if not success: break
        
        img = cv2.flip(img, 1) # Tambahkan flip di sini agar sama dengan skrip utama
        img = detector.findHands(img)
        lmList = detector.findPosition(img, draw=False)

        if lmList:
            fingers = detector.fingersUp()
            print(f"Fingers Up: {fingers}") # Sekarang hasil print akan akurat

        cTime = time.time()
        fps = 1 / (cTime - pTime)
        pTime = cTime
        cv2.putText(img, f'FPS: {int(fps)}', (10, 70), cv2.FONT_HERSHEY_PLAIN, 3, (255, 0, 255), 3)

        cv2.imshow("Hand Tracking Module Test", img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
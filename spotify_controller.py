import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
import threading
from queue import Queue

class SpotifyController:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = 'http://127.0.0.1:8888/spotify-api/callback/'
        self.scope = "user-read-playback-state,user-modify-playback-state"
        self.sp = None
        self.is_authenticated = False
        self._authenticate()

        self.command_queue = Queue()
        self.worker_thread = None
        self.is_running = False

        self.current_volume = 50
        self.is_playing = False

    def start(self):
        if self._authenticate():
            self.is_running = True
            self.worker_thread = threading.Thread(target=self._run, daemon=True)
            self.worker_thread.start()
            return True
        return False

    def _authenticate(self):
        """Melakukan otentikasi dengan Spotify."""
        try:
            auth_manager = SpotifyOAuth(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri,
                scope=self.scope,
                open_browser=True # Otomatis buka browser untuk login pertama kali
            )
            self.sp = spotipy.Spotify(auth_manager=auth_manager)
            self.sp.current_user()
            self.is_authenticated = True
            print("Otentikasi Spotify berhasil.")
            return True
        except Exception as e:
            print(f"Gagal otentikasi Spotify: {e}")
            self.is_authenticated = False
            return False
        
    def stop(self):
        """Menghentikan thread pekerja."""
        self.is_running = False
        if self.worker_thread:
            self.worker_thread.join()

    def _run(self):
        """Loop utama yang berjalan di thread terpisah."""
        status_update_interval = 1.0  # Detik, seberapa sering update status
        last_status_update = 0

        while self.is_running:
            # 1. Proses perintah dari antrian
            if not self.command_queue.empty():
                command = self.command_queue.get()
                if command == "play_pause": self._play_pause_action()
                elif command == "next": self._next_track_action()
                elif command == "previous": self._previous_track_action()
                elif isinstance(command, tuple) and command[0] == "set_volume":
                    self._set_volume_action(command[1])

            # 2. Update status secara berkala
            if time.time() - last_status_update > status_update_interval:
                self._update_status()
                last_status_update = time.time()
            
            time.sleep(0.05) # Beri jeda kecil agar tidak membebani CPU

    def _is_active(self):
        """Mengecek apakah ada lagu yang sedang aktif/diputar."""
        if not self.sp: return None
        try:
            return self.sp.current_playback()
        except Exception:
            return None

    def _play_pause_action(self):
        """Memainkan lagu jika sedang di-pause, atau sebaliknya. Dieksekusi oleh worker."""
        if not self.sp: return
        try:
            # Kita tidak perlu menggunakan variabel self.is_playing di sini,
            # lebih baik dapatkan status terbaru langsung sebelum bertindak.
            playback = self._is_active()
            if playback and playback['is_playing']:
                self.sp.pause_playback()
                print("Spotify: Paused")
                self.is_playing = False
            elif playback:
                self.sp.start_playback()
                print("Spotify: Playing")
                self.is_playing = True
        except Exception as e:
            print(f"Error pada aksi play/pause: {e}")

    def _next_track_action(self):
        if not self.sp: return
        self.sp.next_track()
        print("Spotify: Next Track")

    def _previous_track_action(self):
        if not self.sp: return
        self.sp.previous_track()
        print("Spotify: Previous Track")

    def _set_volume_action(self, level): self.sp.volume(int(max(0, min(100, level))))

    def _update_status(self):
        """Memperbarui variabel state dari API Spotify."""
        try:
            playback = self.sp.current_playback()
            if playback and playback.get('device'):
                self.current_volume = playback['device'].get('volume_percent', self.current_volume)
                self.is_playing = playback.get('is_playing', self.is_playing)
        except Exception as e:
            print(f"Error updating Spotify status: {e}")

    # --- Fungsi Publik (dipanggil oleh GUI untuk mengirim perintah) ---
    def play_pause(self): self.command_queue.put("play_pause")
    def next_track(self): self.command_queue.put("next")
    def previous_track(self): self.command_queue.put("previous")
    def set_volume(self, level): self.command_queue.put(("set_volume", level))
    
    # --- Fungsi Getter (mendapat data dari variabel, BUKAN API langsung) ---
    def get_volume(self): return self.current_volume
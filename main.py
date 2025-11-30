import json
import os
import threading
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton, MDFillRoundFlatIconButton, MDIconButton, MDFlatButton, MDFillRoundFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.list import MDList, TwoLineAvatarIconListItem, IconLeftWidget, IRightBodyTouch
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.dialog import MDDialog
from kivymd.uix.progressbar import MDProgressBar
from kivy.clock import Clock
from kivy.utils import platform
from kivy.core.audio import SoundLoader 
from kivy.network.urlrequest import UrlRequest
from pytube import YouTube

# --- SETTING SERVER ---
URL_CONFIG = "https://gist.githubusercontent.com/ytdownloadermhr/..." # Pastikan ini link kamu

# --- KONFIGURASI FILE LOKAL ---
PATH_DOWNLOAD = "/storage/emulated/0/Download"
FILE_RIWAYAT = os.path.join(PATH_DOWNLOAD, "autotube_history.json")
FILE_CONFIG = os.path.join(PATH_DOWNLOAD, "autotube_config.json")
FILE_PENDING = os.path.join(PATH_DOWNLOAD, "autotube_pending.json")

class TombolHapus(IRightBodyTouch, MDIconButton):
    pass

class MainApp(MDApp):
    sound = None
    dialog_pilihan = None
    loading_dialog = None
    progress_dialog = None
    ad_data = {} 

    def build(self):
        self.theme_cls.primary_palette = "Red"
        self.theme_cls.theme_style = "Light"
        screen = MDScreen()
        layout = MDBoxLayout(orientation='vertical', spacing=10)
        
        # 1. HEADER
        header = MDCard(size_hint_y=None, height=60, elevation=2)
        header.add_widget(MDLabel(text="AutoTube Pro", halign="center", font_style="H5", theme_text_color="Primary"))
        layout.add_widget(header)
        
        # 2. LABEL ERROR (Untuk Debugging)
        self.error_label = MDLabel(
            text="Siap", 
            halign="center", 
            theme_text_color="Custom",
            text_color=(0,0,0,0.5),
            font_style="Caption",
            size_hint_y=None,
            height=30
        )
        layout.add_widget(self.error_label)

        # 3. TOMBOL KONTROL
        control_box = MDBoxLayout(orientation='vertical', adaptive_height=True, padding=20, spacing=15)
        self.status_label = MDLabel(text="Pilih Mode:", halign="center", font_style="Subtitle1")
        
        btn_mp3 = MDFillRoundFlatIconButton(
            text="START AUTO MP3", icon="music-note", 
            pos_hint={'center_x': 0.5}, size_hint_x=0.9,
            on_release=lambda x: self.set_mode_service("mp3")
        )
        
        btn_video = MDFillRoundFlatIconButton(
            text="START VIDEO MODE", icon="youtube", 
            pos_hint={'center_x': 0.5}, size_hint_x=0.9,
            md_bg_color=(0, 0, 0.8, 1),
            on_release=lambda x: self.set_mode_service("mp4")
        )
        
        btn_stop = MDRaisedButton(
            text="STOP SERVICE", md_bg_color=(1, 0, 0, 1),
            pos_hint={'center_x': 0.5},
            on_release=self.stop_service
        )

        control_box.add_widget(self.status_label)
        control_box.add_widget(btn_mp3)
        control_box.add_widget(btn_video)
        control_box.add_widget(btn_stop)
        layout.add_widget(control_box)

        # 4. RIWAYAT
        layout.add_widget(MDLabel(text="  Riwayat Download:", size_hint_y=None, height=30))
        scroll = MDScrollView()
        self.history_list = MDList()
        scroll.add_widget(self.history_list)
        layout.add_widget(scroll)

        screen.add_widget(layout)
        return screen

    def on_start(self):
        # Meminta Izin Android
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.WRITE_EXTERNAL_STORAGE, 
                Permission.READ_EXTERNAL_STORAGE,
                Permission.FOREGROUND_SERVICE
            ])
        Clock.schedule_once(self.mulai_aplikasi, 1)

    def mulai_aplikasi(self, dt):
        try:
            UrlRequest(URL_CONFIG, on_success=self.update_config_server)
            Clock.schedule_interval(self.muat_riwayat, 2)
            Clock.schedule_interval(self.cek_antrean_video, 3)
        except Exception as e:
            self.error_label.text = f"Err Start: {str(e)}"

    def update_config_server(self, req, result):
        if result.get('status') == 'aktif':
            self.ad_data = result
            self.status_label.text = "Siap Digunakan."

    # --- BAGIAN INI YANG KITA PERBAIKI (MENGGUNAKAN INTENT) ---
    def set_mode_service(self, mode):
        try:
            # 1. Simpan Config Mode
            with open(FILE_CONFIG, 'w') as f:
                json.dump({"mode": mode}, f)
            
            # 2. Update Teks UI
            if mode == "mp3":
                self.status_label.text = "🔥 AUTO MP3 AKTIF"
                self.status_label.text_color = (0, 1, 0, 1)
            else:
                self.status_label.text = "🎬 VIDEO MODE AKTIF"
                self.status_label.text_color = (0, 0, 1, 1)
                
            # 3. Jalankan Service dengan INTENT (Cara Baru)
            if platform == 'android':
                from jnius import autoclass
                
                # Mengambil Kelas Activity Utama
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                mActivity = PythonActivity.mActivity
                Intent = autoclass('android.content.Intent')
                
                # Nama Paket Service (PENTING: Harus sesuai buildozer.spec)
                # org.autotube + autotubepro + ServiceMService (Kivy menambahkan 'Service' + nama file kapital)
                service_class_name = 'org.autotube.autotubepro.ServiceMService'
                service_class = autoclass(service_class_name)
                
                # Membuat Intent untuk memulai service
                intent = Intent(mActivity, service_class)
                
                # Menambahkan argumen (opsional)
                intent.putExtra("python_service_argument", "somestring")
                
                # Start Service (Foreground)
                mActivity.startService(intent)
                
                self.error_label.text = "Service Berjalan..."
                
        except Exception as e:
            # Tampilkan detail error jika gagal lagi
            self.error_label.text = f"Gagal Service: {e}"
            print(f"DEBUG ERROR: {e}")

    def stop_service(self, *args):
        self.status_label.text = "⛔ Service Berhenti"
        self.status_label.text_color = (0, 0, 0, 1)
        # Di Android, mematikan service biasanya cukup dengan mematikan app dari recent apps
        # atau kita bisa mengirim sinyal stop lewat file, tapi untuk sekarang UI saja cukup.

    # --- FUNGSI PENDUKUNG LAIN (TETAP SAMA) ---
    def muat_riwayat(self, dt):
        if not os.path.exists(FILE_RIWAYAT): return
        try:
            with open(FILE_RIWAYAT, 'r') as f: data = json.load(f)
            if len(data) == len(self.history_list.children): return
            self.history_list.clear_widgets()
            for i, item in enumerate(reversed(data)):
                idx_asli = len(data) - 1 - i
                list_item = TwoLineAvatarIconListItem(text=item['judul'], secondary_text=item['status'])
                icon_play = IconLeftWidget(icon="play-circle")
                icon_play.bind(on_release=lambda x, p=item.get('file_path'): self.putar_musik(p))
                btn_hapus = TombolHapus(icon="trash-can")
                btn_hapus.bind(on_release=lambda x, idx=idx_asli: self.hapus_file(idx))
                list_item.add_widget(icon_play)
                list_item.add_widget(btn_hapus)
                self.history_list.add_widget(list_item)
        except: pass

    def putar_musik(self, path):
        try:
            if self.sound: self.sound.stop()
            if path and os.path.exists(path):
                self.sound = SoundLoader.load(path)
                if self.sound: self.sound.play()
        except: pass

    def hapus_file(self, index):
        try:
            with open(FILE_RIWAYAT, 'r') as f: data = json.load(f)
            file_path = data[index].get('file_path')
            if file_path and os.path.exists(file_path): os.remove(file_path)
            del data[index]
            with open(FILE_RIWAYAT, 'w') as f: json.dump(data, f)
            self.history_list.clear_widgets()
        except: pass

    def cek_antrean_video(self, dt):
        if os.path.exists(FILE_PENDING):
            try:
                with open(FILE_PENDING, 'r') as f: data = json.load(f)
                os.remove(FILE_PENDING)
                self.tampilkan_pilihan_kualitas(data['url'])
            except: pass

    def tampilkan_pilihan_kualitas(self, url):
        self.loading_dialog = MDDialog(text="Menganalisis Link...")
        self.loading_dialog.open()
        threading.Thread(target=self.analisis_youtube, args=(url,)).start()

    def analisis_youtube(self, url):
        try:
            yt = YouTube(url)
            streams = yt.streams.filter(progressive=True)
            res720 = streams.filter(res="720p").first()
            res360 = streams.filter(res="360p").first()
            Clock.schedule_once(lambda x: self.buka_popup_pilihan(yt, res720, res360), 0)
        except Exception as e:
            Clock.schedule_once(lambda x: self.loading_dialog.dismiss(), 0)
            Clock.schedule_once(lambda x: setattr(self.error_label, 'text', f"Err YT: {str(e)}"), 0)

    def buka_popup_pilihan(self, yt, s720, s360):
        self.loading_dialog.dismiss()
        box = MDBoxLayout(orientation="vertical", spacing=10, size_hint_y=None, height=180)
        if s720:
            box.add_widget(MDFillRoundFlatButton(
                text=f"HD 720p ({s720.filesize_mb:.1f}MB)", pos_hint={'center_x': 0.5}, md_bg_color=(0,0.7,0,1),
                on_release=lambda x: self.mulai_download_foreground(s720, yt.title, "720p")))
        if s360:
            box.add_widget(MDFlatButton(
                text=f"SD 360p ({s360.filesize_mb:.1f}MB)", pos_hint={'center_x': 0.5},
                on_release=lambda x: self.mulai_download_foreground(s360, yt.title, "360p")))
        self.dialog_pilihan = MDDialog(title=f"Download: {yt.title[:20]}...", type="custom", content_cls=box)
        self.dialog_pilihan.open()

    def mulai_download_foreground(self, stream, judul, kualitas):
        self.dialog_pilihan.dismiss()
        self.progress_bar = MDProgressBar(value=0)
        self.progress_dialog = MDDialog(title=f"Downloading {kualitas}...", type="custom", content_cls=self.progress_bar)
        self.progress_dialog.open()
        threading.Thread(target=self.eksekusi_download, args=(stream, judul, kualitas)).start()

    def eksekusi_download(self, stream, judul, kualitas):
        try:
            def on_progress(chunk, file_handle, bytes_remaining):
                total_size = stream.filesize
                bytes_downloaded = total_size - bytes_remaining
                persen = (bytes_downloaded / total_size) * 100
                Clock.schedule_once(lambda x: setattr(self.progress_bar, 'value', persen), 0)

            stream.on_progress = on_progress
            file_path = stream.download(output_path=PATH_DOWNLOAD)
            
            data_baru = {"judul": judul, "status": f"Selesai ({kualitas})", "file_path": file_path}
            list_data = []
            if os.path.exists(FILE_RIWAYAT):
                with open(FILE_RIWAYAT, 'r') as f: list_data = json.load(f)
            list_data.append(data_baru)
            with open(FILE_RIWAYAT, 'w') as f: json.dump(list_data, f)
            Clock.schedule_once(lambda x: self.progress_dialog.dismiss(), 0)
        except Exception as e:
            Clock.schedule_once(lambda x: self.progress_dialog.dismiss(), 0)
            Clock.schedule_once(lambda x: setattr(self.error_label, 'text', f"Err Down: {str(e)}"), 0)

if __name__ == '__main__':
    MainApp().run()

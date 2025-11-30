import json
import os
import threading
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton, MDFillRoundFlatIconButton, MDIconButton, MDFlatButton, MDFillRoundFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.textfield import MDTextField
from kivymd.uix.list import MDList, TwoLineAvatarIconListItem, IconLeftWidget, IRightBodyTouch
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.dialog import MDDialog
from kivymd.uix.progressbar import MDProgressBar
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.utils import platform
from kivy.core.audio import SoundLoader 
from kivy.network.urlrequest import UrlRequest
from pytube import YouTube

# --- CONFIG SERVER ---
URL_CONFIG = "https://gist.githubusercontent.com/ytdownloadermhr/..." # Pastikan link benar

# --- FUNGSI PATH ---
def dapatkan_path_private():
    if platform == 'android':
        try:
            from jnius import autoclass
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            return PythonActivity.mActivity.getExternalFilesDir(None).getAbsolutePath()
        except: return "."
    return "." 

PATH_DOWNLOAD = "/storage/emulated/0/Download" 
PATH_INTERNAL = dapatkan_path_private()        

FILE_RIWAYAT = os.path.join(PATH_INTERNAL, "autotube_history.json")
FILE_CONFIG = os.path.join(PATH_INTERNAL, "autotube_config.json")

class TombolHapus(IRightBodyTouch, MDIconButton):
    pass

class MainApp(MDApp):
    sound = None
    dialog_pilihan = None
    loading_dialog = None
    progress_dialog = None
    link_terakhir_di_cek = ""

    def build(self):
        self.theme_cls.primary_palette = "Red"
        screen = MDScreen()
        layout = MDBoxLayout(orientation='vertical', spacing=10)
        
        # 1. Header
        header = MDCard(size_hint_y=None, height=60, elevation=2)
        header.add_widget(MDLabel(text="AutoTube Pro", halign="center", font_style="H5", theme_text_color="Primary"))
        layout.add_widget(header)
        
        # 2. Status / Input Manual
        input_box = MDBoxLayout(orientation='vertical', adaptive_height=True, padding=20, spacing=10)
        
        self.input_link = MDTextField(
            hint_text="Tempel Link YouTube Disini...",
            mode="rectangle"
        )
        
        btn_manual = MDRaisedButton(
            text="DOWNLOAD MANUAL",
            size_hint_x=1,
            on_release=lambda x: self.cek_manual()
        )
        
        self.status_label = MDLabel(
            text="Copy link, lalu buka aplikasi ini.", 
            halign="center", 
            theme_text_color="Hint",
            font_style="Caption"
        )
        
        input_box.add_widget(self.input_link)
        input_box.add_widget(btn_manual)
        input_box.add_widget(self.status_label)
        layout.add_widget(input_box)

        # 3. Riwayat
        layout.add_widget(MDLabel(text="  Riwayat Download:", size_hint_y=None, height=30))
        scroll = MDScrollView()
        self.history_list = MDList()
        scroll.add_widget(self.history_list)
        layout.add_widget(scroll)

        screen.add_widget(layout)
        
        # BINDING PENTING
        Window.bind(on_resume=self.cek_clipboard_otomatis)
        
        return screen

    def on_start(self):
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE])
        Clock.schedule_once(self.setup_awal, 1)

    def setup_awal(self, dt):
        UrlRequest(URL_CONFIG, on_success=self.dummy_update)
        Clock.schedule_interval(self.muat_riwayat, 2)
        # Cek clipboard dengan delay sedikit agar UI siap dulu
        Clock.schedule_once(self.cek_clipboard_otomatis, 1)

    def dummy_update(self, req, result):
        pass

    # --- FUNGSI BARU: BACA CLIPBOARD ANTI-CRASH ---
    def ambil_clipboard_aman(self):
        if platform == 'android':
            try:
                # Menggunakan JNIUS langsung ke Android (Lebih Stabil)
                from jnius import autoclass, cast
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                Context = autoclass('android.content.Context')
                activity = PythonActivity.mActivity
                clipboard = activity.getSystemService(Context.CLIPBOARD_SERVICE)
                
                # Cek apakah ada isinya
                if clipboard.hasPrimaryClip():
                    item = clipboard.getPrimaryClip().getItemAt(0)
                    teks = item.getText()
                    if teks:
                        return teks.toString()
            except Exception as e:
                print(f"Clipboard Error: {e}")
                return ""
        else:
            # Untuk Komputer
            try:
                from kivy.core.clipboard import Clipboard
                return Clipboard.paste()
            except: return ""
        return ""

    def cek_clipboard_otomatis(self, *args):
        # Gunakan fungsi aman yang baru kita buat
        isi_clipboard = self.ambil_clipboard_aman()

        # Validasi Link
        if isi_clipboard and ("youtube.com" in isi_clipboard or "youtu.be" in isi_clipboard):
            if isi_clipboard != self.link_terakhir_di_cek:
                self.link_terakhir_di_cek = isi_clipboard
                self.input_link.text = isi_clipboard
                # Munculkan status dulu
                self.status_label.text = "Link Terdeteksi! Memproses..."
                self.tampilkan_pilihan_kualitas(isi_clipboard)

    def cek_manual(self):
        link = self.input_link.text
        if "youtube.com" in link or "youtu.be" in link:
            self.tampilkan_pilihan_kualitas(link)
        else:
            self.status_label.text = "Link tidak valid!"

    # --- LOGIKA DOWNLOAD ---
    def tampilkan_pilihan_kualitas(self, url):
        # Tutup dialog lama jika ada (mencegah tumpuk)
        if self.loading_dialog: self.loading_dialog.dismiss()
        
        self.loading_dialog = MDDialog(text="Menganalisis Link...")
        self.loading_dialog.open()
        threading.Thread(target=self.analisis_youtube, args=(url,)).start()

    def analisis_youtube(self, url):
        try:
            yt = YouTube(url)
            audio = yt.streams.filter(only_audio=True).first()
            video = yt.streams.filter(res="720p", progressive=True).first()
            Clock.schedule_once(lambda x: self.buka_popup_pilihan(yt, video), 0)
        except Exception as e:
            Clock.schedule_once(lambda x: self.loading_dialog.dismiss(), 0)
            Clock.schedule_once(lambda x: setattr(self.status_label, 'text', "Gagal Analisis. Coba Manual."), 0)

    def buka_popup_pilihan(self, yt, video_stream):
        if self.loading_dialog: self.loading_dialog.dismiss()
        
        box = MDBoxLayout(orientation="vertical", spacing=10, size_hint_y=None, height=180)
        
        box.add_widget(MDFillRoundFlatIconButton(
            text="DOWNLOAD MP3 (Musik)", icon="music-note",
            pos_hint={'center_x': 0.5}, size_hint_x=1,
            on_release=lambda x: self.mulai_download(yt, "mp3", None)
        ))

        if video_stream:
            box.add_widget(MDFillRoundFlatIconButton(
                text=f"DOWNLOAD VIDEO 720p ({video_stream.filesize_mb:.1f} MB)", icon="video",
                pos_hint={'center_x': 0.5}, size_hint_x=1, md_bg_color=(0,0,1,1),
                on_release=lambda x: self.mulai_download(yt, "mp4", video_stream)
            ))
        else:
             box.add_widget(MDLabel(text="Video 720p Tidak Tersedia", halign="center"))

        self.dialog_pilihan = MDDialog(title=f"{yt.title[:30]}...", type="custom", content_cls=box)
        self.dialog_pilihan.open()

    def mulai_download(self, yt, tipe, stream_obj):
        self.dialog_pilihan.dismiss()
        self.progress_bar = MDProgressBar(value=0)
        self.progress_dialog = MDDialog(title="Mendownload...", type="custom", content_cls=self.progress_bar)
        self.progress_dialog.open()
        threading.Thread(target=self.eksekusi_download, args=(yt, tipe, stream_obj)).start()

    def eksekusi_download(self, yt, tipe, stream_obj):
        try:
            stream = yt.streams.filter(only_audio=True).first() if tipe == "mp3" else stream_obj

            def on_progress(chunk, file_handle, bytes_remaining):
                total = stream.filesize
                now = total - bytes_remaining
                persen = (now / total) * 100
                Clock.schedule_once(lambda x: setattr(self.progress_bar, 'value', persen), 0)

            stream.on_progress = on_progress
            out_file = stream.download(output_path=PATH_DOWNLOAD)

            final_path = out_file
            if tipe == "mp3":
                base, ext = os.path.splitext(out_file)
                new_file = base + '.mp3'
                os.rename(out_file, new_file)
                final_path = new_file

            self.simpan_riwayat(yt.title, f"Sukses ({tipe})", final_path)
            Clock.schedule_once(lambda x: self.progress_dialog.dismiss(), 0)
            Clock.schedule_once(lambda x: setattr(self.status_label, 'text', "Download Selesai!"), 0)

        except Exception as e:
            Clock.schedule_once(lambda x: self.progress_dialog.dismiss(), 0)
            Clock.schedule_once(lambda x: setattr(self.status_label, 'text', "Gagal Download"), 0)

    def simpan_riwayat(self, judul, status, path):
        data_baru = {"judul": judul, "status": status, "file_path": path}
        list_data = []
        if os.path.exists(FILE_RIWAYAT):
            try:
                with open(FILE_RIWAYAT, 'r') as f: list_data = json.load(f)
            except: pass
        list_data.append(data_baru)
        with open(FILE_RIWAYAT, 'w') as f: json.dump(list_data, f)

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
        if self.sound: self.sound.stop()
        if path and os.path.exists(path):
            self.sound = SoundLoader.load(path)
            if self.sound: self.sound.play()

    def hapus_file(self, index):
        try:
            with open(FILE_RIWAYAT, 'r') as f: data = json.load(f)
            file_path = data[index].get('file_path')
            if file_path and os.path.exists(file_path): os.remove(file_path)
            del data[index]
            with open(FILE_RIWAYAT, 'w') as f: json.dump(data, f)
            self.history_list.clear_widgets()
        except: pass

if __name__ == '__main__':
    MainApp().run()

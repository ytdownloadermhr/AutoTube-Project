import time
import json
import os
from pytube import YouTube
from jnius import autoclass
from plyer import notification

# Path
PATH_DOWNLOAD = "/storage/emulated/0/Download"
FILE_RIWAYAT = os.path.join(PATH_DOWNLOAD, "autotube_history.json")
FILE_CONFIG = os.path.join(PATH_DOWNLOAD, "autotube_config.json")
FILE_PENDING = os.path.join(PATH_DOWNLOAD, "autotube_pending.json")

# Clipboard Android
PythonService = autoclass('org.kivy.android.PythonService')
Context = autoclass('android.content.Context')

def get_clipboard_text():
    try:
        service = PythonService.mService
        clipboard = service.getSystemService(Context.CLIPBOARD_SERVICE)
        clip_data = clipboard.getPrimaryClip()
        if clip_data is not None and clip_data.getItemCount() > 0:
            return clip_data.getItemAt(0).getText().toString()
    except:
        pass
    return ""

def download_mp3_auto(url):
    try:
        notification.notify(title="AutoTube", message="Mendownload MP3...", app_name="AutoTube")
        yt = YouTube(url)
        audio = yt.streams.filter(only_audio=True).first()
        out_file = audio.download(output_path=PATH_DOWNLOAD)
        
        base, ext = os.path.splitext(out_file)
        new_file = base + '.mp3'
        os.rename(out_file, new_file)
        
        # Simpan Riwayat
        data = {"judul": yt.title, "status": "Selesai (MP3)", "file_path": new_file}
        list_data = []
        if os.path.exists(FILE_RIWAYAT):
            try:
                with open(FILE_RIWAYAT, 'r') as f: list_data = json.load(f)
            except: pass
        list_data.append(data)
        with open(FILE_RIWAYAT, 'w') as f: json.dump(list_data, f)
        
        notification.notify(title="SUKSES!", message=f"{yt.title}", app_name="AutoTube")
    except:
        notification.notify(title="Gagal", message="Cek Link/Koneksi", app_name="AutoTube")

def kirim_ke_antrean(url):
    with open(FILE_PENDING, 'w') as f:
        json.dump({"url": url}, f)
    notification.notify(title="Link Video!", message="Buka App untuk Pilih Resolusi", app_name="AutoTube")

if __name__ == '__main__':
    link_terakhir = ""
    while True:
        try:
            isi = get_clipboard_text()
            if ("youtube.com" in isi or "youtu.be" in isi) and isi != link_terakhir:
                link_terakhir = isi
                
                mode = "mp3"
                if os.path.exists(FILE_CONFIG):
                    try:
                        with open(FILE_CONFIG, 'r') as f: 
                            mode = json.load(f).get("mode", "mp3")
                    except: pass
                
                if mode == "mp3":
                    download_mp3_auto(isi)
                else:
                    kirim_ke_antrean(isi)
            time.sleep(2)
        except:
            time.sleep(2)

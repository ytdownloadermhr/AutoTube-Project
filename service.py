import time
import json
import os
from pytube import YouTube
from jnius import autoclass
from plyer import notification

# --- FUNGSI PATH (AGAR SINKRON DENGAN MAIN APP) ---
def dapatkan_path_private():
    # Service pakai 'PythonService', bukan 'PythonActivity'
    try:
        PythonService = autoclass('org.kivy.android.PythonService')
        # getExternalFilesDir(None)
        return PythonService.mService.getExternalFilesDir(None).getAbsolutePath()
    except:
        return "." 

PATH_DOWNLOAD = "/storage/emulated/0/Download"
PATH_INTERNAL = dapatkan_path_private()

FILE_RIWAYAT = os.path.join(PATH_INTERNAL, "autotube_history.json")
FILE_CONFIG = os.path.join(PATH_INTERNAL, "autotube_config.json")
FILE_PENDING = os.path.join(PATH_INTERNAL, "autotube_pending.json")

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
        
        simpan_riwayat(yt.title, "Selesai (MP3)", new_file)
        notification.notify(title="SUKSES!", message=f"{yt.title}", app_name="AutoTube")
    except Exception as e:
        notification.notify(title="Gagal", message=str(e)[:30], app_name="AutoTube")

def simpan_riwayat(judul, status, path):
    data_baru = {"judul": judul, "status": status, "file_path": path}
    list_data = []
    if os.path.exists(FILE_RIWAYAT):
        try:
            with open(FILE_RIWAYAT, 'r') as f: list_data = json.load(f)
        except: pass
    list_data.append(data_baru)
    with open(FILE_RIWAYAT, 'w') as f: json.dump(list_data, f)

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
                # Baca config dari folder internal yang aman
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

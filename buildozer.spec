[app]
title = AutoTube Pro
package.name = autotubepro
package.domain = org.autotube
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 1.0

# PERUBAHAN PENTING:
# 1. Update Kivy ke 2.3.0 (Lebih baru & stabil)
# 2. HAPUS 'openssl' dari daftar (Biar gak bentrok)
requirements = python3,kivy==2.3.0,kivymd,pytube,plyer,requests,urllib3,chardet,idna,pyjnius

orientation = portrait
fullscreen = 0
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,FOREGROUND_SERVICE,WAKE_LOCK,ACCESS_NETWORK_STATE
android.api = 31
android.minapi = 21
android.accept_sdk_license = True

# Service Background
services = mService:service.py

# KITA HAPUS BARIS 'p4a.branch' AGAR PAKAI VERSI STABIL

[buildozer]
log_level = 2
warn_on_root = 1

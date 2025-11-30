[app]
title = AutoTube Pro
package.name = autotubepro
package.domain = org.autotube
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 1.0
requirements = python3,kivy==2.2.0,kivymd,pytube,plyer,requests,urllib3,chardet,idna,openssl,pyjnius
orientation = portrait
fullscreen = 0
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,FOREGROUND_SERVICE,WAKE_LOCK,ACCESS_NETWORK_STATE
android.api = 31
android.minapi = 21
android.accept_sdk_license = True
services = mService:service.py
p4a.branch = develop

[buildozer]
log_level = 2
warn_on_root = 1

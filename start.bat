@echo off
title gpt_image_2_openai_public-8170
cd /d "%~dp0"
set PYTHONDONTWRITEBYTECODE=1
set "APP_URL=http://127.0.0.1:8170/"
start "" powershell -NoProfile -WindowStyle Hidden -Command "$url=$env:APP_URL; for($i=0; $i -lt 30; $i++){ try { $r=Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 1; if($r.StatusCode -ge 200){ Start-Process $url; break } } catch {}; Start-Sleep -Seconds 1 }"
python app.py
pause


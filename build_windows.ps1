Set-Location $PSScriptRoot
python -m pip install -r requirements.txt pyinstaller
python -m PyInstaller --noconfirm --onedir --windowed --name PolarRename --icon PolarRename.ico --add-data 'PolarRename.ico;.' --add-data 'PolarRename.png;.' polarrename.py

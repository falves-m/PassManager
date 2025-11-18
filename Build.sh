#!/bin/bash

spinner() {
	local pid=$1
	local i=1
	local sp="/-\|"
	echo -n ' '
	# Tant que le processus existe
	while kill -0 "$pid" 2>/dev/null; do
		printf "\b${sp:i++%${#sp}:1}"
		sleep 0.05
	done
	echo
}

echo "Installing dependecies..."
pip install -r requirements.txt >/dev/null 2>&1 &
spinner $!

echo "Creating config file..."
mkdir ~/.local/share/PassManager >/dev/null 2>&1 &
spinner $!

echo "Compiling program..."
python3 -m PyInstaller --name PassManager --onefile --distpath ./bin --noconfirm main.py >/dev/null 2>&1 &
spinner $!

cat >~/.local/share/applications/passmanager.desktop <<EOF
[Desktop Entry]
Type=Application
Name=PassManager
Comment=Gestionnaire de mots de passe
Exec=$PWD/bin/PassManager
Icon=$PWD/icon.png
Terminal=false
Categories=Utility;Security;
EOF

chmod +x ~/.local/share/applications/passmanager.desktop

echo "PassManager is now available !"

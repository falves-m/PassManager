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

echo "Removing all added files in folder"
rm -rf ./bin main.spec ./build ./dist >/dev/null 2>&1 &
spinner $!

echo "Removing from desktop"
rm -f ~/.local/share/applications/passmanager.desktop >/dev/null 2>&1 &
spinner $!

echo "PassManager is uninstalled !"

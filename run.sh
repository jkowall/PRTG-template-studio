#!/bin/bash
set -e

# Ensure script directory is current working directory
cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
    echo "[-] Virtual environment not found. Creating..."
    python3 -m venv venv
    echo "[+] venv created."
    
    echo "[-] Installing requirements..."
    ./venv/bin/pip install -r requirements.txt
    echo "[+] Requirements installed."
fi

echo "[*] Starting PRTG Template Studio..."
./venv/bin/python app.py "$@"

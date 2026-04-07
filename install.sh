#!/bin/bash

# Detect Operating System
OS_TYPE=$(uname -o)

echo "--- GPG Vault Setup ---"

if [[ "$OS_TYPE" == *"Android"* ]]; then
    echo "[*] Android (Termux) detected."
    pkg update && pkg upgrade -y
    pkg install -y python gnupg termux-api
    echo "[!] IMPORTANT: Please install the 'Termux:API' app from F-Droid or Play Store."

elif [[ "$OS_TYPE" == "GNU/Linux" ]]; then
    echo "[*] Linux system detected."
    sudo apt update
    sudo apt install -y python3 gnupg
    
    if [ "$XDG_SESSION_TYPE" == "wayland" ]; then
        echo "[*] Installing wl-clipboard for Wayland..."
        sudo apt install -y wl-clipboard
    else
        echo "[*] Installing xclip for X11..."
        sudo apt install -y xclip
    fi
else
    echo "[!] System not automatically supported. Please install python3 and gnupg manually."
fi

# Add GPG_TTY to bashrc for terminal password prompts
if [ -f ~/.bashrc ]; then
    echo "" >> ~/.bashrc
    echo "# GPG Vault Configuration" >> ~/.bashrc
    echo "export GPG_TTY=\$(tty)" >> ~/.bashrc
    echo "[+] GPG_TTY added to your .bashrc"
fi

echo "--- Setup Complete ---"
echo "Next steps:"
echo "1. Import your GPG keys: gpg --import your_private_key.asc"
echo "2. Set your recipient email: export VAULT_RECIPIENT='your@email.com' in your .bashrc"
echo "3. gpg --edit-key "your@mail.com" -> trust -> 5 -> y -> quit
echo "4. Create your alias in ~/.bashrc alias vault='python3 ~/path/to/your/vault.py'"
echo "5. Run the vault: python3 vault.py or vault"

# PyGPG-Vault
Minimalist, secure, and cross-platform password manager powered by GPG encryption. No cloud.

## Features
* **Strong Encryption**: GnuPG (GPG) protection at rest.
* **Auto-Gen**: 25-character complex passwords generated on the fly.
* **Smart Search**: Find by name, index, or difflib matching.
* **Auto-Cleanup**: Clipboard and terminal cleared after 15s.
* **Visual Mode**: Use `-v` to display passwords instead of copying.

## Best Practices
1. **Tool Suggestion**: Use **[Syncthing](https://syncthing.net/)** to keep your vault and script automatically updated across all your devices (PC, Android, etc.).
2. **The Golden Rule of Backup**: 
   * Save your **private key** (`private_key.asc`) in a separate, secure physical location (like an encrypted USB drive or a safe).
   * **Never** store your private key in the same directory as your `.vault.gpg`.
   * **Never** upload your private key to a cloud service or in mail.
3. **Disaster Recovery**:
   * If you lose your `.vault.gpg` or fail your password entry three times (depending on your GPG agent settings), your access is locked or destroyed. 
   * Always keep a backup copy of `.vault.gpg` in a different "sync repertory" to restore it if an accident happens.
4. **Folder Separation (Propagation Logic)**: 
   * **Keep your Originals Offline**: Maintain your primary `.vault.gpg` in a secure, non-synced folder.
   * **Propagate Copies Only**: When you want to update your devices, manually copy the vault to your Syncthing folder.
   * **Sync Content**: Only sync the vault and the script. Keep keys and backups strictly offline and separate to avoid accidental exposure or sync conflicts.

4. **Important Notes**:
    * Mobile/Termux: The automatic 'cachetime' is often unreliable due to aggressive OS power management.
    * Safe Exit: It is highly recommended to manually exit the script using 'q' to force a disconnect and ensure your vault is locked.

# Quick Start Summary
Recommended: Perform your GPG key generation and initial vault setup (adding passwords) on a PC/Linux system before syncing to mobile devices.
1. **Installation**: Ensure **Python 3.x** and **GnuPG** are installed. You can run `./setup.sh` to automate package installation, read the script to do it manually.
2. **GPG**: Generate your key pair using `gpg --full-generate-key`. Set trust to level 5 using `gpg --edit-key your@email.com`.
3. **Config**: Set your GPG email in the `RECIPIENT` variable inside `vault.py` and `export export GPG_TTY=$(tty)` in your `.bashrc`

# Platform Guides Installation

## Linux (Manual)
* **Installation**: Use your package manager to install `python3` and `gnupg`.
* **Debian/Ubuntu**: `sudo apt install -y python3 gnupg`.
* **Arch Linux**: `sudo pacman -S python gnupg`.

## Android (Manual)
* **Installation**: Install **Termux** and the **Termux:API** app via **F-Droid**. 
   * *Note*: Avoid the Play Store version (obsolete, no clipboard support).
* **Packages**: On **Termux**, you will have a Linux terminalRun:
    ```bash
    pkg update && pkg upgrade -y
    pkg install -y python gnupg termux-api
    ```

## iOS Setup (Manual)
* Install `iSH`
* **Packages**:
    ```bash
    apk update
    apk add python3 gnupg
    pip3 install clipboard
    ```

## macOS Setup (Manual)
**Note**: Too complex for me, too many solutions and none are simple. Google it or ask to a LLM and feed him with my code
* **Clipboard**: No extra configuration is needed as the script uses the built-in `pbcopy` command.
* **Verification**: Just run `python3 vault.py`. If you have the dependencies installed, it just works.

# Key Generation
```bash
# Generate key if needed
gpg --full-generate-key
# Trust your key (trust > 5 > y)
gpg --edit-key your@mail.com
```

## Key Management
In case your device becomes inaccessible, broken, or corrupted, you **must** have a backup of your keys and your `.vault.gpg` file. You can zip it with strong password avoid same as your vault.
1. Export Public and Private Key:
    ```bash
    gpg --armor --export your@email.com > public.asc
    gpg --armor --export-secret-keys your@email.com > private.asc
    ```
After exporting your keys, you can to move them to your mobile device or secure backup

3. Key Migration (New Device)
To access your vault on a multiple device, do not generate a new key:
    * Transfer your .asc files via USB/Cable or Syncthing (do not use Mail/Cloud)
    * Run installation
    * Import your original keys:

    ```bash
    # Import your keys from a secure USB Cable or with Syncthing
    gpg --import my_private_key.asc
    gpg --import my_public_key.asc

    # Set trust level to 'Ultimate' (required for script automation)
    gpg --edit-key "your@mail.com"
    # Type: trust -> 5 -> y -> quit
    
    # Security: remove the files after import
    rm my_private_key.asc my_public_key.asc
    ```
4. Do the configuration

# GPG Vault: Configuration

## Create an Alias (Fast Launch) and export
To launch your vault by simply typing `vault` instead of the full Python command, add an alias to your shell profile.

1. **Open your profile**:
   - For most users (Bash): `vim ~/.bashrc`
   - For macOS/Zsh users: `vim ~/.zshrc`

2. **Add this line at the end**:
   ```bash
   export GPG_TTY=$(tty)
   alias vault='python3 /path/to/your/vault.py'
   ```

3. Apply the change:

    ```bash
    source ~/.bashrc  # or source ~/.zshrc
    ```

3. Give execution right:

    ```bash
    chmod +x ~/path/to/your/vault.py
    ```

## Configuring GPG Cache (Passphrase Timeout)
If you don't want to type your master passphrase every time you open the vault, you can configure the `gpg-agent` cache duration.

1. Edit the configuration file:
   ```bash
   vim ~/.gnupg/gpg-agent.conf
   ```

2. Add or modify these lines (values are in seconds):
    ```bash
    default-cache-ttl 3600 # Cache the passphrase for 1 hour (3600 seconds)
    max-cache-ttl 7200 # Maximum cache time of 2 hours
    ```

3. Restart the GPG agent to apply changes:
    ```bash
    gpg-connect-agent reloadagent /bye
    ```

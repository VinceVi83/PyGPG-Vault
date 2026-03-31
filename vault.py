#!/usr/bin/env python3

# Copyright 2026 VinceVi83 <vincent@nguyen.lt>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

import os, subprocess, getpass, sys, difflib, secrets, string, time, shutil, json
from datetime import datetime

# CONFIGURATION
# Note: On Ubuntu, ~/.vault.gpg is used. On Android, check the path.
VAULT_FILE = os.path.expanduser("~/.vault.gpg")
RECIPIENT = "your@mail.com"

# ln -s ~/storage/document/SyncDir/.vault.gpg ~/.vault.gpg
# sudo apt update
# sudo apt install python3 gnupg
# gpg --import my_private_key.asc
# gpg --import my_public_key.asc
# Add export GPG_TTY=$(tty) to your ~/.bashrc to ensure the password prompt works in the terminal.
# gpg --edit-key "your@mail.com" -> trust -> 5 -> y -> quit

class VaultManager:
    """Vault Manager Class
    
    Role: Manages vault operations including secure password generation, clipboard operations, and GPG encrypted storage.
    
    Methods:
        generate_secure_password(length=20) : Generate a secure password with a given length.
        smart_copy(text) : Support clipboard operations across platforms.
        secure_exit() : Clear the clipboard and exit the program.
        _select_entry(data, search_term=None, action="select") : Centralized search engine for display, edit, and delete.
        display_vault(data, search_term, force_visual=False) : Display vault entries.
        edit_entry(data) : Edit a vault entry.
        delete_entry(data) : Delete a vault entry.
        get_confirmed_password() : Generate and confirm a secure password with dynamic length support.
        load_vault() : Load the vault from encrypted file.
        save_vault(data_list) : Save the vault to encrypted file.
        _perform_migration(stdout) : Internal helper to convert legacy text format to JSON objects.
    """

    @staticmethod
    def generate_secure_password(length=20):
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        while True:
            pwd = ''.join(secrets.choice(alphabet) for _ in range(length))
            if (any(c.islower() for c in pwd) and any(c.isupper() for c in pwd) and 
                any(c.isdigit() for c in pwd) and any(c in "!@#$%^&*" for c in pwd)):
                return pwd

    @staticmethod
    def smart_copy(text):
        text = text.strip().replace('\ufeff', '')
        try:
            if shutil.which("clip.exe"):
                process = subprocess.Popen(['clip.exe'], stdin=subprocess.PIPE)
                process.communicate(input=text.encode('utf-16-le'))
                return "Windows"
            elif shutil.which("pbcopy"):
                process = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
                process.communicate(input=text.encode('utf-8'))
                return "macOS"
            elif shutil.which("termux-clipboard-set"):
                subprocess.run(['termux-clipboard-set'], input=text.encode('utf-8'))
                return "Android"
            elif shutil.which("wl-copy"):
                subprocess.run(['wl-copy'], input=text.encode('utf-8'))
                return "Linux(Wayland)"
            elif shutil.which("xclip"):
                subprocess.run(['xclip', '-selection', 'clipboard'], input=text.encode('utf-8'))
                return "Linux(X11)"
            
            try:
                import clipboard
                clipboard.set(text)
                return "iOS"
            except ImportError: pass
        except: pass
        return None

    @staticmethod
    def secure_exit():
        VaultManager.smart_copy("")
        os.system('clear' if os.name == 'posix' else 'cls')
        print("\n[!] Vault closed & clipboard cleared.")
        print("\n" + "!"*45)
        print(" [REMINDER - MOBILE SECURITY]")
        print(" The automatic 'cachetime' is not reliable.")
        print(" To ensure your vault is locked, you MUST")
        print(" exit the script using 'q' to disconnect.")
        print("!"*45)
        print("End.")
        sys.exit(0)

    @staticmethod
    def _select_entry(data, search_term=None, action="select"):
        if not data:
            print("[!] Vault is empty.")
            return None

        if search_term is None:
            prompt = f"Search service to {action} (Leave empty to list all): "
            search_term = input(prompt).strip()
            
            if not search_term:
                print(f"\n--- Available services to {action} ---")
                for i, e in enumerate(data, 1):
                    print(f" [{i:2}] {e['service']}")
                
                sel = input(f"\nSelect number to {action} (or Enter to cancel): ").strip()
                if sel.isdigit() and 0 < int(sel) <= len(data):
                    return int(sel) - 1
                return None

        names = [entry['service'] for entry in data]
        
        if search_term.isdigit():
            idx = int(search_term) - 1
            return idx if 0 <= idx < len(data) else None

        matches = [i for i, n in enumerate(names) if search_term.lower() in n.lower()]
        
        if not matches:
            close_names = difflib.get_close_matches(search_term, names, n=3, cutoff=0.6)
            matches = [names.index(c) for c in close_names]

        if not matches:
            print(f"[!] No service found matching '{search_term}'.")
            return None

        if len(matches) == 1:
            return matches[0]
        
        print(f"\nMultiple matches found for '{search_term}':")
        for i, idx in enumerate(matches, 1):
            print(f" [{i}] {names[idx]} (User: {data[idx]['user']})")
        
        sel = input(f"\nSelect number to {action} (or Enter to cancel): ").strip()
        if sel.isdigit() and 0 < int(sel) <= len(matches):
            return matches[int(sel)-1]
        
        return None

    @staticmethod
    def display_vault(data, search_term, force_visual=False):
        idx = VaultManager._select_entry(data, search_term, "display")
        if idx is not None:
            entry = data[idx]
            print(f"\nService: {entry['service']} | User: {entry['user']}")
            if 'updated_at' in entry:
                print(f"Last updated: {entry['updated_at']}")
            
            pwd = entry['password']
            if force_visual:
                print(f"PASSWORD: {pwd}")
                VaultManager.smart_copy("")
            else:
                env = VaultManager.smart_copy(pwd)
                print(f"[OK] Copied to {env}.") if env else print(f"PASSWORD: {pwd}")

            try:
                time.sleep(15)
                VaultManager.secure_exit()
            except KeyboardInterrupt:
                VaultManager.secure_exit()

    @staticmethod
    def edit_entry(data):
        idx = VaultManager._select_entry(data, None, "edit")
        if idx is not None:
            entry = data[idx]
            print(f"\n--- Editing: {entry['service']} ---")
            entry['service'] = input(f"New Service [{entry['service']}]: ") or entry['service']
            entry['user'] = input(f"New User [{entry['user']}]: ") or entry['user']
            
            if input("Change password? (y/N): ").lower() == 'y':
                entry['password'] = VaultManager.get_confirmed_password()
            
            entry['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            VaultManager.save_vault(data)
            print(f"[+] '{entry['service']}' updated.")

    @staticmethod
    def delete_entry(data):
        idx = VaultManager._select_entry(data, None, "DELETE")
        if idx is not None:
            entry = data[idx]
            print(f"\n[!] WARNING: You are about to delete {entry['service']} ({entry['user']})")
            confirm = input(f"Confirm permanent deletion of '{entry['service']}'? (y/N): ").lower().strip()
            
            if confirm == 'y':
                data.pop(idx)
                VaultManager.save_vault(data)
                print(f"[+] '{entry['service']}' deleted.")
            else:
                print("[*] Deletion cancelled.")

    @staticmethod
    def get_confirmed_password():
        current_length = 25
        while True:
            candidate = VaultManager.generate_secure_password(current_length)
            print(f"\nGenerated ({current_length} chars): {candidate}")
            print("Options: [y] Accept | [n] Quit | [manual] Manual entry | [Number] Change length | [Enter] Retry")
            choice = input("> ").lower().strip()
            
            if choice == 'y': 
                return candidate
            elif choice.isdigit():
                new_len = int(choice)
                if new_len < 4:
                    print("[!] Length too short. Minimum is 4.")
                else:
                    current_length = new_len
            elif choice == 'n': 
                VaultManager.secure_exit()
            elif choice == 'manual': 
                return getpass.getpass("Enter password: ")
    
    @staticmethod
    def load_vault():
        if not os.path.exists(VAULT_FILE):
            return []
        
        try:
            result = subprocess.run(
                ['gpg', '--decrypt', '--quiet', '--batch', '--use-agent', VAULT_FILE],
                capture_output=True, text=True, check=False
            )
            
            stdout = result.stdout
            
            if result.returncode != 0:
                print("[*] Authentication required.")
                passphrase = getpass.getpass("GPG Passphrase: ")
                proc = subprocess.Popen(
                    ['gpg', '--decrypt', '--quiet', '--batch', '--no-tty', '--yes', 
                    '--pinentry-mode', 'loopback', '--passphrase-fd', '0', VAULT_FILE],
                    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                )
                stdout, stderr = proc.communicate(input=passphrase)
                if proc.returncode != 0:
                    print(f"\n[!] GPG Error: {stderr.strip()}")
                    return None

            if not stdout.strip():
                return []
                
            try:
                return json.loads(stdout)
            except json.JSONDecodeError:
                return VaultManager._perform_migration(stdout)
                
        except Exception as e:
            print(f"[!] System Error: {e}")
            return None

    @staticmethod
    def save_vault(data_list):
        if os.path.exists(VAULT_FILE):
            backup_file = VAULT_FILE + ".bak"
            shutil.copy2(VAULT_FILE, backup_file)
        
        try:
            json_data = json.dumps(data_list, indent=2)
            
            process = subprocess.run(
                ['gpg', '--encrypt', '--recipient', RECIPIENT, '--armor', '--yes', '--batch', '--output', VAULT_FILE],
                input=json_data, 
                text=True, 
                capture_output=True,
                check=True
            )
            print(f"\n[+] Vault synchronized successfully.")
            
        except subprocess.CalledProcessError as e:
            print(f"\n[!] CRITICAL ERROR during encryption: {e.stderr}")
            print("[!] The .bak backup has been preserved. Check your GPG keys.")
        except Exception as e:
            print(f"\n[!] Unexpected error during save: {e}")

    @staticmethod
    def _perform_migration(stdout):
        """Internal helper to convert legacy text format to JSON objects."""
        print("[!] Legacy format detected. Migrating to JSON structure...")
        migrated_data = []
        for line in stdout.splitlines():
            if not line.strip(): continue
            try:
                parts = [p.strip() for p in line.split('|')]
                svc = parts[0]
                usr = parts[1].replace("User:", "").strip() if len(parts) > 1 else "Unknown"
                pwd = parts[2].replace("PWD:", "").strip() if len(parts) > 2 else ""
                
                migrated_data.append({
                    "service": svc,
                    "user": usr,
                    "password": pwd,
                    "updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
            except Exception:
                continue
        
        if migrated_data:
            VaultManager.save_vault(migrated_data)
            print("[+] Migration complete. Vault is now in JSON format.")
        return migrated_data

def main():
    data = VaultManager.load_vault()
    if data is None: return

    try:
        script_path = os.path.realpath(__file__)
        if os.path.exists(script_path):
            mtime = datetime.fromtimestamp(os.path.getmtime(script_path)).strftime('%Y-%m-%d %H:%M')
            print(f"Script updated : {mtime}")

        if len(sys.argv) > 1:
            vis = "-v" in sys.argv or "--visual" in sys.argv
            args = [a for a in sys.argv[1:] if a not in ["-v", "--visual"]]
            if args:
                VaultManager.display_vault(data, args[0], force_visual=vis)
                return
            elif vis:
                print("[!] Visual mode activated. Choose a service:")
                for i, e in enumerate(data, 1): 
                    print(f"[{i:2}] {e['service']}")
                term = input("\nSearch/Number: ")
                VaultManager.display_vault(data, term, force_visual=True)
                return

        print(f"\n[1] List [2] Add [3] Edit [4] Del [q] Quit")
        c = input("> ").lower().strip()

        if c == '1':
            for i, e in enumerate(data, 1): 
                print(f"[{i}] {e['service']}")
            term = input("\nSearch/Number: ")
            VaultManager.display_vault(data, term)
        elif c == '2':
            svc = input("Service: ")
            if any(e['service'].lower() == svc.lower() for e in data):
                print(f"[!] Warning: '{svc}' already exists. Use Edit instead.")
                return
            usr = input("User: ")
            pwd = VaultManager.get_confirmed_password()
            data.append({
                "service": svc,
                "user": usr,
                "password": pwd,
                "updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            VaultManager.save_vault(data)
        elif c == '3':
            VaultManager.edit_entry(data)
        elif c == '4':
            VaultManager.delete_entry(data)
        elif c == 'q':
            subprocess.run(['gpgconf', '--reload', 'gpg-agent'])
            VaultManager.secure_exit()
        else:
            VaultManager.display_vault(data, c)

    except KeyboardInterrupt:
        VaultManager.secure_exit()

if __name__ == "__main__":
    main()

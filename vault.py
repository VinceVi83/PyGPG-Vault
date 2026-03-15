#!/usr/bin/env python3
import os, subprocess, getpass, sys, difflib, secrets, string, time, shutil
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
    """
    Class to manage the vault operations.
    """

    @staticmethod
    def generate_secure_password(length=20):
        """Generate a secure password with a given length."""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        while True:
            pwd = ''.join(secrets.choice(alphabet) for _ in range(length))
            if (any(c.islower() for c in pwd) and any(c.isupper() for c in pwd) and 
                any(c.isdigit() for c in pwd) and any(c in "!@#$%^&*" for c in pwd)):
                return pwd

    @staticmethod
    def smart_copy(text):
        """Support: Windows(WSL), Android, macOS, Linux(X11/Wayland), iOS."""
        try:
            if shutil.which("clip.exe"):
                process = subprocess.Popen(['clip.exe'], stdin=subprocess.PIPE)
                process.communicate(input=text.encode('utf-16'))
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
    def load_vault():
        if not os.path.exists(VAULT_FILE):
            return []
        try:
            result = subprocess.run(
                ['gpg', '--decrypt', '--quiet', '--batch', '--use-agent', VAULT_FILE],
                capture_output=True, text=True, check=False
            )
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
                return [l for l in stdout.splitlines() if l.strip()]
            return [l for l in result.stdout.splitlines() if l.strip()]
        except Exception as e:
            print(f"[!] System Error: {e}")
            return None

    @staticmethod
    def secure_exit():
        """Clear the clipboard and exit the program."""
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
    def save_vault(lines_list):
        """Save the vault to a GPG-encrypted file."""
        new_data = "\n".join(lines_list) + "\n"
        subprocess.run(['gpg', '--encrypt', '--recipient', RECIPIENT, '--armor', '--yes', '--batch', '--output', VAULT_FILE], input=new_data, text=True, check=True)

    @staticmethod
    def display_vault(lines, search_term, force_visual=False):
        """Display the vault entries, optionally filtering by search term."""
        names = [l.split('|')[0].strip() for l in lines]
        
        target_idx = None
        if search_term.isdigit():
            idx = int(search_term) - 1
            if 0 <= idx < len(lines):
                target_idx = idx

        if target_idx is None:
            matches = [i for i, n in enumerate(names) if search_term.lower() in n.lower()]
            
            if not matches:
                close_names = difflib.get_close_matches(search_term, names, n=3, cutoff=0.6)
                matches = [names.index(c) for c in close_names]

            if not matches:
                print("[!] No service found.")
                return

            if len(matches) == 1:
                target_idx = matches[0]
            else:
                print("\nMultiple matches found:")
                for i, idx in enumerate(matches, 1):
                    print(f" [{i}] {names[idx]}")
                sel = input("\nSelect number (or Enter to cancel): ")
                if sel.isdigit() and 0 < int(sel) <= len(matches):
                    target_idx = matches[int(sel)-1]

        if target_idx is not None:
            parts = [p.strip() for p in lines[target_idx].split('|')]
            pwd = parts[2].split('PWD:')[1].strip() if 'PWD:' in parts[2] else parts[2]
            print(f"\nService: {parts[0]} | User: {parts[1]}")
            
            if force_visual:
                print(f"PASSWORD (Visual Mode) : {pwd}")
                VaultManager.smart_copy("")
            else:
                env = VaultManager.smart_copy(pwd)
                if env:
                    print(f"[OK] Copied to {env}.")
                else:
                    print(f"PASSWORD (Legacy Mode) : {pwd}")

            try:
                time.sleep(15)
                VaultManager.secure_exit()
            except KeyboardInterrupt:
                VaultManager.secure_exit()

    @staticmethod
    def edit_entry(lines):
        """Edit an entry in the vault."""
        for i, l in enumerate(lines, 1): 
            print(f"[{i}] {l.split('|')[0].strip()}")
        
        try:
            choice = input("Edit number: ")
            if not choice: return
            idx = int(choice) - 1
            
            if 0 <= idx < len(lines):
                parts = [x.strip() for x in lines[idx].split('|')]
                current_service = parts[0]
                current_user = parts[1].replace("User:", "").strip() if "User:" in parts[1] else parts[1]
                
                print(f"\n--- Editing: {current_service} ---")

                new_service = input(f"New Service Name [{current_service}]: ") or current_service
                new_usr = input(f"New User [{current_user}]: ") or current_user
                pwd = VaultManager.get_confirmed_password()

                lines[idx] = f"{new_service} | User: {new_usr} | PWD: {pwd}"
                VaultManager.save_vault(lines)
                print(f"\n[+] '{new_service}' has been successfully updated.")
        except ValueError:
            print("[!] Invalid number.")

    @staticmethod
    def delete_entry(lines):
        """Delete an entry from the vault."""
        if not lines:
            print("[!] The vault is empty.")
            return

        for i, l in enumerate(lines, 1):
            print(f"[{i:2}] {l.split('|')[0].strip()}")
    
        try:
            idx_input = input("\nNumber to delete (or Enter to cancel) : ").strip()
            if not idx_input: return
        
            idx = int(idx_input) - 1
            if 0 <= idx < len(lines):
                service_name = lines[idx].split('|')[0].strip()
                confirm = input(f"[?] Delete '{service_name}' permanently? (y/N) : ").lower().strip()
            
                if confirm == 'y':
                    lines.pop(idx)
                    VaultManager.save_vault(lines)
                    print(f"[+] '{service_name}' has been deleted.")
                else:
                    print("[*] Deletion cancelled.")
        except ValueError:
            print("[!] Please enter a valid number.")

    @staticmethod
    def get_confirmed_password():
        """Generate and confirm a secure password with dynamic length support."""
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

def main():
    """Main function to handle user interactions."""
    try:
        script_path = os.path.realpath(__file__)
        vault_path = os.path.realpath(VAULT_FILE)
        mtime_script = datetime.fromtimestamp(os.path.getmtime(script_path)).strftime('%Y-%m-%d %H:%M')
        print(f"Script updated : {mtime_script}")
        if os.path.exists(vault_path):
            mtime_vault = datetime.fromtimestamp(os.path.getmtime(vault_path)).strftime('%Y-%m-%d %H:%M')
            print(f"Vault updated  : {mtime_vault}")
    except Exception as e:
        print(f"Status: Error retrieving dates ({e})")

    lines = VaultManager.load_vault()
    if lines is None: return
    try:
        if len(sys.argv) > 1:
            visual = "-v" in sys.argv or "--visual" in sys.argv
            
            args_clean = [a for a in sys.argv[1:] if a not in ["-v", "--visual"]]
            
            if args_clean:
                VaultManager.display_vault(lines, args_clean[0], force_visual=visual)
                return
            elif visual:
                print("[!] Visual mode activated. Choose a service from the list :")
                for i, l in enumerate(lines, 1): print(f"[{i:2}] {l.split('|')[0].strip()}")
                term = input("\nSearch/Number : ")
                VaultManager.display_vault(lines, term, force_visual=True)
                return

        print(f"\n[1] List [2] Add [3] Edit [4] Del [q] Quit")
        c = input("> ").lower().strip()

        if c == '1':
            for i, l in enumerate(lines, 1): print(f"[{i}] {l.split('|')[0].strip()}")
            term = input("\nSearch/Number: ")
            VaultManager.display_vault(lines, term)
        elif c == '2':
            svc = input("Service: "); usr = input("User: ")
            pwd = VaultManager.get_confirmed_password()
            lines.append(f"{svc} | User: {usr} | PWD: {pwd}")
            VaultManager.save_vault(lines)
        elif c == '3':
            VaultManager.edit_entry(lines)
        elif c == '4':
            VaultManager.delete_entry(lines)
        elif c == 'q':
            subprocess.run(['gpgconf', '--reload', 'gpg-agent'])
            VaultManager.secure_exit()
        else:
            VaultManager.display_vault(lines, c)

    except KeyboardInterrupt:
                VaultManager.secure_exit()

if __name__ == "__main__":
    main()

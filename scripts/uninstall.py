#!/usr/bin/env python3
# scripts/uninstall.py
import os
import sys
import shutil
import subprocess


def uninstall_package():
    """Unregister CLI commands globally via pipx."""
    print("📦 Removing CLI commands globally via pipx...")
    try:
        # Check if secrets-manager is installed in pipx
        output = subprocess.run(["pipx", "list"], capture_output=True, text=True)
        if "secrets-manager" in output.stdout:
            subprocess.run(["pipx", "uninstall", "secrets-manager"], check=True)
            print("✅ CLI commands removed successfully.")
        else:
            print("💡 secrets-manager is not currently installed in pipx.")
    except Exception as e:
        print(f"⚠️ Warning: Could not run pipx uninstall: {e}")


def remove_config():
    """Delete the global secrets-manager directory."""
    config_dir = os.path.join(os.path.expanduser("~"), ".secrets-manager")
    if os.path.exists(config_dir):
        print(f"🧹 Deleting configuration folder: {config_dir}")
        try:
            shutil.rmtree(config_dir)
            print("✅ Configuration directory deleted successfully.")
        except Exception as e:
            print(f"❌ Error deleting configuration folder: {e}")
            sys.exit(1)
    else:
        print("💡 No configuration folder found at ~/.secrets-manager.")


def main():
    print("🗑️ Starting Secrets Manager Uninstallation Script\n" + "="*50)
    confirm = input("⚠️ This will uninstall the CLI commands and permanently delete all S3 configuration keys. Proceed? [y/N]: ").strip().lower()
    if confirm not in ("y", "yes"):
        print("❌ Uninstallation aborted.")
        sys.exit(0)

    print()
    uninstall_package()
    remove_config()
    print("\n✨ Secrets Manager uninstalled successfully.")


if __name__ == "__main__":
    main()

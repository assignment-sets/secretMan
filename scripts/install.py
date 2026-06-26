#!/usr/bin/env python3
# scripts/install.py
import os
import sys
import shutil
import subprocess
import base64
import platform

REPO_URL = "https://github.com/assignment-sets/secretMan.git"


def check_git():
    """Verify Git is installed."""
    if not shutil.which("git"):
        print("❌ Error: Git is not installed on this system.")
        print("Please install Git and try again. Refer to https://git-scm.com/downloads")
        sys.exit(1)
    print("✅ Git is installed.")


def install_pipx_auto():
    """Attempt to install pipx in a standard, safe way depending on the OS."""
    os_type = platform.system().lower()
    print(f"🔍 Detecting OS as {platform.system()}...")

    installed = False
    try:
        if "darwin" in os_type:
            if shutil.which("brew"):
                print("📦 Attempting to install pipx via Homebrew...")
                subprocess.run(["brew", "install", "pipx"], check=True)
                installed = True
        elif "linux" in os_type:
            if shutil.which("apt-get"):
                print("📦 Attempting to install pipx via APT...")
                subprocess.run(["sudo", "apt-get", "update"], check=True)
                subprocess.run(["sudo", "apt-get", "install", "-y", "pipx"], check=True)
                installed = True
            elif shutil.which("dnf"):
                print("📦 Attempting to install pipx via DNF...")
                subprocess.run(["sudo", "dnf", "install", "-y", "pipx"], check=True)
                installed = True
        elif "windows" in os_type:
            if shutil.which("scoop"):
                print("📦 Attempting to install pipx via Scoop...")
                subprocess.run(["scoop", "install", "pipx"], check=True)
                installed = True

        # Fallback to installing via pip if other options fail or aren't present
        if not installed:
            print("📦 Attempting to install pipx via pip...")
            subprocess.run([sys.executable, "-m", "pip", "install", "--user", "pipx"], check=True)
            installed = True

    except subprocess.CalledProcessError as e:
        print(f"⚠️ Automatic installation attempt failed: {e}")

    if installed:
        print("🔄 Running 'pipx ensurepath' to configure your environment paths...")
        try:
            # Run ensurepath using python -m pipx if pip was used, or the binary if available
            pipx_bin = shutil.which("pipx") or "pipx"
            subprocess.run([pipx_bin, "ensurepath"], check=True)
        except Exception:
            # Fallback for python-installed pipx
            try:
                subprocess.run([sys.executable, "-m", "pipx", "ensurepath"], check=True)
            except Exception:
                pass
    return installed


def check_pipx():
    """Verify pipx is installed, or try to install it."""
    if shutil.which("pipx"):
        print("✅ pipx is installed.")
        return

    print("⚠️ pipx not found on system path.")
    if install_pipx_auto():
        # Check again after trying automatic installation
        if shutil.which("pipx"):
            print("✅ pipx is successfully installed.")
            return

        print("\n⚠️ pipx was installed, but it is not yet visible in your terminal session's PATH.")
        print("Action required: Please restart your terminal session and run this installation script again.")
        print("If you still get this message, run 'pipx ensurepath' manually.")
        sys.exit(1)
    else:
        print("\n❌ Error: Could not install pipx automatically.")
        print("Please install pipx manually following the official guide:")
        print("👉 https://pipx.pypa.io/stable/how-to/install-pipx/")
        sys.exit(1)


def clone_repository(dest_dir):
    """Clone the secrets-manager repository from GitHub."""
    print(f"\n📂 Cloning Secrets Manager repository from GitHub to {dest_dir}...")
    if os.path.exists(dest_dir):
        print(f"🧹 Removing existing repository directory: {dest_dir}...")
        try:
            shutil.rmtree(dest_dir)
        except Exception as e:
            print(f"❌ Error cleaning directory: {e}")
            sys.exit(1)

    try:
        subprocess.run(["git", "clone", REPO_URL, dest_dir], check=True)
        print("✅ Repository cloned successfully.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error cloning repository from GitHub: {e}")
        sys.exit(1)


def configure_s3(config_dir):
    """Prompt the developer for S3 config credentials."""
    config_path = os.path.join(config_dir, ".env")

    # Check for existing configuration
    if os.path.exists(config_path):
        print(f"\n💡 Existing S3 configuration found at: {config_path}")
        reuse = input("Do you want to reuse this configuration? [Y/n]: ").strip().lower()
        if reuse in ("", "y", "yes"):
            print("✅ Reusing existing configuration.")
            return

    print("\n✍️ Set up S3 Secrets Manager credentials:")
    aws_key = input("Enter AWS_ACCESS_KEY: ").strip()
    aws_secret = input("Enter AWS_SECRET_ACCESS_KEY: ").strip()
    aws_region = input("Enter AWS_DEFAULT_REGION: ").strip()
    aws_bucket = input("Enter AWS_S3_BUCKET_NAME: ").strip()

    fernet_salt = input("Enter FERNET_SALT (Press Enter to auto-generate a secure random salt): ").strip()
    if not fernet_salt:
        fernet_salt = base64.urlsafe_b64encode(os.urandom(32)).decode("utf-8")
        print(f"✨ Auto-generated secure FERNET_SALT: {fernet_salt}")

    # Write configuration
    with open(config_path, "w") as f:
        f.write(f"AWS_ACCESS_KEY={aws_key}\n")
        f.write(f"AWS_SECRET_ACCESS_KEY={aws_secret}\n")
        f.write(f"AWS_DEFAULT_REGION={aws_region}\n")
        f.write(f"AWS_S3_BUCKET_NAME={aws_bucket}\n")
        f.write(f"FERNET_SALT={fernet_salt}\n")

    # Set owner-only permissions on configuration file
    try:
        os.chmod(config_path, 0o600)
    except Exception:
        pass

    print(f"✅ S3 configuration saved to: {config_path}")


def install_package(repo_dir):
    """Run pipx install to register scripts globally using the local repository path."""
    print("\n📦 Registering CLI commands globally via pipx...")
    try:
        # Force install to overwrite any existing installation idempotently from the cloned folder path
        subprocess.run(["pipx", "install", "--force", repo_dir], check=True)
        print("✅ CLI commands registered successfully.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error during pipx installation: {e}")
        sys.exit(1)


def main():
    print("🔐 Starting Secrets Manager Installation Script\n" + "="*50)
    
    # Define setup folders
    global_dir = os.path.join(os.path.expanduser("~"), ".secrets-manager")
    repo_dir = os.path.join(global_dir, "repo")
    os.makedirs(global_dir, exist_ok=True)

    check_git()
    check_pipx()
    clone_repository(repo_dir)
    install_package(repo_dir)
    configure_s3(global_dir)
    
    print("\n✨ Secrets Manager installed successfully!")
    print("You can now run commands globally: 'suenv', 'sfenv', and 'sdenv'.")
    print("Run 'sfenv --help' to see usage details.")


if __name__ == "__main__":
    main()

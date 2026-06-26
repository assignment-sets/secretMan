# 🔐 Secrets Manager

A secure, zero-knowledge CLI tool to encrypt and synchronize repository-specific environment (`.env`) files to an AWS S3 bucket.

Secrets Manager performs all cryptographic operations **locally** on your machine. S3 is used purely as a secure storage engine for the encrypted ciphertext. No passwords or plaintext secrets ever leave your computer.

---

## 📋 Prerequisites

- **Python 3**: You **must** have Python 3 installed on your system.
- _Note_: The installation script will automatically check for and try to configure standard dependencies like **Git** and **pipx** for you.

---

## 🚀 Quick Setup (For Users)

If you just want to install and use the Secrets Manager CLI:

1. Run the cross-platform automated installer script:

   ```bash
   python -c "$(curl -fsSL https://raw.githubusercontent.com/assignment-sets/secretMan/main/scripts/install.py)"
   ```

   _(Alternatively, clone this repository and run `python scripts/install.py`)_.

2. The installer will:
   - Setup standard dependencies (like `pipx`).
   - Clone the tool repository into your global settings directory (`~/.secrets-manager/repo`).
   - Register the CLI commands globally.
   - Interactively prompt you for S3 keys and automatically create the global configuration file (`~/.secrets-manager/.env`).

Once installed, you can run S3 secrets sync commands (`suenv`, `sfenv`, `sdenv`) from any repository folder.

---

## 🛠️ Developer Setup (For Contributors)

If you are a developer looking to clone the project, run tests, or contribute:

1. Clone the repository:

   ```bash
   git clone https://github.com/assignment-sets/secretMan.git
   cd secretMan
   ```

2. Create your local S3 configuration file:

   ```bash
   cp .env.example .env
   ```

   _(Fill out the S3 access credentials and bucket settings inside `.env`)_.

3. Install the package globally in editable mode:
   ```bash
   pipx install --editable --force .
   ```

---

## 📂 Deep-Dive Documentation

For more specialized details, please refer to:

- **[Architecture & System Overview](AGENT.md)**: Conceptual guide covering folder structures, scope, and the configuration resolution hierarchy.
- **[CLI Reference Guide](docs/cli-guide.md)**: Exhaustive manual for CLI commands, safety flags, and overwrite protection.
- **[Authentication & Encryption Deep-Dive](docs/auth-and-encryption.md)**: Mathematical and cryptographic details of the key derivation (PBKDF2), symmetric encryption (Fernet), and Mermaid sequence diagrams.

# 💻 CLI Command Guide

This guide describes the usage, configuration flags, and safety overrides for the Secrets Manager command-line scripts.

---

## 🚀 Overview

Secrets Manager registers three executable scripts in [pyproject.toml](../pyproject.toml):

- **`suenv`** (Upload Env): Encrypts and uploads environment files.
- **`sfenv`** (Fetch Env): Downloads and decrypts environment files.
- **`sdenv`** (Delete Env): Verifies password and deletes remote environment files.

---

## 📤 `suenv` — Upload Env

Encrypts a local environment file and uploads it to S3 under the SHA-1 hash of the repository URL.

### Usage

```bash
suenv [options]
```

### Options & Flags

| Option      | Long Flag       | Default           | Description                                                |
| :---------- | :-------------- | :---------------- | :--------------------------------------------------------- |
| `-f <path>` | `--file <path>` | `.env`            | Path to the local file to encrypt.                         |
| `-r <url>`  | `--repo <url>`  | _(Auto-detected)_ | Override Git remote URL (useful outside git repositories). |

### Examples

```bash
# Encrypt and upload the default .env from your git folder
suenv

# Encrypt and upload a staging env configuration
suenv -f .env.staging

# Upload a file using a custom repository identifier
suenv -f config.env -r "my-org/my-project"
```

---

## 📥 `sfenv` — Fetch Env

Downloads and decrypts environment files from S3, writing them to a local destination.

### Usage

```bash
sfenv [options]
```

### Options & Flags

| Option      | Long Flag         | Default           | Description                                                      |
| :---------- | :---------------- | :---------------- | :--------------------------------------------------------------- |
| `-o <path>` | `--output <path>` | `.env`            | Destination path to save decrypted secrets.                      |
| `-r <url>`  | `--repo <url>`    | _(Auto-detected)_ | Override Git remote URL to retrieve secrets for another project. |
| `-f`        | `--force`         | `False`           | Overwrite the destination file without prompting.                |

### ⚠️ Overwrite Safety Check

By default, if the output file already exists, `sfenv` will ask for confirmation before writing to prevent accidental loss of local changes:

```text
⚠️ Warning: File already exists at: /path/to/.env
Are you sure you want to overwrite it? [y/N]:
```

Pass `-f` or `--force` to bypass this prompt (useful for automated scripts).

### Examples

```bash
# Decrypt and overwrite the local .env file (prompts if it exists)
sfenv

# Force download and overwrite without confirmation
sfenv -f

# Download secrets for a specific project into a custom output path
sfenv -r "assignment-sets/general-medical-rag" -o .env.prod
```

---

## 🗑️ `sdenv` — Delete Env

Verifies the master password and deletes the encrypted secrets from S3.

### Usage

```bash
sdenv [options]
```

### Options & Flags

| Option     | Long Flag      | Default           | Description                                                  |
| :--------- | :------------- | :---------------- | :----------------------------------------------------------- |
| `-r <url>` | `--repo <url>` | _(Auto-detected)_ | Override Git remote URL to delete another project's secrets. |
| `-y`       | `--yes`        | `False`           | Skip deletion safety confirmation prompt.                    |

### ⚠️ Delete Safety Confirmation

By default, before prompting for the password, `sdenv` will ask for confirmation:

```text
⚠️ Are you sure you want to permanently delete secrets for <repo_url>? [y/N]:
```

Pass `-y` or `--yes` to skip this warning.

### Examples

```bash
# Delete default repo secrets (prompts for confirmation, then asks for master password)
sdenv

# Delete secrets for a specific project skipping the confirmation warning
sdenv -r "my-org/old-project" -y
```

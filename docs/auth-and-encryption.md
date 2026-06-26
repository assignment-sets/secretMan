# 🔑 Authentication & Encryption Flows

This document details how Secrets Manager secures environment variables, performs cryptographic operations, and interacts with AWS S3. It explains the core concepts of S3 Key resolution, dynamic salt key derivation, and the deletion verification flow.

---

## 🔒 Security Summary

> [!IMPORTANT]
> All encryption and decryption operations occur **locally** on your development machine. Plaintext secrets are never transmitted over the network. S3 only receives and stores encrypted ciphertext.

- **Symmetric Encryption**: Fernet (AES-128 in CBC mode with HMAC-SHA256 integrity check).
- **Key Derivation**: PBKDF2HMAC (SHA-256, 480,000 iterations).
- **Dynamic Salt Management**: Every upload generates a new, cryptographically random 16-byte salt (`os.urandom(16)`), stored base64-encoded in S3 metadata.
- **Zero-Knowledge Storage**: No passwords or password hashes (even salted/slow hashes) are stored on S3.
- **Deletion Verification**: Correctness of the password is verified prior to deletion by performing a local test decryption on the S3 payload.

---

## 🏷️ S3 Key Generalization

To prevent identical repositories from resolving to different S3 keys due to different protocol configurations (e.g. HTTPS vs SSH), the CLI normalizes the git URL using the [normalize_repo_url](../src/secrets_manager/utils/helpers.py#L35-L67) function.

### URL Normalization Examples:

- `https://github.com/owner/repo.git` ➔ `owner/repo`
- `git@github.com:owner/repo.git` ➔ `owner/repo`
- `git@github.com-main:owner/repo.git` ➔ `owner/repo`
- `owner/repo` ➔ `owner/repo`

The S3 Key is calculated as `SHA-1(normalized_repo_url)`.

---

## 🗺️ Detailed Process Flows

### 1. Upload Flow (`suenv`)

This flow encrypts a local environment file and stores it in S3 with its unique generated salt.

```mermaid
sequenceDiagram
    autonumber
    actor Dev as Developer
    participant CLI as Secrets Manager CLI
    participant Local as Local Git/FS
    participant S3 as AWS S3 Bucket

    Dev->>CLI: Run `suenv` (with optional -f and -r overrides)
    CLI->>Local: Read Git remote URL (if --repo is not supplied)
    Local-->>CLI: Return Raw Repo URL
    CLI->>CLI: normalize_repo_url() -> 'owner/repo'
    CLI->>CLI: Compute S3 Key = SHA-1('owner/repo')
    CLI->>Dev: Prompt for Master Password
    Dev-->>CLI: Enter Password
    CLI->>CLI: Generate Random 16-byte Salt
    CLI->>CLI: Derive Fernet Key using PBKDF2(Password, Salt)
    CLI->>CLI: Encrypt env file contents using Fernet Key
    CLI->>S3: Upload Encrypted Data (Body) & base64-encoded Salt (Metadata: salt)
    S3-->>CLI: Upload Confirmation
    CLI->>Dev: Print success message
```

---

### 2. Fetch Flow (`sfenv`)

This flow downloads the encrypted data from S3, extracts the salt, and decrypts the payload locally.

```mermaid
sequenceDiagram
    autonumber
    actor Dev as Developer
    participant CLI as Secrets Manager CLI
    participant S3 as AWS S3 Bucket
    participant Local as Local Git/FS

    Dev->>CLI: Run `sfenv` (with optional -o, -r, and -f overrides)
    CLI->>CLI: normalize_repo_url() -> 'owner/repo'
    CLI->>CLI: Compute S3 Key = SHA-1('owner/repo')
    alt Destination file exists and --force is not passed
        CLI->>Dev: Show Warning & Prompt for confirmation
        Dev-->>CLI: Confirm overwrite
    end
    CLI->>S3: Request Object (Bucket, S3 Key)
    S3-->>CLI: Return Encrypted Ciphertext & Metadata
    CLI->>CLI: Extract Salt from Metadata (fallback to local FERNET_SALT if missing)
    CLI->>Dev: Prompt for Master Password
    Dev-->>CLI: Enter Password
    CLI->>CLI: Derive Fernet Key using PBKDF2(Password, Salt)
    alt Password is correct
        CLI->>CLI: Decrypt Ciphertext with Fernet Key
        CLI->>Local: Write decrypted contents to output file with secure permissions (600)
        CLI->>Dev: Print success message
    else Password is incorrect
        CLI->>CLI: Fernet decryption raises InvalidToken
        CLI->>Dev: Print "Decryption failed" error
    end
```

---

### 3. Delete Flow (`sdenv`)

This flow verifies the master password using local test decryption before requesting deletion.

```mermaid
sequenceDiagram
    autonumber
    actor Dev as Developer
    participant CLI as Secrets Manager CLI
    participant S3 as AWS S3 Bucket

    Dev->>CLI: Run `sdenv` (with optional -r and -y overrides)
    CLI->>CLI: normalize_repo_url() -> 'owner/repo'
    CLI->>CLI: Compute S3 Key = SHA-1('owner/repo')
    alt --yes is not passed
        CLI->>Dev: Prompt for Deletion Safety Confirmation
        Dev-->>CLI: Confirm Deletion
    end
    CLI->>S3: Download S3 Object (Body & Metadata)
    S3-->>CLI: Return Encrypted Ciphertext & Metadata
    CLI->>CLI: Extract Salt from Metadata (fallback to local FERNET_SALT if missing)
    CLI->>Dev: Prompt for Master Password
    Dev-->>CLI: Enter Password
    CLI->>CLI: Derive Fernet Key using PBKDF2(Password, Salt)
    alt Decryption succeeds
        CLI->>CLI: Decrypt downloaded payload (verifies password correctness)
        CLI->>S3: Delete S3 Object (delete_object)
        S3-->>CLI: Deletion Confirmation
        CLI->>Dev: Print success message
    else Decryption fails
        CLI->>Dev: Print "Incorrect password. Delete aborted."
    end
```

---

## 💡 Cryptographic Core Details

Here is the helper code that drives the key derivation.

### Key Derivation Code:

From [helpers.py](../src/secrets_manager/utils/helpers.py#L49-L71):

```python
def get_fernet(password: str, salt: bytes = None) -> Fernet:
    """Derive a Fernet key from the password."""
    password_bytes = password.encode()
    if salt is None:
        salt_raw = os.getenv("FERNET_SALT")

        if salt_raw is None:
            print("❌ Error: FERNET_SALT not found in environment variables.")
            print("Tip: Run 'export FERNET_SALT=your_salt' or add it to ~/.bashrc")
            sys.exit(1)

        salt = salt_raw.encode()

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password_bytes))
    return Fernet(key)
```

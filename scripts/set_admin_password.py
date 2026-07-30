#!/usr/bin/env python3
"""Generate an admin password (or use provided one), create a Werkzeug hash,
and save it to `.venv/admin_password.env` as ROSITA_ADMIN_PASSWORD_HASH.
Prints the plaintext password to stdout so the operator can record it.

Usage:
  .venv\Scripts\python.exe scripts\set_admin_password.py [--password P]

If run inside an activated venv, the script will prefer `$VIRTUAL_ENV`.
"""
import os
import sys
import secrets
import argparse
from werkzeug.security import generate_password_hash

p = argparse.ArgumentParser()
p.add_argument("--password", "-p", help="Use this password instead of generating one")
args = p.parse_args()

pw = args.password or secrets.token_urlsafe(18)
# Use Werkzeug default method/params
h = generate_password_hash(pw)

# Determine venv path
venv_path = os.environ.get("VIRTUAL_ENV")
if not venv_path:
    # fallback to .venv in repo root
    repo_root = os.path.abspath(os.path.dirname(__file__) + os.sep + "..")
    venv_path = os.path.join(repo_root, ".venv")

out_path = os.path.join(venv_path, "admin_password.env")
try:
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"ROSITA_ADMIN_PASSWORD_HASH={h}\n")
except Exception as e:
    print("Failed to write admin_password.env:", e, file=sys.stderr)
    sys.exit(2)

print("Admin password generated and hash saved to:", out_path)
print()
print("PLAINTEXT PASSWORD (record it now, will not be shown again):")
print(pw)
print()
print("Keep this secret. To load the hash automatically when activating the venv, the activation scripts were updated to read admin_password.env (if present).")
print("If you prefer to set a custom password, run with --password 'your-pass' and then delete the plaintext shown above.")

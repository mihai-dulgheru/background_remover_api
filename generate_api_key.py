"""
This script generates a secure random API key and can optionally
update your config.py file with the new key.
"""

import secrets


def generate_api_key():
    """
    Generate a secure random API key (64 hex characters).
    """
    return secrets.token_hex(32)


if __name__ == "__main__":
    new_key = generate_api_key()
    print(f"Generated API Key: {new_key}")

import secrets


def generate_api_key():
    """
    Generates a secure random API key using a 32-byte hex token.
    This API key can be used for authentication in the application.

    Returns:
        str: A randomly generated API key in hexadecimal format.
    """
    return secrets.token_hex(32)


if __name__ == "__main__":
    new_key = generate_api_key()
    print(f"Generated API Key: {new_key}")

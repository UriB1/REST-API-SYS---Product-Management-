import secrets
secret_key = secrets.token_hex(32)
print(secret_key) # Generate a secret key and copy it to your .env file  
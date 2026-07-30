from werkzeug.security import generate_password_hash
import secrets

pw = secrets.token_urlsafe(18)
print(pw)
print(generate_password_hash(pw))

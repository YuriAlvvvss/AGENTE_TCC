from werkzeug.security import generate_password_hash
print('ADMIN_HASH=' + generate_password_hash('admin123'))
print('USER_HASH=' + generate_password_hash('usuario123'))

import string
import re

from flask import current_app as app


def generate_user_principal_name(name, domain_name):
    mail_name = generate_mail_nickname(name)
    return f"{mail_name}@{domain_name}.{app.config.get('OFFICE_365_DOMAIN')}"


ESCAPED_PUNCTUATION = re.escape(string.punctuation)


def generate_mail_nickname(name):
    return re.sub(f"[{ESCAPED_PUNCTUATION} ]+", ".", name).lower()

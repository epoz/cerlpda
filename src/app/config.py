import os

DEBUG = os.environ.get("DEBUG", "0") == "1"
ORIGINS = os.environ.get(
    "ORIGINS",
    "http://localhost:8080",
).split(" ")
DATABASE_URL = "sqlite:///cerlpda.sqlite"
ADMIN_DATABASE = os.environ.get("ADMIN_DATABASE", "admin.sqlite")
SECRET_KEY = os.environ.get("SECRET_KEY", "foobarbaz")
ACCESS_TOKEN_EXPIRE_DAYS = int(os.environ.get("ACCESS_TOKEN_EXPIRE_DAYS", "30"))

SITE_URI = "https://pda.cerl.org/"
CONTACT_EMAIL = os.environ.get("CONTACT_EMAIL", "ep@epoz.org")
HELP_PATH = os.environ.get("HELP_PATH", "help")
UPLOADS_PATH = os.environ.get("UPLOADS_PATH")

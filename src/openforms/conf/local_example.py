#
# Any machine specific settings when using development settings.
#

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "openforms",
        "USER": "openforms",
        "PASSWORD": "openforms",
        "HOST": "",  # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        "PORT": "",  # Set to empty string for default.
    }
}

INGENICO_BACKEND = {
    "config_file": os.path.join(ROOT_DIR, "ingenico-sandbox.txt"),
    "api_key_id": "",
    "api_key_secret": "",
    "webhook_key_id": "",
    "webhook_key_secret": "",
}

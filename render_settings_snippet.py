import os
from pathlib import Path

# ... existing settings ...

# Production settings for Render
if os.getenv('RENDER'):
    # Set SECRET_KEY from environment for security
    SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-fallback-key-change-this')
    
    # Database configuration
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': '/var/data/db.sqlite3',  # Render persistent disk location
        }
    }
    
    # HTTPS/Security
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    
    # Allowed hosts - add your Render domain
    ALLOWED_HOSTS = [
        'videodownloader.onrender.com',  # Replace with your actual domain
        'localhost',
        '127.0.0.1'
    ]
    
    # Static files
    STATIC_ROOT = '/var/data/staticfiles'
    STATIC_URL = '/static/'
    
    # Media files - use Render's persistent disk
    MEDIA_ROOT = '/var/data/media'
    MEDIA_URL = '/media/'

from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# Chave secreta
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'default-key')
ENVIRONMENT = os.getenv("DJANGO_ENV", "production")
DEBUG = os.getenv("DJANGO_DEBUG", "False") == "True"

# Hosts permitidos
ALLOWED_HOSTS = [
    "gestaocontratosinteligentes-a3apaqfsc7b0abgh.brazilsouth-01.azurewebsites.net",
    "gestaocontratosinteligentes-a3apaqfsc7b0abgh.brazilsouth-01.azurewebsites.net/",
    "gestaocontratosinteligentes-a3apaqfsc7b0abgh.brazilsouth-01.azurewebsites.net:8501",
    "gestaocontratostela-bee2cpc7gbg7hab9.brazilsouth-01.azurewebsites.net/",
    "gestaocontratostela-bee2cpc7gbg7hab9.brazilsouth-01.azurewebsites.net",
    "localhost",
    "127.0.0.1",
    ".azurewebsites.net"
]

CORS_ALLOW_ALL_ORIGINS = True

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'contratos_inteligentes',
    'rest_framework',
    'corsheaders',
]

CORS_ALLOWED_ORIGINS = [
    "https://gestaocontratosinteligentes-a3apaqfsc7b0abgh.brazilsouth-01.azurewebsites.net",
    "https://gestaocontratosinteligentes-a3apaqfsc7b0abgh.brazilsouth-01.azurewebsites.net:8501"
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'gestao_contratos_inteligentes.urls'

# Templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'gestao_contratos_inteligentes.wsgi.application'

if ENVIRONMENT == "test":
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DJANGO_DB_NAME'),
            'USER': os.getenv('DJANGO_DB_USER'),
            'PASSWORD': os.getenv('DJANGO_DB_PASSWORD'),
            'HOST': os.getenv('DJANGO_DB_HOST'),
            'PORT': os.getenv('DJANGO_DB_PORT'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('PROD_DB_NAME'),
            'USER': os.getenv('PROD_DB_USER'),
            'PASSWORD': os.getenv('PROD_DB_PASSWORD'),
            'HOST': os.getenv('PROD_DB_HOST'),
            'PORT': os.getenv('PROD_DB_PORT'),
        }
    }

# Validação de senha
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internacionalização
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# Arquivos estáticos
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Primary key
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

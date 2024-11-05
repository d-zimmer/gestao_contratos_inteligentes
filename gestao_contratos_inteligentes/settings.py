from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# Chave secreta
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'default-key')

# Ambiente
ENVIRONMENT = os.getenv("DJANGO_ENV", "production")

# Debug
DEBUG = os.getenv("DJANGO_DEBUG", "False") == "True"

# Hosts permitidos
ALLOWED_HOSTS = [
    '.azurewebsites.net',
    "gestaocontratosinteligentes-a3apaqfsc7b0abgh.brazilsouth-01.azurewebsites.net",
    'localhost',
    '127.0.0.1'
]

# Apps instalados
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

# Configurações do CORS
CORS_ALLOWED_ORIGINS = [
    "https://gestaocontratosinteligentes-a3apaqfsc7b0abgh.brazilsouth-01.azurewebsites.net",
]

# Middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.messages.middleware.MessageMiddleware',
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

# Configuração do Banco de Dados
if ENVIRONMENT == "test":
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DJANGO_DB_NAME', 'test_db'),
            'USER': os.getenv('DJANGO_DB_USER', 'postgres'),
            'PASSWORD': os.getenv('DJANGO_DB_PASSWORD', 'postgres'),
            'HOST': os.getenv('DJANGO_DB_HOST', 'localhost'),
            'PORT': os.getenv('DJANGO_DB_PORT', '5432'),
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
            'PORT': os.getenv('PROD_DB_PORT', '5432'),
        }
    }

# Validação de Senha
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
STATIC_ROOT = BASE_DIR / 'staticfiles'  # Para produção, onde coletará todos os arquivos

# Primary key
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

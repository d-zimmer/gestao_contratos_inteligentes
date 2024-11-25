from pathlib import Path
import os
from dotenv import load_dotenv # type: ignore

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv()

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'default-key')
ENVIRONMENT = os.getenv("DJANGO_ENV", "production")
DEBUG = os.getenv("DJANGO_DEBUG", "False") == "True"
ENCRYPTION_KEY = "PKcPPim9-qXIvpQZSx7k1Vri6YWyZBknUBF72mIHcFA="

ALLOWED_HOSTS = [
    "gestaocontratosinteligentes-a3apaqfsc7b0abgh.brazilsouth-01.azurewebsites.net",
    "gestaocontratosinteligentes-a3apaqfsc7b0abgh.brazilsouth-01.azurewebsites.net/",
    "gestaocontratosinteligentes-a3apaqfsc7b0abgh.brazilsouth-01.azurewebsites.net:8501",
    "gestaocontratostela-bee2cpc7gbg7hab9.brazilsouth-01.azurewebsites.net/",
    "gestaocontratostela-bee2cpc7gbg7hab9.brazilsouth-01.azurewebsites.net",
    "localhost",
    "127.0.0.1",
    ".azurewebsites.net",
    "gestaocontratos.brazilsouth.cloudapp.azure.com",
    "4.228.59.7"
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
    'django_celery_results',
    "django_celery_beat",
]

# Configurar o backend e o broker do Celery para o banco de dados
CELERY_BROKER_URL = "sqla+sqlite:///celerydb.sqlite"
CELERY_RESULT_BACKEND = "django-db"  # Salvar resultados das tarefas no banco
CELERY_ACCEPT_CONTENT = ["json"]  # Aceitar apenas JSON
CELERY_TASK_SERIALIZER = "json"  # Serializar tarefas como JSON

CORS_ALLOWED_ORIGINS = [
    "https://gestaocontratosinteligentes-a3apaqfsc7b0abgh.brazilsouth-01.azurewebsites.net",
    "https://gestaocontratosinteligentes-a3apaqfsc7b0abgh.brazilsouth-01.azurewebsites.net:8501",
    "https://gestaocontratos.brazilsouth.cloudapp.azure.com",
    "https://4.228.59.7"
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
        # 'default': {
        #     'ENGINE': 'django.db.backends.postgresql',
        #     'NAME': os.getenv('DJANGO_DB_NAME'),
        #     'USER': os.getenv('DJANGO_DB_USER'),
        #     'PASSWORD': os.getenv('DJANGO_DB_PASSWORD'),
        #     'HOST': os.getenv('DJANGO_DB_HOST'),
        #     'PORT': os.getenv('DJANGO_DB_PORT'),
        # }
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('PROD_DB_NAME', 'gestaocontratos'),
            'USER': os.getenv('PROD_DB_USER', 'david'),
            'PASSWORD': os.getenv('PROD_DB_PASSWORD', 'p**lmonk3y'),
            'HOST': os.getenv('PROD_DB_HOST', '4.228.59.7'),
            'PORT': os.getenv('PROD_DB_PORT', '5432'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('PROD_DB_NAME', 'gestaocontratos'),
            'USER': os.getenv('PROD_DB_USER', 'david'),
            'PASSWORD': os.getenv('PROD_DB_PASSWORD', 'p**lmonk3y'),
            'HOST': os.getenv('PROD_DB_HOST', 'localhost'),
            'PORT': os.getenv('PROD_DB_PORT', '5432'),
        }
    }

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

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'debug.log'),  # Gera o arquivo de log na pasta do projeto
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['file', 'console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'myapp': {  # Configuração para um app específico, se necessário
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

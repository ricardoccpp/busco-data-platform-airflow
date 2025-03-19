"""
Configuração do webserver do Airflow.
Este arquivo pode ser usado para personalizar a interface do Airflow.
"""
import os
from flask_appbuilder.security.manager import AUTH_DB, AUTH_LDAP, AUTH_OAUTH, AUTH_OID, AUTH_REMOTE_USER

# from flask_appbuilder.security.manager import AUTH_OAUTH
# from airflow.www.security import AirflowSecurityManager

# Caminho para o certificado SSL
basedir = os.path.abspath(os.path.dirname(__file__))

# ----------------------------------------------------
# CONFIGURAÇÃO DE AUTENTICAÇÃO
# ----------------------------------------------------
# Para autenticação usando banco de dados (padrão)
AUTH_TYPE = AUTH_DB

# Para autenticação LDAP (descomente se necessário)
# AUTH_TYPE = AUTH_LDAP
# AUTH_LDAP_SERVER = "ldap://ldapserver.new"
# AUTH_LDAP_USE_TLS = False
# AUTH_LDAP_SEARCH = "dc=example,dc=com"
# AUTH_LDAP_BIND_USER = "cn=admin,dc=example,dc=com"
# AUTH_LDAP_BIND_PASSWORD = "admin_password"
# AUTH_LDAP_UID_FIELD = "uid"

# Para autenticação OAuth (descomente se necessário)
# AUTH_TYPE = AUTH_OAUTH
# OAUTH_PROVIDERS = [
#     {
#         'name': 'google',
#         'icon': 'fa-google',
#         'token_key': 'access_token',
#         'remote_app': {
#             'client_id': 'GOOGLE_CLIENT_ID',
#             'client_secret': 'GOOGLE_CLIENT_SECRET',
#             'api_base_url': 'https://www.googleapis.com/oauth2/v2/',
#             'client_kwargs': {
#                 'scope': 'email profile'
#             },
#             'request_token_url': None,
#             'access_token_url': 'https://accounts.google.com/o/oauth2/token',
#             'authorize_url': 'https://accounts.google.com/o/oauth2/auth',
#         }
#     }
# ]

# Se você deseja implementar seu próprio gerenciador de segurança personalizado, descomente abaixo
# SECURITY_MANAGER_CLASS = AirflowSecurityManager

# Configurações de usuários e papéis
# Para uso com autenticação AUTH_DB
SECURITY_MANAGER_CLASS = None
AUTH_USER_REGISTRATION = True
AUTH_USER_REGISTRATION_ROLE = "Public"
FAB_ROLES = {
    "Admin": [
        ["can_read", "WebhookModelView"],
        ["can_create", "WebhookModelView"],
        ["can_edit", "WebhookModelView"],
        ["can_delete", "WebhookModelView"],
    ],
}

# ----------------------------------------------------
# CONFIGURAÇÕES GERAIS
# ----------------------------------------------------
# A chave secreta para o serviço web Flask-WTF
SECRET_KEY = os.environ.get("AIRFLOW__WEBSERVER__SECRET_KEY", "temporary_key")

# Tema a ser usado para as páginas (bootstrap default ou minty, slate, sketchy, etc)
# Mais temas em https://bootswatch.com/
FAB_THEME = "yeti"  # default, cerulean, darkly, flatly, journal, lumen, paper, etc.

# Configuração de internacionalização
# BABEL_DEFAULT_LOCALE = 'pt_BR'
# BABEL_DEFAULT_FOLDER = 'superset/translations'
# LANGUAGES = {
#     'en': {'flag': 'us', 'name': 'English'},
#     'pt_BR': {'flag': 'br', 'name': 'Brazilian Portuguese'},
# }

# Número de itens por página
FAB_API_MAX_PAGE_SIZE = 100
FAB_SQLA_UI_MAX_PAGE_SIZE = 100
PAGE_SIZE = 100

# Comportamento do menu
MENU_CACHE_TIMEOUT = 1
MENU_DEEP_LEVEL = 2

# Personalização da interface
APP_NAME = "Busco Data Platform - Airflow"
APP_ICON = "/static/pin_100.png"
# APP_THEME = "cerulean.css"  # Defina o tema (bootswatch)

# ----------------------------------------------------
# CONFIGURAÇÕES DE DESEMPENHO
# ----------------------------------------------------
# Número de threads por trabalhador
WORKER_THREADS = 4

# Tempo limite para cada requisição HTTP
HTTP_REQUEST_TIMEOUT = 120

# Tempo de vida para itens em cache em segundos
CACHE_LIFETIME = 600

# Tamanho máximo de upload de arquivos em bytes
FAB_MAX_CONTENT_LENGTH = 25 * 1024 * 1024  # 25MB

# ----------------------------------------------------
# CONFIGURAÇÕES DE LOGGING
# ----------------------------------------------------
# Nível de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL = "INFO"

# Formato do log
LOG_FORMAT = "%(asctime)s:%(levelname)s:%(name)s:%(message)s"

# Para personalizar a navbar, rodapé ou CSS, use os seguintes caminhos:
# app.config['CUSTOM_SECURITY_MANAGER'] = CUSTOM_SECURITY_MANAGER
# app.config['NAVBAR_HELP_URL'] = 'https://busco.com.br/help'
# app.config['NAVBAR_LINKS'] = [{
#     'label': 'Busco Docs',
#     'href': 'https://busco.com.br/docs',
#     'icon': 'fa-book',
# }]

# Para ativar CSRF:
WTF_CSRF_ENABLED = True

# Para extensões Flask personalizadas
FLASK_APP_MUTATOR = None

# Timeout para carregamento de estatísticas de DAGs
STORE_SERIALIZED_DAGS = True
STORE_DAG_CODE = True
DAGBAG_IMPORT_TIMEOUT = 60

# Comprometer sessões em cada requisição, mais seguro
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = False  # Defina como True se estiver usando HTTPS
SESSION_COOKIE_SAMESITE = 'Lax'

# Configurações de cabeçalho para segurança
ENABLE_CORS = False
CORS_OPTIONS = {}
X_FRAME_OPTIONS = 'SAMEORIGIN'
# Portal interno de tickets (MVP Django)

MVP funcional de mesa de ayuda interna para gestionar tickets entre usuarios finales y agentes de sistemas.

## Estructura

- `config/`: configuración global Django (settings, urls, wsgi/asgi).
- `core/`: redirección home por rol.
- `accounts/`: áreas y perfil de agente (asignación de áreas).
- `tickets/`: tickets, comentarios, adjuntos, permisos, emails, vistas y seed demo.
- `templates/`: templates con Bootstrap 5.

## Requisitos

- Python 3.10+
- PostgreSQL opcional (si no, SQLite por defecto)

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Variables de entorno

Ejemplo:

```bash
export SECRET_KEY='cambia-esto'
export DEBUG=1
export ALLOWED_HOSTS='127.0.0.1,localhost'
export DATABASE_URL='postgres://usuario:password@localhost:5432/helpdesk'  # opcional

# Email (en dev usa consola por defecto)
export EMAIL_BACKEND='django.core.mail.backends.console.EmailBackend'
export EMAIL_HOST='smtp.tuempresa.com'
export EMAIL_PORT=587
export EMAIL_HOST_USER='usuario'
export EMAIL_HOST_PASSWORD='password'
export EMAIL_USE_TLS=1
export DEFAULT_FROM_EMAIL='helpdesk@tuempresa.com'
```

Si `DATABASE_URL` no se define, se usa `SQLite` automáticamente.

## Migraciones

```bash
python manage.py migrate
```

## Crear superusuario manual

```bash
python manage.py createsuperuser
```

## Cargar datos demo

```bash
python manage.py seed_demo
```

Usuarios demo creados por seed:

- `admin / Admin1234!`
- `agente_infra / Password123!`
- `agente_dev / Password123!`
- `usuario_demo / Password123!`

## Ejecutar el proyecto

```bash
python manage.py runserver
```

- Login: `http://127.0.0.1:8000/accounts/login/`
- Admin: `http://127.0.0.1:8000/admin/`

## Cómo probar emails en consola

Con `EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend`, cada evento de notificación imprime el contenido del email en la terminal donde corre `runserver`.

Eventos implementados:

1. Creación de ticket (aviso a agentes de área + confirmación al creador).
2. Respuesta visible de agente (aviso al creador).
3. Respuesta de usuario (aviso a agentes del área y/o asignado).
4. Cambio de estado (aviso al creador).

## Permisos implementados

- **Usuario final**:
  - Crear ticket.
  - Ver solo sus tickets.
  - Responder solo en sus tickets (no cerrados).
  - No ve notas internas.
- **Agente**:
  - Ve tickets de sus áreas.
  - Comenta y agrega nota interna.
  - Cambia estado.
  - Puede asignarse/quitar asignación.
- **Superusuario**:
  - Acceso total.

## Notas de seguridad básica

- Control de acceso por login + validación de permisos por objeto.
- Protección CSRF en formularios.
- Archivos en `MEDIA_ROOT`.
- Validación de tamaño de adjuntos y nombre seguro.

# Active Gym — Configuración e integración de PostgreSQL

## 1. Objetivo

Configurar PostgreSQL como sistema gestor de base de datos de Active Gym e integrarlo con el backend Flask mediante SQLAlchemy.

La configuración debe mantener las credenciales fuera del código fuente y permitir futuras migraciones del esquema de datos.

## 2. Tecnologías utilizadas

- PostgreSQL 16.15
- Flask-SQLAlchemy 3.1.1
- Flask-Migrate 4.1.0
- psycopg 3.3.6
- python-dotenv 1.2.4
- pytest 9.1.1

## 3. Configuración de PostgreSQL

Se creó una base de datos exclusiva para Active Gym.

| Elemento | Valor |
|---|---|
| Motor | PostgreSQL |
| Base de datos | `active_gym_db` |
| Usuario | `active_gym_user` |
| Servidor de desarrollo | `127.0.0.1` |
| Puerto | `5432` |

El usuario `active_gym_user` es propietario de `active_gym_db`.

La aplicación no utiliza el superusuario `postgres` para sus conexiones habituales.

## 4. Configuración del backend

### `app/config.py`

Centraliza la configuración de Flask y obtiene la dirección de conexión mediante la variable de entorno `DATABASE_URL`.

Utiliza `python-dotenv` para cargar las variables definidas en el archivo `.env`.

### `app/extensions.py`

Declara las extensiones:

- `db`: instancia de Flask-SQLAlchemy.
- `migrate`: instancia de Flask-Migrate.

Las extensiones se inicializan dentro de la fábrica de aplicaciones para mantener una arquitectura modular.

### `app/__init__.py`

La función `create_app()`:

1. Crea la aplicación Flask.
2. Carga la configuración.
3. Inicializa SQLAlchemy.
4. Inicializa Flask-Migrate.
5. Registra el Blueprint de salud.

## 5. Variables de entorno

La conexión a PostgreSQL se configura mediante `DATABASE_URL`.

El archivo `.env` contiene los valores locales y no debe incorporarse al repositorio Git.

El archivo `.env.example` proporciona una plantilla sin credenciales reales.

Ejemplo de estructura:

```dotenv
DATABASE_URL=postgresql+psycopg://USUARIO:CONTRASENA@127.0.0.1:5432/BASE_DE_DATOS
```

Las contraseñas con caracteres especiales deben codificarse correctamente dentro de la URL.

## 6. Verificación de la conexión

Se comprobó la conexión real ejecutando una consulta SQL desde Flask mediante SQLAlchemy:

```sql
SELECT current_database();
```

Resultado esperado:

```text
active_gym_db
```

La consulta se ejecutó correctamente.

## 7. Pruebas automatizadas

Se incorporó `tests/test_database.py` para verificar la conexión con PostgreSQL.

Las pruebas actuales comprueban:

- Creación de la aplicación Flask.
- Funcionamiento del endpoint `/api/health`.
- Conexión real con `active_gym_db`.

**Resultado:** 3 pruebas aprobadas.

La prueba de conexión requiere que PostgreSQL esté disponible y que `DATABASE_URL` esté correctamente configurada.

## 8. Consideraciones de seguridad

- No almacenar contraseñas directamente en el código Python.
- No incorporar `.env` al repositorio.
- Utilizar un usuario específico para la aplicación.
- No utilizar el superusuario `postgres` como cuenta habitual del backend.
- Mantener las credenciales fuera de los mensajes de error y registros compartidos.

## 9. Próximos pasos

- Revisar y registrar los cambios en Git.
- Preparar las migraciones de base de datos.
- Implementar los modelos de datos conforme a los requisitos aprobados de Active Gym.
- Incorporar pruebas para las operaciones de persistencia.
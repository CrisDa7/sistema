# Active Gym — Configuración inicial del backend

## 1. Objetivo

Establecer la estructura inicial del backend de Active Gym utilizando Python y Flask, aplicando una arquitectura modular que facilite el mantenimiento, las pruebas y la incorporación de nuevas funcionalidades.

## 2. Tecnologías utilizadas

- Python 3.12.3
- Flask 3.1.3
- pytest 9.1.1
- Git
- Entorno virtual de Python (`.venv`)

## 3. Arquitectura inicial

Se implementó el patrón Application Factory mediante la función `create_app()`, responsable de crear y configurar la aplicación Flask.

Se incorporó un Blueprint para organizar las rutas de verificación del servicio.

### Estructura

```text
backend/
├── app/
│   ├── __init__.py
│   └── routes/
│       ├── __init__.py
│       └── health.py
├── tests/
│   └── test_health.py
└── requirements.txt
```

## 4. Endpoint implementado

**Método:** GET

**Ruta:** `/api/health`

**Propósito:** comprobar que la API se encuentra disponible.

**Respuesta esperada:**

```json
{
  "status": "ok",
  "message": "Active Gym API funcionando correctamente"
}
```

**Código HTTP:** 200 OK.

## 5. Pruebas automatizadas

Se implementaron dos pruebas:

- `test_create_app`: verifica que Flask crea correctamente la aplicación.
- `test_health_endpoint`: comprueba el código HTTP, el formato JSON y el contenido de la respuesta.

**Resultado:** 2 pruebas aprobadas.

## 6. Comandos principales

Instalar dependencias:

```bash
python -m pip install -r requirements.txt
```

Ejecutar el servidor de desarrollo:

```bash
flask --app app run --debug
```

Ejecutar las pruebas:

```bash
python -m pytest -v
```

Consultar las rutas registradas:

```bash
flask --app app routes
```

## 7. Consideraciones de seguridad

- El entorno virtual no se almacena en Git.
- Los archivos con secretos y variables de entorno están excluidos mediante `.gitignore`.
- El modo de depuración de Flask se utilizará exclusivamente durante el desarrollo local.

## 8. Estado

Configuración inicial del backend implementada y verificada.

**Siguiente etapa:** configuración de PostgreSQL y preparación de la persistencia de datos.
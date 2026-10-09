# SISTEMA

Aplicación web full stack desarrollada con Python, Flask, React, Tailwind CSS y PostgreSQL.

## Descripción

SISTEMA es un proyecto de desarrollo de software orientado al aprendizaje y aplicación de buenas prácticas de ingeniería de software.

Su objetivo es construir una aplicación web modular, mantenible, escalable y documentada, utilizando una arquitectura organizada y patrones de diseño apropiados.

## Tecnologías

### Backend
- Python 3.12
- Flask
- SQLAlchemy
- PostgreSQL 16
- Flask-Migrate

### Frontend
- React
- JavaScript
- Tailwind CSS
- Vite

### Herramientas
- Git y GitHub
- Visual Studio Code
- pytest

## Arquitectura

El proyecto utilizará una arquitectura MVC adaptada a una API REST, incorporando separación por capas:

- **Models:** representación de las entidades de datos.
- **Controllers:** gestión de solicitudes HTTP.
- **Services:** implementación de reglas de negocio.
- **Repositories:** acceso y persistencia de datos.
- **Schemas:** validación y serialización.
- **Frontend:** interfaz de usuario construida con React.

## Estructura prevista

```text
sistema/
├── backend/
├── frontend/
├── docs/
├── .gitignore
└── README.md
```

## Funcionalidades previstas

### Módulo de usuarios

- Registrar usuarios.
- Listar usuarios.
- Consultar un usuario.
- Actualizar información.
- Eliminar usuarios.
- Validar los datos ingresados.

Los datos iniciales de cada usuario serán nombre, apellido y celular.

## Estado del proyecto

**En desarrollo — Fase de configuración inicial.**

## Control de versiones

El proyecto utilizará Git y convenciones de commits para mantener un historial organizado de cambios.

## Licencia

Pendiente de definir.

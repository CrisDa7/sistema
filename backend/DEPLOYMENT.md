# Guía de Despliegue - Active Gym Backend

## Requisitos Previos

- Python 3.12+
- PostgreSQL 14+
- Servidor WSGI (Gunicorn recomendado)
- Variables de entorno configuradas

## Variables de Entorno

Crear archivo `.env` en el directorio raíz del backend:

```bash
# PostgreSQL
DATABASE_URL=postgresql+psycopg://usuario:contraseña@host:puerto/base_datos

# SECRET_KEY (obligatorio en producción)
SECRET_KEY=tu_clave_secreta_aleatoria_segura
```

**Generar SECRET_KEY seguro:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Configuración de Producción

El backend incluye dos configuraciones:

### Config (Desarrollo)
- SECRET_KEY: de entorno o generado aleatorio
- SESSION_COOKIE_SECURE: False (HTTP)
- SESSION_COOKIE_SAMESITE: Lax

### ProductionConfig (Producción)
- SECRET_KEY: obligatorio desde variable de entorno (la aplicación falla al iniciar si no está configurado)
- SESSION_COOKIE_SECURE: True (HTTPS)
- SESSION_COOKIE_SAMESITE: Strict

### Uso

Para desarrollo (predeterminado):
```python
from app import create_app
from app.config import Config

app = create_app(Config)
```

Para producción:
```python
from app import create_app
from app.config import ProductionConfig

app = create_app(ProductionConfig)
```

## Instalación de Dependencias

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

## Migraciones de Base de Datos

El proyecto usa Alembic para migraciones.

### Crear migración inicial
```bash
flask db migrate -m "Initial migration"
```

### Aplicar migraciones
```bash
flask db upgrade
```

### Verificar estado
```bash
flask db current
```

## Crear Administrador

```bash
flask create-admin
```

El comando solicitará:
- Nombre de usuario
- Contraseña (mínimo 12 caracteres, letras y números/símbolos)

## Arranque con Gunicorn

### Instalación
```bash
pip install gunicorn
```

### Comando de arranque
```bash
gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app('app.config.ProductionConfig')"
```

Opciones recomendadas:
- `-w 4`: 4 workers
- `-b 0.0.0.0:5000`: escuchar en todas las interfaces, puerto 5000
- `--timeout 120`: timeout de 120 segundos
- `--access-logfile -`: logs de acceso a stdout

### Con systemd (Linux)

Crear archivo `/etc/systemd/system/active-gym.service`:

```ini
[Unit]
Description=Active Gym Backend
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/ruta/al/backend
Environment="PATH=/ruta/al/backend/.venv/bin"
ExecStart=/ruta/al/backend/.venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 "app:create_app('app.config.ProductionConfig')"
Restart=always

[Install]
WantedBy=multi-user.target
```

Activar e iniciar:
```bash
sudo systemctl enable active-gym
sudo systemctl start active-gym
sudo systemctl status active-gym
```

## Health Check

El endpoint `/api/health` verifica disponibilidad:

```bash
curl https://tu-dominio.com/api/health
```

Respuesta esperada:
```json
{
  "status": "ok",
  "message": "Active Gym API funcionando correctamente"
}
```

## Backup y Restauración

### Backup de PostgreSQL
```bash
pg_dump -U usuario -h host -d active_gym_db > backup_$(date +%Y%m%d).sql
```

### Restauración
```bash
psql -U usuario -h host -d active_gym_db < backup_20241010.sql
```

### Backup Automatizado (cron)
```bash
# Backup diario a las 2 AM
0 2 * * * pg_dump -U usuario -h host -d active_gym_db | gzip > /backups/active_gym_$(date +\%Y\%m\%d).sql.gz
```

## Seguridad en Producción

1. **HTTPS Obligatorio**
   - Configurar certificado SSL/TLS (Let's Encrypt recomendado)
   - ProductionConfig fuerza SESSION_COOKIE_SECURE=True

2. **SECRET_KEY**
   - Nunca compartir ni comprometer
   - Generar valor aleatorio único por despliegue
   - Rotar periódicamente (requiere logout de todos los usuarios)

3. **Base de Datos**
   - Usar usuario PostgreSQL con permisos mínimos
   - No usar usuario con rol de superadmin
   - Limitar conexiones desde IPs específicas

4. **Firewall**
   - Permitir solo puertos necesarios (443, 80)
   - Restringir acceso a PostgreSQL desde IP del servidor de aplicación

5. **Logs**
   - Rotar logs regularmente
   - No incluir SECRET_KEY ni contraseñas en logs
   - Monitorear errores y accesos sospechosos

## Monitoreo

### Métricas clave
- Tiempo de respuesta de endpoints
- Tasa de errores HTTP
- Conexiones a base de datos
- Uso de CPU y memoria

### Logs
- Revisar logs de Gunicorn
- Monitorear errores de autenticación
- Alertar por intentos de fuerza bruta

## Troubleshooting

### Error: SECRET_KEY no está configurado
**Solución:** Establecer variable de entorno SECRET_KEY antes de arrancar.

### Error: Base de datos incorrecta
**Solución:** Verificar DATABASE_URL apunta a la base correcta.

### Error: Migraciones fallan
**Solución:** Verificar estado con `flask db current` y aplicar `flask db upgrade`.

### Sesiones expiran prematuramente
**Solución:** Ajustar PERMANENT_SESSION_LIFETIME en configuración.

## Versionado de Dependencias

El archivo `requirements.txt` tiene versiones fijas para reproducibilidad.

Para actualizar dependencias:
```bash
pip list --outdated
pip install nombre_paquete==nueva_version
pip freeze > requirements.txt
```

## Soporte

Para problemas técnicos o dudas, contactar al equipo de desarrollo.

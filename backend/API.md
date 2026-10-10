# API REST - Active Gym Backend

Documentación de la API REST de Active Gym para integración con frontend.

## Configuración Base

### URL Base
- **Desarrollo**: `http://localhost:5000/api`
- **Producción**: `https://tu-dominio.com/api`

### Headers
- `Content-Type: application/json`
- Para operaciones de escritura: `X-CSRF-Token: <token>` o incluir `csrf_token` en el JSON

### Cookies
La API usa cookies de sesión Flask para autenticación. Las cookies se manejan automáticamente por el navegador.

---

## Flujo de Autenticación

### 1. Obtener Token CSRF
```http
GET /api/auth/csrf
```

**Respuesta Exitosa (200):**
```json
{
  "csrf_token": "abc123xyz..."
}
```

### 2. Login
```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "Contraseña123!",
  "csrf_token": "abc123xyz..."
}
```

**Respuesta Exitosa (200):**
```json
{
  "message": "Sesión iniciada correctamente.",
  "admin": {
    "id": 1,
    "username": "admin"
  }
}
```

**Errores:**
- `401`: Credenciales inválidas
- `403`: Token CSRF inválido
- `429`: Demasiados intentos fallidos (fuerza bruta)

### 3. Verificar Estado de Sesión
```http
GET /api/auth/session
```

**Respuesta Exitosa (200):**
```json
{
  "authenticated": true,
  "admin": {
    "id": 1,
    "username": "admin"
  }
}
```

**Respuesta No Autenticado (200):**
```json
{
  "authenticated": false
}
```

### 4. Logout
```http
POST /api/auth/logout
Content-Type: application/json

{
  "csrf_token": "abc123xyz..."
}
```

**Respuesta Exitosa (200):**
```json
{
  "message": "Sesión cerrada correctamente."
}
```

---

## Clientes

### Registrar Cliente
```http
POST /api/clients
Content-Type: application/json
X-CSRF-Token: <token>

{
  "cedula": "0102030400",
  "first_name": "Juan",
  "last_name": "Pérez",
  "phone": "0991234567"
}
```

**Respuesta Exitosa (201):**
```json
{
  "id": 1,
  "cedula": "0102030400",
  "first_name": "Juan",
  "last_name": "Pérez",
  "phone": "0991234567",
  "registration_date": "2024-10-10"
}
```

**Errores:**
- `400`: Datos inválidos (cédula incorrecta, teléfono inválido, etc.)
- `409`: Cédula duplicada

### Listar Clientes
```http
GET /api/clients
```

**Respuesta Exitosa (200):**
```json
[
  {
    "id": 1,
    "cedula": "0102030400",
    "first_name": "Juan",
    "last_name": "Pérez",
    "phone": "0991234567",
    "registration_date": "2024-10-10"
  }
]
```

### Buscar Clientes
```http
GET /api/clients?search=Juan
```

### Obtener Cliente por ID
```http
GET /api/clients/{client_id}
```

**Respuesta Exitosa (200):**
```json
{
  "id": 1,
  "cedula": "0102030400",
  "first_name": "Juan",
  "last_name": "Pérez",
  "phone": "0991234567",
  "registration_date": "2024-10-10"
}
```

**Error (404):** Cliente no encontrado

### Actualizar Cliente
```http
PATCH /api/clients/{client_id}
Content-Type: application/json
X-CSRF-Token: <token>

{
  "first_name": "Juan Carlos",
  "phone": "0998765432"
}
```

**Respuesta Exitosa (200):**
```json
{
  "id": 1,
  "cedula": "0102030400",
  "first_name": "Juan Carlos",
  "last_name": "Pérez",
  "phone": "0998765432",
  "registration_date": "2024-10-10"
}
```

**Nota:** `cedula`, `id` y `registration_date` no se pueden modificar.

---

## Áreas

### Crear Área
```http
POST /api/areas
Content-Type: application/json
X-CSRF-Token: <token>

{
  "name": "Pesas"
}
```

**Respuesta Exitosa (201):**
```json
{
  "id": 1,
  "name": "Pesas",
  "is_active": true
}
```

**Errores:**
- `400`: Nombre inválido
- `409`: Nombre duplicado

### Listar Áreas
```http
GET /api/areas
```

### Obtener Área por ID
```http
GET /api/areas/{area_id}
```

### Actualizar Área
```http
PATCH /api/areas/{area_id}
Content-Type: application/json
X-CSRF-Token: <token>

{
  "name": "Pesas Libre"
}
```

---

## Planes

### Crear Plan
```http
POST /api/plans
Content-Type: application/json
X-CSRF-Token: <token>

{
  "name": "Mensual Completo",
  "price": "50.00",
  "area_ids": [1, 2]
}
```

**Respuesta Exitosa (201):**
```json
{
  "id": 1,
  "name": "Mensual Completo",
  "price": "50.00",
  "is_active": true,
  "areas": [
    {"id": 1, "name": "Pesas"},
    {"id": 2, "name": "Cardio"}
  ]
}
```

**Errores:**
- `400`: Datos inválidos, áreas inexistentes
- `409`: Nombre duplicado

### Listar Planes
```http
GET /api/plans
```

### Obtener Plan por ID
```http
GET /api/plans/{plan_id}
```

### Actualizar Plan
```http
PATCH /api/plans/{plan_id}
Content-Type: application/json
X-CSRF-Token: <token>

{
  "name": "Mensual Plus",
  "price": "60.00",
  "area_ids": [1, 2, 3]
}
```

---

## Membresías

### Registrar Membresía
```http
POST /api/memberships
Content-Type: application/json
X-CSRF-Token: <token>

{
  "client_id": 1,
  "plan_id": 1,
  "start_date": "2024-10-10",
  "end_date": "2024-11-10",
  "area_ids": [1, 2],
  "contracted_price": "50.00"
}
```

**Respuesta Exitosa (201):**
```json
{
  "id": 1,
  "client_id": 1,
  "plan_id": 1,
  "start_date": "2024-10-10",
  "end_date": "2024-11-10",
  "contracted_price": "50.00",
  "areas": [
    {"id": 1, "name": "Pesas"},
    {"id": 2, "name": "Cardio"}
  ],
  "status": "vigente",
  "reminder_date": "2024-11-10"
}
```

**Estados posibles:**
- `pendiente`: La fecha de inicio es futura
- `vigente`: Fecha actual entre start_date y end_date
- `vencida`: Fecha actual posterior a end_date

**Errores:**
- `400`: Datos inválidos, áreas inexistentes
- `404`: Cliente o plan no encontrado
- `409`: Conflicto con otra membresía (mismas áreas y fechas solapadas)

### Listar Membresías
```http
GET /api/memberships
```

### Obtener Membresía por ID
```http
GET /api/memberships/{membership_id}
```

### Obtener Membresías de un Cliente
```http
GET /api/clients/{client_id}/memberships
```

### Renovar Membresía

#### Modo Continuidad
```http
POST /api/memberships/{membership_id}/renew
Content-Type: application/json
X-CSRF-Token: <token>

{
  "mode": "continuity",
  "area_ids": [1, 2],
  "contracted_price": "50.00"
}
```

**Comportamiento:** La nueva membresía inicia el día siguiente al `end_date` de la membresía anterior.

#### Modo Reingreso
```http
POST /api/memberships/{membership_id}/renew
Content-Type: application/json
X-CSRF-Token: <token>

{
  "mode": "reentry",
  "start_date": "2024-12-01",
  "area_ids": [1, 2],
  "contracted_price": "50.00"
}
```

**Comportamiento:** La nueva membresía inicia en la fecha especificada (para reingresos tras ausencia).

---

## Pagos

### Registrar Pago
```http
POST /api/memberships/{membership_id}/payments
Content-Type: application/json
X-CSRF-Token: <token>

{
  "amount": "50.00",
  "payment_method": "cash",
  "payment_date": "2024-10-10"
}
```

**Métodos de pago:**
- `cash`: Efectivo
- `bank_transfer`: Transferencia bancaria

**Para transferencia bancaria:**
```json
{
  "amount": "50.00",
  "payment_method": "bank_transfer",
  "payment_date": "2024-10-10",
  "transfer_reference": "REF123456",
  "observations": "Pago desde Banco X"
}
```

**Respuesta Exitosa (201):**
```json
{
  "id": 1,
  "membership_id": 1,
  "amount": "50.00",
  "payment_method": "cash",
  "payment_date": "2024-10-10",
  "created_at": "2024-10-10T15:30:00",
  "transfer_reference": null,
  "observations": null
}
```

**Errores:**
- `400`: Datos inválidos, monto no coincide con precio contratado
- `404`: Membresía no encontrada
- `409`: Pago duplicado o referencia bancaria duplicada

### Verificar Estado de Pago
```http
GET /api/memberships/{membership_id}/payment-status
```

**Respuesta Exitosa (200):**
```json
{
  "membership_id": 1,
  "contracted_price": "50.00",
  "paid": true,
  "payment_id": 1
}
```

### Listar Pagos de una Membresía
```http
GET /api/memberships/{membership_id}/payments
```

### Obtener Pago por ID
```http
GET /api/payments/{payment_id}
```

---

## Health Check

```http
GET /api/health
```

**Respuesta Exitosa (200):**
```json
{
  "status": "ok",
  "message": "Active Gym API funcionando correctamente"
}
```

---

## Códigos de Error Comunes

| Código | Significado |
|--------|-------------|
| 400 | Datos inválidos o mal formateados |
| 401 | No autenticado (sesión inválida o expirada) |
| 403 | Token CSRF inválido o ausente |
| 404 | Recurso no encontrado |
| 409 | Conflicto (duplicado, solapamiento, etc.) |
| 429 | Demasiados intentos (fuerza bruta) |
| 500 | Error interno del servidor |

---

## Ejemplo de Flujo Completo

### 1. Login y obtener CSRF
```javascript
// 1. Obtener CSRF
const csrfResponse = await fetch('/api/auth/csrf');
const { csrf_token } = await csrfResponse.json();

// 2. Login
const loginResponse = await fetch('/api/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: 'admin',
    password: 'Contraseña123!',
    csrf_token
  })
});
```

### 2. Registrar cliente
```javascript
const clientResponse = await fetch('/api/clients', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-CSRF-Token': csrf_token
  },
  body: JSON.stringify({
    cedula: '0102030400',
    first_name: 'Juan',
    last_name: 'Pérez',
    phone: '0991234567'
  })
});
const client = await clientResponse.json();
```

### 3. Crear áreas y plan
```javascript
// Crear áreas
const area1 = await createArea('Pesas');
const area2 = await createArea('Cardio');

// Crear plan
const plan = await createPlan('Mensual', '50.00', [area1.id, area2.id]);
```

### 4. Registrar membresía
```javascript
const membership = await fetch('/api/memberships', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-CSRF-Token': csrf_token
  },
  body: JSON.stringify({
    client_id: client.id,
    plan_id: plan.id,
    start_date: '2024-10-10',
    end_date: '2024-11-10',
    area_ids: [area1.id, area2.id],
    contracted_price: '50.00'
  })
});
```

### 5. Registrar pago
```javascript
const payment = await fetch(`/api/memberships/${membership.id}/payments`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-CSRF-Token': csrf_token
  },
  body: JSON.stringify({
    amount: '50.00',
    payment_method: 'cash',
    payment_date: '2024-10-10'
  })
});
```

### 6. Renovar membresía
```javascript
const renewed = await fetch(`/api/memberships/${membership.id}/renew`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-CSRF-Token': csrf_token
  },
  body: JSON.stringify({
    mode: 'continuity',
    area_ids: [area1.id, area2.id],
    contracted_price: '50.00'
  })
});
```

---

## Recomendaciones para Frontend

### Manejo de Sesión
- Las cookies se manejan automáticamente por el navegador
- Verificar `/api/auth/session` para saber si el usuario está autenticado
- Redirigir a login si `authenticated` es `false`

### CSRF
- Obtener un nuevo token CSRF antes de cada operación de escritura
- Incluir el token en el header `X-CSRF-Token` o en el JSON como `csrf_token`
- Si recibes 403, obtener un nuevo token y reintentar

### Validaciones de Cliente
- Validar cédulas ecuatorianas en el frontend antes de enviar
- Validar teléfonos (10 dígitos, empiezan con 09)
- Mostrar errores específicos del servidor al usuario

### Snapshots Históricos
- Las áreas y precios de una membresía se guardan en el momento de creación
- Si el plan o las áreas cambian en el futuro, las membresías existentes no se afectan
- Esto permite mantener historial de contratos

### Estados de Membresía
- Mostrar el estado (`pendiente`, `vigente`, `vencida`) en la UI
- Usar `reminder_date` para mostrar alertas de vencimiento
- El status se calcula dinámicamente según la fecha actual

---

## Consideraciones de Seguridad

1. **HTTPS en Producción**: En producción, la API requiere HTTPS. Las cookies `Secure` solo se envían sobre HTTPS.

2. **CSRF Obligatorio**: Todas las operaciones POST, PUT, PATCH, DELETE requieren token CSRF válido.

3. **Autenticación**: Todas las rutas excepto `/api/health`, `/api/auth/csrf`, `/api/auth/login`, `/api/auth/logout`, `/api/auth/session` requieren autenticación.

4. **Sesiones**: Las sesiones expiran después de 8 horas de inactividad.

5. **Fuerza Bruta**: Después de 5 intentos fallidos, la IP/usuario se bloquea por 15 minutos.

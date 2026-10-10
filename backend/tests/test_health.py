"""
Pruebas automatizadas del endpoint de salud de Active Gym.

Este módulo verifica que la aplicación Flask se crea
correctamente y que el endpoint GET /api/health
devuelve una respuesta válida.
"""

from app import create_app


def test_create_app():
    """
    Verifica que la fábrica de aplicaciones crea Flask.

    La aplicación debe existir y conservar el nombre
    del paquete principal.
    """

    app = create_app()

    assert app is not None
    assert app.name == "app"


def test_health_endpoint():
    """
    Verifica el funcionamiento del endpoint de salud.

    Comprueba:
        - Código HTTP 200.
        - Respuesta en formato JSON.
        - Estado de la API.
        - Mensaje esperado.
    """

    app = create_app()

    # Crear un cliente HTTP de pruebas sin iniciar un servidor.
    client = app.test_client()

    # Simular una solicitud GET al endpoint.
    response = client.get("/api/health")

    # Comprobar el código de respuesta.
    assert response.status_code == 200

    # Comprobar que Flask devuelve JSON.
    assert response.is_json

    # Convertir la respuesta JSON en un diccionario.
    data = response.get_json()

    # Validar los datos recibidos.
    assert data["status"] == "ok"
    assert data["message"] == (
        "Active Gym API funcionando correctamente"
    )
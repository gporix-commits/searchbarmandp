from django.conf import settings
from django.core.exceptions import PermissionDenied


class RestriccionIPGlobalMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Opcional: Puedes permitir rutas estáticas o de archivos multimedia si lo necesitas
        if request.path.startswith("/static/"):
            return self.get_response(request)

        # 1. Obtener la IP real del cliente (considerando el proxy de Render)
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip_cliente = x_forwarded_for.split(",")[0].strip()
        else:
            ip_cliente = request.META.get("REMOTE_ADDR")

        # 2. Obtener la IP autorizada desde las variables de entorno de Render
        ip_permitida = getattr(settings, "IP_SUPERUSER_PERMITIDA", "")

        # 3. Si hay una IP configurada, comparamos
        if ip_permitida:
            if ip_cliente != ip_permitida:
                raise PermissionDenied(
                    f"Acceso denegado. Tu dirección IP ({ip_cliente}) no está autorizada para ver este sitio."
                )

        response = self.get_response(request)
        return response

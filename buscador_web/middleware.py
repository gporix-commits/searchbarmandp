from django.conf import settings
from django.core.exceptions import PermissionDenied


class RestriccionIPGlobalMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/static/"):
            return self.get_response(request)

        # Obtener la IP real
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip_cliente = x_forwarded_for.split(",")[0].strip()
        else:
            ip_cliente = request.META.get("REMOTE_ADDR")

        ip_permitida = getattr(settings, "IP_SUPERUSER", "")

        # ¡Ojo aquí! Imprimimos en los logs de Render para que veas qué IP detecta
        print(f"--- IP DETECTADA: {ip_cliente} | IP PERMITIDA: {ip_permitida} ---")

        if ip_permitida:
            if ip_cliente != ip_permitida:
                raise PermissionDenied(
                    f"Acceso denegado. Tu dirección IP ({ip_cliente}) no está autorizada."
                )

        response = self.get_response(request)
        return response

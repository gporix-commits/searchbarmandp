from django.core.exceptions import PermissionDenied
from .models import (
    PerfilUsuario,
)  # Ajusta la importación según dónde hayas puesto el modelo PerfilUsuario


class RestriccionIPMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. Si el usuario está autenticado
        if request.user.is_authenticated:
            # 2. Excepción: Si es superusuario, lo dejamos pasar libremente
            if not request.user.is_superuser:
                # 3. Intentamos obtener la IP permitida del usuario
                try:
                    perfil = request.user.perfilusuario
                    ip_permitida = perfil.ip_permitida

                    # Si tiene una IP configurada, la validamos
                    if ip_permitida:
                        # Obtenemos la IP real del cliente (considerando si hay proxies como en Render)
                        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
                        if x_forwarded_for:
                            ip_cliente = x_forwarded_for.split(",")[0].strip()
                        else:
                            ip_cliente = request.META.get("REMOTE_ADDR")

                        # Comparamos la IP
                        if ip_cliente != ip_permitida:
                            raise PermissionDenied(
                                "No tienes autorización para acceder desde esta dirección IP."
                            )

                except PerfilUsuario.DoesNotExist:
                    # Si el usuario normal no tiene perfil creado, decides si bloquearlo o dejarlo pasar.
                    # Por seguridad, si requiere IP obligatoria, podrías bloquearlo o dejarlo pasar si no se define.
                    pass

        response = self.get_response(request)
        return response

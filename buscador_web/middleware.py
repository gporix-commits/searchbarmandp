from django.conf import settings
from django.core.exceptions import PermissionDenied
from personas.models import PerfilUsuario


class RestriccionIPPorUsuarioMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/static/"):
            return self.get_response(request)

        # 1. Obtener la IP real del cliente (considerando el proxy de Render)
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip_cliente = x_forwarded_for.split(",")[0].strip()
        else:
            ip_cliente = request.META.get("REMOTE_ADDR")

        # 2. Si el usuario ya inició sesión
        if request.user.is_authenticated:
            # Si es superusuario, pasa libremente
            if request.user.is_superuser:
                return self.get_response(request)

            # Para usuarios normales, verificamos su IP específica en la base de datos
            try:
                perfil = request.user.perfilusuario
                if perfil.ip_permitida and ip_cliente != perfil.ip_permitida:
                    raise PermissionDenied(
                        f"Acceso denegado. Tu usuario no está autorizado desde esta IP ({ip_cliente})."
                    )
            except PerfilUsuario.DoesNotExist:
                # Si el usuario normal no tiene un perfil con IP asignada en la BD, lo bloqueamos por seguridad
                raise PermissionDenied(
                    "Este usuario no tiene una IP autorizada configurada en el sistema."
                )

        else:
            # 3. Si NO ha iniciado sesión (están en la pantalla de login o home pública)
            ip_superuser = getattr(settings, "IP_SUPERUSER_PERMITIDA", "")

            # Verificamos si la IP del visitante está registrada en algún perfil de la base de datos
            ip_registrada_en_db = PerfilUsuario.objects.filter(
                ip_permitida=ip_cliente
            ).exists()

            # Si no es la IP del superuser ni pertenece a ningún usuario registrado en la BD, se bloquea antes de ver el login
            if ip_cliente != ip_superuser and not ip_registrada_en_db:
                raise PermissionDenied(
                    f"Acceso denegado. La dirección IP ({ip_cliente}) no está autorizada."
                )

        response = self.get_response(request)
        return response

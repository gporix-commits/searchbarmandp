from django.contrib import admin
from django.urls import path, include
from personas import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("cuentas/", include("django.contrib.auth.urls")),
    path("buscar/", views.buscar_personas, name="buscar_personas"),
    path("", views.pagina_inicio, name="inicio"),
    path("guardar-busqueda/", views.guardar_historial, name="guardar_historial"),
    path("dashboard/", views.ver_dashboard, name="dashboard"),
    path("buscar-producto/", views.buscar_producto, name="buscar_producto"),
]

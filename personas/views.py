from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.postgres.search import TrigramSimilarity
from .models import Medico, UsuarioBusqueda, Productos
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Q


@login_required(login_url="/cuentas/login/")
def pagina_inicio(request):
    es_jefe = (
        request.user.groups.filter(name="Encargados").exists()
        or request.user.is_superuser
    )
    return render(request, "buscador.html", {"es_encargado": es_jefe})


@login_required
def guardar_historial(request):
    item_id = request.GET.get("id")
    tipo = request.GET.get(
        "tipo", "medico"
    )  # Si no mandan tipo, asumimos que es médico

    if item_id:
        if tipo == "producto":
            # Guardamos el historial para un producto
            producto_seleccionado = Productos.objects.get(cod_producto=item_id)
            UsuarioBusqueda.objects.create(
                usuario=request.user, producto=producto_seleccionado
            )
        else:
            # Guardamos el historial para un médico (comportamiento habitual)
            medico_seleccionado = Medico.objects.get(nro_medico=item_id)
            UsuarioBusqueda.objects.create(
                usuario=request.user, medico=medico_seleccionado
            )

        return JsonResponse({"status": "guardado"})

    return JsonResponse({"status": "error"})


@login_required
def buscar_personas(request):
    query = request.GET.get("q", "").strip()

    if query:
        terminos = query.split()
        consulta_exacta = Q()
        for termino in terminos:
            consulta_exacta &= Q(apeynom__icontains=termino)

        medicos = (
            Medico.objects.annotate(similitud=TrigramSimilarity("apeynom", query))
            .filter(consulta_exacta | Q(similitud__gt=0.5))
            .order_by("-similitud")
            .select_related("cdg_region__id_pais")[:50]
        )
    else:
        medicos = Medico.objects.none()

    resultados = []

    for medico in medicos:
        if medico.cdg_region:
            nombre_pais = (
                medico.cdg_region.id_pais.nombre
                if medico.cdg_region.id_pais
                else "SIN PAÍS"
            )
            codigo_region = medico.cdg_region.cdg_region
        else:
            nombre_pais = "SIN PAÍS"
            codigo_region = "N/A"

        especialidades_lista = [
            esp for esp in [medico.especialidad1, medico.especialidad2] if esp
        ]
        texto_especialidades = " ".join(especialidades_lista)

        texto_provisorio = "Alta Provisoria" if medico.provisorio == "A" else ""
        texto_inactivo = (
            f"Inactivo: {medico.causa}"
            if (medico.activo == "NO" and medico.causa)
            else ("Inactivo" if medico.activo == "NO" else "")
        )

        matricula_texto = medico.matricula1 if medico.matricula1 else ""

        resultados.append(
            {
                "id": medico.nro_medico,
                "pais": nombre_pais,
                "region": codigo_region,
                "nombre": medico.apeynom,
                "matricula": matricula_texto,
                "especialidades": texto_especialidades,
                "inactivo": texto_inactivo,
                "provisorio": texto_provisorio,
            }
        )

    return JsonResponse(resultados, safe=False)


@login_required
def buscar_producto(request):
    query = request.GET.get("q", "").strip()
    resultados = []

    if query:
        # 1. VERIFICAMOS SI EL USUARIO USÓ EL SEPARADOR DE CONCENTRACIÓN
        if "//" in query:
            partes = query.split("//")
            desc_query = partes[0].strip()  # Lo que está antes del //
            conc_query = partes[1].strip()  # Lo que está después del //

            # Filtro para la descripción
            consulta_desc = Q()
            if desc_query:
                for termino in desc_query.split():
                    consulta_desc &= Q(descripcion_raiz__icontains=termino)

            # Filtro para la concentración
            consulta_conc = Q()
            if conc_query:
                for termino in conc_query.split():
                    consulta_conc &= Q(concentracion__icontains=termino)

            # Filtramos exigiendo que coincida la descripción (o similitud) Y la concentración
            productos = (
                Productos.objects.annotate(
                    similitud=TrigramSimilarity("descripcion_raiz", desc_query)
                )
                .filter((consulta_desc | Q(similitud__gt=0.7)) & consulta_conc)
                .order_by("-similitud")
                .select_related("id_labo", "id_forma")
                .prefetch_related("paises_habilitados")[:50]
            )

        # 2. SI NO HAY "//", HACEMOS LA BÚSQUEDA NORMAL
        else:
            terminos = query.split()
            consulta = Q()
            for termino in terminos:
                consulta &= Q(descripcion_raiz__icontains=termino)

            productos = (
                Productos.objects.annotate(
                    similitud=TrigramSimilarity("descripcion_raiz", query)
                )
                .filter(consulta | Q(similitud__gt=0.5))
                .order_by("-similitud")
                .select_related("id_labo", "id_forma")
                .prefetch_related("paises_habilitados")[:50]
            )

        # ========================================================
        # (El resto del código de tu función se mantiene intacto)
        # ========================================================
        for prod in productos:
            abr_labo = prod.id_labo.abr_labo if prod.id_labo else "S/L"

            raiz = prod.descripcion_raiz if prod.descripcion_raiz else ""
            ext = prod.desc_ext if prod.desc_ext else ""
            desc_completa = f"{raiz} / {ext}".strip(" /")

            forma_completa = (
                f"{prod.id_forma.abr_forma} / {prod.id_forma.desc_forma}"
                if prod.id_forma
                else ""
            )
            concentracion = prod.concentracion if prod.concentracion else ""

            paises = prod.paises_habilitados.all()
            lista_abr = [pais.abr_pais for pais in paises if pais.abr_pais]
            habilitaciones_texto = "-".join(lista_abr)

            habilitado_sv = "SV" in lista_abr

            resultados.append(
                {
                    "id": prod.cod_producto,
                    "abr_labo": abr_labo,
                    "desc_completa": desc_completa,
                    "forma": forma_completa,
                    "concentracion": concentracion,
                    "habilitaciones": habilitaciones_texto,
                    "habilitado_sv": habilitado_sv,
                }
            )

    return JsonResponse(resultados, safe=False)


def es_encargado(user):
    return user.groups.filter(name="Encargados").exists() or user.is_superuser


@login_required
@user_passes_test(es_encargado, login_url="/")
def ver_dashboard(request):
    historial = UsuarioBusqueda.objects.select_related(
        "usuario", "medico", "producto"
    ).order_by("-fecha")

    return render(request, "dashboard.html", {"historial": historial})

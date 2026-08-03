import csv
from django.core.management.base import BaseCommand
from personas.models import (
    Productos,
    Pais,
    PaisHabilitacionProducto,
    Forma,
    Laboratorio,
)


class Command(BaseCommand):
    help = (
        "Carga productos, relaciona países y limpia nombres usando un mapeo de alias."
    )

    def handle(self, *args, **kwargs):
        ruta_csv = "FORMATO_CARGA_PRODUCTS_1.csv"

        mapeo_paises = {
            "R.DOMINICANA": "REPUBLICA DOMINICANA",
            "R. DOMINICANA": "REPUBLICA DOMINICANA",
            "REP. DOMINICANA": "REPUBLICA DOMINICANA",
            "COSTA_RICA": "COSTA RICA",
        }

        try:
            with open(ruta_csv, mode="r", encoding="latin1") as archivo:
                # Delimitador de punto y coma
                lector = csv.DictReader(archivo, delimiter=";")

                productos_procesados = 0
                relaciones_creadas = 0

                for fila in lector:
                    cod_prod = fila["cod_producto"]
                    desc_raiz = fila["descripcion_raiz"]
                    desc_ext_val = fila["desc_ext"]
                    concentracion = fila["concentracion"]
                    id_forma_val = fila["id_forma"]

                    # ¡Actualizado para que coincida con tu CSV!
                    id_lab_val = fila["id_labo"]

                    texto_paises = fila["habilitaciones"]

                    forma_inst = None
                    if id_forma_val:
                        forma_inst = Forma.objects.filter(id_forma=id_forma_val).first()

                    lab_inst = None
                    if id_lab_val:
                        lab_inst = Laboratorio.objects.filter(
                            id_labo=id_lab_val
                        ).first()

                    producto, _ = Productos.objects.update_or_create(
                        cod_producto=cod_prod,
                        defaults={
                            "descripcion_raiz": desc_raiz,
                            "concentracion": concentracion,
                            "desc_ext": desc_ext_val,
                            "id_forma": forma_inst,
                            "id_labo": lab_inst,
                        },
                    )
                    productos_procesados += 1

                    if texto_paises:
                        lista_paises = texto_paises.split("-")

                        for nombre_pais in lista_paises:
                            nombre_limpio = (
                                nombre_pais.strip().upper().replace("_", " ")
                            )

                            if nombre_limpio in mapeo_paises:
                                nombre_limpio = mapeo_paises[nombre_limpio]

                            pais_bd = Pais.objects.filter(
                                nombre__icontains=nombre_limpio
                            ).first()

                            if pais_bd:
                                _, rel_creada = (
                                    PaisHabilitacionProducto.objects.get_or_create(
                                        cod_producto=producto, id_pais=pais_bd
                                    )
                                )
                                if rel_creada:
                                    relaciones_creadas += 1
                            else:
                                self.stdout.write(
                                    self.style.WARNING(
                                        f"⚠️ País '{nombre_limpio}' (original: '{nombre_pais.strip()}') no encontrado para el producto {cod_prod}"
                                    )
                                )

            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ Proceso terminado: {productos_procesados} productos actualizados y {relaciones_creadas} habilitaciones creadas."
                )
            )

        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR(
                    f"❌ No se encontró el archivo '{ruta_csv}' en la raíz del proyecto."
                )
            )

from django.db import models
from django.contrib.auth.models import User


class Pais(models.Model):
    id_pais = models.IntegerField(primary_key=True)
    nombre = models.CharField(max_length=50)
    abr_pais = models.CharField(max_length=2, null=True, blank=True)

    class Meta:
        managed = True
        db_table = "Pais"


class Region(models.Model):
    cdg_region = models.IntegerField(primary_key=True)
    nombre = models.CharField(max_length=20)
    id_pais = models.ForeignKey(Pais, models.DO_NOTHING, db_column="id_pais")

    class Meta:
        managed = True
        db_table = "Region"


class Medico(models.Model):
    nro_medico = models.IntegerField(primary_key=True)
    cdg_region = models.ForeignKey(Region, models.DO_NOTHING, db_column="cdg_region")
    matricula1 = models.IntegerField(blank=True, null=True)
    apeynom = models.CharField(max_length=200)
    especialidad1 = models.CharField(max_length=3)
    especialidad2 = models.CharField(max_length=3, blank=True, null=True)
    id_unico = models.IntegerField(blank=True, null=True)
    provisorio = models.CharField(max_length=1, blank=True, null=True)
    activo = models.CharField(max_length=2, blank=True, null=True)
    causa = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = True
        db_table = "Medico"


class Forma(models.Model):
    id_forma = models.IntegerField(primary_key=True)
    desc_forma = models.CharField(max_length=40)
    abr_forma = models.CharField(max_length=5)

    class Meta:
        managed = True
        db_table = "Forma"


class Laboratorio(models.Model):
    id_labo = models.IntegerField(primary_key=True)
    desc_labo = models.CharField(max_length=20)
    abr_labo = models.CharField(max_length=3)

    class Meta:
        managed = True
        db_table = "Laboratorio"


class PaisHabilitacionProducto(models.Model):
    # AutoField le dice a Django: "No te preocupes por este ID, Postgres lo generará solo"
    id_habilitacion = models.AutoField(primary_key=True)
    cod_producto = models.ForeignKey(
        "Productos", models.DO_NOTHING, db_column="cod_producto"
    )
    id_pais = models.ForeignKey(Pais, models.DO_NOTHING, db_column="id_pais")

    class Meta:
        managed = True
        db_table = "Pais_Habilitacion_Producto"


class Productos(models.Model):
    cod_producto = models.IntegerField(primary_key=True)
    descripcion_raiz = models.CharField(max_length=30, blank=True, null=True)
    concentracion = models.CharField(max_length=40, blank=True, null=True)
    desc_ext = models.CharField(max_length=150, blank=True, null=True)
    id_forma = models.ForeignKey("Forma", models.DO_NOTHING, db_column="id_forma")
    id_labo = models.ForeignKey("Laboratorio", models.DO_NOTHING, db_column="id_labo")

    paises_habilitados = models.ManyToManyField(
        Pais, through="PaisHabilitacionProducto"
    )

    class Meta:
        managed = True
        db_table = "Productos"


class UsuarioBusqueda(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    medico = models.ForeignKey(
        Medico, on_delete=models.CASCADE, db_column="nro_medico", null=True, blank=True
    )
    fecha = models.DateTimeField(auto_now_add=True)
    producto = models.ForeignKey(
        Productos,
        on_delete=models.CASCADE,
        db_column="cod_producto",
        null=True,
        blank=True,
    )

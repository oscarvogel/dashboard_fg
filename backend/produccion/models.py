from django.contrib.auth.models import User

from django.db import models

# Create your models here.

class UnidadNegocio(models.Model):
    id = models.AutoField(primary_key=True, db_column="idUnidadNegocio")
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre
    
    class Meta:
        db_table = 'unidadnegocio'

class TipoMovil(models.Model):
    id = models.AutoField(primary_key=True, db_column="id")
    detalle = models.CharField(max_length=50)

    def __str__(self):
        return self.detalle
    
    class Meta:
        db_table = 'tipodemovil'


class RegistroProduccion(models.Model):
    id = models.AutoField(primary_key=True)
    UN = models.CharField(max_length=50)
    operacion = models.CharField(max_length=50)
    operador = models.CharField(max_length=50)
    fecha = models.DateField(null=True, blank=True)
    equipo = models.CharField(max_length=50)
    operador = models.CharField(max_length=50)
    hr_inicio = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    hr_fin = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    m3 = models.IntegerField(default=0)
    tn_despachadas = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    produccion = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    unidad_produccion = models.CharField(max_length=50, null=True, blank=True)
    hrs_no_operativas = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, db_column='hrs_no_op')
    plantas = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    cod_equipo = models.ForeignKey('Equipo', on_delete=models.CASCADE, db_column='cod_equipo')
    combustible = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    aceite_cadena = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    predio = models.CharField(max_length=50, null=True, blank=True)
    stock_abc = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    acta = models.CharField(max_length=50, null=True, blank=True)
    cod_un = models.ForeignKey(UnidadNegocio, on_delete=models.CASCADE, db_column='cod_un', null=True, blank=True)

    class Meta:
        db_table = 'tablero_produccion'

class Equipo(models.Model):
    
    id = models.AutoField(primary_key=True, db_column="idmovil")
    patente = models.CharField(max_length=30)
    detalle = models.CharField(max_length=255, null=True, blank=True)
    ult_hr_km = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    tipo_movil = models.ForeignKey(TipoMovil, on_delete=models.CASCADE, db_column='tipo_movil', null=True, blank=True)
    baja = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'moviles'     
        
class Empleado(models.Model):
    # Relación con User de Django
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)

    id = models.AutoField(primary_key=True, db_column="idPersonal")
    nombre = models.CharField(max_length=30)
    dni = models.CharField(max_length=8)
    password = models.CharField(max_length=255)
    
    class Meta:
        db_table = 'personal'
        
class LugarCarga(models.Model):
    id = models.AutoField(primary_key=True, db_column="idLugarCarga")
    detalle = models.CharField(max_length=50)
    
    def __str__(self):
        return self.detalle
    
    class Meta:
        db_table = 'lugarcarga'

class Panioles(models.Model):
    idPaniol = models.AutoField(primary_key=True, db_column='idPaniol')
    nombre = models.CharField(max_length=50)
    un = models.ForeignKey(UnidadNegocio, on_delete=models.CASCADE, db_column='un')

    def __str__(self):
        return self.nombre

    class Meta:
        db_table = 'panioles'
        
class CargaCombustible(models.Model):
    id = models.AutoField(primary_key=True, db_column="idCargaComb")
    fecha = models.DateField(null=True, blank=True)
    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE, db_column='idmovil')
    litros = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    unidad_negocio = models.ForeignKey(UnidadNegocio, on_delete=models.CASCADE, db_column='UnidadNegocio', null=True, blank=True)
    km = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    lugar_carga = models.ForeignKey(LugarCarga, on_delete=models.CASCADE, db_column='idLugarCarga', null=True, blank=True)
    tipo_mov = models.CharField(max_length=1, choices=[('I', 'Ingreso'), ('E', 'Egreso')], default='I')

    class Meta:
        db_table = 'cargacomb'
        
class ProduccionMensual(models.Model):
    id = models.AutoField(primary_key=True, db_column="id")
    periodo = models.CharField(max_length=7)  # Formato 'YYYY-MM'
    produccion = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    cantidad_equipo = models.IntegerField(default=0)
    unidad_negocio = models.ForeignKey(UnidadNegocio, on_delete=models.CASCADE, db_column='un', null=True, blank=True)

    class Meta:
        db_table = 'produccion_mensual'        
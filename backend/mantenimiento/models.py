from django.db import models
from produccion.models import Empleado, Equipo, UnidadNegocio, Moneda

class UnidadMedida(models.Model):
    id = models.AutoField(primary_key=True)
    descripcion = models.CharField(max_length=80)

    class Meta:
        managed = False
        db_table = 'unidadmedida'
        verbose_name = 'Unidad de Medida'
        verbose_name_plural = 'Unidades de Medida'

    def __str__(self):
        return self.descripcion

class Repuestos(models.Model):
    id = models.AutoField(primary_key=True)
    descripcion = models.CharField(max_length=150)
    stock_actual = models.IntegerField()
    stock_minimo = models.IntegerField()
    costo_unitario = models.FloatField()
    unidad_medida = models.ForeignKey(UnidadMedida, on_delete=models.CASCADE)
    moneda = models.ForeignKey(Moneda, on_delete=models.CASCADE)
    fecha_actualizacion = models.DateField()
    activo = models.BooleanField()
    maneja_stock = models.BooleanField()
    usuario = models.CharField(max_length=30)
    codigo_interno = models.CharField(max_length=30)
    creado = models.DateTimeField()
    id_tango = models.IntegerField(default=0)

    class Meta:
        managed = False # Set to True if you want Django to manage this table
        db_table = 'repuestos' # Assuming the table name is 'repuestos'

    def __str__(self):
        return self.descripcion

class Sector(models.Model):
    id = models.IntegerField(primary_key=True)
    descripcion = models.CharField(max_length=80)
    activo = models.BooleanField()
    cantidad_empleados = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'sectores'
        verbose_name = 'Sector'
        verbose_name_plural = 'Sectores'

    def __str__(self):
        return self.descripcion

class TipoTareas(models.Model):
    id = models.AutoField(primary_key=True)
    tarea = models.CharField(max_length=150)
    cada_cuanto = models.IntegerField()
    anticipacion = models.IntegerField()
    # Assuming tipo_movil_id refers to a model, let's use a ForeignKey.
    # If it's just an integer ID without a related model, keep it as IntegerField.
    # For now, assuming it's an integer ID.
    tipo_movil_id = models.IntegerField() 
    activo = models.BooleanField()
    descripcion = models.TextField()
    usuario = models.CharField(max_length=30)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False # Set to True if you want Django to manage this table
        db_table = 'tipostareas' # Assuming the table name is 'tipo_tareas'
        verbose_name = 'Tipo de Tarea'
        verbose_name_plural = 'Tipos de Tareas'

    def __str__(self):
        return self.tarea

# Create your models here.
class OrdenServicioCabecera(models.Model):
    id = models.AutoField(primary_key=True)
    fecha = models.DateField()
    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE)
    descripcion = models.TextField()
    estado = models.CharField(max_length=20)
    cerrado_por = models.CharField(max_length=30)
    externo = models.BooleanField()
    proveedor = models.IntegerField()  # Assuming proveedor is an ID for now
    mecanico = models.IntegerField()  # Assuming mecanico is an ID for now
    unidad_negocio = models.ForeignKey(UnidadNegocio, on_delete=models.CASCADE)
    usuario = models.CharField(max_length=30)
    creado = models.DateTimeField(auto_now_add=True)
    moneda = models.ForeignKey(Moneda, on_delete=models.CASCADE)
    cambio = models.FloatField()
    orden_servicio = models.CharField(max_length=12)
    planilla_trabajo = models.BooleanField()

    class Meta:
        db_table = 'cab_orden_servicio'
        verbose_name = 'Orden de Servicio Cabecera'
        verbose_name_plural = 'Ordenes de Servicio Cabeceras'
        managed = False

    def __str__(self):
        return f"OS: {self.orden_servicio} - {self.equipo.nombre}"
    

class OrdenServicioDetalle(models.Model):
    id = models.AutoField(primary_key=True)
    cabecera = models.ForeignKey(OrdenServicioCabecera, on_delete=models.CASCADE, db_column='cabecera_id')
    tipo_tarea = models.ForeignKey(TipoTareas, on_delete=models.RESTRICT, db_column='tipo_tarea_id')
    repuesto = models.ForeignKey(Repuestos, on_delete=models.RESTRICT, db_column='repuesto_id', null=True, blank=True)
    cantidad = models.FloatField()
    precio_unitario = models.FloatField()
    preventivo = models.BooleanField()
    correctivo = models.BooleanField()
    realizado = models.BooleanField()
    km_hora = models.FloatField()
    diferencia = models.FloatField()
    detalle = models.TextField()
    fecha_realizacion = models.DateField(null=True, blank=True)
    mecanico = models.ForeignKey(Empleado, on_delete=models.RESTRICT, db_column='mecanico', null=True, blank=True)
    moneda = models.ForeignKey(Moneda, on_delete=models.CASCADE, db_column='moneda_id')
    cambio = models.FloatField()
    observaciones = models.CharField(max_length=200)
    hora_inicio = models.TimeField(null=True, blank=True)
    hora_fin = models.TimeField(null=True, blank=True)
    horas_extras = models.TimeField(null=True, blank=True) # Changed to DurationField for time difference
    sector = models.ForeignKey(Sector, on_delete=models.RESTRICT, db_column='sector_id')

    class Meta:
        db_table = 'det_orden_servicio'
        verbose_name = 'Orden de Servicio Detalle'
        verbose_name_plural = 'Ordenes de Servicio Detalles'
        managed = False

    def __str__(self):
        return f"Detalle OS {self.cabecera.orden_servicio} - {self.detalle}"

# Ejecuta esto en python manage.py shell

from django.contrib.auth.models import User

from produccion.models import Empleado


for emp in Empleado.objects.all():
    username = emp.dni
    password = emp.password  # asumimos que está en texto plano
    first_name = emp.nombre

    # Crear o obtener User
    user, created = User.objects.get_or_create(username=username)

    if created:
        user.set_password(password)  # Django hashea automáticamente
        user.first_name = first_name
        user.save()
        print(f"✅ Usuario creado: {username}")
    else:
        # Si ya existe, actualizamos la contraseña si es necesario
        user.set_password(password)
        user.first_name = first_name
        user.save()
        print(f"🔄 Usuario actualizado: {username}")

    # Vincular con Empleado
    if not emp.user:
        emp.user = user
        emp.save()
        print(f"🔗 Empleado {username} vinculado a User")
    else:
        print(f"⚠️  Empleado {username} ya tenía User")

print("✅ Migración completada.")
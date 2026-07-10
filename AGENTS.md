# AGENTS.md — Loop de trabajo para proyectos de Óscar

Este repositorio debe trabajarse con un loop operativo repetible, no con prompts aislados.

El objetivo es que cada tarea avance de forma ordenada:

**Issue → rama → implementación acotada → validaciones → PR draft → revisión → merge → cleanup → siguiente issue**

---

## 1. Principios generales

* Trabajar siempre desde `main` o la rama base oficial actualizada.
* Crear una rama por issue o tarea.
* Mantener cambios chicos, revisables y testeables.
* No mezclar issues distintos en un mismo PR.
* No implementar fuera de alcance.
* No hacer refactors grandes si no fueron pedidos.
* No modificar datos productivos reales.
* No tocar archivos locales/no trackeados fuera de alcance.
* Si hay dudas fuertes de alcance, frenar y reportar.
* Si hay conflicto real, error de validación o bloqueo de merge, frenar y reportar.
* Todo PR debe abrirse primero como draft.
* No mergear si las validaciones obligatorias no pasan.

---

## 2. Antes de empezar una tarea

1. Verificar estado local:

   ```bash
   git status -sb
   ```

2. Confirmar rama actual.

3. Actualizar rama base:

   ```bash
   git fetch --prune origin
   git pull --ff-only origin main
   ```

4. Confirmar que la rama base está alineada con `origin/main`.

5. Revisar el issue/tarea asignada.

6. Revisar dependencias:

   * Si depende de otro PR no mergeado, no avanzar.
   * Si depende de datos o decisiones faltantes, reportar.
   * Si el bloqueo es real, no inventar solución.

7. Crear rama nueva con formato:

   ```bash
   codex/issue-NN-descripcion-corta
   ```

   O, si no hay issue:

   ```bash
   codex/tarea-descripcion-corta
   ```

---

## 3. Tipos de tareas

### 3.1 Documentación

Si la tarea es documental:

* No modificar código funcional.
* No modificar UI.
* No agregar dependencias.
* Validar formato y consistencia.
* Mantener el PR chico.

Validaciones mínimas:

```bash
git diff --check
```

Si el repo tiene tests rápidos, ejecutarlos también.

---

### 3.2 Modelo / datos / servicios

Si la tarea toca modelos, servicios o reglas funcionales:

* No implementar UI salvo que el issue lo pida.
* No duplicar reglas en pantalla.
* Agregar o actualizar tests.
* Mantener reglas de negocio en servicios/modelos.
* No mezclar impresión, reportes o integraciones futuras si no corresponde.

Validaciones mínimas sugeridas para Python:

```bash
git diff --check
git diff --cached --check
python -m pytest
python -m compileall app
```

Si el repo usa `py -3.12`, preferir:

```bash
py -3.12 -m pytest
py -3.12 -m compileall app
```

---

### 3.3 UI / UX

Si la tarea agrega o modifica pantalla:

* Reutilizar servicios existentes.
* No duplicar reglas de negocio en UI.
* Mantener estilo visual aprobado del proyecto.
* Agregar tests de instanciación/navegación si existen.
* Validar visualmente con Computer Use cuando sea posible.
* Guardar screenshots reales.
* No aprobar visualmente una pantalla sin evidencia.

Validaciones mínimas:

```bash
git diff --check
git diff --cached --check
python -m pytest
python -m compileall app
```

Si existe smoke:

```bash
python -m app.main --smoke
```

Si existe modo demo/UI:

```bash
python -m app.main --demo-ui
```

La evidencia visual debe guardarse en una carpeta tipo:

```text
docs/screenshots/<nombre_tarea>/
```

Agregar un `README.md` explicando las capturas.

Si corresponde, agregar reporte:

```text
docs/<NOMBRE_TAREA>_VISUAL_REVIEW.md
```

El reporte visual debe incluir:

* Fecha.
* Rama/commit validado.
* Comandos ejecutados.
* Resultado de tests.
* Flujo probado.
* Screenshots.
* Hallazgos.
* Veredicto:

  * aprobado visualmente
  * aprobado con observaciones
  * no aprobado

---

### 3.4 Impresión / documentos / reportes

Si la tarea genera documentos, PDFs, remitos, órdenes, reportes o impresiones:

* No modificar UI salvo que sea necesario.
* No modificar reglas de negocio no relacionadas.
* Agregar tests de generación si el proyecto lo permite.
* Validar formato de salida con evidencia.
* Mantener plantillas separadas de lógica cuando sea posible.

---

### 3.5 Integraciones externas

Si la tarea toca APIs, correos, AFIP/ARCA, WhatsApp, n8n, servicios externos o bases externas:

* No usar credenciales reales en código.
* No commitear `.env`.
* Documentar variables necesarias.
* Agregar modo mock/stub si corresponde.
* Separar integración real de tests unitarios.
* No ejecutar acciones productivas sin instrucción explícita.

---

## 4. Implementación

Durante la implementación:

1. Revisar estructura del repo.
2. Buscar patrones existentes antes de crear algo nuevo.
3. Implementar lo mínimo necesario.
4. Agregar tests.
5. Ejecutar validaciones.
6. Corregir errores reales.
7. Mantener commits chicos y claros.

Evitar:

* Cambiar nombres públicos sin necesidad.
* Reordenar archivos masivamente.
* Mezclar formateos con lógica.
* Meter mejoras “ya que estamos”.
* Resolver issues futuros dentro del PR actual.

---

## 5. Validaciones obligatorias

Antes de abrir o actualizar PR, ejecutar las validaciones definidas por el proyecto.

Base sugerida:

```bash
git diff --check
git diff --cached --check
python -m pytest
python -m compileall app
```

Para apps con smoke:

```bash
python -m app.main --smoke
```

Para apps con UI:

```bash
python -m app.main --demo-ui
```

Si algún comando no existe en el proyecto, documentar cuál fue omitido y por qué.

---

## 6. PR

Todo PR debe abrirse primero como draft.

La descripción debe incluir:

* Issue relacionado con `Closes #NN` si aplica.
* Objetivo.
* Cambios realizados.
* Archivos principales modificados.
* Tests agregados o actualizados.
* Validaciones ejecutadas.
* Evidencia visual si aplica.
* Fuera de alcance.
* Riesgos o pendientes.

Formato sugerido:

```markdown
## Objetivo

Closes #NN

## Cambios

- ...

## Tests / Validaciones

- [x] git diff --check
- [x] python -m pytest
- [x] python -m compileall app
- [x] smoke, si aplica
- [x] Computer Use, si aplica

## Evidencia visual

- ...

## Fuera de alcance

- ...

## Riesgos / pendientes

- ...
```

---

## 7. Revisión final del PR

Antes de pasar a ready:

1. Actualizar rama con `main` si corresponde.
2. Revisar diff completo contra la rama base.
3. Confirmar que el alcance coincide con el issue.
4. Repetir validaciones obligatorias.
5. Si es UI, repetir validación visual con Computer Use.
6. Corregir errores reales con commits chicos.
7. Si todo está OK, pasar PR a ready.

---

## 8. Merge

Sólo mergear si:

* El PR está limpio.
* Las validaciones pasan.
* No hay conflictos.
* El issue está correctamente referenciado.
* No hay cambios fuera de alcance.
* En UI, hay evidencia visual real.

Después de mergear:

1. Verificar que el issue se cerró automáticamente.

2. Si no se cerró, cerrarlo manualmente indicando el PR.

3. Actualizar `main` local.

4. Borrar rama local/remota si corresponde.

5. Ejecutar:

   ```bash
   git status -sb
   ```

6. Reportar estado final.

---

## 9. Reporte final esperado

Al terminar cada tarea, reportar:

* Issue trabajado.
* PR creado o mergeado.
* Estado del PR.
* Merge commit si aplica.
* Estado del issue.
* Archivos modificados.
* Validaciones ejecutadas.
* Evidencia visual si aplica.
* Estado local final.
* Siguiente issue recomendado.

---

## 10. Comando corto para ejecutar el loop

Cuando el usuario diga:

```text
Ejecutá el loop para el issue #NN.
```

Se debe aplicar este flujo completo:

1. Revisar issue.
2. Validar dependencias.
3. Crear rama.
4. Implementar alcance acotado.
5. Ejecutar validaciones.
6. Abrir PR draft.
7. Revisar.
8. Si corresponde, pasar ready.
9. Si corresponde, mergear.
10. Limpiar ramas.
11. Reportar resultado final.

---

## 11. Sección específica del proyecto

Cada repositorio debe completar esta sección.

### Nombre del proyecto

`<completar>`

### Stack

`<completar>`

Ejemplos:

* Python / PyQt / MySQL / Peewee
* Django / Vue / MySQL
* FastAPI / Docker / n8n
* VFP / Python bridge

### Comandos reales del proyecto

Tests:

```bash
<completar>
```

Compile/check:

```bash
<completar>
```

Smoke:

```bash
<completar>
```

UI/demo:

```bash
<completar>
```

Build/deploy, si aplica:

```bash
<completar>
```

### Reglas específicas del proyecto

* `<completar>`
* `<completar>`
* `<completar>`

### Archivos/carpetas fuera de alcance local

* `<completar>`
* `<completar>`

### Flujo visual, si aplica

* Comando para abrir UI:

  ```bash
  <completar>
  ```

* Carpeta de screenshots:

  ```text
  docs/screenshots/
  ```

### Orden actual de issues

1. `<completar>`
2. `<completar>`
3. `<completar>`

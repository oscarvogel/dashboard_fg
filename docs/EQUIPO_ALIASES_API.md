# API de aliases de equipos para OpenClaw

## Fuente de verdad

`EquipoAlias` es la fuente de verdad de aliases confirmados. El campo `Equipo.aliases` de `moviles` se conserva como caché compatible y nunca debe escribirse directamente desde un consumidor nuevo.

Un alias activo es globalmente único. La API conserva historial mediante `activo=false`; no borra registros físicamente.

## Autenticación y permisos

Todas las rutas usan JWT:

```http
Authorization: Bearer <JWT>
```

El JWT nunca debe escribirse en logs, mensajes ni archivos del repositorio.

- Buscar equipos y consultar historial: cualquier usuario autenticado.
- Confirmar aliases: `is_staff`, `is_superuser` o permiso `produccion.change_equipoalias`.
- Desactivar aliases: solo `is_staff` o `is_superuser`.
- Sin token: 401.
- Usuario autenticado sin permiso: 403.

## Búsqueda

```http
GET /api/equipos/?q=JS%20220%20F
```

Respuesta:

```json
{
  "query": "JS 220 F",
  "normalized_query": "js220f",
  "total": 1,
  "limit": 50,
  "offset": 0,
  "count": 1,
  "results": [
    {
      "id": 208,
      "patente": "PROCE-Nº2",
      "detalle": "Procesador JCB JS220F - Nº 1",
      "codigo_fg": "",
      "modelo_normalizado": "JCB JS220F",
      "aliases": [],
      "baja": false,
      "match_type": "modelo_normalizado",
      "match_score": 0.8
    }
  ],
  "requires_confirmation": false
}
```

OpenClaw debe respetar `requires_confirmation`. Si es `true`, presenta candidatos al usuario y no elige automáticamente.

Ranking:

1. patente o alias exacto: 1.0;
2. modelo o `codigo_fg` exacto: 0.95;
3. coincidencia parcial en esos campos: 0.8;
4. coincidencia parcial en detalle: 0.6.

## Confirmación

```http
POST /api/equipos/aliases/confirm/
Content-Type: application/json
```

```json
{
  "equipo_id": 208,
  "alias": "JCB",
  "origen": "openclaw",
  "metadata": {
    "source": "whatsapp",
    "conversation_id": "opcional",
    "message_id": "opcional"
  }
}
```

La identidad del confirmador sale exclusivamente del JWT. No enviar ni confiar en `confirmado_por` dentro del payload.

- 201: alias creado.
- 200: alias ya confirmado en el mismo equipo; operación idempotente.
- 400: payload, alias, origen o metadata inválidos.
- 401: falta autenticación.
- 403: usuario sin permiso.
- 404: equipo inexistente.
- 409: alias activo en otro equipo; no se modifica nada.

Respuesta 201/200:

```json
{
  "status": "confirmed",
  "created": true,
  "equipo": {
    "id": 208,
    "patente": "PROCE-Nº2",
    "detalle": "Procesador JCB JS220F - Nº 1"
  },
  "alias": {
    "id": 1,
    "display": "JCB",
    "normalized": "jcb",
    "activo": true,
    "origen": "openclaw",
    "confirmado_por": {
      "id": 123,
      "nombre": "Oscar Vogel"
    },
    "confirmado_at": "2026-07-11T12:00:00-03:00",
    "metadata": {
      "source": "whatsapp"
    }
  }
}
```

Respuesta 409:

```json
{
  "error": "alias_conflict",
  "requires_confirmation": true,
  "candidates": [
    {
      "equipo_id": 209,
      "patente": "PROCE-Nº3",
      "detalle": "Procesador JCB JS220F - Nº 2"
    }
  ]
}
```

## Historial

```http
GET /api/equipos/208/aliases/
```

Devuelve `active` e `history`. El historial incluye aliases inactivos, origen, confirmador y fechas.

## Desactivación

```http
POST /api/equipos/aliases/15/deactivate/
```

Solo administradores. Responde 200 y `changed=false` si ya estaba inactivo.

## Normalización

- trim y espacios colapsados;
- case-insensitive y sin diferencias de acentos;
- guiones Unicode equivalentes;
- espacios y guiones no cambian la clave comparativa;
- `JS 220 F`, `js220f` y `JS220F` son equivalentes;
- `JCB Nº1` y `JCB Nº2` no son equivalentes;
- máximo 120 caracteres;
- números de modelo y ordinales se conservan.

## Endpoint legacy

`PATCH /api/equipos/<patente>/aliases/` continúa disponible temporalmente, protegido y auditado. Responde las cabeceras `Deprecation: true` y `Link` hacia confirmación. OpenClaw no debe usarlo.

## Población inicial

El comando seguro es:

```bash
python manage.py sync_equipo_aliases --dry-run
```

Opciones:

- `--equipo-id ID`: limita el inventario;
- `--apply`: aplica candidatos no ambiguos;
- `--confirmed-by-user-id ID`: obligatorio con `--apply` para auditoría.

Siempre ejecutar y revisar el dry-run productivo antes de considerar `--apply`. El comando no crea equipos, no desactiva aliases y no sobrescribe auditoría manual.

## Restricción vigente del equipo 208

No confirmar ni cargar automáticamente `JCB`, `JS220`, `JS220F` o `Procesador JCB` para el equipo 208. Esa primera carga controlada requiere una nueva confirmación explícita de Oscar después del despliegue.

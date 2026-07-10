# Revision visual: transcripciones de audio WhatsApp

## Fecha y rama

- Fecha: 2026-07-10
- Rama: `codex/issue-27-whatsapp-audio-transcriptions`

## Comandos y flujo

- `npm ci`
- `npm run build`
- Django local con SQLite y datos ficticios
- Login JWT real mediante la pantalla existente
- Navegacion desktop: Control Operativo -> Mensajes WhatsApp
- Viewports: 1440 x 1000 y 390 x 844

## Resultado

Se comprobaron:

- nombre amigable del grupo;
- remitente y fecha/hora;
- identificacion visual de audio;
- transcripcion completada;
- estados `Transcribiendo...` y `No se pudo transcribir`;
- mensaje de texto;
- actualizacion manual;
- ausencia de enlaces o texto con `media_path`;
- navegacion desktop y layout movil.

## Evidencia

- `docs/screenshots/whatsapp_audio_transcriptions/desktop.png`
- `docs/screenshots/whatsapp_audio_transcriptions/mobile.png`

## Hallazgos

La primera iteracion agregaba el acceso al nivel superior y sobrecargaba la barra. Se corrigio ubicandolo dentro de `Control Operativo`, conservando una ruta y pantalla dedicadas.

Los textos con caracteres corruptos observados en la primera captura provenian de la carga de datos ficticios por consola de Windows; se normalizaron y no corresponden a la serializacion de la aplicacion.

## Veredicto

**Aprobado visualmente.**

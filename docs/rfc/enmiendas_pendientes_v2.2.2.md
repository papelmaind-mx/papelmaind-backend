# Enmiendas pendientes — v2.2.2 → v2.2.3

Regla: RFC bloqueante DEBE estar cerrado antes de generar el sprint que lo toca.
Sprint 1 solo requiere cerrar RFC-024 (bloque de claves).

| RFC     | Fix | Prioridad | Bloquea | Motivo                                      | Estado   |
|---------|-----|-----------|---------|---------------------------------------------|----------|
| RFC-024 | F24 | media     | S1      | catalogo_claves_config ausente              | pendiente |
| RFC-035 | F35 | alta      | S8/P1   | validate=False + break en limbo (outbox)    | pendiente |
| RFC-036 | F36 | alta      | S5      | decremento reserva incondicional en FEFO    | pendiente |
| RFC-037 | F37 | media     | S4      | Traslados vacío en líneas exentas (XSD SAT) | pendiente |
| RFC-038 | F38 | crítica   | S3      | columna trace_id fantasma en outbox_eventos | pendiente |
| RFC-ST  | F22/F28 | media  | S4+     | Anexos S/T degradados a stubs               | pendiente |

## Detalle técnico

### F38 — trace_id
- Worker hace `SELECT ... trace_id FROM outbox_eventos`
- Modelo no declara la columna → crash en primera iteración
- Fix: añadir `trace_id VARCHAR(64) NULL` + índice parcial

### F35 — publish validate/break
- `validate=False` viola contrato de envelope
- `else: break` deja evento en limbo (sin intentos, sin DLQ)
- Fix: siempre validar; fallos → excepción → intentos+1

### F36 — reserva en allocator
- `stock_reservado -= cantidad` incondicional en FEFOAllocator
- Incorrecto en POS sync y liquidación de aparado
- Fix: allocator puro; liberación solo en caller con reserva previa

### F37 — CFDI Traslados vacío
- ObjetoImp="01" no debe emitir nodo `<cfdi:Impuestos>`
- Fix: emitir impuestos solo si objeto_imp == "02"

### F24 — catalogo_claves_config
- Tabla de claves canónicas ausente → seed puede inventar claves
- Fix: restaurar bloque de 18 claves (copiar de v2.1.5b / definir abajo)

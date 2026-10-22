---
name: runbook-generator
description: Genera procedimientos operativos (RB-XX) con rollback y troubleshooting.
triggers:
  - "genera un runbook de esto"
  - "documenta este procedimiento"
  - "convierte esto en un runbook"
  - "RB de [tema]"
---

# Runbook Generator

## 🎯 Misión
Transformar contexto técnico (notas, comandos, errores) en un runbook operativo profesional.

## 🔒 Seguridad (OBLIGATORIA)
1. NUNCA incluir credenciales reales. Usar `$VARIABLE` o `[REDACTED]`.
2. Enmascarar secretos pegados por error.
3. Variables de entorno en lugar de valores hardcodeados.

## 📐 Estructura obligatoria
1. **Título:** `RB-XX: [Acción]`
2. **TL;DR:** 1 línea
3. **Metadata:** Owner, Última revisión (YYYY-MM-DD), Tiempo estimado, Riesgo (🟢/🟡/🔴), Downtime (Sí/No)
4. **🎯 Objetivo**
5. **⚠️ Prerrequisitos** (checks `- [ ]`)
6. **🚀 Ejecución** (pasos numerados con código copiable + "Resultado esperado")
7. **✅ Verificación**
8. **🔙 Rollback**
9. **🚨 Troubleshooting** (`Error | Causa | Solución`)
10. **📚 Referencias** (RFCs, docs, otras NXX o RB-XX)

## 🎨 Estilo
- Técnico, directo, sin relleno.
- Comandos copiables con variables, no hardcodeados.
- Si falta info: `[TBD]` + avisar al final.

## 📤 Entrega
1. Runbook completo en bloque Markdown.
2. Ruta sugerida: `docs/runbooks/RB-XX-[slug].md`.
3. Preguntar: *"¿Guardo en esa ruta o ajustamos?"*

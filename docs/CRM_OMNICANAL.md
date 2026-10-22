# CRM Omnicanal Unificado — PapelMaind (canon v2.3.0)

> Implementación: Sprint 5-6. Este documento fija el diseño del canon.

## Bandeja única

Canales convergidos: **WhatsApp, Instagram, Facebook, Telegram, Email, Web**.
Cada conversación es un hilo con contexto de tenant (RLS) y cliente.

```
POST /api/v1/whatsapp/webhook  (HMAC, rol_db erp_worker — F19)
  → resolve_tenant_context(wa_business_id)  ← resuelve tenant SIN token
  → hilo + mensajes persistidos con papeleria_id
```

## Contexto Tenant/Cliente

- Panel lateral: perfil cliente (`tclientes` + `usuario_papeleria_rel`),
  historial de compras (`tventas`), nivel loyalty, notas internas.
- Todo query pasa por RLS (`app.current_tenant_id`): un asesor de la
  papelería A jamás ve hilos de la papelería B.

## Motor BYO-LLM

```
LLM Gateway (application/services/llm_gateway.py)
  ├─ Kimi · Qwen · DeepSeek · Claude · OpenAI GPT-4o · locales (Ollama)
  ├─ Fallback en cascada + presupuesto tokens/tenant/mes
  └─ PII masking (wa_id → SHA-256) ANTES de cualquier LLM
```

Configuración por tenant: `papeleria_api_keys` (cifrado) + `papeleria_configuracion`.

## Escalamiento inteligente (Handoff a humano)

Disparadores canon:
1. **Reglas de negocio**: "hablar con un humano", queja formal, devolución.
2. **Sentimiento/frustración**: score negativo sostenido o 2 errores del bot.
3. **Cierre B2B**: detección de compra mayorista → asesor comercial.

Al dispararse: pausa el bot, notifica (WebSocket + notification_worker),
enruta a asesor/superadmin del tenant y adjunta **resumen IA del hilo**
(generado por el mismo gateway).

## Métricas núcleo

- `erp_crm_first_response_seconds` (por canal)
- `erp_crm_handoff_total` {tenant_id, motivo}
- `erp_llm_tokens_total` {tenant_id, provider}
- Satisfacción post-conversación (NPS por hilo)

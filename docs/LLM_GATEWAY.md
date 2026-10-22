# LLM Gateway (BYO-LLM) — PapelMaind (canon v2.3.0)

> Implementación: Sprint 5-6 junto al CRM omnicanal. Diseño fijado aquí.

## Principio BYO-LLM (Bring Your Own LLM)

Cada papelería conecta SUS credenciales del proveedor que prefiera.
El gateway normaliza la interfaz y la plataforma nunca queda amarrada
a un proveedor.

## Proveedores soportados (canon)

| Proveedor | Modelo base | Uso típico |
|-----------|-------------|-----------|
| Kimi | moonshot-v1 | Chat largo contexto |
| Qwen | qwen-max / qwen-plus | Bilingüe es/en |
| DeepSeek | deepseek-chat | Razonamiento costo-eficiente |
| Claude | claude-sonnet | Guardrails + tono |
| OpenAI | gpt-4o | Multimodal + embeddings |
| Local | Ollama (qwen2.5, llama3) | Privacidad total, 0 egress |

## Contrato del gateway

```python
# src/application/services/llm_gateway.py (Sprint 5)
class LLMGateway:
    providers: dict[str, LLMProvider]   # registrados por tenant
    async def chat(self, tenant_id, messages, *, max_tokens=500, temperature=0.3) -> LLMResponse: ...
    async def embed(self, tenant_id, texts) -> list[list[float]]:   # 1536d
```

Reglas canon:
- **PII masking antes de todo LLM** (wa_id → SHA-256).
- Presupuesto **tokens/tenant/mes** (default 200k) con circuit breaker →
  `respuesta_template` de `ai_agent_reglas`.
- Fallback en cascada proveedor → proveedor → template local.
- embeddings: `text-embedding-3-small` 1536d → pgvector (ivfflat cosine lists=100).

## RAG híbrido (WhatsApp IA — niveles canon)

1. **Nivel 1** Redis FAQ por tenant (respuestas exactas, <10ms)
2. **Nivel 2** pgvector top-5 (catálogo, políticas, historial)
3. **Nivel 3** LLM chain con `<prompt canon="true">`:
   > "Eres el asistente de {tenant_nombre}. Con este contexto: {top5} responde
   > amable y breve en {lang}. NO inventes stock ni precios. Si no sabes,
   > ofrece escalar a un asesor humano."
- Input NO numérico → RAG; numérico → tools directas (precio/stock/FEFO).
- 2 errores consecutivos → ofrecer menú de nuevo (F-flow citas).

## Costos y límites

- Rate limiting Redis token bucket: 30/min por wa_id, 100/min por IP.
- `erp_llm_tokens_total` {tenant_id, provider} + alerta al 80% del presupuesto.

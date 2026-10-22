from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
import sqlalchemy
from app.services.llm_gateway import LLMGateway

router = APIRouter(prefix="/api/v1/crm", tags=["CRM Omnicanal e IA"])

class MensajeEntranteSchema(BaseModel):
    tenant_id: str
    canal: str = Field(..., description="whatsapp, telegram, web, instagram, etc.")
    cliente_id: str
    conversacion_id: str
    mensaje: str
    historial_previo: Optional[List[Dict[str, str]]] = []

@router.post("/webhook/mensaje", status_code=status.HTTP_200_OK)
def procesar_mensaje_omnicanal(
    payload: MensajeEntranteSchema,
    request: Request
):
    """
    Recibe un mensaje de cualquier canal omnicanal, consulta el contexto del tenant,
    invoca al LLM configurado (externo o local) y decide si responde o escala a humano.
    """
    db: Session = request.state.db

    # 1. Aplicar contexto RLS
    db.execute(
        sqlalchemy.text("SELECT set_current_tenant(:tenant_id)"),
        {"tenant_id": payload.tenant_id}
    )

    # 2. Consultar la configuración del LLM preferido por este Tenant
    config_tenant = db.execute(
        sqlalchemy.text("""
            SELECT proveedor_llm, modelo_llm, api_key_llm, prompt_sistema 
            FROM ttenants_config_ia 
            WHERE tenant_id = :tenant_id
        """),
        {"tenant_id": payload.tenant_id}
    ).fetchone()

    # Valores por defecto si el tenant no tiene una configuración personalizada
    proveedor = config_tenant.proveedor_llm if config_tenant else "local"
    modelo = config_tenant.modelo_llm if config_tenant else "llama3"
    api_key = config_tenant.api_key_llm if config_tenant else None
    prompt_sistema = config_tenant.prompt_sistema or (
        "Eres el asistente virtual de PapelMaind, experto en papelería y suministros de oficina. "
        "Ayuda a los clientes a consultar stock, precios y resolver dudas. "
        "Si el cliente muestra enojo, pide factura compleja o solicita un descuento mayorista, "
        "responde exactamente con la etiqueta: [ESCALAR_HUMANO]."
    )

    # 3. Construir el array de mensajes para el LLM
    mensajes_chat = [{"role": "system", "content": prompt_sistema}]
    if payload.historial_previo:
        mensajes_chat.extend(payload.historial_previo)
    
    mensajes_chat.append({"role": "user", "content": payload.mensaje})

    try:
        # 4. Invocar al Gateway LLM agnóstico
        respuesta_ia = LLMGateway.generar_respuesta(
            proveedor=proveedor,
            modelo=modelo,
            mensajes=mensajes_chat,
            api_key=api_key
        )

        # 5. Evaluar si se requiere handoff / escalamiento a humano
        necesita_escalar = "[ESCALAR_HUMANO]" in respuesta_ia
        respuesta_limpia = respuesta_ia.replace("[ESCALAR_HUMANO]", "").strip()

        if necesita_escalar:
            # Registrar evento de escalamiento en la base de datos para el panel del Superadmin/Admin
            db.execute(
                sqlalchemy.text("""
                    INSERT INTO tconversaciones_escaladas (tenant_id, conversacion_id, cliente_id, motivo)
                    VALUES (:tenant_id, :conversacion_id, :cliente_id, 'Disparador automático por IA')
                """),
                {
                    "tenant_id": payload.tenant_id,
                    "conversacion_id": payload.conversacion_id,
                    "cliente_id": payload.cliente_id
                }
            )
            db.commit()

        return {
            "status": "success",
            "canal": payload.canal,
            "respuesta": respuesta_limpia,
            "escalado_a_humano": necesita_escalar
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar el mensaje con el LLM: {str(e)}"
        )

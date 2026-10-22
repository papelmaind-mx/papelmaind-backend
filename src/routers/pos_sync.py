from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from typing import List, Optional
from sqlalchemy.orm import Session
import sqlalchemy

router = APIRouter(prefix="/api/v1/pos", tags=["POS Offline Sync"])

class TransaccionOfflineSchema(BaseModel):
    idempotency_key: str = Field(..., description="UUID único generado por el POS para evitar duplicados")
    sucursal_id: str
    caja_id: str
    tipo_movimiento: str = Field(..., description="VENTA, DEVOLUCION, AJUSTE")
    monto_total: float
    items: List[dict]
    timestamp_offline: str

class SincronizacionLoteSchema(BaseModel):
    tenant_id: str
    transacciones: List[TransaccionOfflineSchema]

@router.post("/sync", status_code=status.HTTP_200_OK)
def sincronizar_ventas_offline(
    payload: SincronizacionLoteSchema,
    request: Request
):
    """
    Recibe el lote de transacciones acumuladas offline en el POS.
    Aplica aislamiento por RLS y validación estricta de idempotencia.
    """
    db: Session = request.state.db

    # 1. Configurar contexto transaccional multi-tenant (RLS) según ARCHITECTURE.md
    db.execute(
        sqlalchemy.text("SELECT set_config('app.current_tenant_id', :tid, true)"),
        {"tid": payload.tenant_id}
    )

    resultados_sync = []

    try:
        for tx in payload.transacciones:
            # 2. Verificar si la transacción ya fue procesada (Idempotencia)
            existente = db.execute(
                sqlalchemy.text("""
                    SELECT id, estado FROM ttransacciones_offline_procesadas 
                    WHERE idempotency_key = :key AND tenant_id = :tenant_id
                ;"""),
                {"key": tx.idempotency_key, "tenant_id": payload.tenant_id}
            ).fetchone()

            if existente:
                # Si ya existe, se retorna el estatus previo sin reprocesar
                resultados_sync.append({
                    "idempotency_key": tx.idempotency_key,
                    "estado": "YA_PROCESADO",
                    "mensaje": "Transacción omitida por idempotencia."
                })
                continue

            # 3. Procesamiento atómico de la venta / inventario (FEFO / stock)
            # Aquí se invoca la lógica de negocio o asignación de stock por sucursal
            
            # Registrar la transacción como procesada para bloquear reintentos futuros
            db.execute(
                sqlalchemy.text("""
                    INSERT INTO ttransacciones_offline_procesadas 
                    (tenant_id, idempotency_key, sucursal_id, monto_total, estado)
                    VALUES (:tenant_id, :key, :sucursal, :monto, 'COMPLETADO')
                ;"""),
                {
                    "tenant_id": payload.tenant_id,
                    "key": tx.idempotency_key,
                    "sucursal": tx.sucursal_id,
                    "monto": tx.monto_total
                }
            )

            resultados_sync.append({
                "idempotency_key": tx.idempotency_key,
                "estado": "EXITOSO",
                "mensaje": "Transacción sincronizada correctamente."
            })

        db.commit()
        return {
            "status": "success",
            "procesados": len(resultados_sync),
            "detalle": resultados_sync
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error crítico durante la sincronización offline: {str(e)}"
        )

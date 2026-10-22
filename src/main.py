from fastapi import FastAPI
from app.core.middleware import TenantMiddleware
from app.routers import crm_gateway # Importar el router del CRM e IA

app = FastAPI(
    title="PapelMaind Enterprise Backend",
    version="2.2.0",
    description="Backend multi-tenant omnicanal con POS offline, facturación CFDI 4.0 y Gateway de IA."
)

# Registrar Middleware de Multi-tenancy y RLS
app.add_middleware(TenantMiddleware)

# Registrar los routers del sistema
app.include_router(crm_gateway.router)

@app.get("/health", tags=["Health Check"])
def health_check():
    return {"status": "healthy", "project": "PapelMaind", "version": "2.2.0"}

# Subir a GitHub — PapelMaind (canon Sección 11: comandos_git_obligatorios)

El repo local ya está inicializado en `main` con 8 commits — S1+S2+S3 completos y verdes (canon-lint 0 issues · ruff OK · pytest 39 passed). Pasos para publicarlo:

> **Dónde está / cómo obtenerlo**: el repositorio vive en este entorno en
> `/home/z/my-project/papelmaind` (con `.git/` e historial completo). También hay un
> **ZIP descargable** (`papelmaind-repo-*.zip`) que incluye `.git/`, así que al
> descomprimirlo tienes el repo exacto con sus commits. Todavía NO está en GitHub
> porque el push requiere tu cuenta (nadie más puede crear el repo por ti).

## 1. Crear el repo en GitHub

- Ir a https://github.com/new
- Nombre: `papelmaind`
- Visibilidad: **Private** (marca en trámite IMPI — código propietario)
- NO inicializar con README/.gitignore/license (ya existen)

## 2. Conectar y subir (copiar/pegar)

```bash
cd papelmaind   # la carpeta del repo (descomprimida del ZIP o clonada)

# Reemplaza [usuario] por tu usuario de GitHub
git remote add origin https://github.com/[usuario]/papelmaind.git

# Autenticación: usa un Personal Access Token (Settings → Developer settings →
# Tokens classic/finos con scope 'repo') — GitHub ya no acepta contraseña.

git push -u origin main

# Rama de desarrollo (canon: flujo PR develop → main)
git checkout -b develop
git push -u origin develop
```

## 3. Proteger ramas + gate F28

En Settings → Branches → Add rule (para `main` y `develop`):
- ✅ Require status checks to pass: **canon-lint** y **backend** (ci.yml)
- ✅ Require pull request before merging

Con eso, `make canon-lint` (F28) queda como gate obligatorio en cada PR,
tal como exige la Sección 12 del canon.

## 4. Secretos para CI (opcionales en P0)

Settings → Secrets and variables → Actions:
- Nada requerido aún (los tests corren en SQLite embebido).

## Alternativa B: push desde este entorno

Si prefieres que el push se haga desde aquí: crea el repo **vacío y privado** en
GitHub (paso 1) y proporciona un **fine-grained PAT** con acceso solo a ese repo,
permiso `Contents: read/write` y expiración corta (1–7 días). Revócalo
inmediatamente después del push en Settings → Developer settings → Tokens.
La opción A (push tú mismo con la guía) es la más segura y recomendada.

## Historial de hitos (estado exacto: `git log --oneline`)

```
0b550d2 docs: historial 7 commits en guía de push
ef34459 feat: S3 POS transaccional — venta idempotente + outbox F17 + DLQ
cf80b53 docs: guía de push a GitHub (canon Sección 11)
e5032f6 chore: infra + docs + frontend placeholders (estructura canon Sección 11)
06598db test: suite E2E 25 passed — T2 fefo_orden + T5 rls_disjoint + T10 cfdi_pac_fallback
c1f83f7 feat: S2 catálogo + impuestos + lotes + FEFO
98f9849 feat: S1 fundación — auth multi-tenant + JWT + refresh ROTACIÓN + RLS
bb10ad2 chore: canon PapelMaind v2.3.0 + gate F28 (lint L1-L6 en cero)
```

# 📓 Sistema de Notas BuJo — Guía para Principiantes

> **¿Qué es esto?** Un sistema de notas técnicas guardadas en tu repo (como un cuaderno Bullet Journal de programador). Cada nota es un archivo `.md` con un número (`N15`, `N16`…), y hay atajos para crearlas, abrirlas y organizarlas sin memorizar comandos.

> **¿Qué necesitas saber antes?** Solo esto: los comandos se escriben en la terminal, se ejecutan con `Enter`, y si algo se ve "trabado", casi siempre es que una comilla quedó abierta o abriste un editor — se arregla con `Esc` y `:q!` + `Enter`.

---

## 🧭 Los 8 comandos que cubren el 90% del uso

| Comando | Qué hace |
|---|---|
| `make help` | Muestra todos los comandos disponibles |
| `make bujo-new TITLE="Titulo idea nueva"` | Crea una nota nueva (`NXX`) |
| `make edit` | Abre la **última** nota en nvim |
| `make edit ID=N15` | Abre la nota `N15` específica |
| `make edit PICK=1` | Menú para elegir nota (requiere `fzf`) |
| `make bujo-index` | Regenera el índice (`docs/bujo/INDEX.md`) |
| `make check` | Verifica que no haya archivos sensibles antes de commitear |
| make list | 
| ./scripts/bujo new "Titulo idea nueva" | Crea una nota nueva (NXX) |
| ./scripts/bujo list | Lista las últimas 20 notas |

---

## 🎯 Primer día: haz esto en orden (15 min)

### Paso 1 — Ver dónde estás

```bash
cd ~/proyectos-python/papelmaind
make help


Paso 2 — Crear tu primera nota
bash

make bujo-new TITLE="Mi primera nota real" PRIORITY=high TAGS=inicio,prueba

Salida esperada:
text

✅ Creada: .../docs/bujo/notes/N15-mi-primera-nota-real.md
   ID: N15 | priority: high | tags: inicio,prueba
✅ INDEX regenerado: N notas → .../INDEX.md

Paso 3 — Abrirla y editarla
bash

make edit ID=N15

Se abre nvim (editor de texto en terminal). Verás la nota con frontmatter, comentarios y 9 bloques (Contexto, Alternativas, Decisión…).

Para escribir:

    Pulsa i (entra a modo insert).

    Escribe debajo de ## Contexto:
    text

    · Tarea: revisar X
    - El sistema usa Y
    ? ¿Por qué Z?

    Pulsa Esc (vuelve a modo normal).

    Escribe :wq y pulsa Enter (guarda y sale).

Paso 4 — Regenerar el índice
bash

make bujo-index

Salida esperada:
text

✅ INDEX regenerado: N notas → .../INDEX.md

Paso 5 — Ver el índice
bash

cat docs/bujo/INDEX.md

Verás tus notas clasificadas en:

    🔴 Alta prioridad (priority: high)

    🟡 Prioridad media (priority: normal)

    🟢 Prioridad baja (priority: low)

    ❌ Retiradas (status: cancelled o done)

Paso 6 — Guardar en Git
bash

make check
# ✅ Limpio: no hay archivos sensibles en stage

git add docs/bujo/
git commit -m "docs(bujo): N15 primera nota real"
git push origin main

Listo. Tu primera nota está creada, editada y versionada.
✍️ Cómo escribir dentro de una nota

Dentro de una nota, cada línea empieza con un símbolo (los "9 significadores BuJo"):
Símbolo	Significado	Ejemplo
·	Tarea (algo por hacer)	· Validar idempotency_key
-	Nota (hecho, información)	- El token expira a los 60 min
o	Evento (fecha, hito)	o Reunión con Mateo el 2026-10-25
*	Prioridad (crítico)	* Rompe el sync si falta el token
!	Idea / inspiración	! Exponer POST /sync/retry
?	Duda bloqueante	? ¿Redis o Postgres para las claves?
@	Esperando a alguien	@ Review de Mateo pendiente
>	Migrada (a otra nota)	> Ver N16
x	Cancelada	x Descartado: usar FIFO

No es obligatorio usarlos todos. Con ·, - y ? cubres el 80%.
🔄 Flujo diario (5 min)
Mañana
bash

cd ~/proyectos-python/papelmaind
cat docs/bujo/INDEX.md        # ver prioridades del día (🔴 primero)
make edit ID=NXX               # abrir la nota a trabajar

Durante el día (captura rápida)

Cuando surja algo que merece sobrevivir >1 semana:
bash

make bujo-new TITLE="Idea nueva" PRIORITY=high TAGS=pos,sync

Tarde
bash

make bujo-index               # regenerar índice
make check                    # verificar seguridad
git add docs/bujo/ && git commit -m "docs(bujo): NXX" && git push origin main

🐛 Si algo falla
"Mi terminal se quedó pasmada, solo veo cursor parpadeando"

Estás dentro de nvim. Sal con:

    Esc

    :q! + Enter (sin guardar)

    o :wq + Enter (guardando)

Nunca uses Ctrl+C para salir de nvim — lo mata de golpe y puede corromper el archivo.
"El commit no se hizo, bash muestra >"

Olvidaste cerrar la comilla. Pulsa Ctrl+C y repite:
bash

git commit -m "texto completo con comilla cerrada"

"El hook bloquea el commit con 🔴 ALTO: archivos sensibles"

Intentaste commitear algo prohibido (.env, papelmaind-setup.md, dev-log/*.md, etc.). Solución:
bash

git restore --staged <archivo>
git commit -m "..."

"make bujo-new no hace nada"

Verifica que estás en la raíz del repo:
bash

pwd     # debe terminar en /papelmaind
ls Makefile    # debe existir

"make edit abre un archivo vacío"

Estás intentando abrir una nota que no existe. Verifica primero:
bash

./scripts/bujo list

📂 ¿Dónde viven las notas?
text

docs/bujo/
├── INDEX.md              ← tabla de contenido (auto-generado, NO editar)
├── README.md             ← qué es esta capa
└── notes/
    ├── N00-inicio-del-sistema.md
    ├── N01-configuracion-git.md
    ├── N14-revisar-idempotencia.md
    ├── N15-solucion-servidor.md
    └── N16-...

Nunca edites INDEX.md a mano — se regenera con make bujo-index y tus cambios se pierden.

Nunca borres notas con rm — usa status: cancelled para conservar el historial.
🎓 Reglas de oro

    Después de editar el frontmatter (priority:, status:, tags:, updated:) → make bujo-index.

    Siempre make check antes de commitear.

    Salir de nvim con :q! o :wq, nunca Ctrl+C.

    Comillas cerradas en git commit -m "...".

    No edites INDEX.md a mano.

    No borres notas con rm si quieres conservar historial.

    Una idea = una nota. No mezcles temas en un solo archivo.

🔗 Más información

    Arquitectura del sistema: docs/ARCHITECTURE.md

    Skills IA disponibles: docs/AUTOMATIZACION-AI-SKILLS.md

    Índice de notas: docs/bujo/INDEX.md

Última actualización: 2026-10-23

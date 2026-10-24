.PHONY: help bootstrap check hooks bujo-new bujo-index edit reindex
.DEFAULT_GOAL := help

help: ## Muestra ayuda
	@grep -E '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  %-14s %s\n", $$1, $$2}'

bootstrap: ## Instala/actualiza la estructura (idempotente)
	@bash scripts/bootstrap-docs.sh

check: ## Verifica que no haya sensibles en stage
	@bash .githooks/pre-commit && echo "✅ Limpio: nada sensible en stage"

hooks: ## Activa los hooks versionados
	@chmod +x .githooks/pre-commit
	@git config core.hooksPath .githooks
	@echo "✅ Hook activo: .githooks/pre-commit"

bujo-new: ## Crea nota: make bujo-new TITLE="Mi decisión"
	@bash scripts/bujo-new.sh "$(TITLE)"

bujo-index: ## Regenera docs/bujo/INDEX.md
	@bash scripts/bujo-reindex.sh

.PHONY: help bootstrap check hooks bujo-new bujo-index edit list reindex

edit:           ## Abre nota BuJo (sin arg=última | make edit ID=N05 | make edit PICK=1)
	@./scripts/bujo-open.sh $(if $(ID),--id $(ID),) $(if $(PICK),--pick,)

list:           ## Lista las últimas 20 notas BuJo
	@./scripts/bujo list

reindex:        ## Alias de bujo-index
	@$(MAKE) bujo-index

.PHONY: help bootstrap check hooks reindex
.DEFAULT_GOAL := help

help: ## Muestra esta ayuda
	@echo "Targets disponibles:"
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

bootstrap: ## Ejecuta bootstrap-docs.sh (idempotente)
	@chmod +x scripts/bootstrap-docs.sh
	@./scripts/bootstrap-docs.sh

check: ## Verifica que no haya archivos sensibles en stage
	@bash .githooks/pre-commit && echo "✅ Limpio: no hay archivos sensibles en stage"

hooks: ## (Re)instala el hook pre-commit
	@chmod +x .githooks/pre-commit
	@git config core.hooksPath .githooks
	@echo "✅ Hook instalado: .githooks/pre-commit"

reindex: ## Regenera docs/bujo/INDEX.md desde frontmatters
	@chmod +x scripts/bujo-reindex.sh
	@./scripts/bujo-reindex.sh

# ==============================================================================
# Canon Lint (F28)
# ==============================================================================
canon-lint:  ## Validar el canon XML contra sí mismo (CI gate F28)
	@XML_FILE=$$(ls -t context-engineer/papelmind_context_engineer_v*.xml 2>/dev/null | head -1); \
	if [ -z "$$XML_FILE" ]; then \
		echo "❌ No se encontró XML canon en context-engineer/"; \
		exit 1; \
	fi; \
	echo "🔍 Linteando: $$XML_FILE"; \
	python3 scripts/canon_lint.py --verbose "$$XML_FILE"

canon-validate:  ## Solo validar XML well-formed
	@XML_FILE=$$(ls -t context-engineer/papelmind_context_engineer_v*.xml 2>/dev/null | head -1); \
	xmllint --noout "$$XML_FILE" && echo "✅ XML well-formed"

canon-stats:  ## Estadísticas del canon
	@XML_FILE=$$(ls -t context-engineer/papelmind_context_engineer_v*.xml 2>/dev/null | head -1); \
	echo "📊 Estadísticas:"; \
	echo "   Archivo: $$XML_FILE"; \
	echo "   Líneas:  $$(wc -l < $$XML_FILE)"; \
	echo "   Modelos: $$(grep -c '<modelo ' $$XML_FILE)"; \
	echo "   Workers: $$(grep -c '<worker ' $$XML_FILE)"

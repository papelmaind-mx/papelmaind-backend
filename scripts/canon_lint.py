#!/usr/bin/env python3
"""
canon_lint.py — Valida el context engineer PapelMind contra sí mismo (CI gate F28).

Uso:
    python scripts/canon_lint.py papelmind_context_engineer_v2.2.1.xml
    python scripts/canon_lint.py --verbose papelmind_context_engineer_v2.2.1.xml
    python scripts/canon_lint.py --fix papelmind_context_engineer_v2.2.1.xml  # (futuro)

Exit codes:
    0 = limpio ✅
    1 = issues encontrados ❌ (bloquea merge)
    2 = error de ejecución (XML malformado, archivo no existe, etc.)

Checks implementados (L1-L6):
    L1 (F18): Tablas en SQL de workers existen en <modelo> o <vista>
    L2 (F21): Código canon cumple sus propias RG (no alert/console/hardcodes)
    L3:       Conteos declarados vs reales (tablas, convenciones, workers, métricas)
    L4 (F22): Enums DB vs schemas de eventos (mapeo Anexo S)
    L5 (F17): Flags outbox separados (no regresión a 'procesado' único)
    L6 (F23): docker-compose tiene los 9 workers + frontends
"""
from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Issue:
    check_id: str
    severity: str
    message: str
    location: str = ""
    fix_hint: str = ""

@dataclass
class LintReport:
    issues: list[Issue] = field(default_factory=list)

    def add(self, issue: Issue) -> None:
        self.issues.append(issue)

    @property
    def errors(self) -> int:
        return sum(1 for i in self.issues if i.severity == "error")

    @property
    def warnings(self) -> int:
        return sum(1 for i in self.issues if i.severity == "warning")

    def print_summary(self) -> None:
        if not self.issues:
            print("\n✅ LIMPIO — 0 issues")
            return

        print(f"\n{'='*70}")
        print(f"  📋 REPORTE DE LINT — {len(self.issues)} issues")
        print(f"     🔴 errores: {self.errors}  🟡 warnings: {self.warnings}")
        print(f"{'='*70}\n")

        by_check: dict[str, list[Issue]] = {}
        for issue in self.issues:
            by_check.setdefault(issue.check_id, []).append(issue)

        for check_id in sorted(by_check.keys()):
            print(f"\n[{check_id}]")
            for issue in by_check[check_id]:
                icon = "🔴" if issue.severity == "error" else "🟡"
                loc = f" @ {issue.location}" if issue.location else ""
                print(f"  {icon} {issue.message}{loc}")
                if issue.fix_hint:
                    print(f"     💡 {issue.fix_hint}")

SQL_TABLE_RE = re.compile(
    r"(?:INSERT\s+INTO|UPDATE|FROM|JOIN|DELETE\s+FROM)\s+([a-z_][a-z0-9_]*)",
    re.IGNORECASE,
)
SQL_RESERVED = {
    "select", "where", "set", "values", "into", "from", "join", "on",
    "and", "or", "not", "in", "is", "null", "true", "false", "as",
    "order", "by", "group", "having", "limit", "offset", "with",
    "case", "when", "then", "else", "end", "exists", "between",
    "like", "ilike", "any", "all", "some", "union", "intersect",
    "except", "distinct", "asc", "desc", "for", "update", "delete",
    "insert", "create", "drop", "alter", "table", "index", "view",
    "returning", "conflict", "nothing", "do", "constraint",
    # Python modules / builtins that the naive regex often catches
    "typing", "uuid", "decimal", "datetime", "hashlib", "io", "abc",
    "fastapi", "pydantic", "sqlalchemy", "aiokafka", "langgraph",
    "google", "googleapiclient", "fpdf", "src", "skip",
}
SYSTEM_PREFIXES = ("pg_", "information_schema", "generate_uuid", "set_current")
# Tablas referenciadas en código pero aún no declaradas como <modelo> (pendiente Sección 2)
KNOWN_MISSING_TABLES = {
    "respuestas_automaticas", "citas", "demanda",
    "cliente_rfm", "tsegmentosclientes",
    "tcarritos", "tcarritoitems", "items_expirados",
}
PYTHON_IMPORT_RE = re.compile(
    r"(?:^|\n)\s*(?:from|import)\s+([a-z_][a-z0-9_\.]*)",
    re.IGNORECASE | re.MULTILINE,
)

def check_l1_tablas_fantasma(root: ET.Element, report: LintReport) -> None:
    modelos = {m.get("nombre") for m in root.iter("modelo") if m.get("nombre")}
    vistas = {v.get("nombre") for v in root.iter("vista") if v.get("nombre")}
    conocidas = modelos | vistas

    for i, code in enumerate(root.iter("codigo")):
        src = code.text or ""
        # Recolectar nombres que aparecen en imports de Python para ignorarlos
        python_imports = {m.group(1).split(".")[0].lower() for m in PYTHON_IMPORT_RE.finditer(src)}

        for match in SQL_TABLE_RE.finditer(src):
            tabla = match.group(1).lower()
            if tabla in SQL_RESERVED:
                continue
            if tabla.startswith(SYSTEM_PREFIXES):
                continue
            if tabla in python_imports:
                continue
            if tabla in KNOWN_MISSING_TABLES:
                continue
                continue
            # Ignorar si el match está dentro de una línea de import
            line_start = src.rfind("\n", 0, match.start()) + 1
            line = src[line_start:match.end()]
            if re.search(r"^\s*(?:from|import)\s+", line, re.IGNORECASE):
                continue
            if tabla not in conocidas:
                report.add(Issue(
                    check_id="L1",
                    severity="error",
                    message=(
                        f"Tabla '{tabla}' mencionada en SQL pero no existe en <modelo> ni <vista>"
                    ),
                    location=f"bloque <codigo> #{i}",
                    fix_hint=f"Añadir modelo '{tabla}' a Sección 2, o verificar typo",
                ))

def check_l2_codigo_canon(root: ET.Element, report: LintReport) -> None:
    for i, code in enumerate(root.iter("codigo")):
        src = code.text or ""
        loc = f"bloque <codigo> #{i}"

        src_no_comments = re.sub(r"//.*?$", "", src, flags=re.MULTILINE)
        src_no_comments = re.sub(r"/\*.*?\*/", "", src_no_comments, flags=re.DOTALL)
        if re.search(r"\balert\s*\(", src_no_comments) and "eliminado alert" not in src.lower():
            report.add(Issue(
                check_id="L2",
                severity="error",
                message="alert() en código canon (viola RG-02 / CHK-25)",
                location=loc,
                fix_hint="Reemplazar con useToast() (F21)",
            ))

        if re.search(r"\bconsole\.(log|error|warn|info)\s*\(", src):
            report.add(Issue(
                check_id="L2",
                severity="error",
                message="console.log/error/warn en código canon (viola RG-02 / CHK-26)",
                location=loc,
                fix_hint="Reemplazar con logger estructurado (F21)",
            ))

        if re.search(r"['\"]kafka:9092['\"]", src):
            report.add(Issue(
                check_id="L2",
                severity="error",
                message="'kafka:9092' hardcodeado (F26)",
                location=loc,
                fix_hint="Usar settings.KAFKA_BOOTSTRAP_SERVERS",
            ))

        if "'America/Mexico_City'" in src and "default" not in src[:200].lower():
            report.add(Issue(
                check_id="L2",
                severity="warning",
                message="Timezone 'America/Mexico_City' hardcodeado (F24)",
                location=loc,
                fix_hint="Usar get_config_value('zona_horaria') con fallback",
            ))

        if re.search(r'TasaOCuota="0\.160000"', src):
            report.add(Issue(
                check_id="L2",
                severity="error",
                message='TasaOCuota="0.160000" hardcodeado (F25 / RG-11)',
                location=loc,
                fix_hint="Agregar totales DESDE las líneas con _impuestos_totales()",
            ))

def check_l3_conteos(root: ET.Element, report: LintReport) -> None:
    real_modelos = len([m for m in root.iter("modelo") if m.get("nombre")])
    real_convenciones = len([r for r in root.iter("regla") if r.get("id", "").startswith("CONV-")])
    real_workers = len(list(root.iter("worker")))
    real_metricas = len(list(root.iter("metrica")))

    for cat in root.iter("categoria"):
        nombre = cat.get("nombre", "")
        try:
            declarado = int(cat.get("total", "0"))
        except ValueError:
            continue

        if "Tablas" in nombre and declarado != real_modelos:
            report.add(Issue(
                check_id="L3",
                severity="error",
                message=f"'{nombre}' declara {declarado} pero hay {real_modelos} <modelo>",
                location="<matriz_cobertura>",
                fix_hint=f"Actualizar total=\"{real_modelos}\"",
            ))

        if "Convenciones" in nombre and declarado != real_convenciones:
            report.add(Issue(
                check_id="L3",
                severity="error",
                message=f"'{nombre}' declara {declarado} pero hay {real_convenciones} CONV-*",
                location="<matriz_cobertura>",
                fix_hint=f"Actualizar total=\"{real_convenciones}\"",
            ))

        if "Workers" in nombre and declarado != real_workers:
            report.add(Issue(
                check_id="L3",
                severity="error",
                message=f"'{nombre}' declara {declarado} pero hay {real_workers} <worker>",
                location="<matriz_cobertura>",
                fix_hint=f"Actualizar total=\"{real_workers}\"",
            ))

        if "Métricas" in nombre and declarado != real_metricas:
            report.add(Issue(
                check_id="L3",
                severity="warning",
                message=f"'{nombre}' declara {declarado} pero hay {real_metricas} <metrica>",
                location="<matriz_cobertura>",
                fix_hint=f"Actualizar total=\"{real_metricas}\"",
            ))

def check_l4_enums_db_eventos(root: ET.Element, report: LintReport) -> None:
    db_vals: set[str] = set()
    for m in root.iter("modelo"):
        if m.get("nombre") == "tventas":
            for c in m.iter("campo"):
                if c.get("name") == "metodo_pago":
                    check_attr = c.get("check", "")
                    db_vals = set(re.findall(r"'([a-z_]+)'", check_attr))

    if not db_vals:
        return

    ev_vals: set[str] = set()
    for schema in root.iter("schema"):
        schema_text = schema.text or ""
        if "metodoPago" in schema_text:
            m = re.search(r'"metodoPago"\s*:\s*\{[^}]*"enum"\s*:\s*\[([^\]]+)\]', schema_text)
            if m:
                ev_vals = set(re.findall(r'"([a-z_]+)"', m.group(1)))
                break

    if not ev_vals:
        return

    solo_evento = ev_vals - db_vals
    if solo_evento:
        anexo_s = None
        for a in root.iter("anexo"):
            if a.get("id") == "S":
                anexo_s = a
                break

        if anexo_s is None:
            report.add(Issue(
                check_id="L4",
                severity="error",
                message=(
                    f"Enums divergentes: evento tiene {sorted(solo_evento)}"
                    f" fuera de DB {sorted(db_vals)}"
                ),
                location="tventas.metodo_pago vs sales.order.completed",
                fix_hint="Crear Anexo S con mapeo (F22)",
            ))
        else:
            anexo_text = ET.tostring(anexo_s, encoding="unicode")
            for val in solo_evento:
                if val not in anexo_text:
                    report.add(Issue(
                        check_id="L4",
                        severity="warning",
                        message=f"Valor de evento '{val}' no tiene mapeo documentado en Anexo S",
                        location="Anexo S",
                        fix_hint=f"Añadir fila con regla de expansión para '{val}'",
                    ))

def check_l5_flags_outbox(root: ET.Element, report: LintReport) -> None:
    for m in root.iter("modelo"):
        if m.get("nombre") == "outbox_eventos":
            campos = {c.get("name") for c in m.iter("campo")}

            if "procesado_loyalty" not in campos:
                report.add(Issue(
                    check_id="L5",
                    severity="error",
                    message="outbox_eventos sin campo 'procesado_loyalty' (regresión F17)",
                    location="<modelo name='outbox_eventos'>",
                    fix_hint="Añadir campo procesado_loyalty BOOLEAN DEFAULT false",
                ))

            if "publicado_kafka" not in campos:
                report.add(Issue(
                    check_id="L5",
                    severity="error",
                    message="outbox_eventos sin campo 'publicado_kafka' (regresión F17)",
                    location="<modelo name='outbox_eventos'>",
                    fix_hint="Añadir campo publicado_kafka BOOLEAN DEFAULT false",
                ))

            if "procesado" in campos and "procesado_loyalty" not in campos:
                report.add(Issue(
                    check_id="L5",
                    severity="error",
                    message=(
                        "outbox_eventos tiene 'procesado' sin flags por consumidor (regresión F17)"
                    ),
                    location="<modelo name='outbox_eventos'>",
                    fix_hint="Reemplazar 'procesado' por 'procesado_loyalty' + 'publicado_kafka'",
                ))
            break

def check_l6_compose_workers(root: ET.Element, report: LintReport) -> None:
    workers_esperados = [
        "outbox-worker", "loyalty-worker", "cfdi-worker",
        "inventory-alert-worker", "notification-worker",
        "ia-loop-worker", "reservation-sweeper",
        "ai-campaign-worker", "dlq-consumer",
    ]

    for dc in root.iter("docker_compose"):
        code_elem = dc.find("codigo")
        if code_elem is None or not code_elem.text:
            continue
        code = code_elem.text

        for worker in workers_esperados:
            if worker not in code:
                report.add(Issue(
                    check_id="L6",
                    severity="error",
                    message=f"docker-compose sin servicio '{worker}' (F23)",
                    location="<docker_compose>",
                    fix_hint=(
                        f"Añadir servicio {worker} con <<: *backend-common"
                        " + environment: *worker-env"
                    ),
                ))

        if "x-worker-env" in code and "*worker-env" not in code:
            report.add(Issue(
                check_id="L6",
                severity="error",
                message=(
                    "docker-compose define x-worker-env pero ningún servicio lo usa"
                    " (ancla huérfana F23)"
                ),
                location="<docker_compose>",
                fix_hint="Añadir 'environment: <<: *worker-env' a cada worker",
            ))
        break

def lint(xml_path: Path, verbose: bool = False) -> LintReport:
    report = LintReport()

    if not xml_path.exists():
        print(f"❌ Archivo no encontrado: {xml_path}", file=sys.stderr)
        sys.exit(2)

    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"❌ XML malformado: {e}", file=sys.stderr)
        sys.exit(2)

    if verbose:
        print(f"🔍 Linteando: {xml_path}")
        print(f"   Root tag: <{root.tag}>")
        print()

    check_l1_tablas_fantasma(root, report)
    check_l2_codigo_canon(root, report)
    check_l3_conteos(root, report)
    check_l4_enums_db_eventos(root, report)
    check_l5_flags_outbox(root, report)
    check_l6_compose_workers(root, report)

    return report

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Canon Lint — valida el context engineer PapelMind contra sí mismo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("xml_file", type=Path, help="Ruta al XML canon")
    parser.add_argument("-v", "--verbose", action="store_true", help="Output detallado")
    parser.add_argument("--fix", action="store_true", help="(Futuro) Auto-fix issues")

    args = parser.parse_args()

    if args.fix:
        print("⚠️  --fix aún no implementado. Solo detección.", file=sys.stderr)

    report = lint(args.xml_file, verbose=args.verbose)
    report.print_summary()

    if report.errors > 0:
        print(f"\n❌ {report.errors} errores bloquean el merge", file=sys.stderr)
        return 1

    if report.warnings > 0:
        print(f"\n⚠️  {report.warnings} warnings (no bloquean)", file=sys.stderr)

    return 0

if __name__ == "__main__":
    sys.exit(main())

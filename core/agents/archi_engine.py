"""
JARVIS 1.5 — ARCHI Engine (Dev & Infrastructure)
SYSTEMS™ · architectofscale.com

ARCHI ist der Dev-Agent. Nutzt primaer Ollama (Tier 2)
fuer alltaegliche Tasks: Bug-Fix, Testing, Daten sammeln.
Nur fuer Code-Reviews und Architektur-Entscheidungen wird Claude (Tier 1) genutzt.

Routing:
  Ollama (Qwen Coder) — Bug-Fix, Testing, einfacher Code, Syntax
  Ollama (Llama)       — Log-Analyse, Daten-Extraktion
  Claude (Sonnet)      — Code-Review, Architektur, Security
"""

import time
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class DevTaskType(Enum):
    # Tier 2 — Ollama (0 EUR)
    BUG_FIX = "bug_fix"
    TESTING = "testing"
    SIMPLE_CODE = "simple_code"
    SYNTAX_FIX = "syntax_fix"
    LOG_ANALYSIS = "log_analysis"
    DATA_MIGRATION = "data_migration"
    DOCUMENTATION = "documentation"
    DEPENDENCY_UPDATE = "dependency_update"

    # Tier 1 — Claude (Qualitaet)
    CODE_REVIEW = "code_review"
    ARCHITECTURE = "architecture"
    SECURITY_AUDIT = "security_audit"
    PERFORMANCE_OPT = "performance_optimization"
    API_DESIGN = "api_design"


# Welches Modell fuer welchen Task-Typ
DEV_MODEL_MAP = {
    DevTaskType.BUG_FIX: "tier2-qwen-coder",
    DevTaskType.TESTING: "tier2-qwen-coder",
    DevTaskType.SIMPLE_CODE: "tier2-qwen-coder",
    DevTaskType.SYNTAX_FIX: "tier2-qwen-coder",
    DevTaskType.LOG_ANALYSIS: "tier2-llama",
    DevTaskType.DATA_MIGRATION: "tier2-qwen-general",
    DevTaskType.DOCUMENTATION: "tier2-llama",
    DevTaskType.DEPENDENCY_UPDATE: "tier2-qwen-general",
    DevTaskType.CODE_REVIEW: "tier1-sonnet",
    DevTaskType.ARCHITECTURE: "tier1-opus",
    DevTaskType.SECURITY_AUDIT: "tier1-sonnet",
    DevTaskType.PERFORMANCE_OPT: "tier1-sonnet",
    DevTaskType.API_DESIGN: "tier1-sonnet",
}


@dataclass
class Bug:
    """Ein Bug-Report."""
    id: str = ""
    title: str = ""
    description: str = ""
    severity: str = "medium"   # critical, high, medium, low
    file_path: str = ""
    error_log: str = ""
    stack_trace: str = ""
    status: str = "open"       # open, analyzing, fixing, testing, resolved
    fix_description: str = ""
    model_used: str = ""
    resolution_time_ms: int = 0


class ArchiEngine:
    """
    ARCHI — Dev & Infrastructure Engine.

    Primaer Ollama-basiert fuer Kosteneffizienz.
    """

    def __init__(self, db_pool=None, brain=None, router=None):
        self.db = db_pool
        self.brain = brain
        self.router = router
        self._bugs = []

    def get_model_for_task(self, task_type: DevTaskType) -> str:
        """Waehle das richtige Modell fuer einen Dev-Task."""
        return DEV_MODEL_MAP.get(task_type, "tier2-qwen-coder")

    def build_bug_fix_prompt(self, bug: Bug) -> str:
        """Baue einen Bug-Fix-Prompt fuer Ollama/Qwen Coder."""
        return f"""Du bist ARCHI, Dev Lead. Finde und behebe diesen Bug.

BUG: {bug.title}
BESCHREIBUNG: {bug.description}
DATEI: {bug.file_path}
SEVERITY: {bug.severity}

ERROR LOG:
```
{bug.error_log[:2000]}
```

STACK TRACE:
```
{bug.stack_trace[:2000]}
```

LIEFERE:
1. Ursache des Bugs (1-2 Saetze)
2. Den Fix (Code-Diff)
3. Test um den Fix zu verifizieren
4. Praeventions-Empfehlung

Format: Direkt, keine Einleitung."""

    def build_code_review_prompt(self, code: str, language: str = "python") -> str:
        """Baue einen Code-Review-Prompt fuer Claude."""
        return f"""Du bist ARCHI, Senior Dev. Reviewe diesen Code.

SPRACHE: {language}

CODE:
```{language}
{code[:5000]}
```

PRUEFE:
1. Bugs und Logik-Fehler
2. Security-Probleme (OWASP Top 10)
3. Performance-Issues
4. Code-Qualitaet und Best Practices
5. Fehlende Error-Handling

FORMAT:
[SEVERITY: critical/high/medium/low]
Zeile X: Problem-Beschreibung
Fix: Konkreter Vorschlag

Am Ende: Gesamt-Bewertung (0-10) und Top-3 Empfehlungen."""

    def build_test_prompt(self, code: str, language: str = "python") -> str:
        """Baue einen Test-Generierungs-Prompt fuer Ollama."""
        return f"""Schreibe Unit Tests fuer diesen Code.

SPRACHE: {language}

CODE:
```{language}
{code[:3000]}
```

ANFORDERUNGEN:
- Teste alle oeffentlichen Funktionen
- Edge Cases abdecken
- Mindestens 3 Tests pro Funktion
- Framework: pytest (Python), jest (JS)

Liefere nur den Test-Code, keine Erklaerung."""

    def classify_dev_task(self, description: str) -> DevTaskType:
        """Klassifiziere einen Dev-Task fuer korrektes Routing."""
        desc_lower = description.lower()

        # Bug-Fix Keywords
        if any(kw in desc_lower for kw in [
            "bug", "fix", "error", "fehler", "broken", "kaputt",
            "crash", "exception", "traceback",
        ]):
            return DevTaskType.BUG_FIX

        # Testing
        if any(kw in desc_lower for kw in ["test", "unittest", "e2e", "coverage"]):
            return DevTaskType.TESTING

        # Security
        if any(kw in desc_lower for kw in ["security", "sicherheit", "vulnerability", "audit"]):
            return DevTaskType.SECURITY_AUDIT

        # Architecture
        if any(kw in desc_lower for kw in ["architektur", "architecture", "design", "refactor"]):
            return DevTaskType.ARCHITECTURE

        # Code Review
        if any(kw in desc_lower for kw in ["review", "pruefe", "check"]):
            return DevTaskType.CODE_REVIEW

        # Performance
        if any(kw in desc_lower for kw in ["performance", "slow", "langsam", "optimier"]):
            return DevTaskType.PERFORMANCE_OPT

        # Log Analysis
        if any(kw in desc_lower for kw in ["log", "logs", "monitoring"]):
            return DevTaskType.LOG_ANALYSIS

        # Default: Simple Code (Ollama)
        return DevTaskType.SIMPLE_CODE

    def get_system_health(self) -> dict:
        """System-Health-Report fuer JARVIS."""
        return {
            "open_bugs": len([b for b in self._bugs if b.status == "open"]),
            "critical_bugs": len([b for b in self._bugs if b.severity == "critical" and b.status != "resolved"]),
            "resolved_today": len([
                b for b in self._bugs
                if b.status == "resolved"
                and (time.time() - b.resolution_time_ms / 1000) < 86400
            ]),
            "avg_resolution_time_ms": (
                sum(b.resolution_time_ms for b in self._bugs if b.status == "resolved")
                / max(len([b for b in self._bugs if b.status == "resolved"]), 1)
            ),
        }

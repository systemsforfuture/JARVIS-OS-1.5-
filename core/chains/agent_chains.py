"""
JARVIS 1.5 — Agent Chain Workflows
SYSTEMS™ · architectofscale.com

Multi-Agent Collaboration — Agenten arbeiten ZUSAMMEN, nicht isoliert.

Eine Chain ist eine Pipeline wo das Output von Agent A
zum Input von Agent B wird. Automatisch. Autonom.

Vordefinierte Chains:
  1. CONTENT PIPELINE:    Steve (Text) → Iris (Visual) → Donna (Schedule)
  2. SALES PIPELINE:      Andreas (Research) → Donald (Outreach) → Felix (Follow-Up)
  3. LAUNCH CAMPAIGN:     Steve (Content) → Iris (Design) → Donald (Distribution) → Andreas (Analytics)
  4. ERROR RESOLUTION:    Archi (Diagnose) → Archi (Fix) → Elon (Review)
  5. WEEKLY REVIEW:       Elon (Analytics) → Jarvis (Summary) → Donna (Report)
  6. CUSTOMER ONBOARDING: Felix (Welcome) → Donna (Docs) → Donald (Upsell Plan)
  7. COMPETITOR INTEL:    Andreas (Research) → Steve (Counter-Content) → Donald (Positioning)

Custom Chains koennen ueber die API erstellt werden.
"""

import uuid
import time
import logging
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Optional, Callable
from enum import Enum

logger = logging.getLogger("jarvis.chains")


class ChainStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


@dataclass
class ChainStep:
    """Ein einzelner Schritt in einer Agent Chain."""
    agent_slug: str
    task_type: str
    prompt_template: str  # {input} wird mit vorherigem Output ersetzt
    name: str = ""
    transform: Optional[str] = None  # Optional: Output-Transformation
    condition: Optional[str] = None  # Optional: Bedingung zum Ueberspringen


@dataclass
class ChainResult:
    """Ergebnis einer kompletten Chain."""
    chain_id: str
    chain_name: str
    status: ChainStatus
    steps_completed: int
    steps_total: int
    outputs: list = field(default_factory=list)
    duration_ms: int = 0
    error: Optional[str] = None


class AgentChainEngine:
    """
    Orchestriert Multi-Agent Workflows.
    Jede Chain besteht aus Schritten die sequentiell ausgefuehrt werden.
    """

    def __init__(self, runtime=None, db_client=None, notify=None):
        self.runtime = runtime
        self.db = db_client
        self.notify = notify  # async callable
        self._active_chains: dict = {}

        # Vordefinierte Chains
        self.templates = self._build_templates()

    def _build_templates(self) -> dict:
        """Erstelle die vordefinierten Chain-Templates."""
        return {
            "content_pipeline": {
                "name": "Content Pipeline",
                "description": "Steve erstellt Text → Iris designt Visual → Donna plant Veroeffentlichung",
                "steps": [
                    ChainStep(
                        agent_slug="steve",
                        task_type="content",
                        name="Content erstellen",
                        prompt_template=(
                            "Erstelle hochwertigen Content zum Thema: {input}\n\n"
                            "Format: Social-Media-Post mit Headline, Body und Call-to-Action.\n"
                            "Tone: Professional aber nahbar."
                        ),
                    ),
                    ChainStep(
                        agent_slug="iris",
                        task_type="design",
                        name="Visual erstellen",
                        prompt_template=(
                            "Erstelle ein passendes Visual-Konzept fuer diesen Content:\n\n"
                            "{input}\n\n"
                            "Beschreibe das ideale Bild (Stil, Farben, Komposition) "
                            "und erstelle einen DALL-E Prompt dafuer."
                        ),
                    ),
                    ChainStep(
                        agent_slug="donna",
                        task_type="planning",
                        name="Veroeffentlichung planen",
                        prompt_template=(
                            "Plane die Veroeffentlichung dieses Contents:\n\n"
                            "{input}\n\n"
                            "Erstelle einen Zeitplan: Beste Uhrzeit pro Plattform, "
                            "Hashtag-Strategie, Cross-Posting Plan."
                        ),
                    ),
                ],
            },

            "sales_pipeline": {
                "name": "Sales Pipeline",
                "description": "Andreas recherchiert → Donald erstellt Outreach → Felix plant Follow-Up",
                "steps": [
                    ChainStep(
                        agent_slug="andreas",
                        task_type="research",
                        name="Lead Research",
                        prompt_template=(
                            "Recherchiere dieses Unternehmen/Person als potenziellen Kunden:\n\n"
                            "{input}\n\n"
                            "Finde: Branche, Groesse, Pain Points, Entscheider, "
                            "aktuelle Herausforderungen, Tech-Stack."
                        ),
                    ),
                    ChainStep(
                        agent_slug="donald",
                        task_type="sales",
                        name="Outreach erstellen",
                        prompt_template=(
                            "Basierend auf dieser Recherche, erstelle eine personalisierte "
                            "Cold-Email und LinkedIn-Nachricht:\n\n"
                            "{input}\n\n"
                            "Sei direkt, zeige dass du ihre Probleme verstehst, "
                            "biete konkreten Mehrwert."
                        ),
                    ),
                    ChainStep(
                        agent_slug="felix",
                        task_type="planning",
                        name="Follow-Up Plan",
                        prompt_template=(
                            "Erstelle einen 5-Touchpoint Follow-Up Plan basierend auf:\n\n"
                            "{input}\n\n"
                            "Plane: Tag 1 (Email), Tag 3 (LinkedIn), Tag 7 (Value Add), "
                            "Tag 14 (Case Study), Tag 21 (Final)."
                        ),
                    ),
                ],
            },

            "launch_campaign": {
                "name": "Launch Campaign",
                "description": "Komplette Kampagne: Content → Design → Distribution → Analytics",
                "steps": [
                    ChainStep(
                        agent_slug="steve",
                        task_type="content",
                        name="Kampagnen-Content",
                        prompt_template=(
                            "Erstelle den kompletten Content fuer diese Kampagne:\n\n"
                            "{input}\n\n"
                            "Erstelle: 1x Hauptpost, 3x Teaser-Posts, "
                            "1x Email-Newsletter Text, 1x Landing-Page Copy."
                        ),
                    ),
                    ChainStep(
                        agent_slug="iris",
                        task_type="design",
                        name="Kampagnen-Design",
                        prompt_template=(
                            "Erstelle ein visuelles Konzept fuer diese Kampagne:\n\n"
                            "{input}\n\n"
                            "Definiere: Farbschema, Visual-Stil, 5 Bild-Prompts "
                            "(Hero, 3x Social, 1x Email Header)."
                        ),
                    ),
                    ChainStep(
                        agent_slug="donald",
                        task_type="distribution",
                        name="Distribution-Plan",
                        prompt_template=(
                            "Erstelle den Distribution-Plan fuer diese Kampagne:\n\n"
                            "{input}\n\n"
                            "Plane: Kanaele, Timing, Budget-Aufteilung, "
                            "Zielgruppen-Targeting, Paid vs Organic Split."
                        ),
                    ),
                    ChainStep(
                        agent_slug="andreas",
                        task_type="analytics",
                        name="Tracking Setup",
                        prompt_template=(
                            "Erstelle den Analytics & Tracking Plan:\n\n"
                            "{input}\n\n"
                            "Definiere: KPIs, UTM-Parameter, Conversion-Goals, "
                            "A/B Test Hypothesen, Reporting-Rhythmus."
                        ),
                    ),
                ],
            },

            "error_resolution": {
                "name": "Error Resolution",
                "description": "Archi diagnostiziert → Archi fixt → Elon reviewed",
                "steps": [
                    ChainStep(
                        agent_slug="archi",
                        task_type="diagnosis",
                        name="Fehler-Diagnose",
                        prompt_template=(
                            "Diagnostiziere diesen Fehler:\n\n{input}\n\n"
                            "Finde: Root Cause, betroffene Systeme, Severity, "
                            "schnellster Fix vs. nachhaltiger Fix."
                        ),
                    ),
                    ChainStep(
                        agent_slug="archi",
                        task_type="fix",
                        name="Fix implementieren",
                        prompt_template=(
                            "Implementiere den Fix basierend auf dieser Diagnose:\n\n"
                            "{input}\n\n"
                            "Erstelle: Code-Aenderungen, Rollback-Plan, "
                            "Test-Schritte, Monitoring-Anpassungen."
                        ),
                    ),
                    ChainStep(
                        agent_slug="elon",
                        task_type="review",
                        name="Quality Review",
                        prompt_template=(
                            "Reviewe diesen Fix auf Qualitaet und Vollstaendigkeit:\n\n"
                            "{input}\n\n"
                            "Pruefe: Wurde Root Cause behoben? Nebenwirkungen? "
                            "Tests ausreichend? Muster fuer Praevention?"
                        ),
                    ),
                ],
            },

            "weekly_review": {
                "name": "Weekly Review",
                "description": "Elon analysiert → Jarvis fasst zusammen → Donna erstellt Report",
                "steps": [
                    ChainStep(
                        agent_slug="elon",
                        task_type="analytics",
                        name="Daten-Analyse",
                        prompt_template=(
                            "Analysiere die Performance der letzten Woche:\n\n{input}\n\n"
                            "Inkludiere: Task-Completion, Quality Scores, Kosten, "
                            "Top/Bottom Performer, Trends."
                        ),
                    ),
                    ChainStep(
                        agent_slug="jarvis",
                        task_type="summary",
                        name="Executive Summary",
                        prompt_template=(
                            "Erstelle eine Executive Summary aus dieser Analyse:\n\n"
                            "{input}\n\n"
                            "Fokus: 3 Highlights, 2 Risiken, 1 Empfehlung. "
                            "Maximal eine halbe Seite."
                        ),
                    ),
                    ChainStep(
                        agent_slug="donna",
                        task_type="document",
                        name="Report erstellen",
                        prompt_template=(
                            "Erstelle einen formatierten Wochenbericht:\n\n"
                            "{input}\n\n"
                            "Format: Professioneller Report mit Sections, "
                            "Key Metrics Table, Action Items."
                        ),
                    ),
                ],
            },

            "customer_onboarding": {
                "name": "Customer Onboarding",
                "description": "Felix begruesst → Donna erstellt Docs → Donald plant Upsell",
                "steps": [
                    ChainStep(
                        agent_slug="felix",
                        task_type="onboarding",
                        name="Welcome Sequence",
                        prompt_template=(
                            "Erstelle eine Welcome-Sequence fuer diesen neuen Kunden:\n\n"
                            "{input}\n\n"
                            "Erstelle: Welcome-Email, Onboarding-Checklist, "
                            "FAQ-Zusammenstellung, erste Check-In Nachricht."
                        ),
                    ),
                    ChainStep(
                        agent_slug="donna",
                        task_type="document",
                        name="Onboarding Docs",
                        prompt_template=(
                            "Erstelle die Onboarding-Dokumentation:\n\n"
                            "{input}\n\n"
                            "Erstelle: Quick-Start Guide, Account-Setup Anleitung, "
                            "Support-Kontakte, SLA-Zusammenfassung."
                        ),
                    ),
                    ChainStep(
                        agent_slug="donald",
                        task_type="upsell",
                        name="Upsell Strategie",
                        prompt_template=(
                            "Erstelle eine Upsell-Strategie fuer diesen Kunden:\n\n"
                            "{input}\n\n"
                            "Plane: Welche Features/Services nach 30/60/90 Tagen vorschlagen, "
                            "Trigger-Events identifizieren, personalisierte Angebote."
                        ),
                    ),
                ],
            },

            "competitor_intel": {
                "name": "Competitor Intelligence",
                "description": "Andreas recherchiert → Steve erstellt Counter-Content → Donald positioniert",
                "steps": [
                    ChainStep(
                        agent_slug="andreas",
                        task_type="research",
                        name="Wettbewerber-Analyse",
                        prompt_template=(
                            "Analysiere diesen Wettbewerber umfassend:\n\n{input}\n\n"
                            "Finde: Staerken/Schwaechen, Pricing, Features, "
                            "Marketing-Strategie, Kundenbewertungen, Tech-Stack."
                        ),
                    ),
                    ChainStep(
                        agent_slug="steve",
                        task_type="content",
                        name="Counter-Content",
                        prompt_template=(
                            "Erstelle Content der uns vom Wettbewerber abgrenzt:\n\n"
                            "{input}\n\n"
                            "Erstelle: Comparison Post, 'Why Us' Messaging, "
                            "Feature-Differenzierung, Testimonial-Request Template."
                        ),
                    ),
                    ChainStep(
                        agent_slug="donald",
                        task_type="positioning",
                        name="Positioning Update",
                        prompt_template=(
                            "Update unsere Sales-Positionierung gegen diesen Wettbewerber:\n\n"
                            "{input}\n\n"
                            "Erstelle: Battle Card, Einwandbehandlung (5 haeufigste), "
                            "Win/Loss Talking Points."
                        ),
                    ),
                ],
            },
        }

    # ═══════════════════════════════════════════════════
    # CHAIN EXECUTION
    # ═══════════════════════════════════════════════════

    async def execute_chain(
        self,
        chain_name: str,
        input_text: str,
        user_id: str = "dom",
        notify_progress: bool = True,
    ) -> ChainResult:
        """
        Fuehre eine komplette Chain aus.
        Jeder Schritt baut auf dem vorherigen auf.
        """
        template = self.templates.get(chain_name)
        if not template:
            return ChainResult(
                chain_id="", chain_name=chain_name,
                status=ChainStatus.FAILED, steps_completed=0,
                steps_total=0, error=f"Unknown chain: {chain_name}",
            )

        chain_id = str(uuid.uuid4())[:8]
        steps = template["steps"]
        start_time = time.time()

        logger.info(f"[CHAIN:{chain_id}] Starting '{template['name']}' ({len(steps)} steps)")

        if notify_progress and self.notify:
            await self.notify(
                f"🔗 Chain gestartet: {template['name']}\n"
                f"   {len(steps)} Schritte | Input: {input_text[:50]}...",
                urgency="info",
            )

        outputs = []
        current_input = input_text
        self._active_chains[chain_id] = ChainStatus.RUNNING

        for i, step in enumerate(steps):
            step_num = i + 1
            logger.info(f"[CHAIN:{chain_id}] Step {step_num}/{len(steps)}: {step.name} ({step.agent_slug})")

            # Prompt mit vorherigem Output fuellen
            prompt = step.prompt_template.replace("{input}", current_input)

            try:
                if self.runtime:
                    from core.agents.agent_runtime import AgentCall
                    call = AgentCall(
                        agent_slug=step.agent_slug,
                        task_description=prompt,
                        task_type=step.task_type,
                        user_id=user_id,
                        metadata={"chain_id": chain_id, "chain_step": step_num},
                    )
                    response = await self.runtime.execute(call)
                    step_output = response.content
                else:
                    step_output = f"[SIMULATION] {step.name} output for: {current_input[:50]}"

                outputs.append({
                    "step": step_num,
                    "name": step.name,
                    "agent": step.agent_slug,
                    "output": step_output,
                })

                # Output wird zum Input des naechsten Schritts
                current_input = step_output

                if notify_progress and self.notify:
                    await self.notify(
                        f"  ✅ Step {step_num}/{len(steps)}: {step.name} ({step.agent_slug})",
                        urgency="info",
                    )

            except Exception as e:
                logger.error(f"[CHAIN:{chain_id}] Step {step_num} failed: {e}")
                self._active_chains[chain_id] = ChainStatus.FAILED

                return ChainResult(
                    chain_id=chain_id,
                    chain_name=template["name"],
                    status=ChainStatus.FAILED,
                    steps_completed=i,
                    steps_total=len(steps),
                    outputs=outputs,
                    duration_ms=int((time.time() - start_time) * 1000),
                    error=str(e),
                )

        duration_ms = int((time.time() - start_time) * 1000)
        self._active_chains[chain_id] = ChainStatus.COMPLETED

        if notify_progress and self.notify:
            await self.notify(
                f"🔗 Chain fertig: {template['name']}\n"
                f"   {len(steps)} Schritte in {duration_ms/1000:.1f}s",
                urgency="info",
            )

        # In DB loggen
        await self._log_chain(chain_id, template["name"], outputs, duration_ms)

        return ChainResult(
            chain_id=chain_id,
            chain_name=template["name"],
            status=ChainStatus.COMPLETED,
            steps_completed=len(steps),
            steps_total=len(steps),
            outputs=outputs,
            duration_ms=duration_ms,
        )

    async def execute_custom_chain(
        self,
        steps: list[dict],
        input_text: str,
        chain_name: str = "Custom",
        user_id: str = "dom",
    ) -> ChainResult:
        """
        Fuehre eine benutzerdefinierte Chain aus.
        steps = [{"agent": "steve", "task": "...", "type": "content"}, ...]
        """
        chain_steps = [
            ChainStep(
                agent_slug=s["agent"],
                task_type=s.get("type", "general"),
                name=s.get("name", f"Step {i+1}"),
                prompt_template=s.get("task", "{input}"),
            )
            for i, s in enumerate(steps)
        ]

        # Temporaer als Template registrieren
        temp_name = f"custom_{uuid.uuid4().hex[:6]}"
        self.templates[temp_name] = {
            "name": chain_name,
            "description": "Custom chain",
            "steps": chain_steps,
        }

        result = await self.execute_chain(temp_name, input_text, user_id)

        # Template wieder entfernen
        del self.templates[temp_name]

        return result

    def list_chains(self) -> list:
        """Liste alle verfuegbaren Chain-Templates."""
        return [
            {
                "id": key,
                "name": tpl["name"],
                "description": tpl["description"],
                "steps": len(tpl["steps"]),
                "agents": [s.agent_slug for s in tpl["steps"]],
            }
            for key, tpl in self.templates.items()
        ]

    async def _log_chain(self, chain_id: str, name: str, outputs: list, duration_ms: int):
        if not self.db:
            return
        try:
            await self.db.insert("tasks", {
                "id": chain_id,
                "agent_slug": "jarvis",
                "task_type": "chain",
                "description": f"Chain: {name}",
                "status": "completed",
                "result": str([o.get("name") for o in outputs]),
                "duration_ms": duration_ms,
                "metadata": {"chain_outputs": len(outputs)},
            })
        except Exception:
            pass

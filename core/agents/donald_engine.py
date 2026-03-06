"""
JARVIS 1.5 — DONALD Engine (Sales & Revenue)
SYSTEMS™ · architectofscale.com

DONALD ist der Sales-Agent mit echten Pipeline-Algorithmen.

Features:
  1. Lead Scoring       — BANT/MEDDIC automatisches Scoring
  2. Pipeline Manager   — Stages, Forecasting, Velocity
  3. Outreach Engine    — Personalisierte Cold E-Mails
  4. Follow-up System   — Automatische Sequenzen mit Timing
  5. Proposal Generator — Massgeschneiderte Angebote
  6. Revenue Forecasting — Pipeline-basierte Prognosen
"""

import time
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class LeadStage(Enum):
    NEW = "new"
    QUALIFIED = "qualified"
    CONTACTED = "contacted"
    MEETING = "meeting"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


class LeadSource(Enum):
    INBOUND = "inbound"         # Ueber Website, Content
    LINKEDIN = "linkedin"       # LinkedIn Outreach
    REFERRAL = "referral"       # Empfehlung
    COLD_EMAIL = "cold_email"   # Cold Outreach
    EVENT = "event"             # Konferenz, Webinar
    PARTNER = "partner"         # Partner-Empfehlung


@dataclass
class Lead:
    """Ein Sales-Lead."""
    id: str = ""
    company: str = ""
    contact_name: str = ""
    contact_email: str = ""
    contact_title: str = ""
    industry: str = ""
    company_size: str = ""          # "1-10", "11-50", "51-200", "201-500", "500+"
    stage: LeadStage = LeadStage.NEW
    source: LeadSource = LeadSource.INBOUND
    score: float = 0.0              # 0-100
    deal_value: float = 0.0         # EUR
    probability: float = 0.0        # 0-1
    next_action: str = ""
    next_action_date: Optional[str] = None
    notes: list = field(default_factory=list)
    interactions: list = field(default_factory=list)
    bant: dict = field(default_factory=dict)  # Budget, Authority, Need, Timeline
    created_at: float = field(default_factory=time.time)
    last_contact: Optional[float] = None


@dataclass
class FollowUpSequence:
    """Eine automatische Follow-up-Sequenz."""
    name: str
    steps: list = field(default_factory=list)  # [{day, channel, template}]
    active: bool = True


# BANT Scoring Matrix
BANT_WEIGHTS = {
    "budget": 30,       # Hat Budget? (0-30 Punkte)
    "authority": 25,    # Entscheider? (0-25 Punkte)
    "need": 25,         # Echtes Problem? (0-25 Punkte)
    "timeline": 20,     # Zeitdruck? (0-20 Punkte)
}

# ICP (Ideal Customer Profile) fuer SYSTEMS™
ICP = {
    "company_size": ["11-50", "51-200", "201-500"],
    "industries": [
        "SaaS", "E-Commerce", "Beratung", "Agentur",
        "Immobilien", "Finanzdienstleistung", "Gesundheit",
    ],
    "titles": [
        "CEO", "CTO", "COO", "Geschaeftsfuehrer", "Inhaber",
        "Head of", "VP", "Director",
    ],
    "signals": [
        "wachsend", "skalieren", "automatisieren", "effizienz",
        "ki", "ai", "digitalisierung",
    ],
}

# Follow-up Sequenzen
DEFAULT_SEQUENCES = {
    "cold_outreach": FollowUpSequence(
        name="Cold Outreach",
        steps=[
            {"day": 0, "channel": "email", "template": "initial_cold"},
            {"day": 3, "channel": "linkedin", "template": "connection_request"},
            {"day": 7, "channel": "email", "template": "value_followup"},
            {"day": 14, "channel": "email", "template": "case_study"},
            {"day": 21, "channel": "email", "template": "last_chance"},
        ],
    ),
    "inbound_lead": FollowUpSequence(
        name="Inbound Lead",
        steps=[
            {"day": 0, "channel": "email", "template": "welcome_inbound"},
            {"day": 1, "channel": "email", "template": "schedule_call"},
            {"day": 3, "channel": "linkedin", "template": "connect"},
            {"day": 7, "channel": "email", "template": "value_reminder"},
        ],
    ),
    "post_meeting": FollowUpSequence(
        name="After Meeting",
        steps=[
            {"day": 0, "channel": "email", "template": "meeting_summary"},
            {"day": 2, "channel": "email", "template": "proposal_send"},
            {"day": 5, "channel": "email", "template": "proposal_followup"},
            {"day": 10, "channel": "email", "template": "decision_check"},
        ],
    ),
}


class DonaldEngine:
    """
    DONALD — Sales & Revenue Engine.

    Pipeline-Management mit echten Scoring-Algorithmen.
    """

    def __init__(self, db_pool=None, brain=None):
        self.db = db_pool
        self.brain = brain
        self._leads = []
        self._pipeline = {}

    def score_lead(self, lead: Lead) -> float:
        """
        Bewerte einen Lead nach BANT + ICP Fit.

        Score: 0-100
          0-30:  Kalt — nicht qualifiziert
          31-60: Warm — potenziell interessant
          61-80: Heiss — aktiv verfolgen
          81-100: Kritisch — sofort handeln
        """
        score = 0.0

        # BANT Scoring
        bant = lead.bant
        if bant.get("budget"):
            score += BANT_WEIGHTS["budget"] * min(bant["budget"], 1.0)
        if bant.get("authority"):
            score += BANT_WEIGHTS["authority"] * min(bant["authority"], 1.0)
        if bant.get("need"):
            score += BANT_WEIGHTS["need"] * min(bant["need"], 1.0)
        if bant.get("timeline"):
            score += BANT_WEIGHTS["timeline"] * min(bant["timeline"], 1.0)

        # ICP Fit Bonus (+0-20)
        icp_score = 0
        if lead.company_size in ICP["company_size"]:
            icp_score += 5
        if lead.industry in ICP["industries"]:
            icp_score += 5
        if any(t.lower() in lead.contact_title.lower() for t in ICP["titles"]):
            icp_score += 10

        score += icp_score

        # Engagement Bonus
        if lead.interactions:
            score += min(len(lead.interactions) * 2, 10)

        # Recency Bonus
        if lead.last_contact:
            days_since = (time.time() - lead.last_contact) / 86400
            if days_since < 3:
                score += 5
            elif days_since > 30:
                score -= 10

        lead.score = max(0, min(100, score))
        return lead.score

    def get_pipeline_summary(self) -> dict:
        """
        Pipeline-Zusammenfassung mit Forecasting.
        """
        stages = {}
        total_value = 0
        weighted_value = 0

        for lead in self._leads:
            stage = lead.stage.value
            if stage not in stages:
                stages[stage] = {"count": 0, "value": 0}
            stages[stage]["count"] += 1
            stages[stage]["value"] += lead.deal_value
            total_value += lead.deal_value
            weighted_value += lead.deal_value * lead.probability

        # Velocity: Durchschnittliche Tage pro Stage
        return {
            "total_leads": len(self._leads),
            "total_pipeline_value": total_value,
            "weighted_forecast": round(weighted_value, 2),
            "stages": stages,
            "conversion_rate": self._calculate_conversion_rate(),
            "avg_deal_size": total_value / max(len(self._leads), 1),
        }

    def generate_cold_email(self, lead: Lead, variant: str = "initial") -> dict:
        """
        Generiere eine personalisierte Cold E-Mail.

        Prompt wird an das LLM gesendet mit Lead-Kontext.
        """
        prompt = f"""Du bist DONALD, Sales Lead bei SYSTEMS™.

Schreibe eine Cold E-Mail an:
  Name: {lead.contact_name}
  Titel: {lead.contact_title}
  Firma: {lead.company}
  Branche: {lead.industry}
  Groesse: {lead.company_size} Mitarbeiter

REGELN:
  - Max. 150 Woerter
  - Personalisiert auf die Branche
  - Ein konkreter Pain Point ansprechen
  - Kein "Ich moechte mich vorstellen"
  - Direkt zum Punkt
  - EIN klarer CTA (z.B. "15-Min Call?")
  - Betreff: Max. 6 Woerter, neugierig machend

SYSTEMS™ verkauft JARVIS: Ein autonomes KI-Betriebssystem
das 10 AI Agents bereitstellt (Marketing, Sales, Dev, Ops).
Preis: ab 20.000 EUR Setup + 4-8K EUR/Monat.

Liefere:
1. Betreff-Zeile
2. E-Mail-Text
3. PS-Zeile (optional)"""

        return {
            "lead_id": lead.id,
            "variant": variant,
            "prompt": prompt,
            "status": "draft",
        }

    def get_next_actions(self, limit: int = 10) -> list:
        """
        Priorisierte Liste der naechsten Aktionen.

        Sortiert nach: Dringlichkeit, Lead-Score, Pipeline-Stage.
        """
        actions = []

        for lead in self._leads:
            if lead.stage in (LeadStage.CLOSED_WON, LeadStage.CLOSED_LOST):
                continue

            urgency = 0

            # Kein Kontakt seit >7 Tagen = dringend
            if lead.last_contact:
                days_since = (time.time() - lead.last_contact) / 86400
                if days_since > 7:
                    urgency += 30
                elif days_since > 3:
                    urgency += 15

            # Hoher Score = dringend
            urgency += lead.score * 0.5

            # Fortgeschrittene Stage = dringend
            stage_urgency = {
                LeadStage.NEGOTIATION: 50,
                LeadStage.PROPOSAL: 40,
                LeadStage.MEETING: 30,
                LeadStage.CONTACTED: 15,
                LeadStage.QUALIFIED: 10,
                LeadStage.NEW: 5,
            }
            urgency += stage_urgency.get(lead.stage, 0)

            actions.append({
                "lead_id": lead.id,
                "company": lead.company,
                "contact": lead.contact_name,
                "stage": lead.stage.value,
                "score": lead.score,
                "urgency": round(urgency, 1),
                "action": lead.next_action or self._suggest_next_action(lead),
            })

        actions.sort(key=lambda a: a["urgency"], reverse=True)
        return actions[:limit]

    def _suggest_next_action(self, lead: Lead) -> str:
        """Schlage naechste Aktion basierend auf Stage vor."""
        suggestions = {
            LeadStage.NEW: "Lead qualifizieren (BANT pruefen)",
            LeadStage.QUALIFIED: "Erste E-Mail senden",
            LeadStage.CONTACTED: "Follow-up senden oder Call vereinbaren",
            LeadStage.MEETING: "Meeting-Summary senden + Proposal vorbereiten",
            LeadStage.PROPOSAL: "Proposal Follow-up in 2-3 Tagen",
            LeadStage.NEGOTIATION: "Einwaende klaeren, Deal abschliessen",
        }
        return suggestions.get(lead.stage, "Status pruefen")

    def _calculate_conversion_rate(self) -> float:
        """Berechne historische Conversion Rate."""
        won = len([l for l in self._leads if l.stage == LeadStage.CLOSED_WON])
        closed = won + len([l for l in self._leads if l.stage == LeadStage.CLOSED_LOST])
        if closed == 0:
            return 0.0
        return round(won / closed, 3)

"""
JARVIS 1.5 — N8N Webhook Connector
Sendet Events an N8N Workflows.

N8N ist extern installiert. JARVIS sendet Events via Webhooks.
N8N kann dann beliebige Aktionen auslösen (E-Mail, Slack, CRM, etc.)

Events die gesendet werden:
  - task_completed — Agent hat Task abgeschlossen
  - error_alert — Kritischer Fehler aufgetreten
  - daily_report — ELON Tagesbericht
  - agent_escalation — Agent eskaliert zum DOM
  - new_lead — Neuer Lead erkannt (DONALD)
  - customer_alert — Kunden-Problem erkannt (FELIX)
"""

import os
import json
import logging
from typing import Optional

logger = logging.getLogger("jarvis.n8n")

DEFAULT_WEBHOOKS = {
    "task_completed": "/webhook/jarvis-task-completed",
    "error_alert": "/webhook/jarvis-error-alert",
    "daily_report": "/webhook/jarvis-daily-report",
    "agent_escalation": "/webhook/jarvis-escalation",
    "new_lead": "/webhook/jarvis-new-lead",
    "customer_alert": "/webhook/jarvis-customer-alert",
}


class N8NConnector:
    """Sendet Events an N8N Webhooks."""

    def __init__(self, n8n_url: Optional[str] = None):
        self.n8n_url = n8n_url or os.getenv("N8N_URL", "http://localhost:5678")
        self.webhooks = dict(DEFAULT_WEBHOOKS)
        self._load_webhook_config()

    def _load_webhook_config(self):
        """Lade Webhook-URLs aus Config-Datei."""
        config_path = os.path.join(
            os.getenv("JARVIS_DIR", "/opt/jarvis"),
            "config/n8n/webhooks.json"
        )
        try:
            with open(config_path) as f:
                config = json.load(f)
                if "webhooks" in config:
                    self.webhooks = config["webhooks"]
                if "n8n_url" in config:
                    self.n8n_url = config["n8n_url"]
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    async def send_event(self, event_type: str, payload: dict) -> bool:
        """Sende ein Event an den entsprechenden N8N Webhook."""
        webhook_url = self.webhooks.get(event_type)
        if not webhook_url:
            logger.warning(f"No webhook configured for event: {event_type}")
            return False

        # Vollständige URL bauen
        if not webhook_url.startswith("http"):
            webhook_url = f"{self.n8n_url}{webhook_url}"

        try:
            import httpx
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    webhook_url,
                    json={
                        "event": event_type,
                        "timestamp": __import__("datetime").datetime.now(
                            __import__("datetime").timezone.utc
                        ).isoformat(),
                        "source": "jarvis",
                        **payload,
                    },
                )
                if response.status_code < 300:
                    logger.info(f"N8N webhook sent: {event_type}")
                    return True
                else:
                    logger.warning(
                        f"N8N webhook {event_type} returned {response.status_code}"
                    )
                    return False
        except Exception as e:
            logger.debug(f"N8N webhook {event_type} failed: {e}")
            return False

    # ─── Schnell-Methoden ───

    async def on_task_completed(
        self,
        agent_slug: str,
        task_description: str,
        result: str,
        score: float,
        **kwargs
    ):
        await self.send_event("task_completed", {
            "agent": agent_slug,
            "task": task_description[:200],
            "result": result[:500],
            "score": score,
            **kwargs,
        })

    async def on_error(
        self,
        agent_slug: str,
        error_type: str,
        error_message: str,
        severity: str = "warning",
        **kwargs
    ):
        await self.send_event("error_alert", {
            "agent": agent_slug,
            "error_type": error_type,
            "error_message": error_message[:500],
            "severity": severity,
            **kwargs,
        })

    async def on_daily_report(self, report: dict):
        await self.send_event("daily_report", {"report": report})

    async def on_escalation(
        self,
        agent_slug: str,
        reason: str,
        context: Optional[dict] = None
    ):
        await self.send_event("agent_escalation", {
            "agent": agent_slug,
            "reason": reason,
            "context": context or {},
        })

    async def on_new_lead(self, lead_data: dict):
        await self.send_event("new_lead", {"lead": lead_data})

    async def on_customer_alert(
        self,
        customer: str,
        alert_type: str,
        details: str,
        **kwargs
    ):
        await self.send_event("customer_alert", {
            "customer": customer,
            "alert_type": alert_type,
            "details": details,
            **kwargs,
        })

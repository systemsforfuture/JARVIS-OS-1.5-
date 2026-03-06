"""
JARVIS 1.5 — Telegram Bot
Hauptkommunikationskanal zwischen DOM und dem JARVIS Team.

Features:
  - Nachrichten an JARVIS senden → Agent Runtime verarbeitet
  - Team-Kommunikation: Agenten antworten mit ihrer Persoenlichkeit
  - Gruppen-Chat: Agents kommunizieren im Team-Channel
  - Proaktive Nachrichten: ELON, DONNA etc. melden sich selbstaendig
  - Agent-Mentions: @steve, @archi, etc.
  - Slash-Commands fuer Agent-Steuerung
  - Team-Updates: automatische Benachrichtigungen
"""

import os
import logging
from typing import Optional

logger = logging.getLogger("jarvis.telegram")


# Agent display info for Telegram messages
AGENT_PROFILES = {
    "jarvis": {"emoji": "\U0001F451", "name": "JARVIS", "title": "Chief Intelligence"},
    "elon": {"emoji": "\U0001F4CA", "name": "ELON", "title": "Analyst & Optimizer"},
    "steve": {"emoji": "\U0001F3AF", "name": "STEVE", "title": "Marketing & Content"},
    "donald": {"emoji": "\U0001F4B0", "name": "DONALD", "title": "Sales & Revenue"},
    "archi": {"emoji": "\U0001F4BB", "name": "ARCHI", "title": "Dev & Infrastructure"},
    "donna": {"emoji": "\U0001F4CB", "name": "DONNA", "title": "Backoffice & Ops"},
    "iris": {"emoji": "\U0001F3A8", "name": "IRIS", "title": "Design & Creative"},
    "satoshi": {"emoji": "\U000020BF", "name": "SATOSHI", "title": "Crypto & Trading"},
    "felix": {"emoji": "\U0001F91D", "name": "FELIX", "title": "Customer Success"},
    "andreas": {"emoji": "\U0001F4C8", "name": "ANDREAS", "title": "Sales Excellence"},
}


class TelegramBot:
    """
    Telegram-Bot-Integration.
    Hauptinterface fuer den DOM und Team-Kommunikation.
    """

    def __init__(self, runtime=None, conversations=None):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
        self.group_id = os.getenv("TELEGRAM_GROUP_ID", "")
        self.runtime = runtime
        self.conversations = conversations
        self._app = None

    async def start(self):
        """Starte den Telegram Bot."""
        if not self.token:
            logger.warning("TELEGRAM_BOT_TOKEN not set — Telegram disabled")
            return

        try:
            from telegram.ext import (
                ApplicationBuilder, CommandHandler, MessageHandler, filters
            )
        except ImportError:
            logger.warning("python-telegram-bot not installed — Telegram disabled")
            return

        self._app = ApplicationBuilder().token(self.token).build()

        # Commands
        self._app.add_handler(CommandHandler("start", self._cmd_start))
        self._app.add_handler(CommandHandler("status", self._cmd_status))
        self._app.add_handler(CommandHandler("agents", self._cmd_agents))
        self._app.add_handler(CommandHandler("elon", self._cmd_elon))
        self._app.add_handler(CommandHandler("team", self._cmd_team))
        self._app.add_handler(CommandHandler("tasks", self._cmd_tasks))
        self._app.add_handler(CommandHandler("memory", self._cmd_memory))
        self._app.add_handler(CommandHandler("learn", self._cmd_learn))
        self._app.add_handler(CommandHandler("kpi", self._cmd_kpi))
        self._app.add_handler(CommandHandler("help", self._cmd_help))

        # Alle Text-Nachrichten → JARVIS
        self._app.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, self._handle_message
        ))

        logger.info("Telegram Bot starting...")
        await self._app.initialize()
        await self._app.start()
        await self._app.updater.start_polling()
        logger.info("Telegram Bot running")

    async def stop(self):
        """Stoppe den Telegram Bot."""
        if self._app:
            await self._app.updater.stop()
            await self._app.stop()
            await self._app.shutdown()

    # ─── Message Handler ───

    async def _handle_message(self, update, context):
        """Jede Nachricht geht durch die Agent Runtime."""
        if not update.message or not update.message.text:
            return

        user_message = update.message.text
        chat_id = str(update.message.chat_id)

        # Autorisierte Chats: Direct + Group
        allowed = {self.chat_id, self.group_id}
        if self.chat_id and chat_id not in allowed:
            await update.message.reply_text("Nicht autorisiert.")
            return

        logger.info(f"Telegram message: {user_message[:50]}...")

        if not self.runtime:
            await update.message.reply_text("JARVIS Runtime nicht verfuegbar.")
            return

        try:
            # Agent-Delegation erkennen (@steve, @archi, etc.)
            agent_slug = self._detect_agent(user_message)
            profile = AGENT_PROFILES.get(agent_slug, AGENT_PROFILES["jarvis"])

            from core.agents.agent_runtime import AgentCall
            call = AgentCall(
                agent_slug=agent_slug,
                task_description=user_message,
                channel="telegram",
                metadata={
                    "telegram_chat_id": chat_id,
                    "is_group": chat_id == self.group_id,
                },
            )
            response = await self.runtime.execute(call)

            # Format agent response with personality header
            reply = self._format_agent_reply(agent_slug, response.content)

            await self._send_long_message(update, reply)

            # If this was in the group, also notify in DM for important stuff
            if chat_id == self.group_id and self.chat_id:
                if any(kw in response.content.lower() for kw in [
                    "dringend", "urgent", "fehler", "error", "problem", "achtung"
                ]):
                    await self.send_message(
                        f"{profile['emoji']} {profile['name']} hat etwas Wichtiges "
                        f"im Team-Chat gemeldet. Schau mal rein.",
                        chat_id=self.chat_id,
                    )

        except Exception as e:
            logger.error(f"Telegram handler error: {e}")
            await update.message.reply_text(
                "Fehler bei der Verarbeitung. Ich arbeite daran."
            )

    def _detect_agent(self, message: str) -> str:
        """Erkennt @agent-Mentions in Nachrichten."""
        agent_map = {
            "@elon": "elon", "@steve": "steve", "@donald": "donald",
            "@archi": "archi", "@donna": "donna", "@iris": "iris",
            "@satoshi": "satoshi", "@felix": "felix", "@andreas": "andreas",
        }
        msg_lower = message.lower()
        for mention, slug in agent_map.items():
            if mention in msg_lower:
                return slug
        return "jarvis"

    def _format_agent_reply(self, agent_slug: str, content: str) -> str:
        """Format reply with agent identity header."""
        profile = AGENT_PROFILES.get(agent_slug, AGENT_PROFILES["jarvis"])
        return f"{profile['emoji']} {profile['name']}\n\n{content}"

    async def _send_long_message(self, update, text: str):
        """Send message, splitting if > 4096 chars."""
        if len(text) > 4000:
            for i in range(0, len(text), 4000):
                await update.message.reply_text(text[i:i + 4000])
        else:
            await update.message.reply_text(text)

    # ─── Commands ───

    async def _cmd_start(self, update, context):
        await update.message.reply_text(
            "\U0001F451 JARVIS 1.5 — Autonomes KI-Betriebssystem\n"
            "SYSTEMS\u2122\n\n"
            "Schreibe einfach eine Nachricht und ich delegiere "
            "an den richtigen Agent.\n\n"
            "Mention einen Agent direkt:\n"
            "@steve — Marketing & Content\n"
            "@donald — Sales & Revenue\n"
            "@archi — Dev & Infrastructure\n"
            "@donna — Backoffice & Ops\n"
            "@elon — Analyse & Optimierung\n\n"
            "/help fuer alle Commands"
        )

    async def _cmd_help(self, update, context):
        await update.message.reply_text(
            "\U0001F4CB JARVIS Commands\n\n"
            "/status — System-Status\n"
            "/agents — Alle Agents\n"
            "/team — Team-Uebersicht (wer arbeitet woran)\n"
            "/tasks — Aktuelle Tasks\n"
            "/elon — ELON System-Report\n"
            "/kpi — KPI Dashboard\n"
            "/memory — Letzte Erinnerungen\n"
            "/learn — Learning-Stats\n\n"
            "Direkt an Agent:\n"
            "@steve schreib einen LinkedIn Post\n"
            "@archi check den Server Status\n"
            "@donna erstell eine Rechnung"
        )

    async def _cmd_status(self, update, context):
        if not self.runtime:
            await update.message.reply_text("Runtime nicht verfuegbar.")
            return
        try:
            improver_status = await self.runtime.improver.get_status()
            await update.message.reply_text(
                "\U0001F4CA JARVIS 1.5 Status\n\n"
                f"Improvement-Cycle: {improver_status.get('last_run', 'nie')}\n"
                f"Tasks pending: {improver_status.get('tasks_since_last_run', 0)}\n"
                f"Improvements: {improver_status.get('pending_improvements', 0)}"
            )
        except Exception as e:
            await update.message.reply_text(f"Status-Fehler: {e}")

    async def _cmd_agents(self, update, context):
        lines = ["\U0001F916 JARVIS 1.5 Team\n"]
        for slug, p in AGENT_PROFILES.items():
            lines.append(f"{p['emoji']} {p['name']} — {p['title']}")
        lines.append("\nMention mit @name fuer direkte Ansprache")
        await update.message.reply_text("\n".join(lines))

    async def _cmd_team(self, update, context):
        """Zeige wer gerade woran arbeitet."""
        if not self.runtime:
            await update.message.reply_text("Runtime nicht verfuegbar.")
            return
        try:
            from core.agents.agent_runtime import AgentCall
            call = AgentCall(
                agent_slug="jarvis",
                task_description=(
                    "Gib einen kurzen Team-Status: Welcher Agent hat gerade "
                    "welche Tasks? Was laeuft, was braucht Aufmerksamkeit? "
                    "Max 15 Zeilen."
                ),
                channel="telegram",
            )
            response = await self.runtime.execute(call)
            reply = self._format_agent_reply("jarvis", response.content)
            await self._send_long_message(update, reply)
        except Exception as e:
            await update.message.reply_text(f"Team-Status Fehler: {e}")

    async def _cmd_tasks(self, update, context):
        """Zeige aktuelle Tasks."""
        if not self.runtime:
            await update.message.reply_text("Runtime nicht verfuegbar.")
            return
        try:
            from core.agents.agent_runtime import AgentCall
            call = AgentCall(
                agent_slug="jarvis",
                task_description=(
                    "Liste die letzten 10 Tasks mit Status. "
                    "Format: Agent | Task | Status. Kurz und knapp."
                ),
                channel="telegram",
            )
            response = await self.runtime.execute(call)
            reply = self._format_agent_reply("jarvis", response.content)
            await self._send_long_message(update, reply)
        except Exception as e:
            await update.message.reply_text(f"Tasks-Fehler: {e}")

    async def _cmd_elon(self, update, context):
        if not self.runtime:
            await update.message.reply_text("Runtime nicht verfuegbar.")
            return
        try:
            from core.agents.agent_runtime import AgentCall
            call = AgentCall(
                agent_slug="elon",
                task_description=(
                    "Erstelle einen kurzen System-Status-Report. "
                    "Was laeuft gut, was muss verbessert werden? "
                    "Welche Patterns hast du erkannt? Max 15 Zeilen."
                ),
                channel="telegram",
            )
            response = await self.runtime.execute(call)
            reply = self._format_agent_reply("elon", response.content)
            await self._send_long_message(update, reply)
        except Exception as e:
            await update.message.reply_text(f"ELON-Fehler: {e}")

    async def _cmd_kpi(self, update, context):
        """KPI Dashboard im Chat."""
        if not self.runtime:
            await update.message.reply_text("Runtime nicht verfuegbar.")
            return
        try:
            from core.agents.agent_runtime import AgentCall
            call = AgentCall(
                agent_slug="elon",
                task_description=(
                    "Zeige die wichtigsten KPIs: Task Completion Rate, "
                    "Kosten heute, aktive Agents, offene Tasks, Fehlerrate. "
                    "Nur Zahlen, keine Erklaerungen. Max 10 Zeilen."
                ),
                channel="telegram",
            )
            response = await self.runtime.execute(call)
            reply = self._format_agent_reply("elon", response.content)
            await self._send_long_message(update, reply)
        except Exception as e:
            await update.message.reply_text(f"KPI-Fehler: {e}")

    async def _cmd_memory(self, update, context):
        if not self.runtime:
            await update.message.reply_text("Runtime nicht verfuegbar.")
            return
        try:
            memories = await self.runtime.conversations.get_recent_messages(limit=5)
            if not memories:
                await update.message.reply_text("Noch keine Erinnerungen.")
                return
            lines = ["\U0001F9E0 Letzte 5 Nachrichten\n"]
            for m in memories:
                role = m.get("role", "?")
                content = m.get("content", "")[:100]
                lines.append(f"[{role}] {content}")
            await update.message.reply_text("\n".join(lines))
        except Exception as e:
            await update.message.reply_text(f"Memory-Fehler: {e}")

    async def _cmd_learn(self, update, context):
        if not self.runtime:
            await update.message.reply_text("Runtime nicht verfuegbar.")
            return
        try:
            stats = await self.runtime.journal.get_stats()
            await update.message.reply_text(
                "\U0001F4D6 Learning-Statistiken\n\n"
                f"Total Learnings: {stats.get('total', 0)}\n"
                f"Avg Impact: {stats.get('avg_impact_score', 0):.2f}\n"
                f"Angewendet: {stats.get('total_times_applied', 0)}x\n"
                f"Nach Typ: {stats.get('by_type', {})}"
            )
        except Exception as e:
            await update.message.reply_text(f"Learning-Fehler: {e}")

    # ─── Proaktive Nachrichten ───

    async def send_message(self, text: str, chat_id: Optional[str] = None):
        """Sende proaktiv eine Nachricht (z.B. von ELON)."""
        target = chat_id or self.chat_id
        if not target or not self._app:
            return
        try:
            await self._app.bot.send_message(chat_id=target, text=text[:4096])
        except Exception as e:
            logger.error(f"Could not send telegram message: {e}")

    async def send_team_update(self, agent_slug: str, message: str):
        """Sende ein Team-Update in den Gruppen-Channel."""
        profile = AGENT_PROFILES.get(agent_slug, AGENT_PROFILES["jarvis"])
        text = f"{profile['emoji']} {profile['name']}\n\n{message}"

        # Send to group if configured, otherwise to DM
        target = self.group_id or self.chat_id
        await self.send_message(text, chat_id=target)

    async def notify_task_complete(self, agent_slug: str, task_title: str):
        """Benachrichtige ueber abgeschlossenen Task."""
        profile = AGENT_PROFILES.get(agent_slug, AGENT_PROFILES["jarvis"])
        text = f"\u2705 {profile['name']}: \"{task_title}\" erledigt."
        target = self.group_id or self.chat_id
        await self.send_message(text, chat_id=target)

    async def notify_error(self, agent_slug: str, error: str):
        """Benachrichtige ueber einen Fehler."""
        profile = AGENT_PROFILES.get(agent_slug, AGENT_PROFILES["jarvis"])
        text = (
            f"\u26A0\uFE0F {profile['name']} — Fehler\n\n"
            f"{error[:500]}"
        )
        await self.send_message(text, chat_id=self.chat_id)

    async def notify_pattern_found(self, pattern_description: str, count: int):
        """ELON meldet ein erkanntes Pattern."""
        text = (
            f"\U0001F4CA ELON — Pattern erkannt\n\n"
            f"Muster: {pattern_description[:200]}\n"
            f"Haeufigkeit: {count}x\n"
            f"Status: Optimierung wird geplant"
        )
        await self.send_message(text, chat_id=self.chat_id)

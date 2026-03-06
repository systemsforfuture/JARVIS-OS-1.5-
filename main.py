"""
JARVIS 1.5 — Haupteinstiegspunkt
SYSTEMS™ · architectofscale.com

Startet alle Module:
  1. Core-Intelligence (DB, Memory, Learning, ELON, Runtime)
  2. Telegram Bot (Kommunikation mit DOM)
  3. Scheduler (ELON-Analyse, Auto-Improver, Cleanup)
  4. API Server (Dashboard-Backend)

Usage:
    python main.py
"""

import os
import sys
import asyncio
import signal
import logging
from pathlib import Path

# Projekt-Root zum Path hinzufügen
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

# ── Logging ───────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("jarvis.main")

# .env laden
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass


BANNER = """
  ═══════════════════════════════════════════════════
   ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗
   ██║██╔══██╗██╔══██╗██║   ██║██║██╔════╝
   ██║███████║██████╔╝██║   ██║██║███████╗
   ██║██╔══██║██╔══██╗╚██╗ ██╔╝██║╚════██║
   ██║██║  ██║██║  ██║ ╚████╔╝ ██║███████║
   ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝
   v1.5 — Autonomes KI-Betriebssystem
   SYSTEMS™ · architectofscale.com
  ═══════════════════════════════════════════════════
"""


async def start_scheduler(jarvis: dict):
    """Starte periodische Jobs."""
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
    except ImportError:
        logger.warning("apscheduler not installed — scheduler disabled")
        return None

    scheduler = AsyncIOScheduler()

    # ELON: Fehler analysieren — alle 6 Stunden
    async def elon_analyze():
        try:
            logger.info("[SCHEDULER] ELON Error Analysis...")
            await jarvis["elon"].analyze_errors()
            logger.info("[SCHEDULER] ELON Error Analysis done")
        except Exception as e:
            logger.error(f"[SCHEDULER] ELON Error Analysis failed: {e}")

    # ELON: KPIs tracken — täglich um 23:00
    async def elon_kpis():
        try:
            logger.info("[SCHEDULER] ELON KPI Tracking...")
            await jarvis["elon"].track_kpis()
            logger.info("[SCHEDULER] ELON KPIs tracked")
        except Exception as e:
            logger.error(f"[SCHEDULER] ELON KPIs failed: {e}")

    # ELON: Wochenanalyse — Montags um 08:00
    async def elon_weekly():
        try:
            logger.info("[SCHEDULER] ELON Weekly Analysis...")
            await jarvis["elon"].weekly_analysis()
            logger.info("[SCHEDULER] ELON Weekly Analysis done")
        except Exception as e:
            logger.error(f"[SCHEDULER] ELON Weekly failed: {e}")

    # Auto-Improver: Verbesserungszyklus — alle 12 Stunden
    async def auto_improve():
        try:
            logger.info("[SCHEDULER] Auto-Improver running...")
            report = await jarvis["improver"].run_improvement_cycle()
            logger.info(
                f"[SCHEDULER] Auto-Improver done: "
                f"{report.get('patterns_found', 0)} patterns, "
                f"{report.get('improvements_proposed', 0)} improvements"
            )
        except Exception as e:
            logger.error(f"[SCHEDULER] Auto-Improver failed: {e}")

    # Memory Cleanup — täglich um 03:00
    async def memory_cleanup():
        try:
            logger.info("[SCHEDULER] Memory cleanup...")
            await jarvis["brain"].cleanup()
            logger.info("[SCHEDULER] Memory cleanup done")
        except Exception as e:
            logger.error(f"[SCHEDULER] Memory cleanup failed: {e}")

    scheduler.add_job(elon_analyze, "interval", hours=6, id="elon_analyze")
    scheduler.add_job(elon_kpis, "cron", hour=23, id="elon_kpis")
    scheduler.add_job(elon_weekly, "cron", day_of_week="mon", hour=8, id="elon_weekly")
    scheduler.add_job(auto_improve, "interval", hours=12, id="auto_improve")
    scheduler.add_job(memory_cleanup, "cron", hour=3, id="memory_cleanup")

    # ── Proactive Intelligence Jobs ──
    proactive = jarvis.get("proactive")
    if proactive:
        scheduler.add_job(
            proactive.morning_briefing,
            "cron", hour=7, minute=0, id="morning_briefing",
        )
        scheduler.add_job(
            proactive.end_of_day_summary,
            "cron", hour=22, minute=0, id="eod_summary",
        )
        scheduler.add_job(
            proactive.weekly_planning,
            "cron", day_of_week="mon", hour=7, minute=30, id="weekly_planning",
        )
        scheduler.add_job(
            proactive.check_deadline_alerts,
            "interval", hours=1, id="deadline_alerts",
        )
        scheduler.add_job(
            proactive.check_birthday_alerts,
            "cron", hour=8, minute=0, id="birthday_alerts",
        )
        scheduler.add_job(
            proactive.proactive_suggestions,
            "interval", hours=4, id="proactive_suggestions",
        )

    # ── OKR Weekly Check-In ──
    goals = jarvis.get("goals")
    if goals:
        scheduler.add_job(
            goals.weekly_checkin,
            "cron", day_of_week="fri", hour=16, id="okr_checkin",
        )

    job_count = len(scheduler.get_jobs())
    scheduler.start()
    logger.info(f"Scheduler started ({job_count} jobs)")
    return scheduler


async def start_telegram(jarvis: dict):
    """Starte den Telegram Bot."""
    from core.integrations.telegram_bot import TelegramBot

    bot = TelegramBot(
        runtime=jarvis["runtime"],
        conversations=jarvis["conversations"],
    )
    await bot.start()
    return bot


async def start_api(jarvis: dict):
    """Starte den FastAPI Server (optional, für zusätzliche API-Endpoints)."""
    try:
        import uvicorn
        from core.api.server import create_app

        app = create_app(jarvis)
        config = uvicorn.Config(
            app, host="0.0.0.0",
            port=int(os.getenv("JARVIS_API_PORT", "8000")),
            log_level="info",
        )
        server = uvicorn.Server(config)
        asyncio.create_task(server.serve())
        logger.info(f"API Server started on port {os.getenv('JARVIS_API_PORT', '8000')}")
    except ImportError:
        logger.info("FastAPI/uvicorn not installed — API server disabled")
    except Exception as e:
        logger.warning(f"API server failed to start: {e}")


async def main():
    print(BANNER)

    # ─── 1. Core Intelligence starten ───
    logger.info("Initializing JARVIS Core Intelligence...")
    from core import init_jarvis
    jarvis = await init_jarvis()
    logger.info(f"JARVIS v{jarvis['version']} Core ready")

    # ─── 2. LLM Client einbinden ───
    try:
        from core.llm.llm_client import LLMClient
        jarvis["llm"] = LLMClient()
        logger.info("LLM Client ready")
    except Exception as e:
        logger.warning(f"LLM Client not available: {e}")

    # ─── 3. Scheduler starten ───
    scheduler = await start_scheduler(jarvis)

    # ─── 4. Telegram Bot starten ───
    telegram_bot = None
    if os.getenv("TELEGRAM_BOT_TOKEN"):
        try:
            telegram_bot = await start_telegram(jarvis)
        except Exception as e:
            logger.warning(f"Telegram Bot failed: {e}")
    else:
        logger.info("TELEGRAM_BOT_TOKEN not set — Telegram disabled")

    # ─── 5. API Server (optional) ───
    await start_api(jarvis)

    # ─── 6. Skills installieren (OpenClaw sync) ───
    skills_installed = None
    try:
        skill_installer = jarvis.get("skills")
        if skill_installer:
            skills_installed = await skill_installer.install_all()
            logger.info(
                f"Skills installed: {skills_installed.get('total_skills', 0)} skills "
                f"for {skills_installed.get('agents', 0)} agents"
            )
    except Exception as e:
        logger.warning(f"Skill installation failed: {e}")

    # ─── 7. Background Cron Jobs (Ollama-powered, 0 EUR) ───
    cron_jobs = None
    try:
        from core.cron.background_jobs import BackgroundJobs
        cron_jobs = BackgroundJobs(
            db_client=jarvis.get("db"),
            llm_client=jarvis.get("llm"),
            router=jarvis.get("router"),
        )
        await cron_jobs.start()
        logger.info("Background jobs started (Ollama-powered)")
    except Exception as e:
        logger.warning(f"Background jobs failed to start: {e}")

    # ─── 8. HEARTBEAT starten (Autonomer Intelligence-Puls) ───
    heartbeat = jarvis.get("heartbeat")
    if heartbeat:
        try:
            await heartbeat.start()
            logger.info("💓 Heartbeat active (5min pulse, Ollama-powered)")
        except Exception as e:
            logger.warning(f"Heartbeat failed to start: {e}")

    # ─── Ready ───
    logger.info("")
    logger.info("═══════════════════════════════════════")
    logger.info("  JARVIS 1.5 — ONLINE")
    logger.info(f"  Modules: {len(jarvis)} active")
    logger.info(f"  Telegram: {'active' if telegram_bot else 'disabled'}")
    logger.info(f"  Scheduler: {'active' if scheduler else 'disabled'}")
    logger.info(f"  Cron Jobs: {'active' if cron_jobs else 'disabled'}")
    logger.info(f"  Skills: {skills_installed.get('total_skills', 0) if skills_installed else 0} installed")
    logger.info(f"  Heartbeat: {'💓 active' if heartbeat else 'disabled'}")
    logger.info(f"  Voice: {'active' if jarvis.get('voice') else 'disabled'}")
    logger.info(f"  Chains: {len(jarvis.get('chains', {}).templates) if jarvis.get('chains') else 0} workflows")
    logger.info("═══════════════════════════════════════")
    logger.info("")

    # ─── Graceful Shutdown ───
    stop_event = asyncio.Event()

    def signal_handler():
        logger.info("Shutdown signal received...")
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)

    # Warte auf Shutdown-Signal
    await stop_event.wait()

    # Cleanup
    logger.info("Shutting down...")
    if heartbeat:
        await heartbeat.stop()
    if cron_jobs:
        await cron_jobs.stop()
    if telegram_bot:
        await telegram_bot.stop()
    if scheduler:
        scheduler.shutdown()
    logger.info("JARVIS offline. Bis bald.")


if __name__ == "__main__":
    asyncio.run(main())

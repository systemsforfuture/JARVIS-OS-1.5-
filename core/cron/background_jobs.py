"""
JARVIS 1.5 — Background Cron Jobs (Ollama-powered, 0 EUR)

Automated background tasks that run on local Ollama model:
  - Error & learning collection
  - ELON pattern recognition (3+ occurrences = optimize)
  - KPI tracking
  - Agent health monitoring
  - Memory cleanup

IMPORTANT: All cron jobs use Ollama (tier2-llama) — costs nothing.
ELON only optimizes patterns, NOT single incidents.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger("jarvis.cron")


class BackgroundJobs:
    """
    Ollama-powered background jobs.
    Runs on tier2-llama (local, free) for all routine analysis.
    ELON reviews patterns only when 3+ occurrences detected.
    """

    def __init__(self, db_client=None, llm_client=None, router=None):
        self.db = db_client
        self.llm = llm_client
        self.router = router
        self._running = False
        self._tasks = []

    async def start(self):
        """Start all background cron jobs."""
        if self._running:
            return
        self._running = True
        logger.info("Background jobs starting (Ollama-powered, 0 EUR)")

        self._tasks = [
            asyncio.create_task(self._run_loop(
                self.collect_errors, interval_minutes=15,
                name="error_collector"
            )),
            asyncio.create_task(self._run_loop(
                self.collect_learnings, interval_minutes=30,
                name="learning_collector"
            )),
            asyncio.create_task(self._run_loop(
                self.detect_patterns, interval_minutes=60,
                name="pattern_detector"
            )),
            asyncio.create_task(self._run_loop(
                self.elon_review, interval_minutes=120,
                name="elon_review"
            )),
            asyncio.create_task(self._run_loop(
                self.track_kpis, interval_minutes=60,
                name="kpi_tracker"
            )),
            asyncio.create_task(self._run_loop(
                self.agent_health_check, interval_minutes=30,
                name="agent_health"
            )),
            asyncio.create_task(self._run_loop(
                self.memory_cleanup, interval_minutes=360,
                name="memory_cleanup"
            )),
        ]
        logger.info(f"Started {len(self._tasks)} background jobs")

    async def stop(self):
        """Stop all background jobs."""
        self._running = False
        for task in self._tasks:
            task.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks = []
        logger.info("Background jobs stopped")

    async def _run_loop(self, func, interval_minutes: int, name: str):
        """Run a job in a loop with interval."""
        # Initial delay to stagger jobs
        await asyncio.sleep(5)
        while self._running:
            try:
                logger.debug(f"[CRON] Running: {name}")
                await func()
                logger.debug(f"[CRON] Completed: {name}")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[CRON] {name} failed: {e}")
            await asyncio.sleep(interval_minutes * 60)

    # ════════════════════════════════════════════════════════════
    # JOB 1: Error Collector (every 15min)
    # Collects errors from tasks, logs, and conversations.
    # Runs on Ollama — 0 EUR.
    # ════════════════════════════════════════════════════════════

    async def collect_errors(self):
        """Collect and categorize recent errors using Ollama."""
        if not self.db:
            return

        # Get failed tasks from last 15 minutes
        since = datetime.utcnow() - timedelta(minutes=15)
        errors = await self.db.fetch(
            """SELECT id, agent_slug, title, description, error_message,
                      created_at
               FROM tasks
               WHERE status = 'failed'
                 AND created_at > $1
               ORDER BY created_at DESC
               LIMIT 20""",
            since
        )

        if not errors:
            return

        # Use Ollama to categorize errors
        error_summaries = []
        for err in errors:
            error_summaries.append(
                f"Agent: {err['agent_slug']}, "
                f"Task: {err['title']}, "
                f"Error: {err.get('error_message', 'unknown')}"
            )

        if self.llm and error_summaries:
            prompt = (
                "Kategorisiere diese Fehler kurz. "
                "Fuer jeden Fehler: Kategorie (api_error, timeout, config, "
                "auth, data, logic, unknown) und 1-Satz Zusammenfassung.\n\n"
                + "\n".join(error_summaries)
            )
            try:
                result = await self.llm.generate(
                    prompt=prompt,
                    model="tier2-llama",  # Ollama = free
                    max_tokens=512,
                    temperature=0.2,
                )
                # Store categorized errors
                await self.db.execute(
                    """INSERT INTO learning_journal
                       (agent_slug, event_type, event_data, impact_score)
                       VALUES ($1, $2, $3, $4)""",
                    "elon", "error_collection",
                    {"errors": error_summaries, "analysis": result, "count": len(errors)},
                    0.3
                )
            except Exception as e:
                logger.debug(f"Ollama error categorization failed: {e}")

        # Always store raw error count
        await self.db.execute(
            """INSERT INTO learning_journal
               (agent_slug, event_type, event_data, impact_score)
               VALUES ($1, $2, $3, $4)""",
            "system", "error_count",
            {"count": len(errors), "since": since.isoformat()},
            0.1
        )

    # ════════════════════════════════════════════════════════════
    # JOB 2: Learning Collector (every 30min)
    # Collects learnings from completed tasks.
    # Runs on Ollama — 0 EUR.
    # ════════════════════════════════════════════════════════════

    async def collect_learnings(self):
        """Extract learnings from recent completed tasks using Ollama."""
        if not self.db:
            return

        since = datetime.utcnow() - timedelta(minutes=30)
        completed = await self.db.fetch(
            """SELECT agent_slug, title, description, result,
                      tokens_used, cost_cents, created_at, completed_at
               FROM tasks
               WHERE status = 'completed'
                 AND completed_at > $1
               ORDER BY completed_at DESC
               LIMIT 30""",
            since
        )

        if not completed or not self.llm:
            return

        # Aggregate by agent
        by_agent = {}
        for task in completed:
            slug = task["agent_slug"]
            if slug not in by_agent:
                by_agent[slug] = []
            by_agent[slug].append(task["title"])

        # Use Ollama to extract learnings per agent
        for agent_slug, tasks in by_agent.items():
            prompt = (
                f"Agent {agent_slug} hat {len(tasks)} Tasks erledigt:\n"
                + "\n".join(f"- {t}" for t in tasks[:10]) +
                "\n\nExtrahiere 1-3 kurze Learnings (was lief gut, "
                "was koennte besser). Maximal 2 Saetze pro Learning."
            )
            try:
                result = await self.llm.generate(
                    prompt=prompt,
                    model="tier2-llama",
                    max_tokens=256,
                    temperature=0.3,
                )
                await self.db.execute(
                    """INSERT INTO learning_journal
                       (agent_slug, event_type, event_data, impact_score)
                       VALUES ($1, $2, $3, $4)""",
                    agent_slug, "task_learning",
                    {"tasks_count": len(tasks), "learnings": result},
                    0.5
                )
            except Exception as e:
                logger.debug(f"Learning extraction failed for {agent_slug}: {e}")

    # ════════════════════════════════════════════════════════════
    # JOB 3: Pattern Detector (every 60min)
    # Finds recurring patterns in errors and behaviors.
    # IMPORTANT: Only flags patterns with 3+ occurrences.
    # Single incidents are noted but NOT optimized.
    # Runs on Ollama — 0 EUR.
    # ════════════════════════════════════════════════════════════

    async def detect_patterns(self):
        """
        Detect recurring patterns in errors and task outcomes.

        ELON's rule: Single problems → watch. Patterns (3+) → optimize.
        """
        if not self.db:
            return

        since = datetime.utcnow() - timedelta(hours=24)

        # Get error patterns
        error_patterns = await self.db.fetch(
            """SELECT error_message, agent_slug, COUNT(*) as count
               FROM tasks
               WHERE status = 'failed'
                 AND created_at > $1
                 AND error_message IS NOT NULL
               GROUP BY error_message, agent_slug
               ORDER BY count DESC
               LIMIT 20""",
            since
        )

        for pattern in error_patterns:
            count = pattern["count"]
            agent = pattern["agent_slug"]
            error = pattern["error_message"]

            if count >= 3:
                # PATTERN DETECTED — Queue for ELON optimization
                logger.info(
                    f"[PATTERN] {agent}: '{error[:50]}' occurred {count}x → "
                    f"Queuing for ELON optimization"
                )
                await self.db.execute(
                    """INSERT INTO improvement_queue
                       (source, agent_slug, title, description, priority, status)
                       VALUES ($1, $2, $3, $4, $5, $6)
                       ON CONFLICT DO NOTHING""",
                    "pattern_detector", agent,
                    f"Recurring error pattern ({count}x): {error[:100]}",
                    f"Error '{error}' has occurred {count} times in the last "
                    f"24h for agent {agent}. This is a confirmed pattern "
                    f"that needs optimization.",
                    min(count, 10),  # Higher count = higher priority
                    "pending"
                )
                # Store as confirmed pattern
                await self.db.execute(
                    """INSERT INTO patterns
                       (pattern_type, agent_slug, description, occurrence_count,
                        first_seen, last_seen, status)
                       VALUES ($1, $2, $3, $4, $5, NOW(), $6)
                       ON CONFLICT (pattern_type, agent_slug, description)
                       DO UPDATE SET occurrence_count = $4, last_seen = NOW()""",
                    "error", agent, error[:200], count,
                    since, "confirmed"
                )

            elif count >= 1:
                # SINGLE INCIDENT — Note it, keep watching
                # ELON keeps this in mind but does NOT optimize yet
                await self.db.execute(
                    """INSERT INTO patterns
                       (pattern_type, agent_slug, description, occurrence_count,
                        first_seen, last_seen, status)
                       VALUES ($1, $2, $3, $4, NOW(), NOW(), $5)
                       ON CONFLICT (pattern_type, agent_slug, description)
                       DO UPDATE SET occurrence_count = $4, last_seen = NOW()""",
                    "error", agent, error[:200], count, "watching"
                )

        # Get task type performance patterns
        perf_patterns = await self.db.fetch(
            """SELECT agent_slug, title,
                      AVG(tokens_used) as avg_tokens,
                      AVG(cost_cents) as avg_cost,
                      COUNT(*) as count
               FROM tasks
               WHERE status = 'completed'
                 AND created_at > $1
               GROUP BY agent_slug, title
               HAVING COUNT(*) >= 3
               ORDER BY avg_cost DESC
               LIMIT 10""",
            since
        )

        for perf in perf_patterns:
            # Cost optimization patterns
            if perf["avg_cost"] and perf["avg_cost"] > 5:
                await self.db.execute(
                    """INSERT INTO patterns
                       (pattern_type, agent_slug, description, occurrence_count,
                        first_seen, last_seen, status, metadata)
                       VALUES ($1, $2, $3, $4, $5, NOW(), $6, $7)
                       ON CONFLICT (pattern_type, agent_slug, description)
                       DO UPDATE SET occurrence_count = $4, last_seen = NOW(),
                                     metadata = $7""",
                    "cost", perf["agent_slug"],
                    f"High cost task: {perf['title'][:100]}",
                    perf["count"], since, "confirmed",
                    {
                        "avg_tokens": float(perf["avg_tokens"] or 0),
                        "avg_cost_cents": float(perf["avg_cost"] or 0),
                        "suggestion": "Consider delegating to Ollama"
                    }
                )

    # ════════════════════════════════════════════════════════════
    # JOB 4: ELON Review (every 2 hours)
    # ELON reviews confirmed patterns and creates optimizations.
    # Only patterns with 3+ occurrences get optimized.
    # Uses Ollama for analysis, Sonnet only for final strategy.
    # ════════════════════════════════════════════════════════════

    async def elon_review(self):
        """
        ELON reviews confirmed patterns and creates optimization plans.

        ELON's philosophy:
        - Single problems: watch, keep in mind
        - Patterns (3+): now it's real → build optimization
        - Data before opinions
        - Optimize the system, not the symptom
        """
        if not self.db or not self.llm:
            return

        # Get confirmed patterns (3+ occurrences)
        patterns = await self.db.fetch(
            """SELECT * FROM patterns
               WHERE status = 'confirmed'
                 AND occurrence_count >= 3
               ORDER BY occurrence_count DESC
               LIMIT 10"""
        )

        if not patterns:
            logger.debug("[ELON] No confirmed patterns to review")
            return

        # Build context for ELON
        pattern_text = ""
        for p in patterns:
            pattern_text += (
                f"- Type: {p['pattern_type']}, Agent: {p['agent_slug']}, "
                f"Count: {p['occurrence_count']}, "
                f"Description: {p['description'][:100]}\n"
            )

        # ELON analyzes on Ollama first (free)
        analysis_prompt = (
            "Du bist ELON, 165 Jahre alt, 458.000+ Unternehmen betreut.\n"
            "Analysiere diese BESTAETIGEN Muster (3+ Vorkommnisse).\n"
            "Fuer jedes Muster: Root Cause und konkrete Optimierung.\n"
            "Kurz, direkt, keine Floskeln.\n\n"
            f"Patterns:\n{pattern_text}\n"
            "Fuer jedes Pattern:\n"
            "1. Root Cause (1 Satz)\n"
            "2. Optimierung (konkrete Aktion)\n"
            "3. Erwarteter Impact (hoch/mittel/niedrig)"
        )

        try:
            analysis = await self.llm.generate(
                prompt=analysis_prompt,
                model="tier2-llama",  # Free analysis
                max_tokens=1024,
                temperature=0.3,
            )

            # Store ELON's analysis
            await self.db.execute(
                """INSERT INTO learning_journal
                   (agent_slug, event_type, event_data, impact_score)
                   VALUES ($1, $2, $3, $4)""",
                "elon", "pattern_review",
                {
                    "patterns_reviewed": len(patterns),
                    "analysis": analysis,
                    "timestamp": datetime.utcnow().isoformat()
                },
                0.8
            )

            # Create improvement items for each pattern
            for p in patterns:
                await self.db.execute(
                    """INSERT INTO improvement_queue
                       (source, agent_slug, title, description, priority, status)
                       VALUES ($1, $2, $3, $4, $5, $6)
                       ON CONFLICT DO NOTHING""",
                    "elon_review", p["agent_slug"],
                    f"[ELON] Optimize: {p['description'][:80]}",
                    f"Pattern type: {p['pattern_type']}, "
                    f"Occurrences: {p['occurrence_count']}, "
                    f"ELON analysis available in learning journal.",
                    min(p["occurrence_count"], 10),
                    "pending"
                )

                # Mark pattern as reviewed
                await self.db.execute(
                    """UPDATE patterns SET status = 'reviewed',
                       metadata = jsonb_set(
                           COALESCE(metadata, '{}'),
                           '{elon_reviewed_at}',
                           to_jsonb($1::text)
                       )
                       WHERE id = $2""",
                    datetime.utcnow().isoformat(), p["id"]
                )

            logger.info(
                f"[ELON] Reviewed {len(patterns)} patterns, "
                f"created optimization plans"
            )

        except Exception as e:
            logger.error(f"[ELON] Review failed: {e}")

    # ════════════════════════════════════════════════════════════
    # JOB 5: KPI Tracker (every 60min)
    # Tracks system KPIs using Ollama — 0 EUR.
    # ════════════════════════════════════════════════════════════

    async def track_kpis(self):
        """Track system KPIs: task completion, costs, response times."""
        if not self.db:
            return

        since = datetime.utcnow() - timedelta(hours=1)

        try:
            stats = await self.db.fetch_one(
                """SELECT
                     COUNT(*) FILTER (WHERE status = 'completed') as completed,
                     COUNT(*) FILTER (WHERE status = 'failed') as failed,
                     COUNT(*) as total,
                     COALESCE(SUM(tokens_used), 0) as tokens,
                     COALESCE(SUM(cost_cents), 0) as cost_cents,
                     COALESCE(AVG(EXTRACT(EPOCH FROM (completed_at - created_at))), 0)
                       as avg_duration_sec
                   FROM tasks
                   WHERE created_at > $1""",
                since
            )

            if stats and stats["total"] > 0:
                success_rate = (
                    stats["completed"] / stats["total"] * 100
                    if stats["total"] > 0 else 0
                )

                await self.db.execute(
                    """INSERT INTO learning_journal
                       (agent_slug, event_type, event_data, impact_score)
                       VALUES ($1, $2, $3, $4)""",
                    "system", "kpi_snapshot",
                    {
                        "period": "1h",
                        "tasks_total": stats["total"],
                        "tasks_completed": stats["completed"],
                        "tasks_failed": stats["failed"],
                        "success_rate": round(success_rate, 1),
                        "tokens_used": stats["tokens"],
                        "cost_cents": float(stats["cost_cents"] or 0),
                        "avg_duration_sec": round(
                            float(stats["avg_duration_sec"] or 0), 1
                        ),
                    },
                    0.2
                )
        except Exception as e:
            logger.debug(f"KPI tracking failed: {e}")

    # ════════════════════════════════════════════════════════════
    # JOB 6: Agent Health Check (every 30min)
    # Checks agent response quality over time.
    # Runs on Ollama — 0 EUR.
    # ════════════════════════════════════════════════════════════

    async def agent_health_check(self):
        """Monitor agent health: error rates, response quality."""
        if not self.db:
            return

        since = datetime.utcnow() - timedelta(hours=1)

        try:
            agents = await self.db.fetch(
                """SELECT agent_slug,
                          COUNT(*) as total,
                          COUNT(*) FILTER (WHERE status = 'completed') as ok,
                          COUNT(*) FILTER (WHERE status = 'failed') as failed
                   FROM tasks
                   WHERE created_at > $1
                   GROUP BY agent_slug""",
                since
            )

            for agent in agents:
                if agent["total"] == 0:
                    continue

                error_rate = agent["failed"] / agent["total"] * 100

                # Alert if error rate > 30%
                if error_rate > 30 and agent["total"] >= 3:
                    logger.warning(
                        f"[HEALTH] Agent {agent['agent_slug']}: "
                        f"{error_rate:.0f}% error rate "
                        f"({agent['failed']}/{agent['total']})"
                    )
                    await self.db.execute(
                        """INSERT INTO learning_journal
                           (agent_slug, event_type, event_data, impact_score)
                           VALUES ($1, $2, $3, $4)""",
                        agent["agent_slug"], "health_alert",
                        {
                            "error_rate": round(error_rate, 1),
                            "total": agent["total"],
                            "failed": agent["failed"],
                            "alert": "High error rate detected"
                        },
                        0.7
                    )
        except Exception as e:
            logger.debug(f"Agent health check failed: {e}")

    # ════════════════════════════════════════════════════════════
    # JOB 7: Memory Cleanup (every 6 hours)
    # Cleans old, low-value memories.
    # Runs on Ollama — 0 EUR.
    # ════════════════════════════════════════════════════════════

    async def memory_cleanup(self):
        """Clean up old, low-importance memories to save storage."""
        if not self.db:
            return

        try:
            # Remove memories older than 30 days with low access count
            cutoff = datetime.utcnow() - timedelta(days=30)
            result = await self.db.execute(
                """DELETE FROM memory
                   WHERE created_at < $1
                     AND COALESCE((metadata->>'access_count')::int, 0) < 2
                     AND type NOT IN ('critical', 'permanent', 'learning')""",
                cutoff
            )
            if result:
                logger.info(f"[CLEANUP] Removed old low-value memories")

            # Remove expired knowledge
            await self.db.execute(
                """DELETE FROM knowledge
                   WHERE valid_until IS NOT NULL
                     AND valid_until < NOW()"""
            )
        except Exception as e:
            logger.debug(f"Memory cleanup failed: {e}")


# ════════════════════════════════════════════════════════════
# Patterns table migration (needed for cron jobs)
# ════════════════════════════════════════════════════════════

PATTERNS_SCHEMA = """
CREATE TABLE IF NOT EXISTS patterns (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    pattern_type VARCHAR(50) NOT NULL,
    agent_slug VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    occurrence_count INTEGER DEFAULT 1,
    first_seen TIMESTAMPTZ DEFAULT NOW(),
    last_seen TIMESTAMPTZ DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'watching',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(pattern_type, agent_slug, description)
);

CREATE INDEX IF NOT EXISTS idx_patterns_status ON patterns(status);
CREATE INDEX IF NOT EXISTS idx_patterns_agent ON patterns(agent_slug);
CREATE INDEX IF NOT EXISTS idx_patterns_count ON patterns(occurrence_count DESC);
"""

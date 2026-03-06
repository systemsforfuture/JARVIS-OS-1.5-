"""
JARVIS 1.5 — Goal & OKR Tracker
SYSTEMS™ · architectofscale.com

Tracke Quartals-Ziele, OKRs und persoenliche Habits.
JARVIS erinnert, motiviert und reportet automatisch.

Struktur:
  Goal (z.B. "100k MRR")
    └── Key Result 1 (z.B. "50 neue Kunden")
        └── Milestone (z.B. "25 Kunden bis Mitte Quartal")
    └── Key Result 2 (z.B. "Churn unter 5%")
    └── Key Result 3 (z.B. "3 Enterprise Deals")

Features:
  - Ziele erstellen mit Key Results
  - Automatisches Fortschritts-Tracking
  - Woechentliche OKR Check-Ins
  - Quartals-Review mit Scoring
  - AI-generierte Empfehlungen bei Rueckstand
  - Habit Tracking (taegliche Gewohnheiten)
"""

import json
import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

logger = logging.getLogger("jarvis.goals")


class GoalTracker:
    """
    OKR und Ziel-Management.
    """

    def __init__(self, db_client=None, llm_client=None, notify=None):
        self.db = db_client
        self.llm = llm_client
        self.notify = notify

    # ═══════════════════════════════════════════════════
    # GOAL CRUD
    # ═══════════════════════════════════════════════════

    async def create_goal(
        self,
        title: str,
        description: str = "",
        category: str = "business",
        quarter: str = "",
        key_results: list = None,
        deadline: str = "",
    ) -> dict:
        """Erstelle ein neues Ziel mit Key Results."""
        if not quarter:
            now = datetime.now(timezone.utc)
            quarter = f"Q{(now.month - 1) // 3 + 1}/{now.year}"

        goal_id = str(uuid.uuid4())[:8]

        goal = {
            "id": goal_id,
            "title": title,
            "description": description,
            "category": category,
            "quarter": quarter,
            "deadline": deadline or self._quarter_end(quarter),
            "status": "active",
            "progress": 0,
            "key_results": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        # Key Results hinzufuegen
        for i, kr in enumerate(key_results or []):
            goal["key_results"].append({
                "id": f"{goal_id}-kr{i+1}",
                "title": kr.get("title", kr) if isinstance(kr, dict) else str(kr),
                "target": kr.get("target", 100) if isinstance(kr, dict) else 100,
                "current": 0,
                "unit": kr.get("unit", "%") if isinstance(kr, dict) else "%",
                "progress": 0,
            })

        # In DB speichern
        if self.db:
            try:
                await self.db.upsert("memory", {
                    "key": f"goal:{goal_id}",
                    "value": json.dumps(goal, ensure_ascii=False),
                    "category": "goals",
                })
            except Exception as e:
                logger.error(f"Could not save goal: {e}")

        logger.info(f"Goal created: {title} ({len(goal['key_results'])} KRs)")
        return goal

    async def update_key_result(
        self,
        goal_id: str,
        kr_index: int,
        current_value: float,
    ) -> dict:
        """Update den Fortschritt eines Key Results."""
        goal = await self.get_goal(goal_id)
        if not goal:
            return {"error": f"Goal {goal_id} not found"}

        if kr_index >= len(goal["key_results"]):
            return {"error": f"KR index {kr_index} out of range"}

        kr = goal["key_results"][kr_index]
        kr["current"] = current_value
        kr["progress"] = min(100, int((current_value / max(kr["target"], 1)) * 100))

        # Gesamt-Progress berechnen
        total_progress = sum(
            k["progress"] for k in goal["key_results"]
        ) / max(len(goal["key_results"]), 1)
        goal["progress"] = int(total_progress)

        # Status updaten
        if goal["progress"] >= 100:
            goal["status"] = "completed"
        elif goal["progress"] >= 70:
            goal["status"] = "on_track"
        elif goal["progress"] >= 40:
            goal["status"] = "at_risk"
        else:
            goal["status"] = "behind"

        # Speichern
        if self.db:
            await self.db.upsert("memory", {
                "key": f"goal:{goal_id}",
                "value": json.dumps(goal, ensure_ascii=False),
                "category": "goals",
            })

        return goal

    async def get_goal(self, goal_id: str) -> Optional[dict]:
        """Lade ein Ziel."""
        if not self.db:
            return None
        try:
            result = await self.db.query("memory", filters={
                "key": f"goal:{goal_id}",
                "category": "goals",
            }, limit=1)
            if result:
                return json.loads(result[0].get("value", "{}"))
        except Exception:
            pass
        return None

    async def get_all_goals(self, quarter: str = "", status: str = "") -> list:
        """Alle Ziele laden, optional gefiltert."""
        if not self.db:
            return []
        try:
            results = await self.db.query("memory", filters={"category": "goals"}, limit=100)
            goals = []
            for r in (results or []):
                try:
                    goal = json.loads(r.get("value", "{}"))
                    if quarter and goal.get("quarter") != quarter:
                        continue
                    if status and goal.get("status") != status:
                        continue
                    goals.append(goal)
                except json.JSONDecodeError:
                    continue
            return sorted(goals, key=lambda g: g.get("progress", 0), reverse=True)
        except Exception:
            return []

    # ═══════════════════════════════════════════════════
    # HABIT TRACKING
    # ═══════════════════════════════════════════════════

    async def create_habit(
        self,
        title: str,
        frequency: str = "daily",
        target_per_period: int = 1,
    ) -> dict:
        """Erstelle einen neuen Habit."""
        habit_id = str(uuid.uuid4())[:8]
        habit = {
            "id": habit_id,
            "title": title,
            "frequency": frequency,
            "target": target_per_period,
            "streak": 0,
            "best_streak": 0,
            "total_completions": 0,
            "history": {},  # {"2024-01-15": 1, ...}
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        if self.db:
            await self.db.upsert("memory", {
                "key": f"habit:{habit_id}",
                "value": json.dumps(habit, ensure_ascii=False),
                "category": "habits",
            })

        return habit

    async def log_habit(self, habit_id: str, count: int = 1) -> dict:
        """Logge eine Habit-Completion."""
        if not self.db:
            return {"error": "No DB"}

        try:
            result = await self.db.query("memory", filters={
                "key": f"habit:{habit_id}", "category": "habits",
            }, limit=1)
            if not result:
                return {"error": "Habit not found"}

            habit = json.loads(result[0].get("value", "{}"))
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

            habit["history"][today] = habit["history"].get(today, 0) + count
            habit["total_completions"] += count

            # Streak berechnen
            habit["streak"] = self._calculate_streak(habit["history"])
            habit["best_streak"] = max(habit["best_streak"], habit["streak"])

            await self.db.upsert("memory", {
                "key": f"habit:{habit_id}",
                "value": json.dumps(habit, ensure_ascii=False),
                "category": "habits",
            })

            return habit
        except Exception as e:
            return {"error": str(e)}

    def _calculate_streak(self, history: dict) -> int:
        """Berechne die aktuelle Streak."""
        today = datetime.now(timezone.utc).date()
        streak = 0
        current = today

        while True:
            date_str = current.strftime("%Y-%m-%d")
            if history.get(date_str, 0) > 0:
                streak += 1
                current -= timedelta(days=1)
            else:
                break

        return streak

    # ═══════════════════════════════════════════════════
    # REPORTS & CHECK-INS
    # ═══════════════════════════════════════════════════

    async def weekly_checkin(self) -> str:
        """
        Woechentlicher OKR Check-In.
        Wird automatisch Freitags um 16:00 ausgefuehrt.
        """
        goals = await self.get_all_goals(status="active")
        if not goals:
            return "Keine aktiven Ziele. Erstelle welche mit /goal create!"

        sections = []

        for goal in goals:
            status_emoji = {
                "on_track": "🟢",
                "at_risk": "🟡",
                "behind": "🔴",
                "completed": "✅",
            }.get(goal.get("status"), "⚪")

            kr_lines = []
            for kr in goal.get("key_results", []):
                bar = self._progress_bar(kr.get("progress", 0))
                kr_lines.append(
                    f"    {bar} {kr.get('current', 0)}/{kr.get('target', 100)} "
                    f"{kr.get('unit', '')} — {kr.get('title', '')}"
                )

            sections.append(
                f"{status_emoji} {goal.get('title', '?')} — {goal.get('progress', 0)}%\n"
                + "\n".join(kr_lines)
            )

        report = (
            f"═══════════════════════════════════\n"
            f"  OKR WEEKLY CHECK-IN\n"
            f"  {datetime.now(timezone.utc).strftime('%d.%m.%Y')}\n"
            f"═══════════════════════════════════\n\n"
            + "\n\n".join(sections)
        )

        # AI-Empfehlungen fuer Ziele die hinterherhinken
        behind = [g for g in goals if g.get("status") == "behind"]
        if behind and self.llm:
            try:
                behind_list = "\n".join(f"- {g['title']} ({g['progress']}%)" for g in behind)
                advice = await self.llm.generate(
                    prompt=(
                        f"Diese Ziele liegen hinter dem Plan:\n{behind_list}\n\n"
                        f"Gib 2-3 kurze, actionable Tipps um aufzuholen."
                    ),
                    model="tier2-llama",
                    max_tokens=200,
                )
                report += f"\n\n💡 COACHING:\n{advice}"
            except Exception:
                pass

        if self.notify:
            await self.notify(report, urgency="info")

        return report

    async def quarter_review(self, quarter: str = "") -> str:
        """Quartals-Review mit Scoring."""
        if not quarter:
            now = datetime.now(timezone.utc)
            quarter = f"Q{(now.month - 1) // 3 + 1}/{now.year}"

        goals = await self.get_all_goals(quarter=quarter)
        if not goals:
            return f"Keine Ziele fuer {quarter} gefunden."

        total_progress = sum(g.get("progress", 0) for g in goals) / max(len(goals), 1)
        completed = sum(1 for g in goals if g.get("status") == "completed")

        score = (
            "🏆 OUTSTANDING" if total_progress >= 90 else
            "✅ ON TARGET" if total_progress >= 70 else
            "⚠️ NEEDS IMPROVEMENT" if total_progress >= 40 else
            "❌ MISSED"
        )

        review = (
            f"═══════════════════════════════════\n"
            f"  QUARTALS-REVIEW {quarter}\n"
            f"  Score: {score}\n"
            f"═══════════════════════════════════\n\n"
            f"Gesamt-Fortschritt: {total_progress:.0f}%\n"
            f"Ziele: {completed}/{len(goals)} abgeschlossen\n\n"
        )

        for goal in goals:
            review += (
                f"{'✅' if goal.get('progress', 0) >= 100 else '❌'} "
                f"{goal.get('title', '?')} — {goal.get('progress', 0)}%\n"
            )

        return review

    def _progress_bar(self, progress: int, width: int = 10) -> str:
        """Erstelle einen visuellen Fortschrittsbalken."""
        filled = int(width * min(progress, 100) / 100)
        return "█" * filled + "░" * (width - filled)

    def _quarter_end(self, quarter: str) -> str:
        """Berechne das Ende eines Quartals."""
        try:
            q_num = int(quarter[1])
            year = int(quarter.split("/")[1])
            month = q_num * 3
            if month == 12:
                return f"{year}-12-31"
            return f"{year}-{month:02d}-{28 if month == 2 else 30}"
        except Exception:
            return ""

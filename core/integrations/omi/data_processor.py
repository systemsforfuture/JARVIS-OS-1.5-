"""
JARVIS 1.5 — OMI Data Processor
Verarbeitet OMI-Daten und baut kontinuierliche Intelligenz auf.

Dieser Processor ist das Herzstück der OMI-Integration:
  - Extrahiert Wissen aus jedem Gespraech (Kontakte, Daten, Fakten)
  - Erkennt Geburtstage, Termine, Namen, Vorlieben
  - Baut ein persoenliches Wissensnetz auf
  - Erstellt automatisch Tasks aus Action Items
  - Erkennt wiederkehrende Themen → Algorithmen
  - Speichert alles in strukturierter JARVIS-Architektur

JARVIS wird jeden Tag schlauer durch jedes Gespraech.
Nutzt Ollama (kostenlos) fuer Routine-Extraktion.
"""

import logging
import re
from datetime import datetime
from typing import Optional

logger = logging.getLogger("jarvis.omi.processor")


class OMIDataProcessor:
    """
    Verarbeitet OMI Memory-Daten und baut JARVIS Intelligence auf.

    Pipeline:
    1. Raw Memory → Structured Extraction (Ollama, free)
    2. Entity Extraction (Personen, Firmen, Daten)
    3. Knowledge Graph Update (Fakten, Beziehungen)
    4. Action Item → Task Pipeline
    5. Pattern Detection (wiederkehrende Themen)
    6. Personal Profile Update (Vorlieben, Gewohnheiten)
    """

    def __init__(self, db_client=None, llm_client=None, brain=None, knowledge=None):
        self.db = db_client
        self.llm = llm_client
        self.brain = brain
        self.knowledge = knowledge

    async def process_memory(
        self,
        memory_id: str,
        uid: str,
        title: str,
        overview: str,
        category: str,
        transcript: str,
        action_items: list,
        events: list,
        raw_data: dict,
        created_at: str,
    ):
        """
        Vollstaendige Verarbeitung einer OMI Memory.
        Wird bei jedem beendeten Gespraech aufgerufen.
        """
        logger.info(f"[OMI] Processing memory: {title}")

        # 1. Store raw memory
        await self._store_raw_memory(
            memory_id, uid, title, overview, category,
            transcript, raw_data, created_at
        )

        # 2. Extract entities (people, dates, companies)
        entities = await self._extract_entities(transcript, overview)

        # 3. Extract knowledge (facts, preferences, decisions)
        knowledge_items = await self._extract_knowledge(
            transcript, overview, category
        )

        # 4. Process action items → Tasks
        await self._process_action_items(action_items, uid)

        # 5. Process events (birthdays, meetings, deadlines)
        await self._process_events(events, uid)

        # 6. Update personal profile
        await self._update_personal_profile(entities, knowledge_items, uid)

        # 7. Detect conversation patterns
        await self._detect_patterns(category, entities, uid)

        # 8. Store in knowledge graph
        await self._update_knowledge_graph(entities, knowledge_items, memory_id)

        logger.info(
            f"[OMI] Memory processed: {len(entities)} entities, "
            f"{len(knowledge_items)} knowledge items, "
            f"{len(action_items)} action items"
        )

    # ═══════════════════════════════════════════════════════════
    # STEP 1: Store Raw Memory
    # ═══════════════════════════════════════════════════════════

    async def _store_raw_memory(self, memory_id, uid, title, overview,
                                 category, transcript, raw_data, created_at):
        """Speichere die rohe OMI Memory in der Datenbank."""
        if not self.db:
            return
        try:
            await self.db.execute(
                """INSERT INTO omi_memories
                   (omi_memory_id, uid, title, overview, category,
                    transcript, raw_data, importance, created_at)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                   ON CONFLICT (omi_memory_id) DO UPDATE SET
                     overview = $4, processed_at = NOW()""",
                memory_id, uid, title, overview, category,
                transcript, raw_data,
                self._calculate_importance(category, overview, transcript),
                created_at,
            )
        except Exception as e:
            logger.debug(f"Store raw memory failed: {e}")

    # ═══════════════════════════════════════════════════════════
    # STEP 2: Entity Extraction
    # Personen, Firmen, Orte, Daten aus Gespraechen extrahieren.
    # Nutzt Ollama (kostenlos).
    # ═══════════════════════════════════════════════════════════

    async def _extract_entities(self, transcript: str, overview: str) -> list:
        """Extrahiere Entities aus dem Gespraech."""
        entities = []

        # Quick regex extraction (free, instant)
        entities.extend(self._regex_extract_entities(transcript))
        entities.extend(self._regex_extract_entities(overview))

        # LLM extraction for deeper understanding (Ollama = free)
        if self.llm and transcript:
            try:
                prompt = (
                    "Extrahiere alle wichtigen Entities aus diesem Gespraech. "
                    "Format: JSON Array mit {type, name, context}\n"
                    "Types: person, company, date, birthday, location, product, "
                    "decision, preference, contact_info\n\n"
                    f"Gespraech:\n{transcript[:2000]}\n\n"
                    "Nur das JSON Array, keine Erklaerung."
                )
                result = await self.llm.generate(
                    prompt=prompt,
                    model="tier2-llama",  # Ollama = free
                    max_tokens=512,
                    temperature=0.2,
                )
                # Parse LLM response
                try:
                    import json
                    parsed = json.loads(result.strip().strip("```json").strip("```"))
                    if isinstance(parsed, list):
                        entities.extend(parsed)
                except (json.JSONDecodeError, ValueError):
                    pass
            except Exception as e:
                logger.debug(f"LLM entity extraction: {e}")

        return entities

    def _regex_extract_entities(self, text: str) -> list:
        """Schnelle Regex-basierte Entity Extraction."""
        entities = []
        if not text:
            return entities

        # Dates (DD.MM.YYYY, DD/MM/YYYY, DD. Month YYYY)
        date_patterns = [
            r'\b(\d{1,2})[./](\d{1,2})[./](\d{2,4})\b',
            r'\b(\d{1,2})\.\s*(Januar|Februar|März|April|Mai|Juni|Juli|'
            r'August|September|Oktober|November|Dezember)\s*(\d{2,4})?\b',
        ]
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for m in matches:
                entities.append({
                    "type": "date",
                    "name": " ".join(str(p) for p in m if p),
                    "context": "date_mention"
                })

        # Email addresses
        emails = re.findall(r'[\w.+-]+@[\w-]+\.[\w.]+', text)
        for email in emails:
            entities.append({
                "type": "contact_info",
                "name": email,
                "context": "email"
            })

        # Phone numbers
        phones = re.findall(
            r'(?:\+\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}',
            text
        )
        for phone in phones:
            if len(phone.replace(" ", "").replace("-", "")) >= 8:
                entities.append({
                    "type": "contact_info",
                    "name": phone.strip(),
                    "context": "phone"
                })

        # Birthday keywords
        bday_patterns = [
            r'(?:geburtstag|birthday).*?(\d{1,2})[./](\d{1,2})',
            r'(\d{1,2})[./](\d{1,2}).*?(?:geburtstag|birthday)',
            r'(?:wird|turned?)\s+(\d{1,3})\s+(?:jahre?\s+alt|years?\s+old)',
        ]
        for pattern in bday_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for m in matches:
                entities.append({
                    "type": "birthday",
                    "name": ".".join(str(p) for p in m if p),
                    "context": "birthday_mention"
                })

        # URLs
        urls = re.findall(r'https?://\S+', text)
        for url in urls:
            entities.append({
                "type": "url",
                "name": url,
                "context": "link"
            })

        return entities

    # ═══════════════════════════════════════════════════════════
    # STEP 3: Knowledge Extraction
    # Fakten, Vorlieben, Entscheidungen aus Gespraechen.
    # ═══════════════════════════════════════════════════════════

    async def _extract_knowledge(self, transcript: str, overview: str,
                                  category: str) -> list:
        """Extrahiere Wissen aus dem Gespraech."""
        knowledge_items = []

        if not self.llm or not transcript:
            return knowledge_items

        try:
            prompt = (
                "Extrahiere wichtiges Wissen aus diesem Gespraech.\n"
                "Format: JSON Array mit {subject, predicate, object, confidence, category}\n"
                "Beispiele:\n"
                '  {"subject":"Max Mueller","predicate":"hat_geburtstag","object":"15.03.","confidence":0.9,"category":"personal"}\n'
                '  {"subject":"Neues Projekt","predicate":"deadline","object":"Ende Q2","confidence":0.8,"category":"business"}\n'
                '  {"subject":"DOM","predicate":"bevorzugt","object":"dunklen Kaffee","confidence":0.7,"category":"preference"}\n\n'
                f"Kategorie: {category}\n"
                f"Zusammenfassung: {overview[:500]}\n"
                f"Gespraech:\n{transcript[:2000]}\n\n"
                "Nur das JSON Array."
            )
            result = await self.llm.generate(
                prompt=prompt,
                model="tier2-llama",
                max_tokens=512,
                temperature=0.2,
            )
            try:
                import json
                parsed = json.loads(result.strip().strip("```json").strip("```"))
                if isinstance(parsed, list):
                    knowledge_items = parsed
            except (json.JSONDecodeError, ValueError):
                pass
        except Exception as e:
            logger.debug(f"Knowledge extraction: {e}")

        return knowledge_items

    # ═══════════════════════════════════════════════════════════
    # STEP 4: Action Items → Tasks
    # ═══════════════════════════════════════════════════════════

    async def _process_action_items(self, action_items: list, uid: str):
        """Konvertiere OMI Action Items zu JARVIS Tasks."""
        if not self.db or not action_items:
            return

        for item in action_items:
            description = item if isinstance(item, str) else item.get("description", "")
            if not description:
                continue

            # Route to best agent
            agent = self._route_action_to_agent(description)

            try:
                await self.db.execute(
                    """INSERT INTO tasks
                       (title, description, agent_slug, priority, status, channel)
                       VALUES ($1, $2, $3, $4, 'pending', 'omi')""",
                    description[:200],
                    f"Auto-created from OMI conversation. UID: {uid}",
                    agent,
                    self._estimate_priority(description),
                )
                logger.info(f"[OMI] Task created: {description[:50]}... → {agent}")
            except Exception as e:
                logger.debug(f"Create task from action item: {e}")

    def _route_action_to_agent(self, description: str) -> str:
        """Route action item to best agent based on content."""
        desc = description.lower()
        if any(kw in desc for kw in ["mail", "email", "kalender", "termin", "rechnung"]):
            return "donna"
        if any(kw in desc for kw in ["post", "content", "blog", "social", "marketing"]):
            return "steve"
        if any(kw in desc for kw in ["angebot", "kunde", "sale", "deal", "preis"]):
            return "donald"
        if any(kw in desc for kw in ["code", "bug", "deploy", "server", "api"]):
            return "archi"
        if any(kw in desc for kw in ["design", "logo", "grafik", "ui", "bild"]):
            return "iris"
        if any(kw in desc for kw in ["support", "ticket", "beschwerde", "feedback"]):
            return "felix"
        return "jarvis"

    def _estimate_priority(self, description: str) -> int:
        """Schaetze die Prioritaet eines Action Items."""
        desc = description.lower()
        if any(kw in desc for kw in ["dringend", "urgent", "sofort", "asap", "heute"]):
            return 1
        if any(kw in desc for kw in ["wichtig", "important", "morgen", "bald"]):
            return 2
        return 3

    # ═══════════════════════════════════════════════════════════
    # STEP 5: Events Processing
    # Geburtstage, Termine, Deadlines automatisch erkennen.
    # ═══════════════════════════════════════════════════════════

    async def _process_events(self, events: list, uid: str):
        """Verarbeite erkannte Events (Geburtstage, Termine, etc.)."""
        if not self.db or not events:
            return

        for event in events:
            title = event.get("title", "") if isinstance(event, dict) else str(event)
            start = event.get("start", "") if isinstance(event, dict) else ""
            duration = event.get("duration", 0) if isinstance(event, dict) else 0

            if not title:
                continue

            try:
                await self.db.execute(
                    """INSERT INTO omi_events
                       (uid, title, event_date, duration_min, source, created_at)
                       VALUES ($1, $2, $3, $4, 'omi_memory', NOW())""",
                    uid, title, start or None, duration
                )

                # Special: Birthday detection → permanent knowledge
                if self._is_birthday_event(title):
                    await self._store_birthday(title, uid)

            except Exception as e:
                logger.debug(f"Process event: {e}")

    def _is_birthday_event(self, title: str) -> bool:
        """Erkennt ob ein Event ein Geburtstag ist."""
        keywords = ["geburtstag", "birthday", "bday", "geboren"]
        return any(kw in title.lower() for kw in keywords)

    async def _store_birthday(self, title: str, uid: str):
        """Speichere einen Geburtstag als permanentes Wissen."""
        if self.knowledge:
            await self.knowledge.store(
                subject=title,
                predicate="is_birthday",
                object_val=title,
                category="personal",
                confidence=0.95,
                source="omi_conversation",
            )
        if self.db:
            await self.db.execute(
                """INSERT INTO knowledge
                   (subject, predicate, object, category, confidence, source)
                   VALUES ($1, 'birthday', $2, 'personal', 0.95, 'omi')
                   ON CONFLICT DO NOTHING""",
                title, title
            )

    # ═══════════════════════════════════════════════════════════
    # STEP 6: Personal Profile Update
    # DOM's Vorlieben, Gewohnheiten, Kontakte aktualisieren.
    # ═══════════════════════════════════════════════════════════

    async def _update_personal_profile(self, entities: list,
                                        knowledge_items: list, uid: str):
        """Aktualisiere das persoenliche Profil des DOM."""
        if not self.db:
            return

        for entity in entities:
            etype = entity.get("type", "")
            name = entity.get("name", "")
            context = entity.get("context", "")

            if not name:
                continue

            try:
                await self.db.execute(
                    """INSERT INTO omi_entities
                       (uid, entity_type, name, context, mention_count, created_at)
                       VALUES ($1, $2, $3, $4, 1, NOW())
                       ON CONFLICT (uid, entity_type, name)
                       DO UPDATE SET mention_count = omi_entities.mention_count + 1,
                                     last_mentioned = NOW(),
                                     context = $4""",
                    uid, etype, name[:200], context[:500]
                )
            except Exception as e:
                logger.debug(f"Update entity: {e}")

        for item in knowledge_items:
            subject = item.get("subject", "")
            predicate = item.get("predicate", "")
            obj = item.get("object", "")
            confidence = item.get("confidence", 0.5)
            category = item.get("category", "general")

            if not subject or not predicate:
                continue

            try:
                await self.db.execute(
                    """INSERT INTO knowledge
                       (subject, predicate, object, category, confidence, source)
                       VALUES ($1, $2, $3, $4, $5, 'omi')
                       ON CONFLICT (subject, predicate)
                       DO UPDATE SET object = $3, confidence = GREATEST(knowledge.confidence, $5),
                                     updated_at = NOW()""",
                    subject[:200], predicate[:100], obj[:500],
                    category, confidence,
                )
            except Exception as e:
                logger.debug(f"Update knowledge: {e}")

    # ═══════════════════════════════════════════════════════════
    # STEP 7: Pattern Detection
    # Wiederkehrende Themen und Muster in Gespraechen erkennen.
    # ═══════════════════════════════════════════════════════════

    async def _detect_patterns(self, category: str, entities: list, uid: str):
        """Erkenne Muster in Gespraechen fuer JARVIS-Algorithmen."""
        if not self.db:
            return

        # Track conversation categories over time
        try:
            await self.db.execute(
                """INSERT INTO omi_conversation_patterns
                   (uid, category, entity_types, created_at)
                   VALUES ($1, $2, $3, NOW())""",
                uid, category,
                list(set(e.get("type", "") for e in entities if e.get("type")))
            )
        except Exception as e:
            logger.debug(f"Pattern tracking: {e}")

        # Check if patterns have emerged (3+ conversations about same topic)
        try:
            patterns = await self.db.fetch(
                """SELECT category, COUNT(*) as count
                   FROM omi_conversation_patterns
                   WHERE uid = $1
                     AND created_at > NOW() - INTERVAL '7 days'
                   GROUP BY category
                   HAVING COUNT(*) >= 3
                   ORDER BY count DESC""",
                uid
            )

            for pattern in (patterns or []):
                await self.db.execute(
                    """INSERT INTO patterns
                       (pattern_type, agent_slug, description, occurrence_count,
                        status, metadata)
                       VALUES ('conversation_topic', 'elon', $1, $2, 'watching',
                               '{"source":"omi"}')
                       ON CONFLICT (pattern_type, agent_slug, description)
                       DO UPDATE SET occurrence_count = $2, last_seen = NOW()""",
                    f"DOM spricht haeufig ueber: {pattern['category']}",
                    pattern["count"]
                )
        except Exception as e:
            logger.debug(f"Pattern analysis: {e}")

    # ═══════════════════════════════════════════════════════════
    # STEP 8: Knowledge Graph Update
    # ═══════════════════════════════════════════════════════════

    async def _update_knowledge_graph(self, entities: list,
                                       knowledge_items: list,
                                       memory_id: str):
        """Update the knowledge graph with new connections."""
        if not self.knowledge:
            return

        for item in knowledge_items:
            try:
                await self.knowledge.store(
                    subject=item.get("subject", ""),
                    predicate=item.get("predicate", ""),
                    object_val=item.get("object", ""),
                    category=item.get("category", "general"),
                    confidence=item.get("confidence", 0.5),
                    source=f"omi:{memory_id}",
                )
            except Exception:
                pass

    # ─── Utility Methods ───

    def _calculate_importance(self, category: str, overview: str,
                               transcript: str) -> int:
        """Berechne wie wichtig eine Memory ist (1-10)."""
        score = 5  # Default

        # Category boost
        high_importance = ["business", "finance", "decision", "meeting"]
        if category and category.lower() in high_importance:
            score += 2

        # Action items mentioned
        action_keywords = [
            "machen", "erledigen", "dringend", "wichtig",
            "must", "need", "asap", "deadline"
        ]
        text = f"{overview} {transcript}".lower()
        action_count = sum(1 for kw in action_keywords if kw in text)
        score += min(action_count, 3)

        # Length = more detailed conversation
        if len(transcript) > 2000:
            score += 1

        return min(score, 10)

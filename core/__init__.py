"""
JARVIS 1.5 — Core Package
SYSTEMS™ · architectofscale.com

Alle Module werden hier zusammengefuehrt.
Initialisierung:

    from core import init_jarvis
    jarvis = await init_jarvis()

    # Jetzt verfuegbar:
    jarvis["db"]            — SupabaseClient
    jarvis["brain"]         — MemoryEngine (Kurzzeit-Memory)
    jarvis["conversations"] — ConversationStore (jede Nachricht)
    jarvis["knowledge"]     — KnowledgeBase (Langzeit-Wissen)
    jarvis["context"]       — ContextManager (intelligente Kontext-Assemblierung)
    jarvis["learning"]      — SelfLearningEngine (Task-Outcomes)
    jarvis["journal"]       — LearningJournal (Lern-Tagebuch)
    jarvis["patterns"]      — PatternEngine (Muster-Erkennung)
    jarvis["improver"]      — AutoImprover (kontinuierliche Verbesserung)
    jarvis["elon"]          — ElonEngine (Qualität & Optimierung)
    jarvis["collector"]     — DataCollector (Daten-Middleware)
    jarvis["runtime"]       — AgentRuntime (Intelligence-Pipeline für jeden Call)
    jarvis["openclaw"]      — OpenClawClient (Agent-Management in OpenClaw)
    jarvis["n8n"]           — N8NConnector (Webhook-Events an N8N)
    jarvis["router"]        — SmartRouter (Model-Routing: Sonnet/Ollama/Groq)
    jarvis["omi"]           — OMIWebhookReceiver (Wearable AI Integration)
    jarvis["skills"]        — SkillInstaller (ClawHub Skills Auto-Install)
    jarvis["proactive"]     — ProactiveEngine (Morgen-Briefing, Alerts, Auto-Actions)
    jarvis["chains"]        — AgentChainEngine (Multi-Agent Workflows)
    jarvis["voice"]         — VoiceEngine (TTS/STT, Telegram Voice)
    jarvis["files"]         — FileProcessor (PDF, Bilder, Spreadsheets)
    jarvis["goals"]         — GoalTracker (OKRs, Habits, Quartals-Ziele)
    jarvis["heartbeat"]     — Heartbeat (Autonomer Intelligence-Puls, Ollama)
"""

__version__ = "1.5.0"


async def init_jarvis() -> dict:
    """
    Initialisiere alle Core-Module.

    Reihenfolge ist wichtig — Module bauen aufeinander auf:
    1. Supabase Client (Basis)
    2. Brain/Memory Engine (Kurzzeit)
    3. Conversation Store (jede Nachricht)
    4. Knowledge Base (Langzeit-Wissen)
    5. Context Manager (Kontext-Assemblierung)
    6. Self-Learning Engine (Task-Outcomes)
    7. Learning Journal (Lern-Tagebuch)
    8. Pattern Engine (Muster-Erkennung)
    9. ELON Engine (Qualität)
    10. Data Collector (Middleware)
    11. Auto-Improver (Verbesserungsloop)
    12. Agent Runtime (Intelligence-Pipeline)
    """
    from core.db.supabase_client import SupabaseClient
    from core.brain.memory_engine import MemoryEngine
    from core.memory.conversation_store import ConversationStore
    from core.memory.knowledge_base import KnowledgeBase
    from core.memory.context_manager import ContextManager
    from core.learning.self_learning import SelfLearningEngine
    from core.learning.learning_journal import LearningJournal
    from core.learning.pattern_engine import PatternEngine
    from core.learning.auto_improver import AutoImprover
    from core.learning.data_collector import DataCollector
    from core.agents.elon_engine import ElonEngine
    from core.agents.agent_runtime import AgentRuntime

    # Optional: Prompt Loader
    prompt_loader = None
    try:
        from core.prompts.prompt_loader import PromptLoader
        prompt_loader = PromptLoader()
    except Exception:
        pass

    # ─── 1. Supabase ───
    db = SupabaseClient()
    await db.connect()

    # ─── 2. Brain (Kurzzeit-Memory) ───
    brain = MemoryEngine(db=db)

    # ─── 3. Conversation Store ───
    conversations = ConversationStore(db_client=db)

    # ─── 4. Knowledge Base ───
    knowledge = KnowledgeBase(db_client=db)

    # ─── 5. Context Manager ───
    context = ContextManager(
        conversation_store=conversations,
        knowledge_base=knowledge,
        memory_engine=brain,
        db_client=db,
    )

    # ─── 6. Self-Learning ───
    learning = SelfLearningEngine(db=db)

    # ─── 7. Learning Journal ───
    journal = LearningJournal(db_client=db)

    # ─── 8. Pattern Engine ───
    patterns = PatternEngine(db_client=db)

    # ─── 9. ELON ───
    elon = ElonEngine(db=db, learning=learning)

    # ─── 10. Data Collector ───
    collector = DataCollector(db=db, learning=learning)

    # ─── 11. Auto-Improver ───
    improver = AutoImprover(
        db_client=db,
        pattern_engine=patterns,
        learning_engine=learning,
        knowledge_base=knowledge,
    )

    # ─── 12. LLM Client ───
    llm_client = None
    try:
        from core.llm.llm_client import LLMClient
        llm_client = LLMClient()
    except Exception:
        pass

    # ─── 13. Smart Router ───
    router = None
    try:
        from core.routing.smart_router import SmartRouter
        router = SmartRouter(db_client=db)
    except Exception:
        pass

    # ─── 14. Agent Runtime ───
    runtime = AgentRuntime(
        context_manager=context,
        conversation_store=conversations,
        knowledge_base=knowledge,
        learning_engine=learning,
        learning_journal=journal,
        elon_engine=elon,
        data_collector=collector,
        auto_improver=improver,
        prompt_loader=prompt_loader,
        smart_router=router,
        llm_client=llm_client,
    )

    # ─── 15. OpenClaw Client ───
    openclaw = None
    try:
        from core.integrations.openclaw_client import OpenClawClient
        openclaw = OpenClawClient()
    except Exception:
        pass

    # ─── 16. N8N Connector ───
    n8n = None
    try:
        from core.integrations.n8n_connector import N8NConnector
        n8n = N8NConnector()
    except Exception:
        pass

    # ─── 17. OMI Wearable Integration ───
    omi = None
    try:
        from core.integrations.omi.webhook_receiver import OMIWebhookReceiver
        omi = OMIWebhookReceiver(
            db_client=db,
            llm_client=llm_client,
            brain=brain,
            knowledge=knowledge,
            runtime=runtime,
        )
    except Exception:
        pass

    # ─── 18. Skill Installer ───
    skill_installer = None
    try:
        from core.skills.skill_installer import SkillInstaller
        skill_installer = SkillInstaller(
            openclaw_client=openclaw,
            db_client=db,
            prompt_loader=prompt_loader,
        )
        await skill_installer.load_manifest()
    except Exception:
        pass

    # ─── 19. Proactive Intelligence ───
    proactive = None
    try:
        from core.proactive.proactive_engine import ProactiveEngine
        proactive = ProactiveEngine(
            db_client=db,
            llm_client=llm_client,
            runtime=runtime,
        )
    except Exception:
        pass

    # ─── 20. Agent Chain Engine ───
    chains = None
    try:
        from core.chains.agent_chains import AgentChainEngine
        chains = AgentChainEngine(
            runtime=runtime,
            db_client=db,
        )
    except Exception:
        pass

    # ─── 21. Voice Engine ───
    voice = None
    try:
        from core.voice.voice_engine import VoiceEngine
        voice = VoiceEngine(llm_client=llm_client)
    except Exception:
        pass

    # ─── 22. File Processor ───
    files = None
    try:
        from core.files.file_processor import FileProcessor
        files = FileProcessor(
            llm_client=llm_client,
            knowledge_base=knowledge,
            db_client=db,
        )
    except Exception:
        pass

    # ─── 23. Goal Tracker ───
    goals = None
    try:
        from core.proactive.goal_tracker import GoalTracker
        goals = GoalTracker(
            db_client=db,
            llm_client=llm_client,
        )
    except Exception:
        pass

    # ─── 24. Heartbeat ───
    heartbeat = None
    try:
        from core.proactive.heartbeat import Heartbeat
        heartbeat = Heartbeat(
            db_client=db,
            llm_client=llm_client,
            runtime=runtime,
            proactive=proactive,
            chains=chains,
            goals=goals,
        )
    except Exception:
        pass

    return {
        "db": db,
        "brain": brain,
        "conversations": conversations,
        "knowledge": knowledge,
        "context": context,
        "learning": learning,
        "journal": journal,
        "patterns": patterns,
        "improver": improver,
        "elon": elon,
        "collector": collector,
        "runtime": runtime,
        "router": router,
        "llm": llm_client,
        "openclaw": openclaw,
        "n8n": n8n,
        "omi": omi,
        "skills": skill_installer,
        "proactive": proactive,
        "chains": chains,
        "voice": voice,
        "files": files,
        "goals": goals,
        "heartbeat": heartbeat,
        "version": __version__,
    }

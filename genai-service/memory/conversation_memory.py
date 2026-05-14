import logging

logger = logging.getLogger("genai-service")


class ConversationMemory:
    """Memoria in-memory della conversazione per sessione."""

    # Dizionario condiviso tra tutte le istanze: session_id → lista messaggi
    _sessions: dict = {}

    def __init__(self, session_id: str = "default", max_messages: int = 10):
        self.session_id = session_id
        self.max_messages = max_messages
        if session_id not in self._sessions:
            self._sessions[session_id] = []

    def add_message(self, role: str, content: str):
        """Aggiunge un messaggio allo storico, rispettando il limite massimo."""
        self._sessions[self.session_id].append({
            "role": role,
            "content": content,
        })
        # Mantieni solo gli ultimi max_messages messaggi
        if len(self._sessions[self.session_id]) > self.max_messages:
            self._sessions[self.session_id] = \
                self._sessions[self.session_id][-self.max_messages:]

    def get_history(self) -> list[dict]:
        """Restituisce la lista dei messaggi della sessione."""
        return self._sessions.get(self.session_id, [])

    def format_history(self) -> str:
        """Formatta lo storico come stringa per il prompt."""
        messages = self.get_history()
        if not messages:
            return "Nessuna conversazione precedente."
        lines = []
        for msg in messages:
            prefix = "Utente" if msg["role"] == "user" else "Assistente"
            lines.append(f"{prefix}: {msg['content']}")
        return "\n".join(lines)

    def clear(self):
        """Svuota la memoria della sessione."""
        self._sessions[self.session_id] = []
        logger.info(f"Memory cleared for session={self.session_id}")

    @classmethod
    def clear_all(cls):
        """Svuota tutte le sessioni (utile nei test)."""
        cls._sessions.clear()
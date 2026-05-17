"""
core/context_memory.py
=======================
Lightweight session-scoped conversational state.
Allows follow-up commands like:
  "Open WhatsApp on phone" → "Send hi to mummy"
  (context knows: app=whatsapp, device=phone)
"""
import logging
from typing import Optional

logger = logging.getLogger("jarvis.memory")


class ContextMemory:
    def __init__(self):
        self.last_app: Optional[str] = None
        self.last_device: Optional[str] = None
        self.last_contact: Optional[str] = None
        self.last_query: Optional[str] = None
        self.last_action: Optional[str] = None

    def update(self, *, app=None, device=None, contact=None, query=None, action=None):
        if app:     self.last_app     = app;     logger.debug("[Mem] app=%s", app)
        if device:  self.last_device  = device;  logger.debug("[Mem] device=%s", device)
        if contact: self.last_contact = contact; logger.debug("[Mem] contact=%s", contact)
        if query:   self.last_query   = query;   logger.debug("[Mem] query=%s", query)
        if action:  self.last_action  = action

    def fill_gaps(self, app=None, device=None, contact=None, query=None):
        """Return tuple with memory fallbacks applied for any None value."""
        return (
            app     or self.last_app,
            device  or self.last_device,
            contact or self.last_contact,
            query   or self.last_query,
        )

    def clear(self):
        self.last_app = self.last_device = self.last_contact = None
        self.last_query = self.last_action = None
        logger.info("[Mem] Context cleared")

    def __repr__(self):
        return (f"Ctx(app={self.last_app!r} dev={self.last_device!r} "
                f"contact={self.last_contact!r} q={self.last_query!r})")


_mem: Optional[ContextMemory] = None

def get_memory() -> ContextMemory:
    global _mem
    if _mem is None:
        _mem = ContextMemory()
    return _mem

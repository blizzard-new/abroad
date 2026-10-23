"""What every desk has in common: a persona (how the office draws them) and a way to report what they are doing."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..office import Office


@dataclass(frozen=True)
class Persona:
    id: str
    name: str
    title: str
    duty: str
    # Appearance for the office floor (seen from behind, over the shoulder): hair, outfit and what sits on the desk.
    hair: str
    hair_color: str
    shirt: str
    accessory: str
    decor: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


class Agent:
    persona: Persona

    def __init__(self, office: "Office"):
        self.office = office

    @property
    def id(self) -> str:
        return self.persona.id

    def status(self, state: str, message: str, screen: dict[str, Any] | None = None, **data: Any) -> None:
        """Change pose and speech bubble; `screen` is what their monitor shows."""
        if screen is not None:
            data["screen"] = screen
        self.office.bus.emit(self.id, "status", message, state=state, **data)

    def handoff(self, to: str, label: str, draft_id: int | None = None) -> None:
        """A sheet of paper flies from this desk to another one."""
        self.office.bus.emit(self.id, "handoff", label, to=to, draft_id=draft_id)

    def log(self, message: str, **data: Any) -> None:
        self.office.bus.emit(self.id, "log", message, **data)

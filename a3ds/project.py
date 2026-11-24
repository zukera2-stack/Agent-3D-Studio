"""Versioned, human-editable project spec: parameters are source of truth, not GLB."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from .surfaces import CrossSection, loft_sections
from .mesh import Mesh

FORMAT = "a3ds.surface-project/1"


@dataclass
class SurfaceProject:
    name: str
    sections: list[CrossSection]
    sides: int = 32
    steps_per_span: int = 3
    unit_label: str = "BU"

    def build(self) -> Mesh:
        return loft_sections(
            self.sections, sides=self.sides,
            steps_per_span=self.steps_per_span, name=self.name
        )

    def as_dict(self) -> dict:
        return {
            "format": FORMAT, "name": self.name, "unit_label": self.unit_label,
            "sides": self.sides, "steps_per_span": self.steps_per_span,
            "sections": [asdict(section) for section in self.sections],
        }

    def save(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.as_dict(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8"
        )

    @classmethod
    def load(cls, path: str | Path) -> "SurfaceProject":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if data.get("format") != FORMAT:
            raise ValueError("Unsupported A3DS project format")
        if not isinstance(data.get("sections"), list):
            raise ValueError("Missing sections")
        return cls(
            name=data["name"],
            sections=[CrossSection(**row) for row in data["sections"]],
            sides=data["sides"],
            steps_per_span=data["steps_per_span"],
            unit_label=data.get("unit_label", "BU"),
        )


def demo_project() -> SurfaceProject:
    """Asymmetric nose/rear geometry fixture; not an approved locomotive."""
    return SurfaceProject(
        name="Stage01_Asymmetric_Loft",
        sections=[
            CrossSection(-3.60, 1.12, 0.68, 0.75),
            CrossSection(-3.30, 1.12, 0.82, 0.84),
            CrossSection(-2.75, 1.14, 0.91, 0.93),
            CrossSection(-1.50, 1.15, 0.93, 0.96),
            CrossSection(0.30, 1.14, 0.91, 0.95),
            CrossSection(1.70, 1.13, 0.85, 0.90),
            CrossSection(2.40, 1.10, 0.72, 0.82),
            CrossSection(3.15, 1.06, 0.40, 0.61),
            CrossSection(3.55, 1.04, 0.20, 0.44),
            CrossSection(3.60, 1.04, 0.17, 0.40),
        ],
        sides=32, steps_per_span=4
    )

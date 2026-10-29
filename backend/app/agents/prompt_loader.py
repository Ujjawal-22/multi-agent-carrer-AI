"""
Loads versioned prompt templates from app/agents/prompts/.
"""

from pathlib import Path

PROMPTS_DIR = Path(__file__).parent / "prompts"


def load_prompt(name: str, **kwargs: str) -> str:
    template_path = PROMPTS_DIR / f"{name}.txt"
    template = template_path.read_text(encoding="utf-8")
    return template.format(**kwargs)

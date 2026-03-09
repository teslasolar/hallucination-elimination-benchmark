"""Triad Engine core — prompt construction, question wrapping, shared logic.
All 5 runners collapsed into this single module.
"""
import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent.parent / "data"
QUESTIONS_FILE = DATA_DIR / "questions.json"
CULTURAL_GUIDE_FILE = DATA_DIR / "cultural_guide.json"
CHARACTERS_FILE = DATA_DIR / "characters.json"


class TriadEngine:
    """Model-agnostic inference layer. Builds grounded prompts from domain guides."""

    def __init__(self, cultural_guide: dict = None, char_map: dict = None):
        self.cultural_guide = cultural_guide
        self.char_map = char_map or {}

    @classmethod
    def from_files(cls, guide_path=None, chars_path=None):
        gp = Path(guide_path) if guide_path else CULTURAL_GUIDE_FILE
        cp = Path(chars_path) if chars_path else CHARACTERS_FILE
        guide = json.loads(gp.read_text()) if gp.exists() else {}
        chars = json.loads(cp.read_text()) if cp.exists() else {"characters": []}
        char_map = {c["id"]: c for c in chars.get("characters", [])}
        return cls(guide, char_map)

    @staticmethod
    def load_questions(path=None):
        p = Path(path) if path else QUESTIONS_FILE
        return json.loads(p.read_text())["questions"]

    def build_system(self, triad: bool, char_id: str = None) -> str:
        if triad and self.cultural_guide:
            return self._build_triad(char_id)
        return self._build_raw(char_id)

    def wrap_question(self, question: str, category: str,
                      char_id: str = None) -> str:
        if category == "ANACHRONISM_DETECTION":
            return (
                "Before answering, check: does this thing exist in 110 CE?\n"
                "If not, say you have never heard of it.\n\n" + question
            )
        if category == "CHARACTER_IDENTITY" and char_id and char_id in self.char_map:
            c = self.char_map[char_id]
            return f"[You are {c['name']}, {c['role']}]\n{question}"
        if category == "COMPLEX_SCENARIOS":
            return (
                "Think through this using Roman law, custom, and social norms "
                "of 110 CE:\n\n" + question
            )
        return question

    # ── Private ──────────────────────────────────────────────────────────

    def _build_triad(self, char_id: str = None) -> str:
        ctx = self.cultural_guide
        locs = [{"name": l["name"], "desc": l["description"]}
                for l in ctx.get("key_locations", [])[:6]]
        ana = ctx.get("anachronisms_to_avoid", {})
        not_built = ", ".join(ana.get("not_yet_built", []))
        not_happened = ", ".join(ana.get("not_yet_happened", []))
        already_dead = ", ".join(ana.get("already_dead", [])[:5])
        no_tech = ", ".join(ana.get("technology_notes", []))

        char_section, char_name, char_role = self._char_block(char_id)

        def _j(obj, limit=500):
            return json.dumps(obj, indent=0)[:limit]

        body = f"""{char_section}
Emperor: {ctx.get('time_period_context', {}).get('emperor', 'Trajan')} | Pop: {ctx.get('time_period_context', {}).get('population', '~1M')} | Currency: {ctx.get('time_period_context', {}).get('currency', 'denarius')}
Timeline: {_j(ctx.get('timeline_recent_events', []), 600)}

ANACHRONISMS — DO NOT EXIST in 110 CE:
Not built: {not_built}
Not happened: {not_happened}
Dead: {already_dead}
No tech: {no_tech}
If asked about something not yet existing, say you don't know what they mean.

Locations: {_j(locs, 600)}
Social: {_j(ctx.get('social_structure', {}), 600)}
Economy: {_j(ctx.get('economy_and_trade', {}), 500)}
Prices: {_j(ctx.get('prices_and_costs', {}), 300)}
Daily life: {_j(ctx.get('daily_life', {}), 400)}
Religion: {_j(ctx.get('roman_religion', {}).get('major_gods', []), 300)}
Entertainment: {_j(ctx.get('entertainment', {}), 400)}
Engineering: {_j(ctx.get('engineering_and_architecture', {}), 300)}
Medicine: {_j(ctx.get('medicine_and_health', {}), 300)}
Customs: {_j(ctx.get('customs', {}), 300)}

=== FINAL REMINDER — READ THIS LAST ===
You are {char_name}, {char_role}. The year is 110 CE. Emperor Trajan rules Rome.
- If asked about anything NOT YET EXISTING: say "I don't know what you mean by that."
- Stay in character at all times.
- Answer in 2-3 sentences maximum.
- NEVER mention anything from after 110 CE."""
        return body

    def _build_raw(self, char_id: str = None) -> str:
        if char_id and char_id in self.char_map:
            c = self.char_map[char_id]
            return (
                f"You are {c['name']}, a Roman citizen in 110 CE. "
                f"Answer questions as this character. "
                f"Keep answers to 2-3 sentences."
            )
        return ("You are a Roman citizen in 110 CE. "
                "Answer questions in character. Keep answers to 2-3 sentences.")

    def _char_block(self, char_id: str = None):
        if char_id and char_id in self.char_map:
            c = self.char_map[char_id]
            section = (
                f"You are {c['name']}, age {c['age']}, {c['role']} in Rome 110 CE.\n"
                f"Backstory: {c['backstory']}\n"
                f"Personality: {', '.join(c['personality_traits'])}\n"
                f"Expertise: {', '.join(c['expertise'])}\n"
                f"Speaking style: {c.get('speaking_style', 'natural')}\n"
            )
            return section, c["name"], c["role"]
        return ("You are a knowledgeable resident of Rome in 110 CE.\n",
                "a Roman citizen", "resident of Rome")

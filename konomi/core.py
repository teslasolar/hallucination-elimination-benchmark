"""LAYER 0: Meta-Standard — how standards and UDTs define themselves."""
import json, os, importlib
from typing import Any, Optional

DEMO = os.environ.get("KONOMI_DEMO", "0") == "1"
_registry: dict[str, "Standard"] = {}
_udt_registry: dict[str, "UDT"] = {}


def demo_mode(on: bool = True):
    global DEMO
    DEMO = on


class Rule:
    __slots__ = ("id", "condition", "action", "severity")
    def __init__(self, id: str, condition: str, action: str, severity: str = "error"):
        self.id, self.condition, self.action, self.severity = id, condition, action, severity
    def check(self, ctx: dict) -> bool:
        if DEMO:
            return True
        try:
            return bool(eval(self.condition, {"__builtins__": {}}, ctx))
        except Exception:
            return False
    def to_dict(self):
        return {s: getattr(self, s) for s in self.__slots__}


class UDT:
    """User-Defined Type — the atom of KONOMI. A UDT can define other UDTs."""
    def __init__(self, name: str, fields: list[dict], base: Optional[str] = None,
                 methods: list[dict] = None, constraints: list[Rule] = None,
                 tags: dict[str, list] = None):
        self.name = name
        self.base = base
        self.fields = fields
        self.methods = methods or []
        self.constraints = constraints or []
        self.tags = tags or {}
        _udt_registry[name] = self

    @property
    def resolved_fields(self) -> list[dict]:
        if self.base and self.base in _udt_registry:
            return _udt_registry[self.base].resolved_fields + self.fields
        return list(self.fields)

    def instantiate(self, **values) -> dict:
        inst = {"_udt": self.name}
        for f in self.resolved_fields:
            inst[f["name"]] = values.get(f["name"], f.get("default"))
        return inst

    def validate(self, instance: dict) -> list[str]:
        errors = []
        for f in self.resolved_fields:
            if f.get("required") and f["name"] not in instance:
                errors.append(f"missing required: {f['name']}")
        for r in self.constraints:
            if not r.check(instance):
                errors.append(f"rule {r.id}: {r.action}")
        return errors

    def to_dict(self):
        return {"name": self.name, "base": self.base, "fields": self.fields,
                "methods": self.methods, "constraints": [r.to_dict() for r in self.constraints],
                "tags": self.tags}

    def tagged(self, category: str) -> list:
        return self.tags.get(category, [])

    @staticmethod
    def get(name: str) -> Optional["UDT"]:
        return _udt_registry.get(name)

    @staticmethod
    def all() -> dict[str, "UDT"]:
        return dict(_udt_registry)


class Standard:
    """A self-describing industrial standard composed of UDTs, hierarchy, states, and rules."""
    def __init__(self, id: str, scope: str, udts: list[UDT] = None,
                 hierarchy: list[dict] = None, states: list[dict] = None,
                 entities: list[dict] = None, relations: list[dict] = None,
                 rules: list[Rule] = None, crosswalks: dict = None):
        self.id = id
        self.scope = scope
        self.udts = {u.name: u for u in (udts or [])}
        self.hierarchy = hierarchy or []
        self.states = states or []
        self.entities = entities or []
        self.relations = relations or []
        self.rules = rules or []
        self.crosswalks = crosswalks or {}
        _registry[id] = self

    def udt(self, name: str) -> Optional[UDT]:
        return self.udts.get(name)

    def add_udt(self, udt: UDT):
        self.udts[udt.name] = udt

    def validate(self, entity: dict) -> list[str]:
        udt_name = entity.get("_udt")
        if udt_name and udt_name in self.udts:
            return self.udts[udt_name].validate(entity)
        return [f"unknown UDT: {udt_name}"]

    def to_dict(self):
        return {"id": self.id, "scope": self.scope,
                "udts": {k: v.to_dict() for k, v in self.udts.items()},
                "hierarchy": self.hierarchy, "states": self.states,
                "entities": self.entities, "relations": self.relations,
                "rules": [r.to_dict() for r in self.rules]}

    @staticmethod
    def get(id: str) -> Optional["Standard"]:
        return _registry.get(id)

    @staticmethod
    def all() -> dict[str, "Standard"]:
        return dict(_registry)


class KS:
    """KONOMI Standard entry point — parse, expand, validate, crosswalk, generate."""

    @staticmethod
    def parse(std_id: str, source: dict | str = None) -> Standard:
        mod_name = f"konomi.standards.{std_id.lower().replace('-', '_')}"
        try:
            mod = importlib.import_module(mod_name)
            if hasattr(mod, "build"):
                return mod.build()
        except ImportError:
            pass
        if std_id in _registry:
            return _registry[std_id]
        raise ValueError(f"Unknown standard: {std_id}")

    @staticmethod
    def expand(std_id: str, target: str = "python") -> dict:
        std = KS.parse(std_id)
        return {"standard": std.id, "target": target,
                "udts": {k: v.to_dict() for k, v in std.udts.items()},
                "hierarchy": std.hierarchy, "states": std.states}

    @staticmethod
    def validate(instance: dict, std_id: str) -> dict:
        std = KS.parse(std_id)
        errors = std.validate(instance)
        return {"valid": len(errors) == 0, "errors": errors, "demo": DEMO}

    @staticmethod
    def crosswalk(entity: dict, from_std: str, to_std: str) -> dict:
        from konomi.crosswalks import engine
        return engine.map_entity(entity, from_std, to_std)

    @staticmethod
    def generate(udt_path: str, lang: str = "python") -> str:
        parts = udt_path.split(".")
        std_id = parts[0] if len(parts) > 1 else None
        udt_name = parts[-1]
        udt = _udt_registry.get(udt_name)
        if not udt:
            raise ValueError(f"UDT not found: {udt_name}")
        if lang == "python":
            return _gen_python(udt)
        return json.dumps(udt.to_dict(), indent=2)

    @staticmethod
    def list_standards() -> list[str]:
        return list(_registry.keys())

    @staticmethod
    def list_udts(std_id: str = None) -> list[str]:
        if std_id and std_id in _registry:
            return list(_registry[std_id].udts.keys())
        return list(_udt_registry.keys())


def _gen_python(udt: UDT) -> str:
    lines = [f"class {udt.name}:"]
    fields = udt.resolved_fields
    args = ", ".join(f["name"] + ": " + f.get("type", "Any") + " = None" for f in fields)
    lines.append(f"    def __init__(self, {args}):")
    for f in fields:
        lines.append(f"        self.{f['name']} = {f['name']}")
    return "\n".join(lines)

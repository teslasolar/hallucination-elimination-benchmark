"""LAYER 4: ISA-101 — HMI Design Standards."""
from konomi.core import UDT, Standard, Rule

HMI_Layer = UDT("HMI_Layer", [
    {"name": "id", "type": "int", "required": True},
    {"name": "name", "type": "str", "required": True},
    {"name": "scope", "type": "str", "required": True},
    {"name": "info", "type": "str", "default": ""},
    {"name": "nav", "type": "str", "default": ""},
], tags={
    "isa": ["ISA-101"],
    "layers": [
        (1, "Overview", "Plant/Site", "KPIs,Status,Alarms"),
        (2, "Area", "Process Area", "Flows,States,Trends"),
        (3, "Unit", "Equipment", "Faceplate,Control"),
        (4, "Detail", "Diagnostic", "Config,Tuning"),
        (5, "Support", "Maintenance", "Calibration,History"),
    ],
})

ColorMeaning = UDT("ColorMeaning", [
    {"name": "state", "type": "str", "required": True},
    {"name": "color", "type": "str", "required": True},
    {"name": "hex", "type": "str", "required": True},
    {"name": "usage", "type": "str", "default": ""},
], tags={
    "isa": ["ISA-101"],
    "palette": [
        ("Normal", "Gray", "#808080"), ("Running", "Green", "#00AA00"),
        ("Warning", "Yellow", "#FFCC00"), ("Alarm", "Red", "#CC0000"),
        ("Maint", "Blue", "#0066CC"), ("Manual", "Orange", "#FF6600"),
        ("Transition", "Cyan", "#00CCCC"),
    ],
})

Faceplate = UDT("Faceplate", [
    {"name": "equipment", "type": "str", "required": True},
    {"name": "title", "type": "str", "required": True},
    {"name": "pv_display", "type": "list", "default": []},
    {"name": "sp_input", "type": "list", "default": []},
    {"name": "commands", "type": "list", "default": []},
], tags={"isa": ["ISA-101"]})

RULES = [
    Rule("R1", "True", "no hardcoded values in graphics"),
    Rule("R2", "True", "bind to tag path not direct address"),
    Rule("R6", "True", "navigation consistent predictable"),
    Rule("R8", "True", "confirmation for critical commands"),
]


def build():
    return Standard("ISA-101", "human machine interface design",
        udts=[HMI_Layer, ColorMeaning, Faceplate], rules=RULES)

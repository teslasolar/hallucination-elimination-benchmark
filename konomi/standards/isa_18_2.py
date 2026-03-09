"""LAYER 5: ISA-18.2 — Alarm Management Lifecycle."""
from konomi.core import UDT, Standard, Rule

AlarmPriority = UDT("AlarmPriority", [
    {"name": "level", "type": "int", "required": True},
    {"name": "name", "type": "str", "required": True},
    {"name": "response", "type": "str", "required": True},
    {"name": "time", "type": "str", "required": True},
    {"name": "color", "type": "str", "required": True},
], tags={
    "isa": ["ISA-18.2"],
    "priorities": [
        (1, "Emergency", "Immediate", "<1min", "Red"),
        (2, "High", "Prompt", "<10min", "Orange"),
        (3, "Medium", "Timely", "<1hr", "Yellow"),
        (4, "Low", "Awareness", "Shift", "Cyan"),
    ],
})

Alarm = UDT("Alarm", [
    {"name": "id", "type": "str", "required": True},
    {"name": "tag", "type": "str", "required": True},
    {"name": "type", "type": "str", "default": "HI"},
    {"name": "priority", "type": "int", "default": 3},
    {"name": "state", "type": "str", "default": "NORM"},
    {"name": "setpoint", "type": "num", "default": None},
    {"name": "deadband", "type": "num", "default": 0},
    {"name": "message", "type": "str", "default": ""},
    {"name": "consequence", "type": "str", "default": ""},
    {"name": "response", "type": "str", "default": ""},
], tags={
    "isa": ["ISA-18.2"],
    "types": ["HI", "HIHI", "LO", "LOLO", "DEV", "ROG", "DISC"],
    "states": ["NORM", "UNACK", "ACKED", "RTN_UNACK", "SHELVED", "OUT_OF_SERVICE"],
    "transitions": [
        ("NORM", "UNACK", "condition"), ("UNACK", "ACKED", "ack"),
        ("ACKED", "NORM", "clear"), ("UNACK", "RTN_UNACK", "clear"),
        ("RTN_UNACK", "NORM", "ack"),
    ],
})

RULES = [
    Rule("R1", "True", "every alarm must be documented"),
    Rule("R3", "True", "every alarm must be actionable"),
    Rule("R6", "True", "review frequency annual minimum"),
]

METRICS = {
    "alarm_rate": "alarms/operator/hour",
    "flood_rate": ">10 alarms in 10 min",
    "stale": "active>24hr",
    "chattering": ">3 transitions/min",
    "target_by_priority": {"P1": "<5%", "P2": "<15%", "P3": "<25%", "P4": "<55%"},
}


def build():
    return Standard("ISA-18.2", "alarm management lifecycle",
        udts=[AlarmPriority, Alarm], rules=RULES,
        states=[{"name": "AlarmLifecycle", "states": Alarm.tags["states"],
                 "initial": "NORM", "transitions": Alarm.tags["transitions"]}])

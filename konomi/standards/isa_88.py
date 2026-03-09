"""LAYER 3: ISA-88 — Batch Process Control."""
from konomi.core import UDT, Standard

ProcessCell = UDT("ProcessCell", [
    {"name": "id", "type": "str", "required": True},
    {"name": "name", "type": "str", "required": True},
    {"name": "units", "type": "list", "default": []},
], base="Equipment", tags={"isa": ["ISA-88"], "layer": ["equipment"]})

Unit = UDT("S88_Unit", [
    {"name": "id", "type": "str", "required": True},
    {"name": "name", "type": "str", "required": True},
    {"name": "ems", "type": "list", "default": []},
    {"name": "allocated_to", "type": "str", "default": None},
], tags={"isa": ["ISA-88"], "states": ["Idle", "Running", "Complete", "Held", "Aborted"]})

Phase = UDT("Phase", [
    {"name": "id", "type": "str", "required": True},
    {"name": "name", "type": "str", "required": True},
    {"name": "params", "type": "list", "default": []},
    {"name": "state", "type": "str", "default": "IDLE"},
], tags={
    "isa": ["ISA-88"],
    "states": ["IDLE", "RUNNING", "COMPLETE", "HOLDING", "HELD",
               "RESTARTING", "STOPPING", "STOPPED", "ABORTING", "ABORTED"],
    "transitions": [
        ("IDLE", "RUNNING", "start"), ("RUNNING", "COMPLETE", "done"),
        ("RUNNING", "HOLDING", "hold"), ("HELD", "RESTARTING", "restart"),
        ("RUNNING", "STOPPING", "stop"), ("RUNNING", "ABORTING", "abort"),
    ],
})

Recipe = UDT("Recipe", [
    {"name": "id", "type": "str", "required": True},
    {"name": "name", "type": "str", "required": True},
    {"name": "version", "type": "str", "default": "1.0"},
    {"name": "level", "type": "str", "default": "Master"},
    {"name": "product", "type": "str", "required": True},
    {"name": "procedure", "type": "dict", "default": {}},
    {"name": "formula", "type": "dict", "default": {}},
], tags={
    "isa": ["ISA-88"],
    "levels": ["General", "Site", "Master", "Control"],
})

Batch = UDT("Batch", [
    {"name": "id", "type": "str", "required": True},
    {"name": "recipe", "type": "str", "required": True},
    {"name": "state", "type": "str", "default": "Created"},
    {"name": "start", "type": "str", "default": None},
    {"name": "end", "type": "str", "default": None},
    {"name": "events", "type": "list", "default": []},
], tags={
    "isa": ["ISA-88"],
    "states": ["Created", "Scheduled", "Running", "Complete", "Held", "Aborted"],
})

HIERARCHY = [
    {"name": "Enterprise"}, {"name": "Site"}, {"name": "Area"},
    {"name": "ProcessCell"}, {"name": "Unit"},
    {"name": "EquipmentModule"}, {"name": "ControlModule"},
]


def build():
    return Standard("ISA-88", "batch process control",
        udts=[ProcessCell, Unit, Phase, Recipe, Batch],
        hierarchy=HIERARCHY,
        states=[{"name": "PhaseState", "states": Phase.tags["states"],
                 "initial": "IDLE", "transitions": Phase.tags["transitions"]}])

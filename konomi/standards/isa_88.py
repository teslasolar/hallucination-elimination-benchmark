"""LAYER 3: ISA-88 — Batch Process Control (ISA-88.01/IEC 61512)."""
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

EquipmentModule = UDT("EquipmentModule", [
    {"name": "id", "type": "str", "required": True},
    {"name": "name", "type": "str", "required": True},
    {"name": "control_modules", "type": "list", "default": []},
    {"name": "unit", "type": "str", "default": None},
], tags={"isa": ["ISA-88"], "layer": ["equipment"],
         "note": "groups CMs for coordinated action"})

ControlModule = UDT("ControlModule", [
    {"name": "id", "type": "str", "required": True},
    {"name": "name", "type": "str", "required": True},
    {"name": "io_type", "type": "str", "default": "AI"},
    {"name": "tag_path", "type": "str", "default": None},
], tags={"isa": ["ISA-88"], "layer": ["equipment"],
         "io_types": ["AI", "AO", "DI", "DO", "PID"]})

Phase = UDT("Phase", [
    {"name": "id", "type": "str", "required": True},
    {"name": "name", "type": "str", "required": True},
    {"name": "params", "type": "list", "default": []},
    {"name": "state", "type": "str", "default": "IDLE"},
], tags={
    "isa": ["ISA-88"],
    "states": ["IDLE", "RUNNING", "COMPLETE", "PAUSING", "PAUSED",
               "HOLDING", "HELD", "RESTARTING",
               "STOPPING", "STOPPED", "ABORTING", "ABORTED", "RESETTING"],
    "transitions": [
        ("IDLE", "RUNNING", "start"), ("RUNNING", "COMPLETE", "done"),
        ("RUNNING", "PAUSING", "pause"), ("PAUSED", "RUNNING", "resume"),
        ("RUNNING", "HOLDING", "hold"), ("HELD", "RESTARTING", "restart"),
        ("RESTARTING", "RUNNING", "done"), ("HOLDING", "HELD", "done"),
        ("RUNNING", "STOPPING", "stop"), ("STOPPING", "STOPPED", "done"),
        ("RUNNING", "ABORTING", "abort"), ("ABORTING", "ABORTED", "done"),
        ("COMPLETE", "RESETTING", "reset"), ("STOPPED", "RESETTING", "reset"),
        ("ABORTED", "RESETTING", "reset"), ("RESETTING", "IDLE", "done"),
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
    "procedure_model": ["Procedure", "UnitProcedure", "Operation", "Phase"],
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
    return Standard("ISA-88", "batch process control (IEC 61512)",
        udts=[ProcessCell, Unit, EquipmentModule, ControlModule, Phase, Recipe, Batch],
        hierarchy=HIERARCHY,
        states=[{"name": "PhaseState", "states": Phase.tags["states"],
                 "initial": "IDLE", "transitions": Phase.tags["transitions"]}])

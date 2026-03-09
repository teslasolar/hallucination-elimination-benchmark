"""LAYER 2: ISA-95 — Enterprise to Control Integration (IEC 62264)."""
from konomi.core import UDT, Standard, Rule
from konomi.standards import base_udts
base_udts.build_all()

LEVELS = [
    {"id": 4, "name": "Business", "scope": "Planning,ERP", "time": "days-months", "sys": ["ERP", "BI"]},
    {"id": 3, "name": "MOM", "scope": "MES,Execution", "time": "shifts-days", "sys": ["MES", "LIMS"]},
    {"id": 2, "name": "Control", "scope": "Supervision", "time": "sec-hours", "sys": ["SCADA", "HMI"]},
    {"id": 1, "name": "Sensing", "scope": "Direct Control", "time": "ms-sec", "sys": ["PLC", "DCS"]},
    {"id": 0, "name": "Process", "scope": "Physical", "time": "continuous", "sys": ["Sensors"]},
]

PhysicalAsset = UDT("PhysicalAsset", [
    {"name": "id", "type": "str", "required": True},
    {"name": "path", "type": "str", "required": True},
    {"name": "name", "type": "str", "required": True},
    {"name": "level", "type": "int", "default": 0},
    {"name": "parent", "type": "str", "default": None},
], tags={"isa": ["ISA-95"], "layer": ["equipment"]})

Equipment = UDT("Equipment", [
    {"name": "capability", "type": "list", "default": []},
    {"name": "state", "type": "str", "default": "Idle"},
    {"name": "mode", "type": "str", "default": "Automatic"},
], base="PhysicalAsset", tags={
    "states": ["Idle", "Running", "Faulted", "Maintenance", "Offline"],
    "modes": ["Production", "Maintenance", "Manual", "Automatic", "Semiauto"],
})

Material = UDT("Material", [
    {"name": "id", "type": "str", "required": True},
    {"name": "name", "type": "str", "required": True},
    {"name": "lot", "type": "str", "default": None},
    {"name": "sublot", "type": "str", "default": None},
    {"name": "props", "type": "dict", "default": {}},
], tags={"isa": ["ISA-95"], "classes": ["Raw", "Intermediate", "Finished", "Consumable"]})

Personnel = UDT("Personnel", [
    {"name": "id", "type": "str", "required": True},
    {"name": "name", "type": "str", "required": True},
    {"name": "role", "type": "str", "required": True},
    {"name": "qualifications", "type": "list", "default": []},
], tags={"isa": ["ISA-95"]})

ProcessSegment = UDT("ProcessSegment", [
    {"name": "id", "type": "str", "required": True},
    {"name": "name", "type": "str", "required": True},
    {"name": "equipment", "type": "list", "default": []},
    {"name": "materials_in", "type": "list", "default": []},
    {"name": "materials_out", "type": "list", "default": []},
    {"name": "personnel", "type": "list", "default": []},
    {"name": "duration", "type": "num", "default": None},
], tags={"isa": ["ISA-95"]})

OperationsSchedule = UDT("OperationsSchedule", [
    {"name": "id", "type": "str", "required": True},
    {"name": "start", "type": "str", "required": True},
    {"name": "end", "type": "str", "required": True},
    {"name": "ops_type", "type": "str", "default": "Production"},
    {"name": "requests", "type": "list", "default": []},
], tags={"isa": ["ISA-95"],
         "ops_types": ["Production", "Maintenance", "Quality", "Inventory"]})

ProductionCapability = UDT("ProductionCapability", [
    {"name": "id", "type": "str", "required": True},
    {"name": "equipment", "type": "list", "default": []},
    {"name": "personnel", "type": "list", "default": []},
    {"name": "material", "type": "list", "default": []},
    {"name": "capability_type", "type": "str", "default": "Committed"},
], tags={"isa": ["ISA-95"],
         "capability_types": ["Committed", "Available", "Unattainable"]})

HIERARCHY = [
    {"name": "Enterprise", "card": "1"},
    {"name": "Site", "card": "N"},
    {"name": "Area", "card": "N"},
    {"name": "WorkCenter", "card": "N"},
    {"name": "WorkUnit", "card": "N"},
    {"name": "Equipment", "card": "N"},
]

DATA_FLOWS = {
    "L4→L3": ["Schedule", "MaterialDef", "ProductDef", "WorkOrder"],
    "L3→L4": ["Performance", "Inventory", "Quality", "Status"],
    "L3→L2": ["Recipe", "Setpoints", "Commands"],
    "L2→L3": ["ProcessData", "Events", "Alarms", "Batch"],
}


def build():
    return Standard("ISA-95", "enterprise to control integration (IEC 62264)",
        udts=[PhysicalAsset, Equipment, Material, Personnel, ProcessSegment,
              OperationsSchedule, ProductionCapability],
        hierarchy=HIERARCHY, entities=[{"name": "Equipment", "udt": "Equipment"}],
        relations=[{"type": "contains", "from": "Site", "to": "Area", "cardinality": "1:N"}])

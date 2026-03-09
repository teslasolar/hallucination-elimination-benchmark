"""Crosswalk engine — maps entities between ISA/OPC standards."""

CROSSWALK_TABLE = {
    ("ISA-95", "ISA-88"): {
        "WorkCenter": {"to": "ProcessCell", "mapping": "exact"},
        "WorkUnit": {"to": "S88_Unit", "mapping": "exact"},
        "ProcessSegment": {"to": "Operation", "mapping": "exact"},
        "ProductionSchedule": {"to": "Batch", "mapping": "partial", "note": "instantiate"},
    },
    ("ISA-95", "OPC-UA"): {
        "Equipment": {"to": "OPC_Node", "mapping": "exact", "ns": "isa95"},
        "Property": {"to": "OPC_Variable", "mapping": "exact"},
        "Capability": {"to": "OPC_Method", "mapping": "exact"},
    },
    ("ISA-101", "ISA-18.2"): {
        "AlarmIndicator": {"to": "AlarmState", "mapping": "exact", "note": "visual"},
        "ColorMeaning": {"to": "Priority", "mapping": "partial", "note": "color code"},
    },
    ("OPC-UA", "MQTT-Sparkplug"): {
        "OPC_Variable": {"to": "Metric", "mapping": "exact"},
        "OPC_Subscription": {"to": "NDATA/DDATA", "mapping": "partial"},
        "OPC_Method": {"to": "NCMD/DCMD", "mapping": "exact"},
    },
    ("ISA-88", "PackML"): {
        "ProcessCell": {"to": "Machine", "mapping": "exact"},
        "Unit": {"to": "Unit", "mapping": "exact"},
        "Phase": {"to": "ActingState", "mapping": "partial", "note": "state subset"},
        "IDLE": {"to": "STOPPED", "mapping": "exact"},
        "RUNNING": {"to": "EXECUTE", "mapping": "exact"},
        "HELD": {"to": "HELD", "mapping": "exact"},
        "ABORTED": {"to": "ABORTED", "mapping": "exact"},
        "COMPLETE": {"to": "COMPLETE", "mapping": "exact"},
        "STOPPING": {"to": "STOPPING", "mapping": "exact"},
        "RESETTING": {"to": "RESETTING", "mapping": "exact"},
    },
    ("ISA-95", "MDIS"): {
        "Equipment": {"to": "MDISObject", "mapping": "exact", "note": "field device"},
        "ProcessSegment": {"to": "ServiceProcedure", "mapping": "partial"},
        "Material": {"to": "Fluid", "mapping": "partial", "note": "process fluid"},
        "Property": {"to": "ProcessVariable", "mapping": "exact"},
    },
    ("ISA-95", "ISA-101"): {
        "Equipment": {"to": "Faceplate", "mapping": "partial", "note": "equipment→HMI display"},
        "Idle": {"to": "Gray", "mapping": "exact", "note": "state→color"},
        "Running": {"to": "Green", "mapping": "exact"},
        "Faulted": {"to": "Red", "mapping": "exact"},
        "Maintenance": {"to": "Blue", "mapping": "exact"},
    },
    ("ISA-88", "ISA-101"): {
        "IDLE": {"to": "Gray", "mapping": "exact"},
        "RUNNING": {"to": "Green", "mapping": "exact"},
        "COMPLETE": {"to": "Gray", "mapping": "exact"},
        "HELD": {"to": "Yellow", "mapping": "exact"},
        "ABORTED": {"to": "Red", "mapping": "exact"},
        "Phase": {"to": "Faceplate", "mapping": "partial", "note": "phase→unit display"},
    },
    ("ISA-18.2", "OPC-UA"): {
        "Alarm": {"to": "OPC_Node", "mapping": "partial", "note": "alarm→condition node"},
        "AlarmPriority": {"to": "OPC_Variable", "mapping": "partial", "note": "priority→severity"},
        "UNACK": {"to": "Active", "mapping": "exact", "note": "OPC alarm state"},
        "ACKED": {"to": "Acknowledged", "mapping": "exact"},
        "NORM": {"to": "Inactive", "mapping": "exact"},
    },
    ("ISA-88", "PLCopen"): {
        "Phase": {"to": "FunctionBlock", "mapping": "partial", "note": "control logic"},
        "IDLE": {"to": "STANDSTILL", "mapping": "exact"},
        "RUNNING": {"to": "CONTINUOUS_MOTION", "mapping": "partial"},
        "HELD": {"to": "SYNCHRONIZED_MOTION", "mapping": "partial"},
        "ABORTED": {"to": "ERRORSTOP", "mapping": "exact"},
        "Recipe": {"to": "Program", "mapping": "partial", "note": "IEC 61131-3"},
    },
}


def map_entity(entity: dict, from_std: str, to_std: str) -> dict:
    udt_name = entity.get("_udt", "")
    key = (from_std, to_std)
    rev_key = (to_std, from_std)

    table = CROSSWALK_TABLE.get(key) or CROSSWALK_TABLE.get(rev_key)
    if not table:
        return {"mapped": False, "error": f"No crosswalk: {from_std} <-> {to_std}"}

    mapping = table.get(udt_name)
    if not mapping:
        return {"mapped": False, "error": f"No mapping for {udt_name} in {key}"}

    result = dict(entity)
    result["_udt"] = mapping["to"]
    result["_crosswalk"] = {
        "from_std": from_std, "to_std": to_std,
        "from_udt": udt_name, "to_udt": mapping["to"],
        "mapping": mapping["mapping"],
    }
    return {"mapped": True, "entity": result}


def list_crosswalks() -> list[dict]:
    out = []
    for (f, t), mappings in CROSSWALK_TABLE.items():
        for from_entity, m in mappings.items():
            out.append({"from_std": f, "to_std": t,
                        "from_entity": from_entity, "to_entity": m["to"],
                        "mapping": m["mapping"]})
    return out

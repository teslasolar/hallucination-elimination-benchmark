"""LAYER 9: KPIs — Operational Performance Metrics."""
from konomi.core import UDT, Standard

OEE = UDT("OEE", [
    {"name": "availability", "type": "num", "required": True},
    {"name": "performance", "type": "num", "required": True},
    {"name": "quality", "type": "num", "required": True},
], tags={
    "isa": ["KPI"],
    "formula": "oee = availability * performance * quality",
    "targets": {"availability": 0.90, "performance": 0.95, "quality": 0.99, "oee": 0.85},
})

MTBF = UDT("MTBF", [
    {"name": "total_uptime", "type": "num", "required": True},
    {"name": "failure_count", "type": "int", "required": True},
], tags={"formula": "mtbf = total_uptime / failure_count"})

MTTR = UDT("MTTR", [
    {"name": "total_downtime", "type": "num", "required": True},
    {"name": "failure_count", "type": "int", "required": True},
], tags={"formula": "mttr = total_downtime / failure_count"})

CycleTime = UDT("CycleTime", [
    {"name": "ideal", "type": "num", "required": True},
    {"name": "actual", "type": "num", "required": True},
], tags={"formula": "efficiency = ideal / actual"})

Throughput = UDT("Throughput", [
    {"name": "value", "type": "num", "required": True},
    {"name": "unit", "type": "str", "default": "units/hour"},
])

EnergyKPI = UDT("EnergyKPI", [
    {"name": "kwh_per_unit", "type": "num", "required": True},
    {"name": "peak_demand", "type": "num", "default": None},
    {"name": "power_factor", "type": "num", "default": None},
    {"name": "cost_per_unit", "type": "num", "default": None},
])

FirstPassYield = UDT("FirstPassYield", [
    {"name": "good_units", "type": "int", "required": True},
    {"name": "total_units", "type": "int", "required": True},
], tags={"formula": "fpy = good_units / total_units",
         "isa": ["KPI", "ISO-22400"]})

DefectRate = UDT("DefectRate", [
    {"name": "defects", "type": "int", "required": True},
    {"name": "units_produced", "type": "int", "required": True},
    {"name": "category", "type": "str", "default": "all"},
], tags={"formula": "rate = defects / units_produced",
         "categories": ["scrap", "rework", "return", "all"]})

Downtime = UDT("Downtime", [
    {"name": "duration", "type": "num", "required": True},
    {"name": "reason", "type": "str", "required": True},
    {"name": "planned", "type": "bool", "default": False},
    {"name": "equipment", "type": "str", "default": None},
], tags={"isa": ["KPI"],
         "reasons": ["Breakdown", "Setup", "Adjustment", "Startup",
                      "Reduced Speed", "Idling", "Material", "Planned"]})

KPI_TREE = {
    "OEE": {
        "Availability": ["MTBF", "MTTR", "Downtime"],
        "Performance": ["CycleTime", "Throughput"],
        "Quality": ["FirstPassYield", "DefectRate"],
    }
}


def build():
    return Standard("KPI", "operational performance metrics (ISO 22400)",
        udts=[OEE, MTBF, MTTR, CycleTime, Throughput, EnergyKPI,
              FirstPassYield, DefectRate, Downtime])

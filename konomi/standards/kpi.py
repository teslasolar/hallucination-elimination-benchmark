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
])

KPI_TREE = {
    "OEE": {
        "Availability": ["MTBF", "MTTR", "Downtime"],
        "Performance": ["CycleTime", "Throughput"],
        "Quality": ["FirstPassYield", "DefectRate"],
    }
}


def build():
    return Standard("KPI", "operational performance metrics",
        udts=[OEE, MTBF, MTTR, CycleTime, Throughput, EnergyKPI])

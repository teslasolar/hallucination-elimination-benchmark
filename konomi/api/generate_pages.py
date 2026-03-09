"""Generate static JSON + HTML for GitHub Pages KONOMI dashboard.
Run: python -m konomi.api.generate_pages
"""
import json, os

# Bootstrap all standards
from konomi.core import KS, UDT
from konomi.standards import base_udts, isa_95, isa_88, isa_101, isa_18_2, opc_ua, mqtt_sparkplug, modbus, kpi
from konomi.crosswalks.engine import list_crosswalks

base_udts.build_all()
MODS = {"ISA-95": isa_95, "ISA-88": isa_88, "ISA-101": isa_101,
        "ISA-18.2": isa_18_2, "OPC-UA": opc_ua, "MQTT-Sparkplug": mqtt_sparkplug,
        "Modbus": modbus, "KPI": kpi}
for m in MODS.values():
    m.build()

OUT = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "konomi")
os.makedirs(OUT, exist_ok=True)


def write_json(name, data):
    with open(os.path.join(OUT, name), "w") as f:
        json.dump(data, f, indent=2, default=str)


# Standards index
write_json("standards.json", {"standards": KS.list_standards()})

# Each standard
for sid in KS.list_standards():
    std = KS.parse(sid)
    safe = sid.lower().replace("-", "_").replace(".", "_")
    write_json(f"{safe}.json", std.to_dict())

# All UDTs
all_udts = {}
for name, udt in UDT.all().items():
    all_udts[name] = udt.to_dict()
write_json("udts.json", all_udts)

# Crosswalks
write_json("crosswalks.json", {"crosswalks": list_crosswalks()})

print(f"Generated {len(os.listdir(OUT))} files in {OUT}")
for f in sorted(os.listdir(OUT)):
    print(f"  {f}")

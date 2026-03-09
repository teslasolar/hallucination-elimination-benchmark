"""LAYER 7: MQTT/Sparkplug B — Lightweight Pub/Sub Messaging."""
from konomi.core import UDT, Standard, Rule

MQTT_Topic = UDT("MQTT_Topic", [
    {"name": "namespace", "type": "str", "default": "spBv1.0"},
    {"name": "group", "type": "str", "required": True},
    {"name": "edge", "type": "str", "required": True},
    {"name": "device", "type": "str", "default": None},
    {"name": "verb", "type": "str", "default": "DDATA"},
], tags={
    "isa": ["Sparkplug"],
    "verbs": ["NBIRTH", "NDEATH", "DBIRTH", "DDEATH", "NDATA", "DDATA", "NCMD", "DCMD"],
})

SparkplugPayload = UDT("SparkplugPayload", [
    {"name": "timestamp", "type": "int", "required": True},
    {"name": "metrics", "type": "list", "default": []},
    {"name": "seq", "type": "int", "default": 0},
], tags={
    "isa": ["Sparkplug"],
    "data_types": ["Int8", "Int16", "Int32", "Int64", "UInt8", "UInt16",
                    "UInt32", "UInt64", "Float", "Double", "Boolean",
                    "String", "DateTime", "UUID", "DataSet", "Bytes"],
    "qos": [(0, "AtMostOnce"), (1, "AtLeastOnce"), (2, "ExactlyOnce")],
})

RULES = [
    Rule("R1", "True", "NBIRTH before any NDATA"),
    Rule("R2", "True", "seq increments 0-255 wrap"),
    Rule("R4", "True", "alias for bandwidth optimization"),
    Rule("R5", "True", "store-forward on disconnect"),
]


def build():
    return Standard("MQTT-Sparkplug", "lightweight pub/sub messaging",
        udts=[MQTT_Topic, SparkplugPayload], rules=RULES)

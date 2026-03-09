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
    {"name": "uuid", "type": "str", "default": None},
], tags={
    "isa": ["Sparkplug"],
    "qos": [(0, "AtMostOnce"), (1, "AtLeastOnce"), (2, "ExactlyOnce")],
})

SparkplugMetric = UDT("SparkplugMetric", [
    {"name": "name", "type": "str", "required": True},
    {"name": "alias", "type": "int", "default": None},
    {"name": "datatype", "type": "str", "required": True},
    {"name": "value", "type": "any", "default": None},
    {"name": "timestamp", "type": "int", "default": None},
    {"name": "is_historical", "type": "bool", "default": False},
    {"name": "is_transient", "type": "bool", "default": False},
    {"name": "properties", "type": "dict", "default": {}},
], tags={
    "isa": ["Sparkplug"],
    "data_types": ["Int8", "Int16", "Int32", "Int64", "UInt8", "UInt16",
                    "UInt32", "UInt64", "Float", "Double", "Boolean",
                    "String", "DateTime", "UUID", "DataSet", "Bytes"],
})

RULES = [
    Rule("R1", "True", "NBIRTH before any NDATA"),
    Rule("R2", "True", "seq increments 0-255 wrap"),
    Rule("R3", "True", "metrics must include name, datatype; alias after BIRTH"),
    Rule("R4", "True", "alias for bandwidth optimization"),
    Rule("R5", "True", "store-forward on disconnect"),
]


def build():
    return Standard("MQTT-Sparkplug", "lightweight pub/sub messaging (Sparkplug B)",
        udts=[MQTT_Topic, SparkplugPayload, SparkplugMetric], rules=RULES)

"""LAYER 1: Base UDTs — primitives all standards share."""
from konomi.core import UDT

Identifier = UDT("Identifier", [
    {"name": "value", "type": "str", "required": True},
    {"name": "id_type", "type": "str", "default": "UUID"},
    {"name": "scope", "type": "str", "default": "global"},
    {"name": "format", "type": "str", "default": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"},
])

Timestamp = UDT("Timestamp", [
    {"name": "value", "type": "str", "required": True},
    {"name": "format", "type": "str", "default": "ISO8601"},
    {"name": "resolution", "type": "str", "default": "ms"},
    {"name": "timezone", "type": "str", "default": "UTC"},
])

Quality = UDT("Quality", [
    {"name": "value", "type": "int", "default": 192},
    {"name": "good", "type": "bool", "default": True},
    {"name": "bad", "type": "bool", "default": False},
    {"name": "uncertain", "type": "bool", "default": False},
], tags={"code": [("GOOD", 192), ("BAD", 0), ("UNCERTAIN", 64)]})

Value = UDT("Value", [
    {"name": "v", "type": "any", "required": True},
    {"name": "q", "type": "Quality", "default": None},
    {"name": "t", "type": "Timestamp", "default": None},
    {"name": "unit", "type": "str", "default": None},
])

Range = UDT("Range", [
    {"name": "lo", "type": "num", "required": True},
    {"name": "hi", "type": "num", "required": True},
    {"name": "unit", "type": "str", "default": None},
])

Quantity = UDT("Quantity", [
    {"name": "value", "type": "num", "required": True},
    {"name": "unit", "type": "str", "required": True},
    {"name": "uncertainty", "type": "num", "default": None},
])

Duration = UDT("Duration", [
    {"name": "value", "type": "num", "required": True},
    {"name": "unit", "type": "str", "default": "s"},
])

Status = UDT("Status", [
    {"name": "code", "type": "int", "required": True},
    {"name": "name", "type": "str", "required": True},
    {"name": "severity", "type": "str", "default": "info"},
], tags={"severity": ["info", "warn", "error", "fatal"]})

ErrorInfo = UDT("ErrorInfo", [
    {"name": "code", "type": "int", "required": True},
    {"name": "message", "type": "str", "required": True},
    {"name": "source", "type": "str", "default": None},
    {"name": "severity", "type": "str", "default": "error"},
], tags={"severity": ["info", "warn", "error", "fatal"]})

Measurement = UDT("Measurement", [
    {"name": "value", "type": "num", "required": True},
    {"name": "unit", "type": "str", "required": True},
    {"name": "quality", "type": "int", "default": 192},
    {"name": "timestamp", "type": "str", "default": None},
    {"name": "uncertainty", "type": "num", "default": None},
], tags={"si_base": ["m", "kg", "s", "A", "K", "mol", "cd"]})

Enumeration = UDT("Enumeration", [
    {"name": "name", "type": "str", "required": True},
    {"name": "values", "type": "list", "required": True},
    {"name": "default", "type": "str", "default": None},
])


def build_all():
    return [Identifier, Timestamp, Quality, Value, Range, Quantity,
            Duration, Status, ErrorInfo, Measurement, Enumeration]

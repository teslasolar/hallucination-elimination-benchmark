"""LAYER 8: Modbus — Simple Field Device Communication."""
from konomi.core import UDT, Standard

ModbusRegister = UDT("ModbusRegister", [
    {"name": "addr", "type": "int", "required": True},
    {"name": "reg_type", "type": "str", "required": True},
    {"name": "access", "type": "str", "default": "RW"},
    {"name": "data_type", "type": "str", "default": "UINT16"},
    {"name": "fc_read", "type": "int", "default": 3},
    {"name": "fc_write", "type": "int", "default": None},
], tags={
    "isa": ["Modbus"],
    "register_types": [
        ("Coil", "RW", "bit", 1, 5),
        ("DiscreteInput", "RO", "bit", 2, None),
        ("HoldingReg", "RW", "uint16", 3, 6),
        ("InputReg", "RO", "uint16", 4, None),
    ],
    "data_types": ["BOOL", "INT16", "UINT16", "INT32", "UINT32",
                    "FLOAT32", "INT64", "FLOAT64", "STRING"],
})

ModbusMap = UDT("ModbusMap", [
    {"name": "tag", "type": "str", "required": True},
    {"name": "unit_id", "type": "int", "required": True},
    {"name": "register_type", "type": "str", "required": True},
    {"name": "addr", "type": "int", "required": True},
    {"name": "count", "type": "int", "default": 1},
    {"name": "data_type", "type": "str", "default": "UINT16"},
    {"name": "scale", "type": "num", "default": 1},
    {"name": "offset", "type": "num", "default": 0},
    {"name": "byte_order", "type": "str", "default": "ABCD"},
    {"name": "protocol", "type": "str", "default": "TCP"},
], tags={"isa": ["Modbus"],
         "byte_orders": ["ABCD", "DCBA", "BADC", "CDAB"],
         "protocols": ["TCP", "RTU", "ASCII"]})

FUNCTION_CODES = {
    1: "Read Coils", 2: "Read DI", 3: "Read HR", 4: "Read IR",
    5: "Write Coil", 6: "Write HR", 15: "Write Multi Coil", 16: "Write Multi HR",
}

# Correct FC per register type (fc_read must match)
FC_BY_TYPE = {
    "Coil": (1, 5), "DiscreteInput": (2, None),
    "HoldingReg": (3, 6), "InputReg": (4, None),
}

# Multi-register: count for 32/64-bit types
REGISTER_COUNT = {
    "BOOL": 1, "INT16": 1, "UINT16": 1,
    "INT32": 2, "UINT32": 2, "FLOAT32": 2,
    "INT64": 4, "UINT64": 4, "FLOAT64": 4,
    "STRING": None,  # variable
}

EXCEPTION_CODES = {
    1: "Illegal Function", 2: "Illegal Address", 3: "Illegal Value",
    4: "Device Fail", 5: "Ack", 6: "Busy",
}


def build():
    return Standard("Modbus", "simple field device communication (Modbus/TCP+RTU)",
        udts=[ModbusRegister, ModbusMap])

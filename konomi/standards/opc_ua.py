"""LAYER 6: OPC-UA — Industrial Interoperability."""
from konomi.core import UDT, Standard

OPC_Node = UDT("OPC_Node", [
    {"name": "node_id", "type": "str", "required": True},
    {"name": "browse_name", "type": "str", "required": True},
    {"name": "display_name", "type": "str", "required": True},
    {"name": "node_class", "type": "str", "default": "Variable"},
    {"name": "parent", "type": "str", "default": None},
], tags={
    "isa": ["OPC-UA"],
    "node_classes": ["Object", "ObjectType", "Variable", "VariableType",
                     "Method", "View", "DataType", "ReferenceType"],
})

OPC_Variable = UDT("OPC_Variable", [
    {"name": "data_type", "type": "str", "required": True},
    {"name": "value", "type": "any", "default": None},
    {"name": "access", "type": "str", "default": "RO"},
    {"name": "historizing", "type": "bool", "default": False},
], base="OPC_Node", tags={"isa": ["OPC-UA"]})

OPC_Method = UDT("OPC_Method", [
    {"name": "input_args", "type": "list", "default": []},
    {"name": "output_args", "type": "list", "default": []},
    {"name": "executable", "type": "bool", "default": True},
], base="OPC_Node", tags={"isa": ["OPC-UA"]})

OPC_Subscription = UDT("OPC_Subscription", [
    {"name": "id", "type": "int", "required": True},
    {"name": "publishing_interval", "type": "num", "default": 1000},
    {"name": "enabled", "type": "bool", "default": True},
    {"name": "monitored_items", "type": "list", "default": []},
], tags={"isa": ["OPC-UA"]})

ADDRESS_SPACE = {
    "Root": {
        "Objects": ["Server", "DeviceSet", "Aliases"],
        "Types": ["ObjectTypes", "VariableTypes", "DataTypes"],
        "Views": ["Engineering", "Operations", "Maintenance"],
    }
}

COMPANION_SPECS = {
    "ISA-95": "ns=isa95;Equipment,Material,Personnel",
    "PackML": "ns=packml;StateMachine,Admin,Status",
}


def build():
    return Standard("OPC-UA", "industrial interoperability",
        udts=[OPC_Node, OPC_Variable, OPC_Method, OPC_Subscription],
        hierarchy=[{"name": "Root"}, {"name": "Objects"}, {"name": "Types"}, {"name": "Views"}])

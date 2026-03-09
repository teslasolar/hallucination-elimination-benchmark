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
    {"name": "keep_alive_count", "type": "int", "default": 10},
    {"name": "lifetime_count", "type": "int", "default": 100},
    {"name": "enabled", "type": "bool", "default": True},
    {"name": "monitored_items", "type": "list", "default": []},
], tags={"isa": ["OPC-UA"]})

OPC_DataType = UDT("OPC_DataType", [
    {"name": "name", "type": "str", "required": True},
    {"name": "type_id", "type": "int", "required": True},
    {"name": "encoding", "type": "str", "default": "Binary"},
], tags={"isa": ["OPC-UA"],
         "built_in": ["Boolean", "SByte", "Byte", "Int16", "UInt16",
                       "Int32", "UInt32", "Int64", "UInt64", "Float",
                       "Double", "String", "DateTime", "Guid", "ByteString",
                       "NodeId", "StatusCode", "QualifiedName", "LocalizedText"]})

OPC_SecurityPolicy = UDT("OPC_SecurityPolicy", [
    {"name": "uri", "type": "str", "required": True},
    {"name": "mode", "type": "str", "default": "SignAndEncrypt"},
    {"name": "auth_type", "type": "str", "default": "Certificate"},
], tags={"isa": ["OPC-UA"],
         "policies": ["None", "Basic128Rsa15", "Basic256", "Basic256Sha256",
                       "Aes128_Sha256_RsaOaep", "Aes256_Sha256_RsaPss"],
         "modes": ["None", "Sign", "SignAndEncrypt"],
         "auth_types": ["Anonymous", "UserName", "Certificate", "IssuedToken"]})

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
    return Standard("OPC-UA", "industrial interoperability (IEC 62541)",
        udts=[OPC_Node, OPC_Variable, OPC_Method, OPC_Subscription,
              OPC_DataType, OPC_SecurityPolicy],
        hierarchy=[{"name": "Root"}, {"name": "Objects"}, {"name": "Types"}, {"name": "Views"}])

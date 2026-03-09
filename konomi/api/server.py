"""KONOMI API server — lightweight HTTP API with demo flag.
Run: python -m konomi.api.server [--demo] [--port 8095]
"""
import json, sys, os
from http.server import HTTPServer, BaseHTTPRequestHandler
from konomi.core import KS, UDT, demo_mode

# Load all standards on import
from konomi.standards import base_udts, isa_95, isa_88, isa_101, isa_18_2, opc_ua, mqtt_sparkplug, modbus, kpi
base_udts.build_all()
STANDARDS = {"ISA-95": isa_95, "ISA-88": isa_88, "ISA-101": isa_101,
             "ISA-18.2": isa_18_2, "OPC-UA": opc_ua, "MQTT-Sparkplug": mqtt_sparkplug,
             "Modbus": modbus, "KPI": kpi}
for mod in STANDARDS.values():
    mod.build()


def _json(obj):
    return json.dumps(obj, indent=2, default=str).encode()


class Handler(BaseHTTPRequestHandler):
    def _respond(self, code, body):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(_json(body))

    def do_GET(self):
        path = self.path.rstrip("/")

        if path == "/api/standards":
            self._respond(200, {"standards": KS.list_standards(),
                                "demo": os.environ.get("KONOMI_DEMO") == "1"})

        elif path.startswith("/api/standards/"):
            std_id = path.split("/")[-1]
            try:
                std = KS.parse(std_id)
                self._respond(200, std.to_dict())
            except ValueError as e:
                self._respond(404, {"error": str(e)})

        elif path.startswith("/api/udts"):
            parts = path.split("/")
            if len(parts) > 3:
                std_id = parts[3]
                self._respond(200, {"udts": KS.list_udts(std_id)})
            else:
                self._respond(200, {"udts": KS.list_udts()})

        elif path.startswith("/api/expand/"):
            std_id = path.split("/")[-1]
            try:
                self._respond(200, KS.expand(std_id))
            except ValueError as e:
                self._respond(404, {"error": str(e)})

        elif path.startswith("/api/crosswalks"):
            from konomi.crosswalks.engine import list_crosswalks
            self._respond(200, {"crosswalks": list_crosswalks()})

        elif path.startswith("/api/generate/"):
            udt_path = path.split("/")[-1]
            try:
                code = KS.generate(udt_path)
                self._respond(200, {"udt": udt_path, "code": code})
            except ValueError as e:
                self._respond(404, {"error": str(e)})

        elif path == "/api/health":
            self._respond(200, {"status": "ok", "version": "1.0.0",
                                "demo": os.environ.get("KONOMI_DEMO") == "1"})
        else:
            self._respond(404, {"error": "not found", "endpoints": [
                "/api/standards", "/api/standards/{id}", "/api/udts",
                "/api/expand/{id}", "/api/crosswalks", "/api/generate/{udt}",
                "/api/health"]})

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}
        path = self.path.rstrip("/")

        if path == "/api/validate":
            std_id = body.get("standard", "")
            entity = body.get("entity", {})
            try:
                result = KS.validate(entity, std_id)
                self._respond(200, result)
            except ValueError as e:
                self._respond(400, {"error": str(e)})

        elif path == "/api/crosswalk":
            entity = body.get("entity", {})
            from_std = body.get("from", "")
            to_std = body.get("to", "")
            result = KS.crosswalk(entity, from_std, to_std)
            self._respond(200, result)

        else:
            self._respond(404, {"error": "not found"})

    def log_message(self, fmt, *args):
        pass  # quiet


def main():
    port = 8095
    if "--demo" in sys.argv:
        os.environ["KONOMI_DEMO"] = "1"
        demo_mode(True)
    if "--port" in sys.argv:
        port = int(sys.argv[sys.argv.index("--port") + 1])
    print(f"KONOMI Standard API on :{port} [demo={'on' if os.environ.get('KONOMI_DEMO') == '1' else 'off'}]")
    HTTPServer(("", port), Handler).serve_forever()


if __name__ == "__main__":
    main()

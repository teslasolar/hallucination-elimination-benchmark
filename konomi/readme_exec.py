"""README executor — parses UDT tags from markdown, runs CLI commands, logs state machines.
Run: python -m konomi.readme_exec [--dry-run] [--tag TAG] [README.md]
"""
import re, sys, os, subprocess, json, time
from konomi.core import KS, UDT, Standard, demo_mode
from konomi.standards import base_udts, isa_95, isa_88, isa_101, isa_18_2, opc_ua, mqtt_sparkplug, modbus, kpi

# Bootstrap
base_udts.build_all()
for m in [isa_95, isa_88, isa_101, isa_18_2, opc_ua, mqtt_sparkplug, modbus, kpi]:
    m.build()

TAG_RE = re.compile(
    r'<!--\s*@(\w+)(?:\[([^\]]*)\])?\s*-->\s*```(\w+)?\n(.*?)```',
    re.DOTALL
)
STATE_RE = re.compile(r'<!--\s*@state\[([^\]]*)\]\s*-->')
LOG_FILE = ".konomi/exec.log"


def parse_tags(md_text: str) -> list[dict]:
    tags = []
    for m in TAG_RE.finditer(md_text):
        tag_type, tag_meta, lang, body = m.group(1), m.group(2), m.group(3), m.group(4)
        meta = {}
        if tag_meta:
            for pair in tag_meta.split(","):
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    meta[k.strip()] = v.strip()
                else:
                    meta["id"] = pair.strip()
        tags.append({"type": tag_type, "meta": meta, "lang": lang or "bash", "body": body.strip()})
    return tags


def parse_states(md_text: str) -> list[dict]:
    states = []
    for m in STATE_RE.finditer(md_text):
        raw = m.group(1)
        parts = {}
        for pair in raw.split(","):
            if "=" in pair:
                k, v = pair.split("=", 1)
                parts[k.strip()] = v.strip()
        states.append(parts)
    return states


def log_event(event: dict):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    event["ts"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(event) + "\n")


def run_tag(tag: dict, dry_run: bool = False) -> dict:
    result = {"tag": tag["type"], "meta": tag["meta"], "status": "pending"}
    log_event({"action": "run_tag", "tag": tag["type"], "meta": tag["meta"], "dry_run": dry_run})

    if tag["type"] == "run":
        if dry_run:
            result["status"] = "dry_run"
            result["cmd"] = tag["body"]
            print(f"  [DRY] {tag['body'][:80]}")
        else:
            try:
                proc = subprocess.run(
                    tag["body"], shell=True, capture_output=True, text=True, timeout=120
                )
                result["status"] = "pass" if proc.returncode == 0 else "fail"
                result["returncode"] = proc.returncode
                result["stdout"] = proc.stdout[:500]
                result["stderr"] = proc.stderr[:500]
                log_event({"action": "cmd_result", "rc": proc.returncode, "cmd": tag["body"][:80]})
            except subprocess.TimeoutExpired:
                result["status"] = "timeout"

    elif tag["type"] == "test":
        if dry_run:
            result["status"] = "dry_run"
            print(f"  [DRY TEST] {tag['body'][:80]}")
        else:
            try:
                proc = subprocess.run(
                    tag["body"], shell=True, capture_output=True, text=True, timeout=120
                )
                result["status"] = "pass" if proc.returncode == 0 else "fail"
                result["returncode"] = proc.returncode
                result["stdout"] = proc.stdout[:500]
                log_event({"action": "test_result", "rc": proc.returncode, "cmd": tag["body"][:80]})
            except subprocess.TimeoutExpired:
                result["status"] = "timeout"

    elif tag["type"] == "path":
        target = tag["body"].strip()
        exists = os.path.exists(target)
        result["status"] = "pass" if exists else "fail"
        result["path"] = target
        result["exists"] = exists
        log_event({"action": "path_check", "path": target, "exists": exists})

    elif tag["type"] == "udt":
        udt_name = tag["meta"].get("id", tag["body"].strip())
        udt = UDT.get(udt_name)
        if udt:
            result["status"] = "pass"
            result["udt"] = udt.to_dict()
            result["tags"] = {k: str(v)[:100] for k, v in udt.tags.items()}
        else:
            result["status"] = "fail"
            result["error"] = f"UDT not found: {udt_name}"
        log_event({"action": "udt_check", "udt": udt_name, "found": udt is not None})

    elif tag["type"] == "validate":
        std_id = tag["meta"].get("std", "")
        try:
            entity = json.loads(tag["body"])
            report = KS.validate(entity, std_id)
            result["status"] = "pass" if report["valid"] else "fail"
            result["report"] = report
        except Exception as e:
            result["status"] = "fail"
            result["error"] = str(e)

    elif tag["type"] == "crosswalk":
        from_std = tag["meta"].get("from", "")
        to_std = tag["meta"].get("to", "")
        try:
            entity = json.loads(tag["body"])
            mapped = KS.crosswalk(entity, from_std, to_std)
            result["status"] = "pass" if mapped.get("mapped") else "fail"
            result["mapped"] = mapped
        except Exception as e:
            result["status"] = "fail"
            result["error"] = str(e)

    else:
        result["status"] = "skip"
        result["reason"] = f"unknown tag type: {tag['type']}"

    return result


def execute_readme(path: str = "README.md", dry_run: bool = False, filter_tag: str = None):
    with open(path) as f:
        md = f.read()

    tags = parse_tags(md)
    states = parse_states(md)
    if filter_tag:
        tags = [t for t in tags if t["type"] == filter_tag or t["meta"].get("id") == filter_tag]

    print(f"KONOMI README Executor — {len(tags)} tags, {len(states)} state refs")
    log_event({"action": "exec_start", "file": path, "tags": len(tags), "states": len(states)})

    results = []
    for i, tag in enumerate(tags):
        label = tag["meta"].get("id", tag["type"])
        print(f"[{i+1}/{len(tags)}] @{tag['type']}[{label}]", end=" ")
        r = run_tag(tag, dry_run)
        icon = {"pass": "OK", "fail": "FAIL", "dry_run": "DRY", "skip": "SKIP", "timeout": "TIMEOUT"}
        print(f"→ {icon.get(r['status'], r['status'])}")
        results.append(r)

    # State machine logging
    for s in states:
        udt_name = s.get("udt", "")
        udt = UDT.get(udt_name)
        if udt:
            log_event({"action": "state_ref", "udt": udt_name,
                        "states": udt.tagged("states"), "transitions": str(udt.tagged("transitions"))[:200]})

    passed = sum(1 for r in results if r["status"] == "pass")
    failed = sum(1 for r in results if r["status"] == "fail")
    print(f"\nResults: {passed} passed, {failed} failed, {len(results)-passed-failed} other")
    log_event({"action": "exec_done", "passed": passed, "failed": failed, "total": len(results)})
    return results


def main():
    args = sys.argv[1:]
    dry_run = "--dry-run" in args
    args = [a for a in args if a != "--dry-run"]
    filter_tag = None
    if "--tag" in args:
        idx = args.index("--tag")
        filter_tag = args[idx + 1]
        args = args[:idx] + args[idx+2:]
    path = args[0] if args else "README.md"
    execute_readme(path, dry_run, filter_tag)


if __name__ == "__main__":
    main()

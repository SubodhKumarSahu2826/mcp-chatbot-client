import json
import sys

TOOLS = [
    {
        "name": "calculator.add",
        "description": "Add two numbers",
        "inputSchema": {
            "type": "object",
            "properties": {"a": {"type": "number"}, "b": {"type": "number"}},
            "required": ["a", "b"],
        },
    }
]


def handle(method: str, params: dict):
    if method == "initialize":
        return {"protocolVersion": "2024-11-05", "serverInfo": {"name": "fake", "version": "1.0"}}
    if method == "tools/list":
        return {"tools": TOOLS}
    if method == "tools/call":
        if params.get("name") != "calculator.add":
            return {"isError": True, "content": [{"type": "text", "text": "Unknown tool"}]}
        args = params.get("arguments", {})
        result = float(args.get("a", 0)) + float(args.get("b", 0))
        return {"content": [{"type": "text", "text": str(result)}], "sum": result}
    raise ValueError(f"Unknown method: {method}")


for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    req = json.loads(line)
    try:
        result = handle(req["method"], req.get("params", {}))
        resp = {"jsonrpc": "2.0", "id": req.get("id"), "result": result}
    except Exception as exc:
        resp = {
            "jsonrpc": "2.0",
            "id": req.get("id"),
            "error": {"code": -32000, "message": str(exc)},
        }
    sys.stdout.write(json.dumps(resp) + "\n")
    sys.stdout.flush()

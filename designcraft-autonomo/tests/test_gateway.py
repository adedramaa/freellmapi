import base64
import importlib
import json
import os

os.environ.setdefault("MCP_BEARER_TOKEN", "this-is-an-example-secret-for-tests-only")
os.environ.setdefault("WORKSPACE_DIR", "/tmp/designcraft-autonomo-tests")
server = importlib.import_module("server")
from fastapi.testclient import TestClient

class FakeBridge:
    def __init__(self): self.calls = []
    async def exchange(self, message, expect_reply=True):
        self.calls.append(message)
        if not expect_reply: return None
        if message["method"] == "tools/list":
            return {"jsonrpc":"2.0","id":message["id"],"result":{"tools":[{"name":"execute","inputSchema":{"type":"object"}}]}}
        return {"jsonrpc":"2.0","id":message["id"],"result":{"protocolVersion":"2025-06-18","capabilities":{"tools":{}},"serverInfo":{"name":"designcraft-mock","version":"0.0.0"}}}

def client(monkeypatch):
    fake = FakeBridge()
    monkeypatch.setattr(server,"bridge",fake)
    return TestClient(server.app), fake

def test_auth_and_methods(monkeypatch):
    api,fake = client(monkeypatch)
    payload={"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}
    assert api.post("/mcp",json=payload).status_code==401
    headers={"Authorization":f"Bearer {server.TOKEN}"}
    ok=api.post("/mcp",json=payload,headers=headers)
    assert ok.status_code==200
    assert ok.json()["result"]["serverInfo"]["name"]=="designcraft-mock"
    denied=api.post("/mcp",json={"jsonrpc":"2.0","id":4,"method":"resources/read"},headers=headers)
    assert denied.json()["error"]["code"]==-32601
    assert len(fake.calls)==1

def test_tools_merge_and_notification(monkeypatch):
    api,fake=client(monkeypatch)
    headers={"Authorization":f"Bearer {server.TOKEN}"}
    out=api.post("/mcp",json={"jsonrpc":"2.0","id":7,"method":"tools/list"},headers=headers)
    names=[x["name"] for x in out.json()["result"]["tools"]]
    assert "execute" in names and "gateway_save_asset" in names
    notify=api.post("/mcp",json={"jsonrpc":"2.0","method":"notifications/initialized"},headers=headers)
    assert notify.status_code==202
    assert len(fake.calls)==2

def test_file_and_download_signatures(monkeypatch):
    api,fake=client(monkeypatch)
    headers={"Authorization":f"Bearer {server.TOKEN}"}
    raw=b"\x89PNG\r\n\x1a\n"+b"data"
    req={"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"gateway_save_asset","arguments":{"filename":"image.png","base64_data":base64.b64encode(raw).decode()}}}
    assert "Asset saved" in api.post("/mcp",json=req,headers=headers).json()["result"]["content"][0]["text"]
    assert (server.INPUT/"image.png").read_bytes()==raw
    (server.OUTPUT/"test.pdf").write_bytes(b"%PDF-1.7\nhello")
    req["params"]={"name":"gateway_get_download_link","arguments":{"filename":"test.pdf"}}
    link=api.post("/mcp",json=req,headers=headers).json()["result"]["content"][0]["text"]
    import urllib.parse
    path=urllib.parse.urlsplit(link)
    actual=api.get(path.path+"?"+path.query)
    assert actual.status_code==200 and actual.content.startswith(b"%PDF-")
    assert api.get(path.path+"?"+path.query.replace("signature=","signature=x")).status_code==403
    req["params"]={"name":"gateway_get_download_link","arguments":{"filename":"../secret.pdf"}}
    err=api.post("/mcp",json=req,headers=headers).json()["result"]
    assert err.get("isError") is True

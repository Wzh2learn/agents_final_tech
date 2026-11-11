"""Private-evidence transport for the authorized BUPT research model.

The credential is read from the process environment or stdin and never persisted.
This module supplies transport and accounting, not an Agent or task evaluator.
"""
from __future__ import annotations

import argparse
from contextlib import nullcontext
import hashlib
import json
import os
from pathlib import Path
import socket
import ssl
import sys
import threading
import time
from urllib.parse import urlsplit


BASE_URL = "https://myai.bupt.edu.cn/llm-gw/v1"
MODEL = "deepseek-v4-flash"
REQUEST_TOKEN_CEILING = 262_144  # Full advertised 256K input-plus-output ceiling.


def usage_from_body(body):
    """Read provider totals; cache/reasoning details are subsets, never added."""
    try:
        objects = [json.loads(body)]
    except (ValueError, UnicodeDecodeError):
        objects = []
        for line in body.splitlines():
            if line.startswith(b"data:"):
                try:
                    objects.append(json.loads(line[5:].strip()))
                except (ValueError, UnicodeDecodeError):
                    pass
    usages = [o["usage"] for o in objects if isinstance(o, dict) and isinstance(o.get("usage"), dict)]
    if not usages:
        return None
    usage = usages[-1]
    values = [usage.get(k) for k in ("prompt_tokens", "completion_tokens", "total_tokens")]
    if not all(type(v) is int and v >= 0 for v in values) or values[0] + values[1] != values[2]:
        return None
    return usage


class BatchBudget:
    """One batch owner, one request at a time; unknown sends reserve 256K."""

    def __init__(self, root, *, posts=24, tokens=500_000):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
        self.posts, self.tokens = posts, tokens
        self.path = self.root / "gateway_ledger.json"
        self.lease = self.root / "gateway_owner.lock"
        self.fd = os.open(self.lease, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        try:
            self.rows = json.loads(self.path.read_text()) if self.path.exists() else []
            self.pending = None
            if any(r["state"] in ("reserved", "sending") for r in self.rows):
                raise RuntimeError("unresolved previous request; reconcile before continuing")
        except BaseException:
            self.close()
            raise

    def save(self):
        temp = self.path.with_suffix(".tmp")
        temp.write_text(json.dumps(self.rows, ensure_ascii=False, indent=2) + "\n")
        os.chmod(temp, 0o600)
        os.replace(temp, self.path)

    def reserve(self, body):
        with self.lock:
            if self.pending is not None:
                raise RuntimeError("single-concurrency batch already has an active request")
            charged = [r for r in self.rows if r["state"] != "not_sent"]
            used = sum(r.get("usage", {}).get("total_tokens", REQUEST_TOKEN_CEILING) for r in charged)
            if len(charged) >= self.posts or used + REQUEST_TOKEN_CEILING > self.tokens:
                raise RuntimeError("batch hard cap: cannot reserve the complete request ceiling")
            row = dict(index=len(self.rows) + 1, state="reserved", model=MODEL,
                       request_sha256=hashlib.sha256(body).hexdigest(), request_bytes=len(body),
                       reserved_tokens=REQUEST_TOKEN_CEILING, started_unix=time.time())
            self.rows.append(row)
            self.pending = row
            self.save()
            return row["index"]

    def sending(self):
        with self.lock:
            self.pending["state"] = "sending"
            self.save()

    def finish(self, *, status=None, body=None, sent=True):
        with self.lock:
            row = self.pending
            if row is None:
                return
            usage = usage_from_body(body) if body is not None else None
            row.update(state="complete" if usage is not None else "unknown" if sent else "not_sent",
                       http_status=status, finished_unix=time.time())
            if body is not None:
                row["response_sha256"] = hashlib.sha256(body).hexdigest()
            if usage is not None:
                row["usage"] = usage
            self.pending = None
            self.save()

    def close(self):
        if getattr(self, "fd", None) is not None:
            os.close(self.fd)
            self.fd = None
            self.lease.unlink()


class SchoolGateway:
    """TLS transport; the only credential-bearing data is the outgoing header."""

    def __init__(self, api_key, budget):
        if not api_key or any(c in api_key for c in "\r\n"):
            raise ValueError("missing or invalid credential")
        self._api_key, self.budget = api_key, budget

    def open(self, body, *, timeout=60, send_lock=None, admit=None):
        value = json.loads(body)
        if value.get("model") != MODEL:
            raise ValueError("unapproved model")
        forbidden = {"thinking", "reasoning_effort", "chat_template_kwargs", "max_completion_tokens"}
        if forbidden.intersection(value):
            raise ValueError("unsupported provider fields")
        if type(value.get("max_tokens")) is not int or not 1 <= value["max_tokens"] <= 8192:
            raise ValueError("explicit output cap required")
        index = self.budget.reserve(body)
        parsed = urlsplit(BASE_URL)
        connection = None
        sending = False
        try:
            raw = socket.create_connection((parsed.hostname, 443), timeout=timeout)
            try:
                connection = ssl.create_default_context().wrap_socket(raw, server_hostname=parsed.hostname)
            except BaseException:
                raw.close()
                raise
            packet = (f"POST {parsed.path}/chat/completions HTTP/1.1\r\n"
                      f"Host: {parsed.hostname}\r\nAuthorization: Bearer {self._api_key}\r\n"
                      f"Content-Type: application/json\r\nContent-Length: {len(body)}\r\n"
                      "Connection: close\r\n\r\n").encode() + body
            with send_lock if send_lock is not None else nullcontext():
                if admit is not None:
                    admit(connection)
                self.budget.sending()
                sending = True
                connection.sendall(packet)
            return index, connection
        except BaseException:
            if connection is not None:
                connection.close()
            self.budget.finish(sent=sending)
            raise


class SchoolBackend:
    """Use the existing owned OpenCode lifecycle with a distinct external model."""

    def __init__(self, api_key, budget, core):
        self.gateway = SchoolGateway(api_key, budget)
        self.core = core

    def verify(self, profile):
        if profile != dict(provider="bupt_chat_v1", base_url=BASE_URL, model_id=MODEL,
                           context=262144, output=4096):
            raise ValueError("school backend profile differs from the admitted configuration")
        return dict(kind="external_chat_gateway", base_url=BASE_URL, model_id=MODEL,
                    weights_precision="provider_managed_unknown", verification="configuration_only")

    def make_relay(self, root, profile, h, *, deadline, caps, **options):
        core, gateway = self.core, self.gateway
        if options:
            raise ValueError("local source sampling/capture options do not apply to school gateway")

        class Relay(core.Relay):
            def handle(self, client):
                upstream = None
                provider_index = None
                with self.lock:
                    self.attempts += 1
                    index = self.attempts
                    self.active.add(client)
                self.event(index, "attempt")
                try:
                    client.settimeout(max(.001, self.deadline - time.monotonic()))
                    value = h.actor.receive_http(client, self.caps['combined_wire_bytes'])
                    value, contract = core.prepare_tool_contract(value)
                    if value.get('model') != MODEL:
                        raise ValueError("incoming model does not match school backend")
                    value.pop('max_completion_tokens', None)
                    value.update(max_tokens=profile['output'], stream=True, stream_options=dict(include_usage=True))
                    body = json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(',', ':')).encode()
                    path = self.root / 'wire' / f'{index:05d}.request.json'
                    path.write_bytes(body)
                    self.event(index, 'tool_contract_prepared', **contract, body_bytes=len(body), body_sha256=core.sha(path))
                    with self.lock:
                        if self.closing or time.monotonic() >= self.deadline:
                            raise TimeoutError("episode closed before provider request")
                        if self.posts >= self.caps['posts'] or self.used + len(body) > self.caps['combined_wire_bytes']:
                            self.event(index, 'refused', reason='HARD_CAP')
                            client.sendall(b'HTTP/1.1 403 Forbidden\r\nContent-Length: 0\r\nConnection: close\r\n\r\n')
                            return
                        self.used += len(body)
                    def admit(connection):
                        if self.closing or time.monotonic() >= self.deadline:
                            raise TimeoutError("episode closed before POST")
                        self.active.add(connection)
                    provider_index, upstream = gateway.open(body, timeout=max(.001, min(60, self.deadline - time.monotonic())),
                                                            send_lock=self.lock, admit=admit)
                    with self.lock:
                        self.posts += 1
                        self.active.add(upstream)
                    self.event(index, 'forwarded', body_bytes=len(body), body_sha256=core.sha(path), provider_request=provider_index)
                    relay = self
                    class ClientMeter:
                        def sendall(self, data):
                            with relay.lock:
                                if time.monotonic() >= relay.deadline:
                                    raise TimeoutError("episode deadline")
                                if relay.used + len(data) > relay.caps['combined_wire_bytes']:
                                    raise RuntimeError("response byte cap")
                                relay.used += len(data)
                                relay.response_bytes += len(data)
                            client.sendall(data)
                    class DeadlineSocket:
                        def settimeout(self, seconds):
                            upstream.settimeout(max(.001, min(seconds, relay.deadline - time.monotonic())))
                        def makefile(self, *args, **kwargs):
                            return upstream.makefile(*args, **kwargs)
                    response_path = path.with_suffix('.response')
                    response = h.agg.relay_one_model_response(ClientMeter(), DeadlineSocket(), response_path)
                    gateway.budget.finish(status=response['status'], body=response_path.read_bytes())
                    self.event(index, 'response_completed', **response)
                    if response['status'] != 200:
                        raise RuntimeError('upstream HTTP ' + str(response['status']))
                except Exception as exc:
                    if provider_index is not None and gateway.budget.pending is not None:
                        gateway.budget.finish()
                    with self.lock:
                        self.failures.append(dict(request=index, type=type(exc).__name__, message=str(exc)))
                    self.event(index, 'failed', error_type=type(exc).__name__, message=str(exc))
                    if upstream is None:
                        try:
                            client.sendall(b'HTTP/1.1 502 Bad Gateway\r\nContent-Length: 0\r\nConnection: close\r\n\r\n')
                        except OSError:
                            pass
                finally:
                    for connection in (upstream, client):
                        if connection is not None:
                            with self.lock:
                                self.active.discard(connection)
                            connection.close()

        return Relay(root, profile, h, deadline=deadline, caps=caps)


def main():
    import http.client
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    parser.add_argument("--key-stdin", action="store_true")
    args = parser.parse_args()
    key = os.environ.get("BUPT_API_KEY")
    if args.key_stdin:
        print("CREDENTIAL_INPUT_READY", flush=True)
        key = sys.stdin.readline().rstrip("\r\n")
    budget = BatchBudget(args.root)
    connection = None
    try:
        payload = dict(model=MODEL, messages=[dict(role="user", content=
            "Use verification_echo exactly once with value gateway-canary-42.")],
            tools=[dict(type="function", function=dict(name="verification_echo", description="Return the supplied value.",
                parameters=dict(type="object", properties=dict(value=dict(type="string")), required=["value"])))],
            max_tokens=512, temperature=0, stream=True, stream_options=dict(include_usage=True))
        body = json.dumps(payload, separators=(",", ":")).encode()
        (budget.root / "probe.request.json").write_bytes(body)
        index, connection = SchoolGateway(key, budget).open(body)
        response = http.client.HTTPResponse(connection)
        response.begin()
        raw = response.read(4 * 1024**2 + 1)
        if len(raw) > 4 * 1024**2:
            raise RuntimeError("probe response byte cap")
        (budget.root / "probe.response").write_bytes(raw)
        budget.finish(status=response.status, body=raw)
        print(json.dumps(dict(request=index, http_status=response.status, response_bytes=len(raw),
                              usage=usage_from_body(raw), native_tool_fragment=b'"tool_calls"' in raw)))
    finally:
        if budget.pending is not None:
            budget.finish()
        if connection is not None:
            connection.close()
        budget.close()


if __name__ == "__main__":
    main()

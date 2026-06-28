# STRIDE Threat Model — shopping-assistant Agent

> **Generated**: 2026-06-27
> **Scope**: `shopping-assistant` ADK 2.0 agent project
> **Methodology**: STRIDE (Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege)

---

## 1. System Boundaries & Attack Surface

### 1.1 Entry Points

| Entry Point | File | Description |
|---|---|---|
| **LLM Chat Interface** | `app/agent.py` (root_agent) | User queries are routed through the Gemini model to the agent's instruction set and tools. |
| **`redeem_discount_code` Tool** | `app/agent.py:41-64` | Accepts `user_id` and `code` parameters from the LLM and mutates in-memory state. |
| **Agent Runtime HTTP API** | `app/agent_runtime_app.py` | FastAPI-based runtime exposing the agent via HTTP, including a `register_feedback` endpoint. |
| **Feedback Endpoint** | `app/agent_runtime_app.py:44-47` | Accepts arbitrary JSON feedback dictionaries from callers. |

### 1.2 Data Storage Layers

| Layer | Type | Location | Sensitivity |
|---|---|---|---|
| Discount Codes Store | In-memory Python dict | `app/agent.py:35-38` | Business-critical (financial impact) |
| Telemetry / Logs | GCS bucket (optional) | `app/app_utils/telemetry.py` | May contain metadata about prompts |
| Artifact Storage | GCS or In-memory | `app/agent_runtime_app.py:64-68` | Session artifacts |

### 1.3 Configuration & Secrets

| Item | Location | Risk |
|---|---|---|
| Hardcoded API Key | `app/agent.py:72` | **CRITICAL** — `AIzaSyD-mock-key-value-12345` is committed in source code. |
| GCP Project ID | `app/agent.py:27-28` | Loaded via `google.auth.default()` at module import time. |
| Environment Variables | `app/agent.py:28-30` | Project ID and location set as env vars at import. |

---

## 2. STRIDE Evaluation

### 2.1 🔴 Spoofing — Identity Verification

| Finding | Severity | Details |
|---|---|---|
| **No user identity verification** | **HIGH** | The `redeem_discount_code` tool accepts any arbitrary `user_id` string. There is no authentication, session binding, or identity verification. A malicious user could spoof any user ID to redeem codes on behalf of others. |
| **No caller authentication on runtime API** | **MEDIUM** | The `AgentEngineApp` HTTP endpoints do not enforce caller authentication. Any network-reachable client can invoke the agent or submit feedback. |

**Recommendations**:
- Bind `user_id` to an authenticated session token rather than accepting it as a free-text LLM parameter.
- Add authentication middleware (e.g., IAM, OAuth2, API key validation) to the Agent Runtime HTTP layer.

---

### 2.2 🔴 Tampering — Data Integrity

| Finding | Severity | Details |
|---|---|---|
| **Mutable global state** | **HIGH** | `DISCOUNT_CODES` is a mutable global dictionary. Any tool call can permanently alter its state. In a multi-threaded runtime (e.g., uvicorn workers), concurrent requests could cause race conditions, allowing a code to be redeemed multiple times. |
| **No input schema enforcement** | **MEDIUM** | Tool parameters (`user_id`, `code`) are validated with basic string checks but lack Pydantic schema validation as mandated by the project's `CONTEXT.md` secure coding standards. |
| **Unvalidated feedback input** | **MEDIUM** | The `register_feedback` method in `agent_runtime_app.py:44` accepts a raw `dict[str, Any]` and validates it with Pydantic *after* receipt. Malformed payloads could trigger unexpected errors. |

**Recommendations**:
- Replace the mutable global dict with a thread-safe store (e.g., `threading.Lock` or a database).
- Enforce Pydantic `BaseModel` schemas on all tool inputs, not just string validation.
- Validate feedback payloads at the HTTP boundary before passing to business logic.

---

### 2.3 🟡 Repudiation — Audit Logging

| Finding | Severity | Details |
|---|---|---|
| **No transaction logging for discount redemptions** | **HIGH** | When a discount code is redeemed, no audit log is written. There is no record of who redeemed which code, when, or from which session. Disputed transactions cannot be verified. |
| **Telemetry is optional and metadata-only** | **MEDIUM** | The telemetry module (`telemetry.py:31`) defaults to `NO_CONTENT` mode, meaning prompts and responses are not logged. While privacy-conscious, this makes forensic analysis difficult. |
| **Feedback logging exists** | **LOW** | The `register_feedback` path does log to Google Cloud Logging with structured data — this is a positive pattern. |

**Recommendations**:
- Add structured audit logging to `redeem_discount_code` capturing: timestamp, user_id, code, result, and session context.
- Consider a separate audit log sink for financial transactions (discount redemptions).

---

### 2.4 🔴 Information Disclosure — Data Leakage

| Finding | Severity | Details |
|---|---|---|
| **Hardcoded API key in source code** | **CRITICAL** | `api_key="AIzaSyD-mock-key-value-12345"` is committed directly in `agent.py:72`. Even though this is a mock key, this pattern will be replicated with real keys. The Semgrep rule correctly flags this. |
| **User IDs leaked in error messages** | **MEDIUM** | When a code has already been redeemed, the error message at `agent.py:60` returns the original redeemer's `user_id` to the current caller: `"already been redeemed by user '{code_info['user_id']}'"`. This leaks PII to unauthorized parties. |
| **Raw stack traces in production** | **LOW** | No custom error handling wraps the agent runtime. Unhandled exceptions will expose internal file paths, module names, and stack traces to callers. |
| **GCP Project ID exposed** | **LOW** | `project_id` is loaded and set as an environment variable at module level. If error responses include environment details, this could leak infrastructure information. |

**Recommendations**:
- Move the API key to an environment variable or Google Secret Manager. The pre-commit Semgrep hook already blocks this pattern.
- Redact the redeemer's `user_id` from error messages returned to other users.
- Add a global exception handler to the FastAPI runtime to prevent raw stack trace leakage.

---

### 2.5 🟡 Denial of Service — Resource Exhaustion

| Finding | Severity | Details |
|---|---|---|
| **No rate limiting on LLM calls** | **MEDIUM** | The agent has `retry_options` with 3 attempts but no rate limiting. A flood of requests could exhaust the Gemini API quota and incur significant costs. |
| **No rate limiting on tool invocations** | **MEDIUM** | The `redeem_discount_code` tool can be called unlimited times per session. While invalid codes are rejected, the processing overhead is unbounded. |
| **No request size limits** | **LOW** | The Agent Runtime HTTP API does not enforce payload size limits. Extremely large input payloads could consume memory. |
| **In-memory store volatility** | **LOW** | Since `DISCOUNT_CODES` is in-memory, a process restart resets all state — codes become redeemable again. This is a reliability issue more than a DoS vector. |

**Recommendations**:
- Implement rate limiting at the HTTP gateway layer (e.g., Cloud Armor, API Gateway quotas).
- Add per-session tool call limits in the agent configuration.
- Set maximum payload size limits on the FastAPI endpoints.

---

### 2.6 🟡 Elevation of Privilege — Access Control

| Finding | Severity | Details |
|---|---|---|
| **No role-based access control** | **MEDIUM** | All users have identical access to all tools. There is no distinction between a regular customer and an admin. Any user can attempt to redeem any code. |
| **LLM prompt injection risk** | **MEDIUM** | The agent instruction is a static string. A crafted user prompt could attempt to override the instruction (prompt injection) to bypass the requirement for a `user_id` or manipulate the tool call arguments. |
| **PreToolUse hook only gates `run_command`** | **LOW** | The `hooks.json` safety gate intercepts `run_command` but does not gate other sensitive operations. Extensibility of the hook framework is positive but coverage is narrow. |

**Recommendations**:
- Implement role-based tool access (e.g., admin-only tools vs. customer tools).
- Add prompt injection defenses such as input sanitization or a guardrail agent.
- Extend the PreToolUse hook to gate all tool executions, not just `run_command`.

---

## 3. Risk Summary Matrix

| STRIDE Category | Critical | High | Medium | Low | Total |
|---|---|---|---|---|---|
| **Spoofing** | 0 | 1 | 1 | 0 | **2** |
| **Tampering** | 0 | 1 | 2 | 0 | **3** |
| **Repudiation** | 0 | 1 | 1 | 1 | **3** |
| **Information Disclosure** | 1 | 0 | 1 | 2 | **4** |
| **Denial of Service** | 0 | 0 | 2 | 2 | **4** |
| **Elevation of Privilege** | 0 | 0 | 2 | 1 | **3** |
| **Total** | **1** | **3** | **9** | **6** | **19** |

---

## 4. Priority Remediation Roadmap

| Priority | Action | STRIDE | Files Affected |
|---|---|---|---|
| **P0** | Remove hardcoded API key; load from env/Secret Manager | Info Disclosure | `app/agent.py:72` |
| **P0** | Add audit logging for discount code redemptions | Repudiation | `app/agent.py:41-64` |
| **P1** | Add thread-safe locking to `DISCOUNT_CODES` store | Tampering | `app/agent.py:35-38, 58-63` |
| **P1** | Redact redeemer user_id from error messages | Info Disclosure | `app/agent.py:60` |
| **P1** | Bind user identity to authenticated session | Spoofing | `app/agent.py:41` |
| **P2** | Enforce Pydantic schemas on tool inputs | Tampering | `app/agent.py:41` |
| **P2** | Add rate limiting to HTTP endpoints | DoS | `app/agent_runtime_app.py` |
| **P2** | Implement role-based tool access control | EoP | `app/agent.py:67-81` |
| **P3** | Add global exception handler to runtime | Info Disclosure | `app/agent_runtime_app.py` |
| **P3** | Extend PreToolUse hooks to cover all tools | EoP | `.agents/hooks.json` |

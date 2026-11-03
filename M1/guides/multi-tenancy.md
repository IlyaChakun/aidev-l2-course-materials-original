# Multi-tenancy: identity, isolation, tests

> Compiled 02.08.2026. Primary sources opened and checked 01-02.08.2026.
> The code is valid for the official Python SDK `mcp` 2.0.0 and protocol revision `2026-07-28`.

## Why this file

Security answers the question of how a server makes sure it is talking to a legitimate client.
What comes next is what the specification does not cover: which tenant exactly, what that tenant
is allowed to do, how not to hand it someone else's data, and how to prove all of that later in an
audit. **The protocol is transport, not governance:** tenant isolation, permissions and audit are
yours to write.

The technical reason to deal with this now: the 2026-07-28 revision knocked out the load-bearing
structure of tenancy. Sessions are gone, so there is nothing left to bind a tenant to a
connection. This is not an abstraction for architects, it is a code change for everyone who has
already stood up a remote server, because half of such servers are written in a model where
identity lives in the session.

---

## 1. Where identity went

The answer is short and singular: **into the token of the presented request. And nowhere else.**

| Source | Suitable | Why |
|---|---|---|
| Claim of a verified token | **yes, the only one** | The only thing signed by the issuer and verified on this request |
| `Mcp-Session-Id` | no mechanism | Removed by SEP-2567. While it existed, routing went without checking against the identity |
| Request `_meta` | no | The registry of reserved keys has no tenant. You can put in your own namespaced key, but that is client data, and the client is the one who makes it up |
| `clientInfo` | no | "self-reported by the sender and are not verified by the protocol… **SHOULD NOT** rely on them for security decisions" |
| HTTP header | no | "Headers are client-supplied input - fine for a locale or a feature flag, **never an identity**" |
| Tool argument | no | Filled in by the model, that is, by the party being talked into things in the chat |

There are exactly two mandatory keys in `_meta` on every request: the protocol version and the
client capabilities. The tenant does not travel through `_meta` and cannot.

### This is a fix, not a loss

The temptation to say "it used to be safer" is strong here, and it is wrong. SEP-2567 says it
plainly:

> "Session→user pinning was a defense against the session-routing/auth decoupling… and **is not
> needed once every request is independently authenticated**"

And in the same place, what exactly was being fixed:

> "the Python SDK's stateful session manager, for example, routes by `Mcp-Session-Id` alone
> **without verifying that the authenticated identity on the request matches the one that created
> the session**, so a leaked session ID allows hijack by any other authenticated principal"

### Identity is not one field but a triple

`client_id`, `issuer`, `subject`. The official Python SDK warns that a verifier that does not
supply `subject` "**degrades the binding to the client identity alone**, which under URL-based
client IDs is shared by every user of that client software".

Without `sub`, all users of the same client software merge into a single principal, and you are
isolating applications, not people.

**Under whose token the server calls downstream services.** This is a product argument, not only
a security one: if the server goes downstream under a service key, the downstream log shows the
server, not the person. "Who did this" cannot be reconstructed, neither in an incident nor in
compliance.

### The marker of outdated advice

Everything written about multi-tenant MCP before the end of July 2026 recommends binding the
session to the user in the form `<user_id>:<session_id>`. That mechanism no longer exists. **Re-read
any material on this topic older than the end of July for references to sessions.**

---

## 2. The specification legalized tool-level RBAC and put a rake right next to it

Two quotes from the July 28 revision. They sit in different sections, and they are not usually
put side by side.

**The first, from the tools section.** The set of tools

> "**MAY** vary by the authorization presented on the request — for example, returning only the
> tools the caller's granted scopes permit — since credentials are per-request input, not
> connection state"

and right away a prohibition:

> "**MUST NOT** vary per-connection or as a side effect of other requests on the connection"

Read literally: the list is computed from the token of **this** request. The pattern "build a
server per user at connect time and keep it" formally diverges from the requirement, even if the
result looks similar.

**The second, from the caching section.** Responses with `cacheScope: "public"`

> "may be shared between callers **even if the Result is coming from an authenticated
> endpoint**… (i.e. different access tokens can leverage the same cache)"

and next to it: servers "**MUST NOT** rely on `cacheScope` alone to prevent unauthorized access".

### Putting them together: a tool list leak in four moves

Both norms are correct on their own; together they produce a leak surface that did not exist
before the end of July: while the list was the same for everyone, caching it publicly was safe
by construction.

| Move | What happens | Assessment |
|---|---|---|
| 1 | A `tools/list` request arrives | normal; caching hints on it are **mandatory**, you make the caching decision in any case |
| 2 | You filter the list by the caller's permissions | normal, the revision explicitly allowed it |
| 3 | `cacheScope` stays `"public"` — most often the string was simply not touched | this is where it breaks |
| 4 | The filtered list is reused for a different token | leak: no denial, no error, nothing in the logs |

**What exactly leaks.** Not tenant data, but a map of the administrative surface: tool names,
their descriptions and input schemas. The user sees `delete_tenant` or `export_all_billing` in
their client together with instructions on how to use them. They will not be able to call them if
the denial on call is written correctly, but the reconnaissance comes for free.

**Why it is silent.** The response serves the cache instead of the server. Your process never saw
this request: no line in the log, no denial, no metric, no alert fires. It is discovered from a
user complaint or by eye in a config.

**The cache is not necessarily yours.** `cacheScope` travels over the wire and is addressed to
everyone standing between you and the client. The specification on `"public"`: "Any client,
shared gateway, or caching proxy **MAY** store and serve the cached response to any user".

| Place | Value |
|---|---|
| SDK default | `ttlMs: 0`, `cacheScope: "private"` (a safe default, broken by a manual edit) |
| `tools/list` example in the specification itself | `cacheScope: "public"` — it is about an unfiltered list |
| **A permission-filtered `tools/list`** | **must be `"private"`** |
| SDK documentation wording | "never use cacheScope as access control: it is a label, not a lock" |
| Specification requirement | **MUST NOT** rely on `cacheScope` alone to prevent unauthorized access |

Three formulations from the caching section that close the question entirely. **The first, choice
of mode:** `"public"` is appropriate for lists of tools, prompts and resource templates "when they
are **identical for all users**", while `"private"` is "for **filtered list results that vary per
user**". That is, the filtered list is named in the specification in so many words. **The second,
what `private` means:** "Cached responses **MAY** be reused for the same authorization context.
Caches **MUST NOT** be shared across authorization contexts (e.g. a different access token
requires a different cache)". **The third, from Security Considerations, verbatim:** server
implementors "**MUST** apply appropriate per-primitive access controls, and **MUST NOT** rely on
`cacheScope` alone to prevent unauthorized access to primitives".

> **There is no discrepancy within the primary source** (checked on the caching page on
> 03.08.2026). The example with `"public"` shows the mechanics for an unfiltered list, while the
> "Choosing a Cache Scope" section of the same page sends a filtered list straight to `"private"`.
> An early edition of this file called the situation a discrepancy: that is withdrawn.

**Pagination breaks this separately.** The specification: "Servers **MUST** apply the same
`cacheScope` to all response pages for a given list request". If you set `private` on the first
page and forgot it on the second, that is not "partially private", it is a violation of the
requirement and the same leak from the second page.

**The rule that stays with a human:** as soon as the content of a response starts to depend on
the caller's permissions, its mode must become `private`. This has to be checked not at the moment
caching is turned on, but at the moment a filter is added, because it is the second commit that
breaks it, not the first.

### Two corrections that remove false comfort

**Filtering the list is not access control.** The model or a direct API call will reach a tool
that was not in the list it was given. The filter is UX, the protection is the denial on call.

| | `tools/list` filtering | Denial on `tools/call` |
|---|---|---|
| What it is | UX: the user does not see what they should not | Protection: the call does not go through |
| Specification sanction | the set **MAY** vary by the authorization presented on the request | outside the protocol, this is your code |
| What is forbidden | varying per connection, **MUST NOT** | |
| Can be bypassed | by a direct call that skips the list, or by a sufficiently capable model | no |
| Cached | yes, and this is where the `cacheScope` trap is | no |
| Does the SDK do it | no, you write the filter | no |

**By role, it is not only the presence of a tool that varies, but also the schema and the
description.** For an admin the entity field is free, for an ordinary user it is locked to their
scope. The tool is one, the `inputSchema` is different. And the description too: the model decides
whether to call based on the description, so the description must match the caller's real
permissions.

---

## 3. What this looks like in code

Five steps on the official Python SDK, version 2.0.

> Step 4 (`cache_hints` and `cache_scope`) is cross-checked against the SDK documentation. The
> other steps are assembled from documented primitives and were **not run**: check the names of
> the middleware context fields against your SDK version.

### Step 1. The only function in the process that knows who the caller is

```python
from dataclasses import dataclass

from mcp.server.auth.middleware.auth_context import get_access_token
from mcp.server.auth.provider import AccessToken, principal_components

# There is no standard tenant claim in MCP. Use your own namespaced one and record it in the README.
TENANT_CLAIM = "https://tickets.example.com/tenant_id"


@dataclass(frozen=True)
class Principal:
    tenant_id: str
    subject: str
    client_id: str
    issuer: str
    scopes: frozenset[str]


def current_principal() -> Principal:
    """The only source of identity in the process.
    Neither headers, nor _meta, nor tool arguments enter here."""
    token: AccessToken | None = get_access_token()
    if token is None:
        raise PermissionError("unauthenticated")

    client_id, issuer, subject = principal_components(token)
    if subject is None:
        # Without sub the binding degrades to client_id, which under a URL-based client ID
        # is shared by all users of that client software.
        raise PermissionError("token verifier supplied no subject")

    tenant_id = (token.claims or {}).get(TENANT_CLAIM)
    if not isinstance(tenant_id, str) or not tenant_id:
        raise PermissionError("no tenant claim in token")

    return Principal(tenant_id, subject, client_id, str(issuer), frozenset(token.scopes))
```

### Step 2. A "tool → required scopes" table, and it is fail-closed

```python
DENY = frozenset({"__never_granted__"})   # sentinel: an unreachable scope

TOOL_SCOPES: dict[str, frozenset[str]] = {
    "search_tickets": frozenset({"tickets:read"}),
    "create_ticket":  frozenset({"tickets:write"}),
    "delete_ticket":  frozenset({"tickets:admin"}),
}


def scopes_for(tool_name: str) -> frozenset[str]:
    """Fail-closed. A new tool forgotten in the table will not be callable by anyone."""
    return TOOL_SCOPES.get(tool_name, DENY)
```

This matters more than it looks: we will come back to the consequences in the section on tests.

### Step 3. Middleware: denial on call and audit

```python
async def tenant_guard(ctx, call_next):
    """Middleware signature: async (ctx, call_next)."""
    if ctx.method != "tools/call":
        return await call_next(ctx)

    principal = current_principal()
    tool_name = ctx.request.params.name          # check the field name against your SDK version
    if not scopes_for(tool_name) <= principal.scopes:
        await audit(principal, tool_name, verdict="denied")
        raise PermissionError(f"insufficient scope for {tool_name}")
    await audit(principal, tool_name, verdict="allowed")
    return await call_next(ctx)
```

The norm for the response to such a denial is **403 with `error="insufficient_scope"`** and the
full set of required scopes in one response, see the [security guide](security-and-authorization.md).
Advice to return 404 exists, it is useful as hardening against name enumeration, but it is not a
specification norm.

A detail people stumble on at first launch: `token_verifier=` and `auth=` only go as a pair, one
without the other makes the constructor fail with `ValueError` before any request is served. And
separately: authorization is an HTTP concern. Over stdio and in-memory it does not exist at all.

### Step 4. Filter the list and explicitly set its `cache_scope`

```python
async def visible_tools(ctx, call_next):
    """List filtering. The SDK does not do this, it is your code."""
    if ctx.method != "tools/list":
        return await call_next(ctx)

    principal = current_principal()
    result = await call_next(ctx)
    result.tools = [t for t in result.tools if scopes_for(t.name) <= principal.scopes]
    # The list depends on the presented authorization → it is private.
    # The Python attribute is cache_scope; cacheScope is the name on the wire.
    result.cache_scope = "private"
    return result
```

Registration and the server-wide default for cache hints:

```python
from mcp.server.caching import CacheHint

mcp = MCPServer(
    "tickets",
    token_verifier=MyVerifier(),                 # must populate subject and claims
    auth=AuthSettings(
        issuer_url=AnyHttpUrl("https://auth.example.com"),
        resource_server_url=AnyHttpUrl("https://tickets.example.com/mcp"),
        required_scopes=["tickets:read"],        # entry threshold, not a replacement for RBAC
    ),
    cache_hints={"tools/list": CacheHint(ttl_ms=0, scope="private")},
    middleware=[tenant_guard, visible_tools],
)
```

> The trap here was not a missing API but the name: the Python attribute is `cache_scope`,
> `cacheScope` is the name on the wire. A public API for this exists and is documented on a
> separate page.

### Step 5. Data access: there is no bare pool in the module

```python
import contextlib


@contextlib.asynccontextmanager
async def tenant_db(principal: Principal):
    """The only way to get a connection. The pool is private to the module."""
    async with _POOL.acquire() as conn:
        async with conn.transaction():
            # The third argument True = transaction-local. Without it the value outlives
            # the request on a reused connection and the next tenant
            # reads the previous tenant's data.
            await conn.execute(
                "SELECT set_config('app.tenant_id', $1, true)", principal.tenant_id
            )
            yield conn


@mcp.tool()
async def search_tickets(query: str, limit: int = 20) -> list[Ticket]:
    """The scope of visibility is determined by the token, not by arguments."""
    principal = current_principal()
    async with tenant_db(principal) as conn:
        # tenant_id is not written by hand in SQL: the RLS policy supplies it.
        rows = await conn.fetch(
            "SELECT name, status FROM tickets WHERE name ILIKE $1 LIMIT $2",
            f"%{query}%", limit,
        )
    return [Ticket(**dict(r)) for r in rows]
```

```sql
ALTER TABLE tickets ENABLE ROW LEVEL SECURITY;
-- FORCE is mandatory: otherwise the table owner bypasses its own policy,
-- and if the application connects under the owner role, there is no isolation.
ALTER TABLE tickets FORCE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON tickets
    USING       (tenant_id = current_setting('app.tenant_id', true))
    WITH CHECK  (tenant_id = current_setting('app.tenant_id', true));
-- USING cuts reads, WITH CHECK prevents writing a row into another tenant.
```

You cannot forget `WHERE tenant_id`, because there is nowhere to write it by hand.

### The same RBAC on standalone `fastmcp` 3.x

> API per the documentation, snapshot of 01.08.2026, the 3.4.5 line. The sessionless revision is
> carried by the beta `4.0.0b1`. Whether the middleware contract survived in the 4.0 line is not
> confirmed: check before porting.

```python
from fastmcp import FastMCP
from fastmcp.server.middleware import Middleware, MiddlewareContext

mcp = FastMCP("tickets")


class TenantRBAC(Middleware):
    """One class covers both levels: list filtering and denial on call."""

    async def on_list_tools(self, context: MiddlewareContext, call_next):
        principal = current_principal()
        tools = await call_next(context)
        return [t for t in tools if scopes_for(t.name) <= principal.scopes]

    async def on_call_tool(self, context: MiddlewareContext, call_next):
        principal = current_principal()
        tool_name = context.message.name
        # A hard denial, not a filter: a direct call that skips tools/list arrives here too.
        if not scopes_for(tool_name) <= principal.scopes:
            await audit(principal, tool_name, verdict="denied")
            raise ToolError(f"not permitted: {tool_name}")
        await audit(principal, tool_name, verdict="allowed")
        return await call_next(context)


mcp.add_middleware(TenantRBAC())
```

A formulation from a public write-up of a production gateway that captures this structure:
"`tool_name not in allowed` is a hard rejection, not a filter".

---

## 4. Isolation: three layers and five places where it leaks besides SQL

**Layer one.** The tenant is taken from the verified token, never from tool arguments. If the
server accepts `tenant_id` as a parameter, an agent that has been talked into it in the chat will
pass someone else's, and the server will return someone else's data.

**Layer two.** A single point of data access, step 5 above.

**Layer three.** Row-level security in the database engine. The point is exactly one: even if
there is a bug in the code and the `WHERE` is forgotten, the engine will not return someone else's
row. Two details on which this breaks for everyone: `FORCE ROW LEVEL SECURITY` (otherwise the
table owner bypasses its own policy, and applications often connect under the owner role) and the
transaction-local third argument of `set_config`.

No layer replaces another.

### Five surfaces where the tenant filter is forgotten more often than in SQL

| Surface | How it leaks | What to do |
|---|---|---|
| Result cache | The key is built from arguments without the tenant | Tenant prefix in the key, audit for gaps |
| Vector store | One index, tenant filter only on the query | An index or namespace per tenant, enforced by the store, not by the application |
| Telemetry | `tenant_id` stripped as high-cardinality | Tenant as a first-class dimension with the same access rights as the data |
| Backups and exports | The filter is applied in the interface, not in the generator | Filter in the export generator |
| Environment variables | Tenant credentials loaded into env at startup | Fetch from a vault per call, short-lived context, clear afterwards |

The fifth is the most dangerous, because it looks like correct architecture. The source's
wording, verbatim: "This architecture is comfortable because it matches twelve-factor app
conventions, and **it is wrong for multi-tenant MCP**". Any tool that reads the environment will
pull out someone else's secret.

The list is incomplete, and here is an honest sixth place from practice: **a signed file link
handed to the model lives longer than the permission check that issued it.** This is visible on
any platform where tenants are customers with their own file libraries and their own link
lifetimes.

### Anti-patterns in one list

| Anti-pattern | What breaks |
|---|---|
| Tenant from tool arguments | The agent passed someone else's `tenant_id`, the server returned someone else's data |
| Tenant from a header or `_meta` | Client input, made up by the caller |
| Authorization on `Mcp-Session-Id` | The mechanism no longer exists. While it did, routing went without checking against the identity |
| A verifier that does not populate `subject` | The binding degrades to the client software |
| Tenant credentials in environment variables | One bug away from a cross-tenant leak |
| List filtering instead of denial on call | A direct call that skips `tools/list` goes through |
| A cache without the tenant in the key | One tenant's result goes to another |
| `cacheScope: "public"` on a response that depends on permissions | The cache is shared across authorization contexts |
| One vector index with a filter only on the query | A bug or misconfig returns cross-tenant chunks |
| `tenant_id` cut from telemetry as high-cardinality | Errors with tenant data in a shared dashboard |
| Tenant model drift (started with the organization, added the user) | "Retrofitting is painful and usually **incomplete**" |
| Tenant isolation by "prompt" | In agentic systems everyone technically has access |

---

## 5. How to make sure this cannot be forgotten

Discipline does not work. Three mechanisms work together, and all three are verifiable by a test.

> The tests below are a synthesis for the code above, not a quotation. There is no working example
> of MCP server isolation tests in public sources: there are requirements (provision two test
> tenants, a red-team check that other tenants' data is unreachable, a check for escalation from
> read-only to admin), but no framework.

```python
import pytest

PAIRS = [("acme", "globex"), ("globex", "acme")]


@pytest.mark.parametrize("caller,victim", PAIRS)
@pytest.mark.parametrize("tool", sorted(TOOL_SCOPES))
async def test_no_cross_tenant_access(caller, victim, tool, seeded):
    """Matrix: every tool × every pair of tenants."""
    client = client_for(caller)                     # token with tenant_id=caller and full scopes
    result = await client.call_tool(tool, {"id": seeded[victim]})

    assert result.isError
    assert seeded[victim] not in text_of(result)    # the other tenant's id is not echoed back


async def test_every_tool_has_scope_declaration(admin_client):
    """Catches a tool added to the code and forgotten in the permissions table.
    Without this test, fail-closed will silently take a new tool down in prod."""
    names = {t.name for t in await admin_client.list_tools()}
    assert names <= set(TOOL_SCOPES), f"without scope: {sorted(names - set(TOOL_SCOPES))}"


async def test_list_tools_varies_by_token(reader_client, admin_client):
    reader = {t.name for t in await reader_client.list_tools()}
    admin = {t.name for t in await admin_client.list_tools()}
    assert reader < admin


async def test_pooled_connection_does_not_leak_tenant(pool):
    """set_config without transaction-local outlives the request. We check that it does not."""
    async with tenant_db(principal_of("acme")):
        pass
    async with pool.acquire() as conn:
        assert await conn.fetchval("SELECT current_setting('app.tenant_id', true)") is None
```

The most useful one here is the second. It catches what review does not catch: a tool added to
the code and forgotten in the permissions table. Without it, fail-closed will silently take a new
tool down in prod, and a week after the merge at that.

The three mechanisms together are the answer to the question "how do we make sure the filter
cannot be forgotten": there is no bare pool (nowhere to forget `WHERE`), RLS catches an
application miss at the engine, and the test catches a tool without declared permissions before
release.

**A process on top of the tests:** a review of the tool set every quarter, plus within
forty-eight hours after adding any new one. A tool that is not registered cannot be exploited.

### Least-privilege

- A read token does not write. One tenant's token does not reach another. No token has "all
  tools" by default.
- The `readOnlyHint` annotation for reading tools, narrow scopes instead of omnibus permissions.
- Remove what is unused.
- Separate data-access roles from general roles, so that the set of identities (people and agents)
  that reach sensitive data stays minimal.
- The question when designing every grant: what is the blast radius if this role is compromised.
- Servers with shell access or credential access are a separate class: a wildcard grant is
  unacceptable for them.

---

## 6. Four ways to serve different consumers with one server

In order of increasing coupling to your code. All four are from public sources, all four are
implemented, none has been fact-checked.

1. **Policy per key, same URL.** Permissions are bound to the key at issuance and applied at the
   gateway regardless of what the agent's bearer claims. Plus: it does not touch the IdP. Minus:
   permissions live separately from the corporate role model.
2. **Roles and grants in the gateway.** Three primitives: server, role, grant. Wildcard only for
   admins: with an explicit list, a new upstream tool does not appear for anyone until it is added,
   and that review step is exactly the point where excess is caught. Default for a new server:
   zero grants.
3. **A live per-user list.** The broker pulls `tools/list` live with the caller's headers instead
   of from a service account's cache. Every list is an additional round-trip: enable it only where
   the upstream really returns different sets.
4. **The role is resolved in the server itself.** One query into the roles table, then tool
   registration by role. "Same endpoint. Same connector. Different manifest." Fail-closed on any
   resolution error.

**An enterprise layer on top of any of them:** a control plane between clients and servers,
integration with the corporate IdP, token brokering (raw OAuth tokens never leave the control
plane), server registries tied to IdP groups. The operational win that this is done for: removal
from an IdP group automatically ends access. Revocation stops being a separate procedure.

---

## 7. What remains open

Three honest holes that nobody has closed yet.

**There is no standard claim for a tenant.** In circulation are `tenant_id`, `org_id`, vendor ones
like `custom:tenantId`, and URNs. This is not a dispute between sources, it is a hole in the
standard: portability across IdPs is on you. Choose your own namespaced claim and record it in the
server's README.

**Per-tenant limits in the sessionless model.** All the schemes that could be found were
described before July and operate on sessions or connections. How to count windows over the triple
`issuer`, `subject`, `tenant` without a session, there are no sources. One thing can be said
firmly: keep counters in a shared store, because there are several instances and the server is
stateless.

**Where enforcement sits.** One school: "The answer that scales is a control plane. **Not auth in
every MCP server.**" Another: "Every registered tool is a separate authorization boundary. Treat it
like one". In practice this is defence in depth, not a choice. The difference is who owns the
policy: the platform team or the service team.

Three more disputes you will meet:

- **Tenant in the URL versus tenant in the token.** One school makes the URL itself the boundary:
  a unique server address for every connected account, with a secret in the path. Another is
  softer: the subdomain carries the tenant, but the decision is made from the claim, that is, the
  URL is routing and the token is authorization. The objection on the merits: a secret in the URL
  path is a bearer token that leaks into the referrer, proxy logs and browser history. Both
  schemes are in prod.
- **Where to get the role from: claims or the database.** One reference implementation demands
  exactly the opposite of what the others do: "Resolve from the database, not JWT claims. JWTs are
  issued at login time and carry whatever was true then". The dispute is real, and it is about the
  delay in revoking permissions.
- **How often to re-read permissions.** Three answers from three production implementations: a
  120-second cache; a query to the role store on every `tools/list`; no caching at all and honest
  documentation of the added latency. The spread of revocation delay is from zero to two minutes.
  Nobody provides measurements of the cost.

---

## 8. Versions the code is valid for

| Package | Version | What matters here |
|---|---|---|
| `mcp` (PyPI) | **2.0.0**, 28.07.2026 | `FastMCP` renamed to `MCPServer`. `token_verifier=` and `auth=` only as a pair |
| `fastmcp` (standalone) | **3.4.5** (27.07), beta `4.0.0b1` (28.07) | The sessionless revision is carried by the beta. The middleware contract in the 4.0 line is not confirmed |
| TypeScript SDK v2 | 2.0.0, nine packages | The old `@modelcontextprotocol/sdk` stayed at 1.30.0 |

SDK documentation pages are not dated at all. The whole of step 4 and the label/lock quote rest on
one live page: check it before building this into code.

Full list of primary sources with links and dates: [reading-list.md](../reading-list.md).

---

## Appendix A. How not to and how to

A summary of the whole file in pairs. On the left is what occurs most often, on the right what to
do instead. The "why" column answers the question "what exactly will break", not "this is more
correct".

**Identity and tenant**

| How not to | How to | Why |
|---|---|---|
| `tenant_id` arrives as a tool argument | `tenant_id` only from the claim of the verified token | The argument is filled in by the model, and the model is talked into things in the chat |
| Tenant from an HTTP header or `_meta` | The same: the claim of this request's token | Client input, the client makes it up |
| Binding to `Mcp-Session-Id` | The triple `client_id`, `issuer`, `subject` | The mechanism has not existed since 28.07.2026 |
| A decision based on `clientInfo` | Do not use it in security decisions | "SHOULD NOT rely on them for security decisions" |
| A verifier without `subject` | Fail if `subject` is empty | Otherwise you isolate applications, not people |
| The principal is computed at connect time and cached | Computed on every request | The set **MUST NOT** vary per-connection; behind a load balancer the instance is different |
| Every module fetches the tenant on its own | One `current_principal()` function per process | Otherwise there are as many identity sources as there are places |

**Permissions and the tool list**

| How not to | How to | Why |
|---|---|---|
| A permission "on the server" | A permission on the tool: `read_record` ≠ `delete_record` | A server is a unit of deployment, not a unit of risk |
| Absence from the permissions table = allowed | Fail-closed: an unknown tool gets an unreachable scope | Otherwise a new tool ships to prod open |
| A `tools/list` filter as protection | The filter is UX, the protection is the denial on `tools/call` | A direct call that skips the list goes through |
| One tool description for all roles | Schema and description vary by the caller's permissions | The model decides about the call from the description |
| The denial leaks another tenant's identifier in the text | 403 `insufficient_scope`, no other tenants' identifiers | An error message is also a leak channel |

**Cache**

| How not to | How to | Why |
|---|---|---|
| `cacheScope: "public"` on a filtered list | `"private"` | Specification: `private` for "filtered list results that vary per user" |
| `private` on the first page, forgotten on the second | One `cacheScope` on all pages of one list | **MUST** apply the same `cacheScope` to all response pages |
| "The cache is mine, I control it" | Assume any node along the path caches | "Any client, shared gateway, or caching proxy **MAY** store and serve" |
| `cacheScope` as access control | Access control separately, on call | **MUST NOT** rely on `cacheScope` alone |

**Data and isolation**

| How not to | How to | Why |
|---|---|---|
| A bare connection pool in the module | A single access point that injects the tenant | There is nowhere to forget `WHERE` if queries only go through it |
| Only a filter in code | Plus row isolation in the database engine | Insurance against a bug in the single point itself |
| An isolation policy without enforcement | `FORCE ROW LEVEL SECURITY` | The table owner bypasses its own policy |
| The tenant parameter is set on the connection | Set it transactionally | The value outlives the request on a pooled connection |
| Cache key built from arguments | Tenant prefix in the key | One tenant's result arrives at another |
| One vector index, filter on the query | An index or namespace per tenant | A bug silently returns cross-tenant fragments |
| `tenant_id` cut from telemetry | Tenant as a first-class dimension | Otherwise an incident for a customer is not visible in the dashboard |
| The export filter sits in the interface | Filter in the export generator | The interface is bypassed by calling the generator directly |
| Tenant credentials in environment variables | Fetch from the store per call, clear afterwards | Any tool that reads env will pull out someone else's secret |
| A signed link with a long lifetime | A short lifetime; treat the link as granted access | The link lives longer than the permission check that issued it |
| Isolation by "prompt" | Isolation by code on three layers | In agentic systems everyone technically has access |

---

## Appendix B. Pre-release review checklist

Go through the whole server. [common mistake] marks the items people stumble on most often.

**Identity**

- [ ] there is exactly one function in the process that returns the principal, and all paths go through it;
- [ ] it fails if there is no token, no `subject` or no tenant claim;
- [ ] [common mistake] the name of the tenant claim is recorded in the README next to an example token;
- [ ] a `grep` over the code finds no reads of the tenant from arguments, headers or `_meta`;
- [ ] [common mistake] under whose token the server calls downstream services is named explicitly and consciously.

**Permissions**

- [ ] a "tool → required scopes" table exists and is keyed by tool name;
- [ ] its default is denial, not permission;
- [ ] the denial on call returns 403 and contains no other tenants' identifiers;
- [ ] [common mistake] every tool from the admin list is present in the permissions table;
- [ ] scope names describe an operation on an entity, not the server.

**List and cache**

- [ ] `tools/list` is filtered by the permissions of this request, not by connection state;
- [ ] [common mistake] the filtered response has `cacheScope: "private"`;
- [ ] [common mistake] the same `cacheScope` is set on all pages of a paginated list;
- [ ] tool descriptions and schemas match the caller's permissions;
- [ ] there are no places in the code where filtering is treated as protection.

**Data**

- [ ] there is no bare connection pool in the modules;
- [ ] row isolation is enabled and enforced, the tenant parameter is set transactionally;
- [ ] [common mistake] the five surfaces besides SQL have been checked: cache, vector, telemetry, exports, environment;
- [ ] signed links are short-lived, the lifetime is aligned with the lifetime of the permission.

**Tests and process**

- [ ] a "tool × two tenants" matrix with a check of the error text;
- [ ] a completeness test for the permissions table;
- [ ] a "the reader's list is strictly smaller than the admin's list" test;
- [ ] [common mistake] a "a pooled connection does not remember the tenant after leaving the context" test;
- [ ] a review of the tool set every quarter and within 48 hours after a new one.

---

## Appendix C. How to hand this file to an agent

The guide is written so that it can be put into an agent's context to get multi-tenancy designed
by rules rather than by taste.

**Design prompt:**

```
Read multi-tenancy.md in full. Design multi-tenancy for an MCP server for <domain>.

Work by the guide:
1. Name what counts as a tenant in this product (organization, user, project,
   environment) and what we pay for this choice. Model drift is hard to fix — justify it once.
2. Describe where the tenant comes from, per section 1. The only source is the claim of this
   request's token. Give the principal-retrieval function for my stack.
3. Build a "tool → required scopes" table (section 3, step 2), fail-closed.
   Show separately how list filtering differs from denial on call.
4. Set the caching modes per section 2, including pagination.
5. Lay isolation out across three layers (section 4) and go through the five surfaces besides SQL.
6. Give the four isolation tests from section 5 for my test framework.
7. Run the result against the checklist in appendix B and show the unclosed items with the reason.

Rules: do not lower normative levels — MUST stays MUST, SHOULD stays SHOULD.
Do not invent numbers and thresholds: if the guide has no number, say so directly. Everything
written about multi-tenant MCP before the end of July 2026 relies on sessions and is outdated.
```

**Prompt for reviewing an existing server:**

```
Read multi-tenancy.md. Run my server against appendix B and show the violations
with quotes from my code. For each violation give a row from appendix A: how it is now
and how it should be. Start with the three most expensive: the tenant source, the fail-closed
permissions table, cacheScope on the filtered list.
```

**Prompt for migrating from the session model:**

```
Read multi-tenancy.md, section 1. My server is written around Mcp-Session-Id.
Find all the places where identity is taken from the session or from connection state,
and propose a migration order: what to fix first, what can be left for later,
what will break on a load balancer with several instances.
```

---

## Links mentioned in the session

Collected from the screens of this block: what I relied on out loud and what is worth opening yourself. The links are live as of the date the materials were compiled, SDK documentation pages are not dated and change without notice.

| What it is | Link |
|---|---|
| Base protocol and the registry of _meta keys | [https://modelcontextprotocol.io/specification/2026-07-28/basic](https://modelcontextprotocol.io/specification/2026-07-28/basic) |
| Python SDK: authorization | [https://py.sdk.modelcontextprotocol.io/v2/run/authorization/](https://py.sdk.modelcontextprotocol.io/v2/run/authorization/) |
| Python SDK: middleware | [https://py.sdk.modelcontextprotocol.io/v2/advanced/middleware/](https://py.sdk.modelcontextprotocol.io/v2/advanced/middleware/) |
| PostgreSQL: Row Security Policies | [https://www.postgresql.org/docs/current/ddl-rowsecurity.html](https://www.postgresql.org/docs/current/ddl-rowsecurity.html) |
| Python SDK: handler context and identity | [https://py.sdk.modelcontextprotocol.io/v2/handlers/context/](https://py.sdk.modelcontextprotocol.io/v2/handlers/context/) |
| Caching and cacheScope | [https://modelcontextprotocol.io/specification/2026-07-28/server/utilities/caching](https://modelcontextprotocol.io/specification/2026-07-28/server/utilities/caching) |
| Tools and the rule about tools/list | [https://modelcontextprotocol.io/specification/2026-07-28/server/tools](https://modelcontextprotocol.io/specification/2026-07-28/server/tools) |
| SEP-2567 "Sessionless MCP" | [https://github.com/modelcontextprotocol/modelcontextprotocol](https://github.com/modelcontextprotocol/modelcontextprotocol) |
| Python SDK documentation, multi-round-trip | [https://py.sdk.modelcontextprotocol.io/v2/handlers/multi-round-trip/](https://py.sdk.modelcontextprotocol.io/v2/handlers/multi-round-trip/) |
| MCP specification 2026-07-28, authorization | [https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization) |

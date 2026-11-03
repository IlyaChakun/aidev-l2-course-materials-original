# What to read for the module

> All links were opened and checked on **02.08.2026**, and the specification URLs were rechecked on **03.08.2026**.
> All sources are public. Three domains (`nsa.gov`, `medium.com`, `ai.meta.com`) block automated
> requests and were opened by hand from a browser: this is marked in the corresponding rows.
>
> Each row has one date or two. The **publication date** says how fresh the source is. The **check
> date** says when the link was last seen with human eyes. In a domain where the specification
> came out last week and half the tools are younger than a month, a list without the second date
> goes stale silently.
>
> Specification pages are dated by revision. **SDK and vendor pages are not dated at all:**
> their content and address can change between this check and your reading.

---

## 1. Specification: the firmest layer

Read it word for word; it is versioned and dated by revision. If someone else's text diverges from the
specification, the primary source is right.

| What | Address | Why read it |
|---|---|---|
| Versioning | `modelcontextprotocol.io/docs/2026-07-28/learn/versioning` | One page that shows the current revision and the rules of the deprecation window. **The unnumbered `/specification/versioning` redirects here permanently** |
| Changelog of revision 2026-07-28 | `/specification/2026-07-28/changelog` | The full list of changes with SEP numbers. The fastest way to understand what exactly broke for you |
| Registry of deprecated features | `/specification/2026-07-28/deprecated` | What is marked Deprecated, from what date, and when it becomes eligible for removal. **The normative source of status, unlike the blog** |
| Lifecycle policy | `/community/feature-lifecycle` | A ready-made model for your own server's policy |
| Base Protocol | `/specification/2026-07-28/basic/index` | "MCP is a stateless protocol", the error code table, the `_meta` key registry, the rule on mandatory envelope keys |
| Discovery | `/specification/2026-07-28/server/discover` | "Servers MUST implement it" and the full response shape, including the `instructions` field |
| Tools | `/specification/2026-07-28/server/tools` | Naming rules, `x-mcp-header`, annotations as untrusted, the split between Protocol Errors and Tool Execution Errors, `tools/list` varying by authorization |
| Multi Round-Trip Requests | `/specification/2026-07-28/basic/patterns/mrtr` | The retry-request mechanics and three MUSTs on `requestState` integrity |
| Caching | `/specification/2026-07-28/server/utilities/caching` | `ttlMs`, `cacheScope` and the section on leakage between authorization contexts |
| Versioning and Compatibility | `/specification/2026-07-28/basic/versioning` | The era compatibility matrix and the wording on an old client having no fall-forward |
| Streamable HTTP | `/specification/2026-07-28/basic/transports/streamable-http` | Three required headers on POST and the behavior with old traffic |
| Security Best Practices | `/docs/2026-07-28/tutorials/security/security_best_practices` | Eleven sections, including State Handle Hijacking, Mix-Up Attacks, SSRF and Scope Minimization. **The page moved from `/specification/…/basic/`: the old path still redirects here, and links without a revision number lead to the previous version with the section on sessions** |
| Authorization (four pages) | `/specification/2026-07-28/basic/authorization` plus `/authorization-server-discovery`, `/client-registration`, `/security-considerations` | The section is split into four pages in this revision. Links to the old single-page anchor break |
| Elicitation | `/specification/2026-07-28/client/elicitation` | The ban on form mode for secrets and the paired requirement for URL mode. **The address changed within a week** |
| Protocol schema, source | `raw.githubusercontent.com/modelcontextprotocol/modelcontextprotocol/main/schema/2026-07-28/schema.ts` | `ToolAnnotations` defaults and negative results (no `version` field in `Tool`). **Check against the schema, not the site** |
| SEP-2567, sessionless MCP | the `modelcontextprotocol` repository → `docs/seps/2567-sessionless-mcp.mdx` | "Possession is not authorization" and an analysis of exactly which defect was fixed by removing sessions |
| Revision release blog post | `blog.modelcontextprotocol.io/posts/2026-07-28/` | An overview from the maintainers. **Useful, but check a feature's status in the registry, not here** |

> A useful trick: the specification site serves markdown with the `.md` suffix on any path
> (`/specification/2026-07-28/changelog.md`). The full list of the revision's pages is in `/llms.txt`.

---

## 2. SDK documentation

Not dated. Re-read it before building it into code.

| What | Address | Why read it |
|---|---|---|
| Python SDK, authorization | `py.sdk.modelcontextprotocol.io/v2/run/authorization/` | `TokenVerifier`, `AuthSettings` and the rule "only as a pair, otherwise `ValueError` before the first request" |
| Python SDK, OpenTelemetry | `py.sdk.modelcontextprotocol.io/run/opentelemetry/` | "Your server is already traced. You don't have to add anything". Two install commands and how to turn it off |
| Python SDK, middleware | `py.sdk.modelcontextprotocol.io/v2/advanced/middleware/` | The `async (ctx, call_next)` signature and the interception points |
| Python SDK, caching | `py.sdk.modelcontextprotocol.io/client/caching/` | The public API for `cache_scope` and the wording "never use cacheScope as access control: it is a label, not a lock" |
| Python SDK, provider source | `github.com/modelcontextprotocol/python-sdk` → `src/mcp/server/auth/provider.py` | The `AccessToken` model and `principal_components`: where the `client_id`, `issuer`, `subject` triple comes from |
| TypeScript SDK v2, migration | `ts.sdk.modelcontextprotocol.io/v2/migration/support-2026-07-28.html` | The package fork and the warning that authorization requirements are an SDK-level opt-in |
| FastMCP, middleware | `gofastmcp.com/servers/middleware` | The alternative middleware contract for the standalone line |
| PostgreSQL, Row Security Policies | `postgresql.org/docs/current/ddl-rowsecurity.html` | On `FORCE ROW LEVEL SECURITY` and the table owner bypassing the policy |

---

## 3. Telemetry conventions: the address changed

This is the first thing to open if you are building a dashboard.

| Address | What it returns as of 02.08.2026 |
|---|---|
| `opentelemetry.io/docs/specs/semconv/gen-ai/mcp/` | a stub: "GenAI semantic conventions have moved… no longer maintained in this repository". **This is the exact address the MCP specification links to** |
| `raw.githubusercontent.com/open-telemetry/semantic-conventions/main/docs/gen-ai/mcp.md` | the same stub. The move was done in PR #3696 of 05.05.2026 |
| **`raw.githubusercontent.com/open-telemetry/semantic-conventions-genai/main/docs/gen-ai/mcp.md`** | the full document. **The working address** |

Models nearby, in the same `semantic-conventions-genai` repository:

- `main/model/mcp/metrics.yaml`: four histograms, two of them per session. **There are no bucket
  boundaries in the YAML**, only in the text;
- `main/model/mcp/spans.yaml`: `mcp.client` and `mcp.server`, the enrichment rule, opt-in attributes;
- `main/model/mcp/registry.yaml`: the `mcp.method.name` enum of 25 values.

> Warning: **This document currently has no version.** Not a single release has been published in the `semantic-conventions-genai`
> repository; the conventions exist only as the main branch. They can be cited only
> with an access date, and there is nothing to pin to. Any edit lands instantly and without notice.

Open questions worth following (the conventions repository): issue #314 (what the server session
duration metric actually measures, opened 27.01.2026, last activity 16.06.2026,
no answer), issue #313 (`error.type` versus
`rpc.response.status_code`), PR #404 to issue #389 (stop marking client problems as errors
on the server). **If #404 is merged, the alerting logic on span status will change.**

---

## 4. Research and measurements with open methodology

Usable under one condition: the snapshot date, the denominator and the detection method are named.

| What | Address | Date | Why read it |
|---|---|---|---|
| **"Scaling Enterprise Agent Routing: Degradation, Diagnosis, and Recovery"**, Kellen Gillespie, Robyn Perry | `arxiv.org/abs/2606.17519` | 16.06.2026 | The only public controlled routing degradation curve. A catalog of 110 agents and 584 tools, three frontier models. This is where the split into retrieval gap and confusion gap comes from |
| **"Terminal Agents Suffice for Enterprise Automation"**, ServiceNow Research | `arxiv.org/abs/2604.00073` | 31.03.2026 | Why MCP loses where it loses: not the protocol, but field coverage. 729 tasks on three live platforms, programmatic verification |
| **"MCP vs. CLI: Does an AI Agent's Tool Interface Still Matter?"**, Scale Labs | `labs.scale.com/blog/mcp-vs-cli` | published 31.07.2026, snapshot 08.07.2026 | The only correct control in the group: the CLI is generated from the same MCP schemas. The conclusion about the harness and the cost reversal. **The page header shows the snapshot date, not the publication date:** the material is fresher than it looks |
| **"MCP vs CLI: Benchmarking AI Agent Cost & Reliability"** plus the benchmark repository | `scalekit.com/blog/mcp-vs-cli-use` · `github.com/scalekit-inc/mcp-vs-cli-benchmark` | 27.05.2026 | The primary source of the "CLI is 17 times cheaper" figure. **Read together with the repository:** it says "Both modalities achieve 100% task completion", while the blog says "MCP 72%". Also, `METHODOLOGY.md` there states 30 runs per task, while 5 were actually done. The best exercise in the module for cross-checking someone else's measurement: the discrepancy is caught not in the numbers but in two files of the same repository |
| **"From REST to MCP"**, Mastouri et al. | `arxiv.org/abs/2507.16044` | 21.07.2025, v4 06.04.2026 | A corpus of official servers: 80 of 87 REST-backed repositories are bare wrappers |
| **MCPTox**, AAAI 2026 | `ojs.aaai.org/index.php/AAAI/article/view/40895` | 14.03.2026 | 45 live servers, 353 genuine tools, 1,348 malicious cases: an attack through the tool description |

---

## 5. Measurement tools with open code and a dataset

The best class of sources for ecosystem numbers: the run is reproducible, the dataset is available,
the definitions are printed.

| What | Address | Why read it |
|---|---|---|
| **ContextTax** (MIT) | `github.com/PavelTkachenk0/ContextTax` | Measure the context cost of your stack with one command. Ground truth via `count_tokens`, plus a measurement of the keyless proxy's 16–43% discrepancy |
| **RoninForge / state-of-mcp** (tool MIT, dataset CC BY) | `github.com/RoninForge/state-of-mcp` | A census of the official registry with a **printed definition** of a dead server. This is where spec-readiness comes from: 4,937 reachable, 0 ready, 81.2% counterweight |
| **mcp-spec-check** | `github.com/Roee-Tsur/mcp-spec-check` | An independent check of the same thing with a different tool and ten days earlier: 4,356 servers, one ready. Keep it next to the previous row |
| **MCP Queen, State of the MCP Ecosystem** | `mcpqueen.com/reports/state-of-mcp-2026-07` | 43,320 probes across 9,326 remote servers, a deterministic rubric, a CSV dataset. This is where 17.2% dead remotes comes from |
| **The MCP Census** | `mcpcensus.pages.dev/report` | A registry crawl plus GitHub GraphQL. "Unknown stays unknown": an honest method of handling uncertainty |
| **PolicyLayer, State of MCP** (dataset CC BY) | `policylayer.com/research/state-of-mcp` | 32,820 servers and 517,973 tools, snapshot 01.07.2026. This is where 28.1% / 43% / 96.4% about destructive tools comes from |
| **"52% of MCP Servers Are Dead"**, Tijo Gaucher | `rapidclaw.dev/blog/mcp-servers-dead-what-it-means-2026` | The second half of the twelvefold gap: a nine-point rubric, a portrait of the median server (6 commits, 1 maintainer, 0 tests). A vendor source, they sell managed hosting |

---

## 6. Security

| What | Address | Why read it |
|---|---|---|
| **NVD, vulnerability records** | `nvd.nist.gov/vuln/detail/<CVE-ID>` | Check the numbers one by one. The score is assigned by two parties and they diverge: keep the range, not a single number |
| **MITRE registry, CVE Services API** | `cveawg.mitre.org/api/cve/<CVE-ID>` | **The only channel that catches a nonexistent number.** For a missing ID, NVD returns an empty result, while MITRE returns an explicit `CVE_RECORD_DNE` |
| **NVD API 2.0, search by publication window** | `services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch=Model+Context+Protocol` | The channel for finding recent items. **The list of MCP CVEs goes stale within a week** |
| GitHub Security Advisories | `github.com/advisories?query=modelcontextprotocol` | The same from the other side, plus fix dates |
| **Meta, "Agents Rule of Two"** | `ai.meta.com/blog/practical-ai-agent-security/` | Three properties, of which an agent should have no more than two: untrusted input, access to sensitive data, a channel outward. The domain blocks non-browser clients (400 on any automated request), opens only by hand from a browser |
| **Anthropic, "How we contain Claude"** | `anthropic.com/engineering/how-we-contain-claude` | "Our telemetry showed users approved roughly 93% of permission prompts". A counterargument to the advice "confirm everything" |
| **NSA, press release for the MCP recommendations set** | `nsa.gov/Press-Room/Press-Releases-Statements/Press-Release-View/Article/4496698/` | Nine items. **The word "requirements" does not fit:** verbatim "practical recommendations", "adopters are advised to proceed with caution". **There is no compliance deadline there.** The domain returns 403 on a direct request, readable via a reader |
| **OWASP MCP Top 10** | `owasp.org/www-project-mcp-top-10/` | A catalog of risks. Codes are written with the `:2025` suffix. Status "Phase 3, Beta Release and Pilot Testing, we are here right now", October 2026 is Phase 5, not the first release. The page contradicts itself on the name of the sixth item |
| **Smokescreen**, egress proxy | `github.com/stripe/smokescreen` | A tool named by name in the specification. The specification asks you **not to write your own IP parser** |

---

## 7. Engineering write-ups and vendor blogs

A vendor measures itself, and the method is almost never disclosed. Read as a position, not as a measurement.

| What | Address | Date | Why read it |
|---|---|---|---|
| **"Most MCP servers don't need to exist. Your case might be an exception."**, Evil Martians | `evilmartians.com/chronicles/most-mcp-servers-dont-need-to-exist-your-case-might-be-an-exception` | 30.06.2026 | The deciding signal for building your own server, three contracts (API, CLI, MCP) and the boundary "encapsulate operations, not workflows" |
| **Anthropic, "Advanced tool use"** | `anthropic.com/engineering/advanced-tool-use` | 24.11.2025 | An estimate of context consumption on a multi-server stack. Read next to ContextTax as "a vendor's estimate versus a reproducible measurement" |
| **Anthropic, "Code execution with MCP"** | `anthropic.com/engineering/code-execution-with-mcp` | November 2025 | The upper limit that code mode was invented to address |
| **Tool search tool**, Claude documentation | `platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool` | live | The verbatim mechanics of `defer_loading` and the 30-50 threshold. **This is also where the key caveat is:** "You still send every tool's full definition in the `tools` array on every request, including the deferred ones". The domain moved from `docs.claude.com` |
| **OpenAI, Function calling** | `developers.openai.com/api/docs/guides/function-calling` | live | "Fewer than 20, though this is just a soft suggestion": a second vendor threshold, and the vendor itself calls it soft |
| **Google, Function calling, Best practices** | `ai.google.dev/gemini-api/docs/function-calling` | live | "Keep active set to 10–20 tools maximum": a third vendor threshold |
| **Shopify Engineering, "Building production-ready agentic systems"** | `shopify.engineering/building-production-ready-agentic-systems` | 26.08.2025 | The primary source of the 0–20 / 20–50 / 50+ scale. **It is an engineering blog and the experience of one product, not a conference talk**, as is sometimes written |
| **Atlassian, "Inside Rovo MCP usage"** | `atlassian.com/blog/company-news/inside-rovo-mcp-usage` | 01.07.2026 | Who is at the other end: 44% of users outside software teams, about a third of calls are writes. The vendor does not disclose the denominator |
| **Pinterest Engineering, "Building an MCP ecosystem at Pinterest"** | `medium.com/pinterest-engineering/building-an-mcp-ecosystem-at-pinterest-d881eb4c16f1` | 19.03.2026 | How the internal paved road is built: review by three teams before prod, a registry for two audiences. Medium returns 403 to automated clients, opens by hand |
| **Cloudflare, "Enterprise MCP"** | `blog.cloudflare.com/enterprise-mcp/` | 14.04.2026 | Governance built into the platform: the template, default-deny on writes, the audit log and the kill switch come to the developer for free |
| **Stacklok, "State of MCP in Software 2026"** | `stacklok.com/resources/state-of-mcp-in-software-2026` | survey December 2025, published January 2026 | A survey, n=300, Director+ respondents. **Read with the denominator column:** some numbers refer to all 300, some to the software cohort n=100, and they are regularly mixed up in retellings |
| **A full pass over 10,716 remote endpoints** | `dev.to/theopslog` | 29–30.07.2026 | The author's public self-correction: a 2.8% sample of the registry gave a twice as rosy picture as the full pass. Plus a measurement that counting auth-gated servers as dead inflates the failure fivefold |
| **"4.4% of MCP servers changed their tool contract in 36 hours"**, the same author | `dev.to/theopslog/44-of-mcp-servers-changed-their-tool-contract-in-36-hours-i3m` | 01.08.2026 | An external measurement of silent contract drift, i.e. the thesis of the [versioning guide](guides/versioning.md) from the consumer's side. Method: a random sample of 500 live servers, hashes of each tool's `inputSchema`, a repeat pass over the same sample after 36 hours, 21 of 475 comparable. Of these, **15 changed the schema of a tool that kept its name**. We did not recheck the figure, but the author himself analyzes what cannot be concluded from it: he explicitly forbids extrapolating 4.4% to a month, because the edits cluster on active servers. A good model of what an honest presentation of your own measurement looks like |
| **n8n, documentation and changelog** | `docs.n8n.io` | live | Data table, limits, scope selection, public OpenTelemetry endpoints |

---

## 8. How to read other people's numbers

Four techniques that save more time in this field than any single source.

**Ask for the snapshot date, the denominator and the detection method before the number itself.** Three loud
numbers about "the same thing" usually measure three different quantities.

**A server count without the registry named is not a number.** For the same week: 19.4 thousand
in the official registry, 61.4 thousand in one aggregator, 69.4 thousand in a deduplicated
union. All three are correct.

**The same word means different things in two sources.** "Dead server" is either "does not respond
right now" (and then a 401 counts as alive), or "cannot be relied on in prod" (and then a project
is knocked out for lacking tests). Hence the twelvefold gap between two honest measurements.

**Open the repository the author links to himself.** The best-known figure comparing CLI
and MCP is refuted by the repository of the very person who published it.

---

## 9. What is intentionally not in this list

Claims for which a primary source was searched for and not found. They circulate in overviews and sound
convincing.

| Claim | Verification result |
|---|---|
| "~46,000 tokens for the GitHub server", "~18,000 tokens added to every message" | There are no primary sources. The range of public measurements is 11-55 thousand. The second formulation is also wrong in its mechanics |
| "OpenAI errors out at 75-85 tools" | The threshold does not exist. The public 128 refers to the Assistants API, which is shut down on 26.08.2026 |
| "A production server with 118 tools held together by grouping by domain" | A counterexample was not found in any source |
| A compliance deadline for contractors of 30.09.2026 | Does not exist. The only carrier is a lead-generation site |
| "250 million SDK downloads per week" | The named article was read in full, the figure is not in it |
| An n8n parallel execution ceiling of "220" or "~272" | Neither figure is in the documentation. The real mechanics: `N8N_CONCURRENCY_PRODUCTION_LIMIT`, default `-1` |
| The pair "41% versus 5%" from an industry survey | 41% is real. The numbers 5%, 86% and 9% are not in the report in any form |
| "An attack through the tool description succeeds in about 84% of cases" | 84.2% is the maximum across twelve agents in a separate paper, not the average |
| A CVE number attached to the story of "an open CRM with 5,000+ customer records" | Does not exist: the MITRE registry returns `CVE_RECORD_DNE`. It circulates with an academic attribution and so looks more reliable than its neighbors |
| Nine observability and FinOps thresholds | Eight of the nine went through verification and found no primary source, the ninth (token spend) rests on a press report, not a measurement. Published in the [observability guide](guides/observability.md) under an explicit header "starting guidelines", not as norms |

---

## 10. What goes stale first

In descending order of speed.

1. **The list of MCP CVEs: a week.** This was confirmed in the week the revision came out: two batches of records
   came out after the material was collected.
2. **Telemetry conventions: unpredictably.** A main branch without releases, an edit lands instantly.
3. **SDK versions: weeks.** Both ecosystems released major versions a day before and on the day of the
   revision's release.
4. **Ecosystem numbers: a month.** The registry grew by 24% in twenty days.
5. **Live vendor pages: without warning.** There is already a precedent: the documentation domain
   moved, and the address of the elicitation page changed within a week.
6. **The specification: slowest of all.** Dated by revision, versioned, read word for word.
   Start here.

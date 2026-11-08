# contracts: shared JSON contracts

JSON Schema (draft 2020-12) at the system boundaries. Contract version: `schema_version = "1.0"` in every object; `additionalProperties: false`.

| File | What it describes |
|---|---|
| `ticket.schema.json` | the ticket as `get_ticket` returns it |

Dependencies go in one direction: `contracts ← domain ← mcp_server`. Contracts import nothing.

## How to change a contract
Change the schema, then the server code that returns the ticket. An incompatible change means a new `schema_version` and an entry in the project's decision log.

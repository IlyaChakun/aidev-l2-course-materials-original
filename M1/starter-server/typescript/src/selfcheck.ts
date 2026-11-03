/**
 * Check the skeleton without Inspector.
 *
 * Starts server.ts as a separate process over stdio - exactly the way
 * Inspector and the IDE do - and prints what the server returned over the protocol.
 *
 * Run:  npm run selfcheck
 *
 * If this script ran through, the environment is set up: the packages are installed, the server starts,
 * the tool and resource are registered, and stdout is not polluted by stray output.
 */

import { fileURLToPath } from 'node:url';

import { Client } from '@modelcontextprotocol/client';
import { StdioClientTransport } from '@modelcontextprotocol/client/stdio';

const SERVER = fileURLToPath(new URL('./server.ts', import.meta.url));

const transport = new StdioClientTransport({
  command: process.execPath,
  args: [SERVER]
});

// mode: 'auto' - the client first tries `server/discover` (revision 2026-07-28)
// and falls back to the old handshake if the server does not understand it.
// The client default is 'legacy', and then 2025-11-25 is negotiated.
const client = new Client(
  { name: 'selfcheck', version: '0.1.0' },
  { versionNegotiation: { mode: 'auto' } }
);
await client.connect(transport);

console.log(`protocol:   ${client.getNegotiatedProtocolVersion()}`);
console.log(`server:     ${JSON.stringify(client.getServerVersion())}`);

const tools = await client.listTools();
console.log(`tools:      ${JSON.stringify(tools.tools.map((t) => t.name))}`);

const resources = await client.listResources();
console.log(`resources:  ${JSON.stringify(resources.resources.map((r) => r.uri))}`);

const called = await client.callTool({ name: 'ping', arguments: { message: 'selfcheck' } });
console.log(`ping call:  ${JSON.stringify(called.content)}`);

const read = await client.readResource({ uri: 'starter://info' });
console.log(`read:       ${JSON.stringify(read.contents)}`);

await client.close();
console.log('\nOK: the skeleton starts, the tool and resource are visible.');

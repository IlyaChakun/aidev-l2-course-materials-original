/**
 * Starter MCP server skeleton: one tool, one resource.
 *
 * Purpose of the file: check that the environment is set up and the server is visible in MCP Inspector
 * and in the IDE. There is intentionally no business logic here. Replace the contents with your own.
 *
 * SDK: the @modelcontextprotocol/server + /core packages, line 2.x.
 * Protocol: revision 2026-07-28.
 *
 * IMPORTANT about the packages. The old @modelcontextprotocol/sdk package stayed on line 1.x
 * and does not support revision 2026-07-28. Here, line 2.x in the new packages is used.
 * The fork is explained in the README next to this file.
 */

import { McpServer } from '@modelcontextprotocol/server';
import { serveStdio } from '@modelcontextprotocol/server/stdio';
import { z } from 'zod';

function createServer(): McpServer {
  const server = new McpServer({ name: 'starter-server', version: '0.1.0' });

  // ───────────────────────────────────────────────────────────────────────────
  // TOOL. Your tool goes here.
  //
  // What you substitute in your own project:
  //   - first argument -> the tool name the agent will see (getArticle, moveTicket...)
  //   - description    -> the agent picks the tool by it, write it as a contract
  //   - inputSchema    -> the argument schema; in line 2.x this is a Standard Schema,
  //                       i.e. z.object({...}), not a bare shape object
  //   - callback       -> returns { content: [...] }
  //
  // For now there is exactly one tool and it does nothing with data. This is deliberate:
  // the skeleton checks the environment, it does not solve the homework.
  // ───────────────────────────────────────────────────────────────────────────
  server.registerTool(
    'ping',
    {
      title: 'Ping',
      description: 'Return the passed message together with server diagnostics.',
      inputSchema: z.object({
        message: z.string().describe('Any string, to check that the arguments arrive')
      })
    },
    async ({ message }) => {
      const payload = {
        echo: message,
        server_time_utc: new Date().toISOString(),
        node_version: process.version
      };
      return { content: [{ type: 'text', text: JSON.stringify(payload, null, 2) }] };
    }
  );

  // ───────────────────────────────────────────────────────────────────────────
  // RESOURCE. Your resource goes here.
  //
  // The assignment requires at least one resource: the DB schema or a state summary.
  // Change the URI and the callback body: for example, `db://schema` returns the DDL of your tables,
  // and `db://summary` returns the number of entities per status.
  //
  // A URI with a parameter (`db://entity/{id}`) is registered via ResourceTemplate -
  // that is the advanced level. The syntax is shown in the README next to this file.
  // ───────────────────────────────────────────────────────────────────────────
  server.registerResource(
    'info',
    'starter://info',
    { title: 'Starter info', mimeType: 'application/json' },
    async (uri) => ({
      contents: [
        {
          uri: uri.href,
          mimeType: 'application/json',
          text: JSON.stringify(
            {
              server: 'starter-server',
              tools: ['ping'],
              resources: ['starter://info'],
              note: 'A skeleton for checking the environment. Replace it with your own contract.'
            },
            null,
            2
          )
        }
      ]
    })
  );

  return server;
}

// stdio is the transport used by MCP Inspector and the IDE.
//
// Warning: in a stdio server, stdout is taken by the protocol. Any console.log breaks
// the connection. For debugging, write to stderr: console.error(...).
console.error('starter-server: starting on stdio');
serveStdio(createServer);

"""Check the skeleton without Inspector.

Starts server.py as a separate process over stdio - exactly the way
Inspector and the IDE do - and prints what the server returned over the protocol.

Run:  python selfcheck.py

If this script ran through, the environment is set up: the SDK is installed, the server starts,
the tool and resource are registered, and stdout is not polluted by stray output.
"""

import sys
from pathlib import Path

import anyio
from mcp import Client, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER = str(Path(__file__).with_name("server.py"))


async def main() -> None:
    params = StdioServerParameters(command=sys.executable, args=[SERVER])

    async with Client(stdio_client(params)) as client:
        print(f"protocol:      {client.protocol_version}")
        print(f"server:        {client.server_info.name} {client.server_info.version}")

        tools = await client.list_tools()
        print(f"tools:         {[t.name for t in tools.tools]}")

        resources = await client.list_resources()
        print(f"resources:     {[str(r.uri) for r in resources.resources]}")

        called = await client.call_tool("ping", {"message": "selfcheck"})
        print(f"ping call:     {called.content[0].text}")

        read = await client.read_resource("starter://info")
        print(f"read:          {read.contents[0].text}")

    print("\nOK: the skeleton starts, the tool and resource are visible.")


if __name__ == "__main__":
    anyio.run(main)

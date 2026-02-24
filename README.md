# Example MCP Servers

MCP servers



# Cursor and MCP Servers
To add an MCP Server to Cursor:

- Add the server in Cursor-> Cursor Settings-> Tools and MCP, OR
- Add the server to '~/.cursor/mcp.json'. For local command line servers:
```
{
  "mcpServers": {
    "<name of MCP>": {
      "command": "<path to executable>"
    }
  }
}
```
- Restart Cursor.
- Look in Cursor-> Cursor Settings-> Tools and MCP to ensure the config is correctly formatted.

To use the server, in the agent chat type: `<server name> <tool> <parameters>`.

For the weather example server: `weather get_alerts ca`.


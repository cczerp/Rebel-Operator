#!/usr/bin/env node

/**
 * Render MCP Server
 * Provides tools to interact with Render.com API
 */

const RENDER_API_KEY = process.env.RENDER_API_KEY;
const RENDER_API_BASE = 'https://api.render.com/v1';

if (!RENDER_API_KEY) {
  console.error('Error: RENDER_API_KEY environment variable is required');
  process.exit(1);
}

// MCP Protocol implementation
const tools = [
  {
    name: 'get_services',
    description: 'List all Render services',
    inputSchema: {
      type: 'object',
      properties: {},
    },
  },
  {
    name: 'get_service',
    description: 'Get details about a specific Render service',
    inputSchema: {
      type: 'object',
      properties: {
        serviceId: {
          type: 'string',
          description: 'The Render service ID',
        },
      },
      required: ['serviceId'],
    },
  },
  {
    name: 'get_deploys',
    description: 'Get deployment history for a service',
    inputSchema: {
      type: 'object',
      properties: {
        serviceId: {
          type: 'string',
          description: 'The Render service ID',
        },
        limit: {
          type: 'number',
          description: 'Number of deploys to retrieve (default: 10)',
          default: 10,
        },
      },
      required: ['serviceId'],
    },
  },
  {
    name: 'get_logs',
    description: 'Get logs for a Render service',
    inputSchema: {
      type: 'object',
      properties: {
        serviceId: {
          type: 'string',
          description: 'The Render service ID',
        },
        tail: {
          type: 'number',
          description: 'Number of recent log lines to retrieve (default: 100)',
          default: 100,
        },
      },
      required: ['serviceId'],
    },
  },
];

async function fetchRender(endpoint) {
  const response = await fetch(`${RENDER_API_BASE}${endpoint}`, {
    headers: {
      Authorization: `Bearer ${RENDER_API_KEY}`,
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Render API error: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

async function handleToolCall(name, args) {
  switch (name) {
    case 'get_services': {
      const data = await fetchRender('/services');
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(data, null, 2),
          },
        ],
      };
    }

    case 'get_service': {
      const data = await fetchRender(`/services/${args.serviceId}`);
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(data, null, 2),
          },
        ],
      };
    }

    case 'get_deploys': {
      const limit = args.limit || 10;
      const data = await fetchRender(`/services/${args.serviceId}/deploys?limit=${limit}`);
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(data, null, 2),
          },
        ],
      };
    }

    case 'get_logs': {
      const tail = args.tail || 100;
      const data = await fetchRender(`/services/${args.serviceId}/logs?tail=${tail}`);
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(data, null, 2),
          },
        ],
      };
    }

    default:
      throw new Error(`Unknown tool: ${name}`);
  }
}

// MCP stdio communication
const readline = require('readline');
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
  terminal: false,
});

rl.on('line', async (line) => {
  try {
    const request = JSON.parse(line);

    if (request.method === 'initialize') {
      const response = {
        jsonrpc: '2.0',
        id: request.id,
        result: {
          protocolVersion: '2024-11-05',
          serverInfo: {
            name: 'render-mcp',
            version: '1.0.0',
          },
          capabilities: {
            tools: {},
          },
        },
      };
      console.log(JSON.stringify(response));
    } else if (request.method === 'tools/list') {
      const response = {
        jsonrpc: '2.0',
        id: request.id,
        result: {
          tools: tools,
        },
      };
      console.log(JSON.stringify(response));
    } else if (request.method === 'tools/call') {
      const result = await handleToolCall(request.params.name, request.params.arguments || {});
      const response = {
        jsonrpc: '2.0',
        id: request.id,
        result: result,
      };
      console.log(JSON.stringify(response));
    } else {
      const response = {
        jsonrpc: '2.0',
        id: request.id,
        error: {
          code: -32601,
          message: `Method not found: ${request.method}`,
        },
      };
      console.log(JSON.stringify(response));
    }
  } catch (error) {
    const response = {
      jsonrpc: '2.0',
      id: null,
      error: {
        code: -32603,
        message: error.message,
      },
    };
    console.log(JSON.stringify(response));
  }
});

console.error('Render MCP Server started');

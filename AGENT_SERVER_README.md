# Agent API Server for n8n

This server receives tasks from n8n and processes them using the Ollama-powered agent.

## Quick Start

### 1. Start Ollama
**In a separate terminal**, run:
```bash
ollama serve
```

### 2. Start the Agent API Server
**Windows:**
```cmd
start-agent-server.cmd
```

**Linux/Mac:**
```bash
./start-agent-server.sh
```

**Or directly:**
```bash
node server.js
```

The server will start on `http://localhost:3030`

## Testing

Test if it's working:
```bash
curl http://localhost:3030/health
```

Should return:
```json
{"status":"ok","timestamp":"2026-01-10T..."}
```

## n8n Configuration

In your n8n workflow, configure the HTTP Request node:
- **Method:** POST
- **URL:** `http://localhost:3030/execute-task`
- **Body:**
  ```json
  {
    "task_id": "task_123",
    "task_instruction": "Your instruction here"
  }
  ```

## Troubleshooting

### Error: ECONNREFUSED on port 3030
- Make sure you ran `node server.js` or the start script
- Check if something else is using port 3030: `netstat -ano | findstr :3030` (Windows)

### Error: Ollama connection failed
- Start Ollama: `ollama serve` in a separate terminal
- Verify it's running: `curl http://localhost:11434/api/version`

### Agent not processing tasks
- Check the server console for error messages
- Verify `agents/agent.js` exists and has proper permissions
- Make sure Ollama has the required model: `ollama list`

## Files Structure
```
/
├── server.js                  # Main API server (port 3030)
├── agents/
│   └── agent.js              # Ollama-powered agent
├── package.json              # Dependencies
├── start-agent-server.cmd    # Windows startup script
└── start-agent-server.sh     # Linux/Mac startup script
```

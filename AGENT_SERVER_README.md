# Agent API Servers for n8n

Two AI agent servers that receive tasks from n8n and process them using Ollama-powered agents:
- **Judge Trudy** - Port 3030
- **Qwen Ryche** - Port 3131

## Quick Start

### 1. Start Ollama
**In a separate terminal**, run:
```bash
ollama serve
```

### 2. Start the Agent Servers

**Option A - Start BOTH agents:**
```cmd
start-both-agents.cmd
```

**Option B - Start individually:**

Judge Trudy (port 3030):
```bash
npm run start:trudy
```

Qwen Ryche (port 3131):
```bash
npm run start:qwen
```

**Or directly:**
```bash
node judge-trudy-server.js
node qwen-ryche-server.js
```

## Testing

Test if they're working:
```bash
curl http://localhost:3030/health
curl http://localhost:3131/health
```

Should return:
```json
{"status":"ok","agent":"Judge Trudy","timestamp":"2026-01-10T..."}
{"status":"ok","agent":"Qwen Ryche","timestamp":"2026-01-10T..."}
```

## n8n Configuration

Configure the HTTP Request nodes for each agent:

**Judge Trudy:**
- **Method:** POST
- **URL:** `http://localhost:3030/execute-task`
- **Body:**
  ```json
  {
    "task_id": "task_123",
    "task_instruction": "Your instruction here"
  }
  ```

**Qwen Ryche:**
- **Method:** POST
- **URL:** `http://localhost:3131/execute-task`
- **Body:**
  ```json
  {
    "task_id": "task_456",
    "task_instruction": "Your instruction here"
  }
  ```

## Troubleshooting

### Error: ECONNREFUSED on port 3030 or 3131
- Make sure you started the appropriate server
- Check if something else is using the port: `netstat -ano | findstr :3030` or `netstat -ano | findstr :3131` (Windows)

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
├── judge-trudy-server.js      # Judge Trudy API server (port 3030)
├── qwen-ryche-server.js       # Qwen Ryche API server (port 3131)
├── agents/
│   └── agent.js              # Ollama-powered agent (shared by both)
├── package.json              # Dependencies with npm scripts
├── start-both-agents.cmd     # Windows: Start both servers
├── start-agent-server.cmd    # Windows: Legacy single server script
└── start-agent-server.sh     # Linux/Mac: Legacy single server script
```

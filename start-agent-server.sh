#!/bin/bash

echo "🚀 Starting Agent API Server for n8n"
echo ""

# Check if Ollama is running
echo "Checking Ollama connection..."
if curl -s http://localhost:11434/api/version > /dev/null 2>&1; then
    echo "✅ Ollama is running"
else
    echo "❌ Ollama is NOT running!"
    echo ""
    echo "Please start Ollama first:"
    echo "  - Windows: Open a terminal and run 'ollama serve'"
    echo "  - Linux: Run 'ollama serve' or 'sudo systemctl start ollama'"
    echo ""
    exit 1
fi

echo ""
echo "Starting API server on port 3030..."
echo ""

node server.js

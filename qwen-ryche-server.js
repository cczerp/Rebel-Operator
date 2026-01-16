#!/usr/bin/env node

const express = require('express');
const { spawn } = require('child_process');
const path = require('path');

const app = express();
const PORT = 3131;

// Middleware
app.use(express.json());

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'ok', agent: 'Qwen Ryche', timestamp: new Date().toISOString() });
});

// Main task execution endpoint
app.post('/execute-task', async (req, res) => {
  try {
    const { task_id, task_instruction } = req.body;

    if (!task_id || !task_instruction) {
      return res.status(400).json({
        success: false,
        error: 'Missing task_id or task_instruction'
      });
    }

    console.log(`[QWEN RYCHE - ${new Date().toISOString()}] Received task: ${task_id}`);

    // Prepare task data
    const taskData = JSON.stringify({ task_id, task_instruction });

    // Call the agent
    const agentPath = path.join(__dirname, 'agents', 'agent.js');
    const agentProcess = spawn('node', [agentPath, taskData]);

    let stdout = '';
    let stderr = '';

    agentProcess.stdout.on('data', (data) => {
      stdout += data.toString();
    });

    agentProcess.stderr.on('data', (data) => {
      stderr += data.toString();
      console.error(`[QWEN RYCHE STDERR]: ${data}`);
    });

    agentProcess.on('close', (code) => {
      console.log(`[QWEN RYCHE - ${new Date().toISOString()}] Agent process exited with code ${code}`);

      if (code === 0) {
        try {
          const result = JSON.parse(stdout);
          res.json(result);
        } catch (parseError) {
          console.error('Failed to parse agent output:', stdout);
          res.status(500).json({
            success: false,
            error: 'Failed to parse agent output',
            raw_output: stdout,
            stderr: stderr
          });
        }
      } else {
        res.status(500).json({
          success: false,
          error: `Agent process failed with code ${code}`,
          stderr: stderr,
          stdout: stdout
        });
      }
    });

    agentProcess.on('error', (error) => {
      console.error('Failed to start agent process:', error);
      res.status(500).json({
        success: false,
        error: `Failed to start agent: ${error.message}`
      });
    });

  } catch (error) {
    console.error('Request handling error:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Start server
app.listen(PORT, () => {
  console.log(`✅ Qwen Ryche Agent API Server running on http://localhost:${PORT}`);
  console.log(`   - Health check: http://localhost:${PORT}/health`);
  console.log(`   - Execute task: POST http://localhost:${PORT}/execute-task`);
  console.log(`\nWaiting for tasks from n8n...`);
});

// Graceful shutdown
process.on('SIGINT', () => {
  console.log('\n\n👋 Shutting down Qwen Ryche server...');
  process.exit(0);
});

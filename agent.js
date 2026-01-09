#!/usr/bin/env node

const { Ollama } = require('ollama');
const fs = require('fs').promises;
const { execSync } = require('child_process');
const path = require('path');

// Configuration
const REPO_PATH = 'C:\\Users\\Dragon\\Desktop\\projettccs\\resell-rebel';
const MODEL = 'llama3.1:8b';
const ollama = new Ollama({ host: 'http://localhost:11434' });

// Available tools for the AI
const tools = [
  {
    type: 'function',
    function: {
      name: 'read_file',
      description: 'Read the contents of a file from the repository',
      parameters: {
        type: 'object',
        properties: {
          file_path: {
            type: 'string',
            description: 'Relative path to the file from repo root (e.g., "src/components/Vault.jsx")'
          }
        },
        required: ['file_path']
      }
    }
  },
  {
    type: 'function',
    function: {
      name: 'write_file',
      description: 'Write or overwrite a file in the repository',
      parameters: {
        type: 'object',
        properties: {
          file_path: {
            type: 'string',
            description: 'Relative path to the file from repo root'
          },
          content: {
            type: 'string',
            description: 'Full content to write to the file'
          }
        },
        required: ['file_path', 'content']
      }
    }
  },
  {
    type: 'function',
    function: {
      name: 'list_files',
      description: 'List files in a directory of the repository',
      parameters: {
        type: 'object',
        properties: {
          dir_path: {
            type: 'string',
            description: 'Relative directory path from repo root (use "." for root)'
          }
        },
        required: ['dir_path']
      }
    }
  },
  {
    type: 'function',
    function: {
      name: 'execute_command',
      description: 'Execute a shell command in the repository directory. Use sparingly.',
      parameters: {
        type: 'object',
        properties: {
          command: {
            type: 'string',
            description: 'Shell command to execute'
          }
        },
        required: ['command']
      }
    }
  },
  {
    type: 'function',
    function: {
      name: 'task_complete',
      description: 'Call this when the task is fully completed',
      parameters: {
        type: 'object',
        properties: {
          summary: {
            type: 'string',
            description: 'Summary of what was accomplished'
          },
          files_modified: {
            type: 'array',
            items: { type: 'string' },
            description: 'List of files that were created or modified'
          }
        },
        required: ['summary', 'files_modified']
      }
    }
  }
];

// Tool implementations
async function read_file(file_path) {
  try {
    const fullPath = path.join(REPO_PATH, file_path);
    const content = await fs.readFile(fullPath, 'utf-8');
    return { success: true, content };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

async function write_file(file_path, content) {
  try {
    const fullPath = path.join(REPO_PATH, file_path);
    await fs.mkdir(path.dirname(fullPath), { recursive: true });
    await fs.writeFile(fullPath, content, 'utf-8');
    return { success: true, message: `File written: ${file_path}` };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

async function list_files(dir_path) {
  try {
    const fullPath = path.join(REPO_PATH, dir_path);
    const files = await fs.readdir(fullPath, { withFileTypes: true });
    const fileList = files.map(f => ({
      name: f.name,
      type: f.isDirectory() ? 'directory' : 'file'
    }));
    return { success: true, files: fileList };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

function execute_command(command) {
  try {
    const output = execSync(command, { 
      cwd: REPO_PATH,
      encoding: 'utf-8',
      maxBuffer: 10 * 1024 * 1024
    });
    return { success: true, output };
  } catch (error) {
    return { success: false, error: error.message, output: error.stdout };
  }
}

// Execute tool calls
async function executeTool(name, args) {
  switch (name) {
    case 'read_file':
      return await read_file(args.file_path);
    case 'write_file':
      return await write_file(args.file_path, args.content);
    case 'list_files':
      return await list_files(args.dir_path);
    case 'execute_command':
      return execute_command(args.command);
    case 'task_complete':
      return { completed: true, ...args };
    default:
      return { error: `Unknown tool: ${name}` };
  }
}

// Main agent loop
async function runAgent(taskData) {
  const messages = [
    {
      role: 'system',
      content: `You are a code modification assistant. You have access to tools to read, write, and modify files in the resell-rebel repository.

Your job is to complete the given task by:
1. Reading relevant files to understand the current code
2. Making the necessary modifications
3. Writing the updated files back
4. Calling task_complete when done

Be efficient - only read files you need. Make concrete changes that can be directly implemented.

Repository path: ${REPO_PATH}`
    },
    {
      role: 'user',
      content: `Task ID: ${taskData.task_id}\n\nInstructions:\n${taskData.task_instruction}`
    }
  ];

  let iterations = 0;
  const MAX_ITERATIONS = 20;
  let taskCompleted = false;
  let completionData = null;

  while (!taskCompleted && iterations < MAX_ITERATIONS) {
    iterations++;
    
    // Call Ollama with tools
    const response = await ollama.chat({
      model: MODEL,
      messages: messages,
      tools: tools,
    });

    messages.push(response.message);

    // Check if there are tool calls
    if (!response.message.tool_calls || response.message.tool_calls.length === 0) {
      // No tool calls, AI is done or stuck
      break;
    }

    // Execute all tool calls
    for (const toolCall of response.message.tool_calls) {
      const result = await executeTool(
        toolCall.function.name,
        toolCall.function.arguments
      );

      // Check if task is complete
      if (result.completed) {
        taskCompleted = true;
        completionData = result;
      }

      // Add tool result to messages
      messages.push({
        role: 'tool',
        content: JSON.stringify(result)
      });
    }
  }

  return {
    success: taskCompleted,
    iterations,
    completion: completionData,
    messages: messages.slice(-3) // Last 3 messages for context
  };
}

// Entry point
async function main() {
  try {
    // Get task from command line argument
    const taskJson = process.argv[2];
    
    if (!taskJson) {
      console.error('Error: No task provided');
      console.error('Usage: node agent.js \'{"task_id":"...","task_instruction":"..."}\'');
      process.exit(1);
    }

    const taskData = JSON.parse(taskJson);

    console.error(`Starting task: ${taskData.task_id}`);
    
    const result = await runAgent(taskData);

    // Output JSON result for n8n to consume
    console.log(JSON.stringify({
      task_id: taskData.task_id,
      success: result.success,
      iterations: result.iterations,
      summary: result.completion?.summary || 'Task incomplete',
      files_modified: result.completion?.files_modified || [],
      timestamp: new Date().toISOString()
    }, null, 2));

  } catch (error) {
    console.error('Agent error:', error.message);
    console.log(JSON.stringify({
      success: false,
      error: error.message
    }, null, 2));
    process.exit(1);
  }
}

main();

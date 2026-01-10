#!/usr/bin/env node

const { Ollama } = require('ollama');
const fs = require('fs');
const path = require('path');

// Configuration
const REPO_PATH = 'C:\\Users\\Dragon\\Desktop\\projettccs\\resell-rebel';
const MODEL = 'qwen2.5:7b-instruct';
const ollama = new Ollama({ host: 'http://localhost:11434' });

// Main agent function
async function runAgent(taskData) {
  console.error(`Starting task: ${taskData.task_id}\n`);

  // Read relevant files based on task
  const relevantFiles = await discoverRelevantFiles(taskData);
  
  console.error(`Reading ${relevantFiles.length} relevant files...\n`);
  
  const fileContents = {};
  for (const filePath of relevantFiles) {
    try {
      const fullPath = path.join(REPO_PATH, filePath);
      fileContents[filePath] = fs.readFileSync(fullPath, 'utf-8');
      console.error(`✓ Read: ${filePath}`);
    } catch (error) {
      console.error(`✗ Could not read: ${filePath}`);
    }
  }

  // Build context for AI
  let contextPrompt = `You are modifying a Flask web application.

PROJECT STRUCTURE:
- Flask backend: web_app.py
- Templates: templates/ (Jinja2/HTML with Bootstrap + Font Awesome)  
- Static: static/ (CSS, JS, images)
- Backend: src/ (Python modules)

CURRENT FILES:\n`;

  for (const [filePath, content] of Object.entries(fileContents)) {
    contextPrompt += `\n=== ${filePath} ===\n${content}\n`;
  }

  contextPrompt += `\n\nTASK: ${taskData.task_instruction}

CRITICAL OUTPUT FORMAT - FOLLOW EXACTLY:
You MUST output files in this EXACT format with NO markdown, NO code blocks, NO extra text:

=== FILEPATH: templates/vault.html ===
{% extends "base.html" %}
(rest of complete file content)
=== END ===

DO NOT use markdown code blocks like \`\`\`html
DO NOT add explanatory text before or after
DO NOT say "Here is the modified file"
ONLY output the exact format shown above with the complete file contents.`;

  try {
    console.error('\nSending to AI...\n');
    
    const response = await ollama.chat({
      model: MODEL,
      messages: [
        { role: 'user', content: contextPrompt }
      ],
      stream: false
    });

    const output = response.message.content;
    console.error('--- AI Response ---');
    console.error(output.substring(0, 500) + '...\n');
    console.error('--- End Response ---\n');

    // Parse AI output for file contents
    const files = parseFileOutput(output);
    
    if (files.length === 0) {
      return {
        task_id: taskData.task_id,
        success: false,
        error: 'AI did not generate any file outputs',
        timestamp: new Date().toISOString()
      };
    }

    // Write files
    console.error(`Writing ${files.length} files...\n`);
    const filesWritten = [];
    
    for (const { filepath, content } of files) {
      try {
        const fullPath = path.join(REPO_PATH, filepath);
        
        // Ensure directory exists
        const dir = path.dirname(fullPath);
        if (!fs.existsSync(dir)) {
          fs.mkdirSync(dir, { recursive: true });
        }
        
        fs.writeFileSync(fullPath, content, 'utf-8');
        filesWritten.push(filepath);
        console.error(`✓ Wrote: ${filepath}`);
      } catch (error) {
        console.error(`✗ Failed to write: ${filepath} - ${error.message}`);
      }
    }

    return {
      task_id: taskData.task_id,
      success: filesWritten.length > 0,
      files_modified: filesWritten,
      summary: `Modified ${filesWritten.length} file(s)`,
      timestamp: new Date().toISOString()
    };

  } catch (error) {
    console.error('Agent error:', error.message);
    return {
      task_id: taskData.task_id,
      success: false,
      error: error.message,
      timestamp: new Date().toISOString()
    };
  }
}

// Discover which files are relevant to the task
async function discoverRelevantFiles(taskData) {
  const instruction = taskData.task_instruction.toLowerCase();
  const files = [];

  // Vault-related tasks
  if (instruction.includes('vault') || instruction.includes('inventory') || instruction.includes('collection')) {
    files.push('templates/vault.html');
    // Also include base if we might need to add scripts/styles
    if (instruction.includes('modal') || instruction.includes('drawer') || instruction.includes('panel')) {
      files.push('templates/base.html');
    }
  }

  // Default to vault if nothing detected
  if (files.length === 0) {
    files.push('templates/vault.html');
  }

  return files;
}

// Parse AI output for file contents
function parseFileOutput(output) {
  const files = [];
  const fileRegex = /===\s*FILEPATH:\s*(.+?)\s*===\s*\n([\s\S]*?)(?=\n===\s*(?:FILEPATH:|END))/g;
  
  let match;
  while ((match = fileRegex.exec(output)) !== null) {
    files.push({
      filepath: match[1].trim(),
      content: match[2].trim()
    });
  }

  return files;
}

// Entry point
async function main() {
  try {
    const taskJson = process.argv[2];
    
    if (!taskJson) {
      console.error('Error: No task provided');
      console.error('Usage: node agent.js \'{"task_id":"...","task_instruction":"..."}\'');
      process.exit(1);
    }

    const taskData = JSON.parse(taskJson);
    const result = await runAgent(taskData);

    // Output JSON result for n8n
    console.log(JSON.stringify(result, null, 2));

  } catch (error) {
    console.error('Fatal error:', error.message);
    console.log(JSON.stringify({
      success: false,
      error: error.message
    }, null, 2));
    process.exit(1);
  }
}

main();

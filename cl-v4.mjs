import express from "express";
import { execSync } from "child_process";
import * as readline from "readline";
import dotenv from "dotenv";
import Anthropic from "@anthropic-ai/sdk";

dotenv.config();

const REPO_PATH = "/mnt/c/Users/Dragon/Desktop/projettccs/resell-rebel";
const GITHUB_TOKEN = process.env.GITHUB_API_ACCESS;
const ANTHROPIC_API_KEY = process.env.CLAUDE_AUTH_API;
const REPO_OWNER = "cczerp";
const REPO_NAME = "Resell-Rebel";

const WORK_BRANCH = "n8n-run-test01";      // Claude does work here
const GRADE_BRANCH = "grade-test01";        // PRs target this for preview
const PASS_BRANCH = "pass";                 // Successful tasks merge here

const CONFIDENCE_THRESHOLD = 80; // Validator AI must be this confident to auto-pass

const anthropic = new Anthropic({
  apiKey: ANTHROPIC_API_KEY,
});

const run = (cmd, opts = {}) => {
  return execSync(cmd, { 
    cwd: REPO_PATH, 
    encoding: "utf8", 
    shell: true,  // Use native shell (cmd.exe on Windows)
    ...opts 
  });
};

const prompt = (question) => {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });
  return new Promise((resolve) => {
    rl.question(question, (answer) => {
      rl.close();
      resolve(answer.trim());
    });
  });
};

const githubAPI = async (endpoint, method = "GET", body = null) => {
  const url = `https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}${endpoint}`;
  const options = {
    method,
    headers: {
      Authorization: `token ${GITHUB_TOKEN}`,
      Accept: "application/vnd.github.v3+json",
      "Content-Type": "application/json",
    },
  };
  if (body) options.body = JSON.stringify(body);
  
  const response = await fetch(url, options);
  const data = await response.json();
  
  if (!response.ok) {
    throw new Error(`GitHub API error: ${data.message}`);
  }
  return data;
};

const createPR = async (title, head, base) => {
  try {
    const pr = await githubAPI("/pulls", "POST", {
      title,
      head,
      base,
      body: `Automated task: ${title}\n\nCreated by Claude Code automation.`,
    });
    return pr;
  } catch (err) {
    // PR might already exist
    if (err.message.includes("A pull request already exists")) {
      console.log("   PR already exists, fetching...");
      const prs = await githubAPI(`/pulls?head=${REPO_OWNER}:${head}&base=${base}`);
      return prs[0];
    }
    throw err;
  }
};

const ensureBranchExists = (branchName, fromBranch = "main") => {
  try {
    run(`git checkout ${branchName}`, { stdio: "pipe" });
    run(`git checkout ${WORK_BRANCH}`, { stdio: "pipe" });
  } catch {
    console.log(`   Creating branch: ${branchName}`);
    run(`git checkout ${fromBranch}`, { stdio: "pipe" });
    run(`git checkout -b ${branchName}`, { stdio: "pipe" });
    run(`git push origin ${branchName}`, { stdio: "pipe" });
    run(`git checkout ${WORK_BRANCH}`, { stdio: "pipe" });
  }
};

const mergeToBranch = (targetBranch, commitSha, taskTitle) => {
  console.log(`\n📦 Merging to ${targetBranch}...`);
  run(`git checkout ${targetBranch}`, { stdio: "inherit" });
  run(`git merge ${commitSha} -m "Merge passed task: ${taskTitle}"`, { stdio: "inherit" });
  run(`git push origin ${targetBranch}`, { stdio: "inherit" });
  run(`git checkout ${WORK_BRANCH}`, { stdio: "inherit" });
};

const createFailBranch = (taskId, taskTitle, commitSha) => {
  const safeName = taskTitle.toLowerCase().replace(/[^a-z0-9]+/g, "-").slice(0, 30);
  const failBranch = `fail/task-${taskId}-${safeName}`;
  
  console.log(`\n🔴 Creating fail branch: ${failBranch}`);
  run(`git checkout -b ${failBranch} ${commitSha}`, { stdio: "inherit" });
  run(`git push origin ${failBranch}`, { stdio: "inherit" });
  run(`git checkout ${WORK_BRANCH}`, { stdio: "inherit" });
  
  return failBranch;
};

const runClaudeTask = async (taskInstruction, commitMessage, isRetry = false, feedback = "") => {
  let taskPrompt = taskInstruction;
  
  const systemContext = `═══════════════════════════════════════════════════════════
🐧 LINUX ENVIRONMENT (WSL)
═══════════════════════════════════════════════════════════

You are working in a Linux/WSL environment.

STANDARD LINUX COMMANDS:
• List directory: ls -la
• View file: cat filename
• Current path: pwd
• Create directory: mkdir dirname
• Copy file: cp source dest
• Delete file: rm filename
• Find text: grep "text" file
• Check file exists: [ -f filename ] && echo yes

PATH FORMAT: Use forward slashes /path/to/file

REPOSITORY INFO:
• Location: /mnt/c/Users/Dragon/Desktop/projettccs/resell-rebel
• Current branch: n8n-run-test01
• You have bash tool to execute commands

YOUR JOB:
1. Actually DO the task (create/modify files as instructed)
2. Use standard Linux/bash commands
3. Verify changes with git status
4. Stage with: git add -A
5. Commit with the provided message
6. Do NOT just describe what you would do - DO IT

═══════════════════════════════════════════════════════════
`;

  if (isRetry) {
    taskPrompt = `${systemContext}

🔄 RETRY ATTEMPT - Previous attempt failed.

FEEDBACK FROM HUMAN REVIEWER:
${feedback}

IMPORTANT: Research this issue thoroughly before attempting. Consider:
- Platform integration requirements
- Best practices for this type of task
- Common pitfalls and how to avoid them

ORIGINAL TASK:
${taskInstruction}

After making changes:
1. Stage all changes with: git add -A
2. Commit with message: "${commitMessage}"

Do NOT ask for confirmation. Execute the task and commit.`;
  } else {
    taskPrompt = `${systemContext}

TASK:
${taskInstruction}

After making changes:
1. Stage all changes with: git add -A
2. Commit with message: "${commitMessage}"

Do NOT ask for confirmation. Execute the task and commit.`;
  }

  console.log("\n📝 Task prompt prepared");
  console.log("\n⏳ Claude is working via API…\n");

  // Use Anthropic API directly with bash tool for agentic capabilities
  const maxRetries = 3;
  let attempt = 0;
  let lastError = null;
  let claudeResponse = null;

  while (attempt < maxRetries) {
    try {
      let messages = [
        {
          role: "user",
          content: taskPrompt
        }
      ];

      // Conversation loop for tool use
      let continueLoop = true;
      let iterationCount = 0;
      const maxIterations = 20; // Prevent infinite loops

      while (continueLoop && iterationCount < maxIterations) {
        iterationCount++;
        
        const message = await anthropic.messages.create({
          model: "claude-sonnet-4-20250514",
          max_tokens: 8192,
          messages: messages,
          tools: [
            {
              name: "bash",
              description: "Run bash commands in the repository directory. Use this to modify files, run git commands, etc.",
              input_schema: {
                type: "object",
                properties: {
                  command: {
                    type: "string",
                    description: "The bash command to execute"
                  }
                },
                required: ["command"]
              }
            }
          ]
        });

        // Check if Claude used tools
        const toolUses = message.content.filter(block => block.type === "tool_use");
        const textBlocks = message.content.filter(block => block.type === "text");

        // Log any text responses
        if (textBlocks.length > 0) {
          const text = textBlocks.map(b => b.text).join("\n");
          console.log("\n🤖 Claude:", text.slice(0, 300) + (text.length > 300 ? "..." : ""));
        }

        if (toolUses.length === 0) {
          // No more tool uses, we're done
          continueLoop = false;
          claudeResponse = textBlocks.map(b => b.text).join("\n");
        } else {
          // Execute tool uses and continue conversation
          const toolResults = [];

          for (const toolUse of toolUses) {
            if (toolUse.name === "bash") {
              const command = toolUse.input.command;
              console.log(`\n🔧 Executing: ${command}`);

              try {
                const output = run(command, { stdio: "pipe" });
                console.log(`   ✅ Output: ${output.slice(0, 200)}${output.length > 200 ? "..." : ""}`);
                
                toolResults.push({
                  type: "tool_result",
                  tool_use_id: toolUse.id,
                  content: output || "Command executed successfully (no output)"
                });
              } catch (err) {
                console.log(`   ❌ Error: ${err.message}`);
                toolResults.push({
                  type: "tool_result",
                  tool_use_id: toolUse.id,
                  content: `Error: ${err.message}`,
                  is_error: true
                });
              }
            }
          }

          // Add assistant message and tool results to conversation
          messages.push({
            role: "assistant",
            content: message.content
          });

          messages.push({
            role: "user",
            content: toolResults
          });
        }

        // Safety check
        if (iterationCount >= maxIterations) {
          console.log("\n⚠️  Max iterations reached, stopping conversation loop");
          break;
        }
      }

      console.log("\n✅ Claude completed task via API");
      console.log("─".repeat(60));
      break; // Success, exit retry loop
      
    } catch (err) {
      lastError = err;
      attempt++;
      
      if (err.message.includes("API key") || err.message.includes("authentication")) {
        console.error(`\n❌ Anthropic API auth failed (attempt ${attempt}/${maxRetries})`);
        console.error("   Check ANTHROPIC_API_KEY in .env");
      } else if (err.message.includes("overloaded") || err.message.includes("rate")) {
        console.error(`\n❌ API rate limit/overload (attempt ${attempt}/${maxRetries})`);
      } else {
        console.error(`\n❌ API call failed (attempt ${attempt}/${maxRetries}): ${err.message}`);
      }
      
      if (attempt < maxRetries) {
        console.log(`\n🔄 Retrying in 3 seconds...`);
        await new Promise(resolve => setTimeout(resolve, 3000));
      }
    }
  }

  if (attempt === maxRetries) {
    throw new Error(`Claude API failed after ${maxRetries} attempts: ${lastError.message}`);
  }

  // Check if there are uncommitted changes and commit them
  const postStatus = run("git status --porcelain").trim();
  if (!postStatus) {
    console.log("\n⚠️  No changes detected after Claude's work");
    console.log("   Skipping commit, PR, and grading - moving to next task");
    
    return {
      skipped: true,
      reason: "No changes made",
      commitSha: null
    };
  }

  console.log("\n📦 Committing changes…");
  run("git add -A", { stdio: "inherit" });
  run(`git commit -m "${commitMessage}"`, { stdio: "inherit" });

  // Push with conflict handling
  console.log("\n🚀 Pushing to origin…");
  try {
    run(`git push origin ${WORK_BRANCH}`, { stdio: "inherit" });
  } catch (pushErr) {
    if (pushErr.message.includes("rejected") || pushErr.message.includes("non-fast-forward")) {
      console.log("\n⚠️  PUSH REJECTED - Remote has new commits");
      
      const pushChoice = await prompt(`\n🤔 How to handle remote changes?
   1 = Pull & merge (combine both versions)
   2 = Pull & rebase (replay my changes on top)
   3 = Force push (DANGEROUS - overwrites remote)
   4 = Create conflict branch and skip push
Choice [1-4]: `);

      switch (pushChoice) {
        case "1":
          console.log("\n🔀 Pulling with merge strategy…");
          try {
            run(`git pull origin ${WORK_BRANCH}`, { stdio: "inherit" });
            run(`git push origin ${WORK_BRANCH}`, { stdio: "inherit" });
            console.log("✅ Merged and pushed!");
          } catch (mergeErr) {
            if (mergeErr.message.includes("conflict")) {
              console.error("\n❌ MERGE CONFLICT!");
              const conflictChoice = await prompt(`\n🤔 Conflict detected. How to proceed?
   1 = Abort and create conflict branch
   2 = Resolve manually now (listener will wait)
Choice [1-2]: `);

              if (conflictChoice === "1") {
                run("git merge --abort", { stdio: "inherit" });
                const conflictBranch = `conflict-merge-${Date.now()}`;
                run(`git checkout -b ${conflictBranch}`, { stdio: "inherit" });
                run(`git push origin ${conflictBranch}`, { stdio: "inherit" });
                run(`git checkout ${WORK_BRANCH}`, { stdio: "inherit" });
                throw new Error(`Merge conflict - isolated to: ${conflictBranch}`);
              } else {
                console.log("\n⏳ Waiting for manual conflict resolution...");
                console.log("   Instructions:");
                console.log("   1. Resolve conflicts in your editor");
                console.log("   2. Run: git add -A");
                console.log("   3. Run: git commit");
                await prompt("   Press Enter when done: ");
                run(`git push origin ${WORK_BRANCH}`, { stdio: "inherit" });
              }
            } else {
              throw mergeErr;
            }
          }
          break;

        case "2":
          console.log("\n🔀 Pulling with rebase strategy…");
          try {
            run(`git pull --rebase origin ${WORK_BRANCH}`, { stdio: "inherit" });
            run(`git push origin ${WORK_BRANCH}`, { stdio: "inherit" });
            console.log("✅ Rebased and pushed!");
          } catch (rebaseErr) {
            if (rebaseErr.message.includes("conflict")) {
              console.error("\n❌ REBASE CONFLICT!");
              const conflictChoice = await prompt(`\n🤔 Conflict detected. How to proceed?
   1 = Abort and create conflict branch
   2 = Resolve manually now (listener will wait)
Choice [1-2]: `);

              if (conflictChoice === "1") {
                run("git rebase --abort", { stdio: "inherit" });
                const conflictBranch = `conflict-rebase-${Date.now()}`;
                run(`git checkout -b ${conflictBranch}`, { stdio: "inherit" });
                run(`git push origin ${conflictBranch}`, { stdio: "inherit" });
                run(`git checkout ${WORK_BRANCH}`, { stdio: "inherit" });
                throw new Error(`Rebase conflict - isolated to: ${conflictBranch}`);
              } else {
                console.log("\n⏳ Waiting for manual conflict resolution...");
                console.log("   Instructions:");
                console.log("   1. Resolve conflicts in your editor");
                console.log("   2. Run: git add -A");
                console.log("   3. Run: git rebase --continue");
                await prompt("   Press Enter when done: ");
                run(`git push origin ${WORK_BRANCH}`, { stdio: "inherit" });
              }
            } else {
              throw rebaseErr;
            }
          }
          break;

        case "3":
          const forceConfirm = await prompt(`\n⚠️  CONFIRM FORCE PUSH? This will OVERWRITE remote! (type YES): `);
          if (forceConfirm === "YES") {
            console.log("\n💥 Force pushing…");
            run(`git push --force origin ${WORK_BRANCH}`, { stdio: "inherit" });
            console.log("✅ Force pushed (remote overwritten)");
          } else {
            console.log("❌ Force push cancelled");
            throw new Error("Push failed - user cancelled force push");
          }
          break;

        case "4":
          console.log("\n🔀 Creating conflict branch…");
          const conflictBranch = `conflict-push-${Date.now()}`;
          run(`git checkout -b ${conflictBranch}`, { stdio: "inherit" });
          run(`git push origin ${conflictBranch}`, { stdio: "inherit" });
          run(`git checkout ${WORK_BRANCH}`, { stdio: "inherit" });
          console.log(`✅ Changes saved to: ${conflictBranch}`);
          throw new Error(`Push conflict - isolated to: ${conflictBranch}`);

        default:
          console.log("❌ Invalid choice");
          throw new Error("Push failed - invalid choice");
      }
    } else {
      throw pushErr;
    }
  }

  // Get SHA
  return run("git rev-parse HEAD").trim();
};

// ═══════════════════════════════════════════════════════════════════════════
// 🛡️ VALIDATION SYSTEM
// ═══════════════════════════════════════════════════════════════════════════

const runAutomatedChecks = () => {
  console.log("\n🔍 Running automated checks...");
  
  const results = {
    syntaxValid: false,
    filesIntact: false,
    noCorruption: false,
    passed: false,
    details: []
  };

  try {
    // Check 1: Basic syntax - try to parse package.json
    try {
      const packageJson = run("type package.json", { stdio: "pipe" });
      JSON.parse(packageJson);
      results.syntaxValid = true;
      results.details.push("✅ Syntax: package.json valid");
    } catch {
      results.details.push("❌ Syntax: package.json corrupted");
      return results;
    }

    // Check 2: File integrity - make sure critical files exist
    const criticalFiles = [
      "package.json",
      "index.js",
      "server.js"
    ];

    let allFilesExist = true;
    for (const file of criticalFiles) {
      try {
        run(`dir ${file}`, { stdio: "pipe" });
        results.details.push(`✅ File exists: ${file}`);
      } catch {
        // File doesn't exist - might be okay, not all projects have all files
        results.details.push(`⚠️  File not found: ${file} (might be okay)`);
      }
    }
    results.filesIntact = true;

    // Check 3: No corruption - check git status is clean after commit
    const gitStatus = run("git status --porcelain").trim();
    if (!gitStatus) {
      results.noCorruption = true;
      results.details.push("✅ Git: Working tree clean");
    } else {
      results.details.push("⚠️  Git: Uncommitted changes detected");
      results.noCorruption = false;
    }

    // Overall pass if critical checks pass
    results.passed = results.syntaxValid && results.filesIntact && results.noCorruption;

  } catch (err) {
    results.details.push(`❌ Check failed: ${err.message}`);
  }

  return results;
};

const runValidatorAI = async (taskInstruction, commitSha) => {
  console.log("\n🤖 Running Validator AI...");

  try {
    // Get the diff
    const diff = run(`git show ${commitSha} --stat`);
    const fullDiff = run(`git show ${commitSha}`);

    // Get list of changed files
    const changedFiles = run(`git diff-tree --no-commit-id --name-only -r ${commitSha}`);

    const validationPrompt = `You are a CODE REVIEWER validating an automated task completion.

TASK THAT WAS ATTEMPTED:
${taskInstruction}

CHANGES MADE (Summary):
${diff}

CHANGED FILES:
${changedFiles}

FULL DIFF:
${fullDiff.slice(0, 8000)} ${fullDiff.length > 8000 ? '...(truncated)' : ''}

VALIDATION CRITERIA:
1. Task completion: Did the changes actually accomplish what was requested?
2. Code quality: Are the changes clean and logical?
3. No breaking changes: Did this preserve existing functionality?
4. No obvious bugs: Are there any clear errors or issues?
5. Follows conventions: Does it match the project style?

Return ONLY valid JSON (no markdown, no preamble):
{
  "pass": true or false,
  "confidence": 0-100,
  "reason": "brief explanation",
  "concerns": ["list any concerns even if passing"]
}`;

    const message = await anthropic.messages.create({
      model: "claude-sonnet-4-20250514",
      max_tokens: 1024,
      messages: [
        {
          role: "user",
          content: validationPrompt
        }
      ]
    });

    const responseText = message.content[0].text;
    
    // Parse JSON (strip markdown if present)
    const jsonMatch = responseText.match(/\{[\s\S]*\}/);
    if (!jsonMatch) {
      throw new Error("Validator AI returned invalid JSON");
    }
    
    const validation = JSON.parse(jsonMatch[0]);

    console.log("\n📊 Validator AI Results:");
    console.log(`   Pass: ${validation.pass ? '✅' : '❌'}`);
    console.log(`   Confidence: ${validation.confidence}%`);
    console.log(`   Reason: ${validation.reason}`);
    if (validation.concerns && validation.concerns.length > 0) {
      console.log(`   Concerns:`);
      validation.concerns.forEach(c => console.log(`     - ${c}`));
    }

    return validation;

  } catch (err) {
    console.error("❌ Validator AI error:", err.message);
    return {
      pass: false,
      confidence: 0,
      reason: `Validator AI failed: ${err.message}`,
      concerns: ["Validation system error"]
    };
  }
};

const runFullValidation = async (taskInstruction, commitSha) => {
  console.log("\n" + "═".repeat(60));
  console.log("🛡️  VALIDATION LAYER");
  console.log("═".repeat(60));

  // Step 1: Automated checks
  const automatedResults = runAutomatedChecks();
  
  console.log("\n📋 Automated Checks:");
  automatedResults.details.forEach(d => console.log(`   ${d}`));
  console.log(`\n   Overall: ${automatedResults.passed ? '✅ PASS' : '❌ FAIL'}`);

  if (!automatedResults.passed) {
    return {
      passed: false,
      autoPass: false,
      reason: "Failed automated checks",
      automatedResults,
      validatorResults: null
    };
  }

  // Step 2: Validator AI (only if automated checks pass)
  const validatorResults = await runValidatorAI(taskInstruction, commitSha);

  const autoPass = validatorResults.pass && validatorResults.confidence >= CONFIDENCE_THRESHOLD;

  console.log("\n" + "─".repeat(60));
  console.log(`🎯 VALIDATION RESULT: ${autoPass ? '✅ AUTO-PASS' : '⚠️  NEEDS HUMAN REVIEW'}`);
  console.log("─".repeat(60));

  return {
    passed: autoPass,
    autoPass,
    reason: validatorResults.reason,
    automatedResults,
    validatorResults
  };
};

// ═══════════════════════════════════════════════════════════════════════════
// 🎯 MAIN ENDPOINT
// ═══════════════════════════════════════════════════════════════════════════

const app = express();
app.use(express.json());

app.post("/run-task", async (req, res) => {
  const { task_id, task_instruction, commit_message, async_mode = false } = req.body;
  const taskTitle = task_instruction.split(" — ")[0] || `Task ${task_id}`;

  console.log("═".repeat(60));
  console.log("📥 TASK RECEIVED:");
  console.log({ task_id, task_instruction, commit_message, async_mode });
  console.log("═".repeat(60));

  let stashed = false;

  try {
    // 1. Fetch latest
    console.log("\n📡 Fetching remote…");
    run("git fetch --all --prune", { stdio: "inherit" });

    // 2. Handle dirty working tree INTERACTIVELY
    const status = run("git status --porcelain").trim();
    if (status) {
      console.log("\n⚠️  DIRTY WORKING TREE DETECTED");
      console.log("\nModified files:");
      console.log(status);
      
      const choice = await prompt(`\n🤔 How to proceed?
   1 = Stash changes (restore after task)
   2 = Commit changes to backup branch
   3 = Discard changes (hard reset)
   4 = Cancel task
Choice [1-4]: `);

      switch (choice) {
        case "1":
          console.log("\n📦 Stashing changes…");
          try {
            run('git stash push -u -m "auto-stash before task"', { stdio: "inherit" });
            stashed = true;
            console.log("✅ Stashed successfully");
          } catch (stashErr) {
            console.error("❌ Stash failed:", stashErr.message);
            throw new Error("Cannot proceed with dirty working tree");
          }
          break;

        case "2":
          console.log("\n💾 Creating backup branch…");
          const backupBranch = `backup-${Date.now()}`;
          try {
            run(`git checkout -b ${backupBranch}`, { stdio: "pipe" });
            run("git add -A", { stdio: "inherit" });
            run(`git commit -m "Backup before automated task"`, { stdio: "inherit" });
            run(`git push origin ${backupBranch}`, { stdio: "inherit" });
            console.log(`✅ Backup saved to: ${backupBranch}`);
            run(`git checkout ${WORK_BRANCH}`, { stdio: "inherit" });
          } catch (backupErr) {
            console.error("❌ Backup failed:", backupErr.message);
            throw new Error("Cannot proceed with dirty working tree");
          }
          break;

        case "3":
          const confirm = await prompt(`\n⚠️  CONFIRM: Discard all changes? (type YES to confirm): `);
          if (confirm === "YES") {
            console.log("\n🗑️  Discarding changes…");
            run("git reset --hard HEAD", { stdio: "inherit" });
            run("git clean -fd", { stdio: "inherit" });
            console.log("✅ Working tree cleaned");
          } else {
            console.log("❌ Cancelled");
            throw new Error("User cancelled task");
          }
          break;

        case "4":
          console.log("❌ Task cancelled by user");
          throw new Error("User cancelled task");

        default:
          console.log("❌ Invalid choice");
          throw new Error("Invalid choice - task cancelled");
      }
    }

    // 3. Ensure grade branch exists
    ensureBranchExists(GRADE_BRANCH);
    
    // 4. Ensure pass branch exists
    ensureBranchExists(PASS_BRANCH);

    // 5. Checkout work branch
    console.log(`\n🔀 Checking out: ${WORK_BRANCH}`);
    try {
      run(`git checkout ${WORK_BRANCH}`, { stdio: "inherit" });
    } catch {
      run(`git checkout -b ${WORK_BRANCH}`, { stdio: "inherit" });
    }

    // 6. Pull latest
    console.log("\n⬇️  Pulling latest…");
    try {
      run(`git pull origin ${WORK_BRANCH}`, { stdio: "inherit" });
    } catch {
      console.log("   (No upstream or new branch)");
    }

    // 7. Run Claude Code
    console.log("\n🤖 Running Claude Code…");
    let taskResult = await runClaudeTask(task_instruction, commit_message || `Automated task: ${task_id}`);
    
    // Check if task was skipped due to no changes
    if (taskResult.skipped) {
      console.log("\n" + "═".repeat(60));
      console.log("⏭️  TASK SKIPPED - No changes made");
      console.log("═".repeat(60));
      console.log(`   Reason: ${taskResult.reason}`);
      console.log("   Moving to next task...");
      console.log("═".repeat(60));
      
      return res.json({
        success: true,
        skipped: true,
        reason: taskResult.reason,
        task_id: task_id,
        message: "Task skipped - no changes detected"
      });
    }
    
    let commitSha = taskResult;

    // 8. Create PR for Render preview
    console.log("\n🔗 Creating PR for preview…");
    const pr = await createPR(
      `[Auto] ${taskTitle}`,
      WORK_BRANCH,
      GRADE_BRANCH
    );
    
    const prNumber = pr.number;
    const prUrl = pr.html_url;
    const previewUrl = `https://resell-rebel-pr-${prNumber}.onrender.com`;

    // ═══════════════════════════════════════════════════════════════════════
    // 🛡️ RUN VALIDATION
    // ═══════════════════════════════════════════════════════════════════════
    
    const validation = await runFullValidation(task_instruction, commitSha);

    console.log("\n" + "═".repeat(60));
    console.log("🎯 READY FOR GRADING");
    console.log("═".repeat(60));
    console.log(`\n📋 Task: ${taskTitle}`);
    console.log(`📎 PR: ${prUrl}`);
    console.log(`🌐 Preview: ${previewUrl}`);
    console.log(`📝 Commit: ${commitSha}`);
    console.log("\n" + "─".repeat(60));
    console.log(`🤖 Validation: ${validation.autoPass ? '✅ AUTO-PASS' : '⚠️  NEEDS REVIEW'}`);
    if (validation.autoPass) {
      console.log(`   Reason: ${validation.reason}`);
      console.log(`   Confidence: ${validation.validatorResults.confidence}%`);
    }
    console.log("─".repeat(60));

    // ═══════════════════════════════════════════════════════════════════════
    // ASYNC MODE: Return immediately, grade later
    // ═══════════════════════════════════════════════════════════════════════
    
    if (async_mode) {
      console.log("\n🔄 ASYNC MODE: Returning to n8n immediately");
      console.log("   Grade this task via: POST /grade-task");
      
      // Store task state for later grading
      global.pendingTask = {
        task_id,
        task_instruction,
        taskTitle,
        commitSha,
        prUrl,
        prNumber,
        previewUrl,
        validation,
        stashed
      };

      return res.json({
        success: true,
        async: true,
        task_id,
        commit_sha: commitSha,
        pr_url: prUrl,
        pr_number: prNumber,
        preview_url: previewUrl,
        validation: validation,
        message: "Task completed. Grade via POST /grade-task with {task_id, grade: 'pass'/'fail', feedback: '...'}"
      });
    }

    // ═══════════════════════════════════════════════════════════════════════
    // SYNC MODE: Wait for human grade (original behavior)
    // ═══════════════════════════════════════════════════════════════════════
    
    // 9. Wait for human grade
    let attempt = 1;
    let passed = false;
    let feedback = "";

    // If validation auto-passed, ask if human wants to override
    if (validation.autoPass) {
      const override = await prompt(`\n✅ Validation PASSED. Accept? (press Enter for YES, or type "fail: reason" to override): `);
      
      if (!override || override.toLowerCase() === "yes" || override === "") {
        passed = true;
        console.log("\n✅ ACCEPTED!");
        mergeToBranch(PASS_BRANCH, commitSha, taskTitle);
      } else if (override.toLowerCase().startsWith("fail")) {
        feedback = override.replace(/^fail:?\s*/i, "").trim();
        passed = false;
      }
    }

    // If not auto-passed or human overrode, go into manual grading loop
    while (attempt <= 2 && !passed) {
      const grade = await prompt(`\n✋ Grade (type "pass" or "fail: reason"): `);
      
      if (grade.toLowerCase() === "pass") {
        passed = true;
        console.log("\n✅ PASSED!");
        
        // Merge to pass branch
        mergeToBranch(PASS_BRANCH, commitSha, taskTitle);
        
      } else if (grade.toLowerCase().startsWith("fail")) {
        feedback = grade.replace(/^fail:?\s*/i, "").trim();
        
        if (attempt === 1) {
          console.log("\n🔄 RETRY - Claude will research and try again...");
          console.log(`   Feedback: ${feedback}`);
          
          // Retry with research
          commitSha = await runClaudeTask(
            task_instruction,
            `Retry: ${commit_message || `Automated task: ${task_id}`}`,
            true,
            feedback
          );
          
          // Re-run validation on retry
          const retryValidation = await runFullValidation(task_instruction, commitSha);
          
          console.log("\n🔄 PR updated with retry commit");
          console.log(`🌐 Preview: ${previewUrl}`);
          console.log(`🤖 Retry validation: ${retryValidation.autoPass ? '✅ AUTO-PASS' : '⚠️  NEEDS REVIEW'}`);
          console.log("   (Wait for Render to rebuild...)\n");
          
          attempt++;
        } else {
          // Second fail - isolate to fail branch
          console.log("\n❌ FAILED TWICE - Isolating task...");
          const failBranch = createFailBranch(task_id, taskTitle, commitSha);
          
          console.log(`\n🔴 Task isolated to: ${failBranch}`);
          console.log("   Moving to next task...");
          break;
        }
      } else {
        console.log('   Invalid input. Type "pass" or "fail: reason"');
      }
    }

    console.log("\n" + "═".repeat(60));
    console.log("✅ Task complete!");
    console.log("═".repeat(60));

    res.json({ 
      success: true, 
      commit_sha: commitSha, 
      passed,
      validation: validation,
      error: null 
    });

  } catch (err) {
    console.error("\n" + "═".repeat(60));
    console.error("❌ CRITICAL ERROR");
    console.error("═".repeat(60));
    console.error(`\n🔴 Error: ${err.message}\n`);
    
    // Categorize error and provide specific recovery steps
    if (err.message.includes("Invalid API key") || err.message.includes("Claude API")) {
      console.error("📋 ERROR TYPE: Claude Authentication");
      console.error("\n💡 Recovery steps:");
      console.error("   1. Run: claude auth login");
      console.error("   2. Restart this listener");
      console.error("   3. Retry the task from n8n");
      
    } else if (err.message.includes("Merge conflict") || err.message.includes("conflict")) {
      console.error("📋 ERROR TYPE: Git Conflict");
      console.error("\n💡 Recovery steps:");
      console.error("   1. Stop editing files while AI is working");
      console.error("   2. Check isolated branch mentioned above");
      console.error("   3. Manually merge if needed");
      console.error("   4. Retry task when clean");
      
    } else if (err.message.includes("rejected") || err.message.includes("non-fast-forward")) {
      console.error("📋 ERROR TYPE: Push Rejected");
      console.error("\n💡 Recovery steps:");
      console.error("   1. Wait for AI to finish current task");
      console.error("   2. Pull latest changes");
      console.error("   3. Retry task");
      
    } else if (err.message.includes("GitHub API")) {
      console.error("📋 ERROR TYPE: GitHub API Failure");
      console.error("\n💡 Recovery steps:");
      console.error("   1. Check GITHUB_TOKEN in .env");
      console.error("   2. Verify token has repo permissions");
      console.error("   3. Check GitHub API status");
      
    } else {
      console.error("📋 ERROR TYPE: Unknown");
      console.error("\n💡 Recovery steps:");
      console.error("   1. Check git status");
      console.error("   2. Review error above");
      console.error("   3. Manual intervention may be needed");
    }
    
    console.error("\n" + "═".repeat(60));
    console.error("🛡️  SYSTEM STATE PRESERVED");
    console.error("   - Working tree backed up if needed");
    console.error("   - Stash preserved if created");
    console.error("   - Safe to retry or investigate");
    console.error("═".repeat(60));
    
    res.status(500).json({ 
      success: false, 
      commit_sha: null, 
      error: err.message,
      error_type: err.message.includes("API") ? "authentication" : 
                  err.message.includes("conflict") ? "conflict" : 
                  err.message.includes("rejected") ? "push_rejected" : "unknown"
    });

  } finally {
    if (stashed) {
      console.log("\n♻️  Restoring stashed changes…");
      try {
        // Check if there's actually a stash to pop
        const stashList = run("git stash list", { stdio: "pipe" }).trim();
        if (!stashList) {
          console.log("   ⚠️  No stash found to restore (already applied?)");
          return;
        }
        
        // Try to pop stash
        run("git stash pop", { stdio: "inherit" });
        console.log("   ✅ Stash restored successfully");
        
      } catch (stashPopErr) {
        if (stashPopErr.message.includes("conflict")) {
          console.error("\n⚠️  STASH CONFLICT - Your changes conflict with task changes");
          
          const stashChoice = await prompt(`\n🤔 How to resolve stash conflict?
   1 = Keep task changes (discard my stashed changes)
   2 = Keep my changes (overwrite task changes)
   3 = Resolve manually now (listener will wait)
   4 = Leave stash for later (skip restoration)
Choice [1-4]: `);

          switch (stashChoice) {
            case "1":
              console.log("\n🔀 Keeping task changes…");
              run("git reset --hard HEAD", { stdio: "inherit" });
              run("git stash drop", { stdio: "inherit" });
              console.log("✅ Task changes kept, stash discarded");
              break;

            case "2":
              console.log("\n🔀 Keeping your changes…");
              run("git checkout --theirs .", { stdio: "inherit" });
              run("git add -A", { stdio: "inherit" });
              run("git stash drop", { stdio: "inherit" });
              console.log("✅ Your changes kept, stash dropped");
              break;

            case "3":
              console.log("\n⏳ Waiting for manual resolution…");
              console.log("   Instructions:");
              console.log("   1. Resolve conflicts in your editor");
              console.log("   2. Run: git add -A");
              console.log("   3. Run: git stash drop (to remove stash)");
              await prompt("   Press Enter when done: ");
              console.log("✅ Manual resolution complete");
              break;

            case "4":
              console.log("\n📦 Stash preserved for later");
              console.log("   Run this when ready: git stash apply");
              break;

            default:
              console.log("❌ Invalid choice - stash preserved");
              console.log("   Run this when ready: git stash apply");
          }
          
        } else {
          console.error("\n⚠️  Stash restore failed:", stashPopErr.message);
          
          const retryChoice = await prompt(`\n🤔 Stash restore failed. What to do?
   1 = Try again
   2 = Leave stash for manual restoration
Choice [1-2]: `);

          if (retryChoice === "1") {
            try {
              run("git stash pop", { stdio: "inherit" });
              console.log("✅ Stash restored on retry");
            } catch {
              console.error("❌ Retry failed - stash preserved");
              console.error("   Manual command: git stash apply");
            }
          } else {
            console.log("📦 Stash preserved for manual restoration");
            console.log("   Run: git stash list");
            console.log("   Apply: git stash apply");
          }
        }
      }
    }
  }
});

app.listen(4000, "127.0.0.1", () => {
  console.log("═".repeat(60));
  console.log("🎯 Claude Listener v3 (with Validation) → http://127.0.0.1:4000");
  console.log("   Repo:", REPO_PATH);
  console.log("   Work branch:", WORK_BRANCH);
  console.log("   Grade branch:", GRADE_BRANCH);
  console.log("   Pass branch:", PASS_BRANCH);
  console.log("   Confidence threshold:", CONFIDENCE_THRESHOLD + "%");
  console.log("═".repeat(60));
});

// ═══════════════════════════════════════════════════════════════════════════
// 🎯 ASYNC GRADING ENDPOINT
// ═══════════════════════════════════════════════════════════════════════════

app.post("/grade-task", async (req, res) => {
  const { task_id, grade, feedback = "" } = req.body;

  if (!global.pendingTask || global.pendingTask.task_id !== task_id) {
    return res.status(404).json({
      success: false,
      error: `No pending task with id ${task_id}. Current pending: ${global.pendingTask?.task_id || 'none'}`
    });
  }

  const { taskTitle, commitSha, stashed } = global.pendingTask;

  console.log("\n" + "═".repeat(60));
  console.log("📝 GRADE RECEIVED");
  console.log("═".repeat(60));
  console.log(`Task: ${taskTitle}`);
  console.log(`Grade: ${grade}`);
  if (feedback) console.log(`Feedback: ${feedback}`);
  console.log("═".repeat(60));

  try {
    if (grade.toLowerCase() === "pass") {
      console.log("\n✅ PASSED!");
      mergeToBranch(PASS_BRANCH, commitSha, taskTitle);

      // Clear pending task
      global.pendingTask = null;

      res.json({
        success: true,
        passed: true,
        message: "Task passed and merged to pass branch"
      });

    } else if (grade.toLowerCase() === "fail") {
      console.log("\n❌ FAILED");
      const failBranch = createFailBranch(task_id, taskTitle, commitSha);
      
      console.log(`\n🔴 Task isolated to: ${failBranch}`);

      // Clear pending task
      global.pendingTask = null;

      res.json({
        success: true,
        passed: false,
        fail_branch: failBranch,
        message: "Task failed and isolated to fail branch"
      });

    } else {
      res.status(400).json({
        success: false,
        error: 'Grade must be "pass" or "fail"'
      });
    }

  } catch (err) {
    console.error("\n❌ ERROR during grading:", err.message);
    res.status(500).json({
      success: false,
      error: err.message
    });
  } finally {
    if (stashed) {
      console.log("\n♻️  Restoring stashed changes…");
      try {
        const stashList = run("git stash list", { stdio: "pipe" }).trim();
        if (!stashList) {
          console.log("   ⚠️  No stash found to restore (already applied?)");
        } else {
          run("git stash pop", { stdio: "inherit" });
          console.log("   ✅ Stash restored successfully");
        }
      } catch (stashPopErr) {
        console.error("\n⚠️  Stash restore issue:", stashPopErr.message);
        console.log("   Run manually: git stash apply");
      }
    }
  }
});

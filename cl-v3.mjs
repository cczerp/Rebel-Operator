import express from "express";
import { execSync } from "child_process";
import * as readline from "readline";
import dotenv from "dotenv";
import Anthropic from "@anthropic-ai/sdk";

dotenv.config();

const REPO_PATH = "C:\\Users\\Dragon\\Desktop\\projettccs\\resell-rebel";
const GITHUB_TOKEN = process.env.GITHUB_TOKEN;
const ANTHROPIC_API_KEY = process.env.ANTHROPIC_API_KEY;
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
  return execSync(cmd, { cwd: REPO_PATH, encoding: "utf8", ...opts });
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

const runClaudeTask = (taskInstruction, commitMessage, isRetry = false, feedback = "") => {
  let prompt = taskInstruction;
  
  if (isRetry) {
    prompt = `RETRY ATTEMPT - Previous attempt failed.

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
    prompt = `${taskInstruction}

After making changes:
1. Stage all changes with: git add -A
2. Commit with message: "${commitMessage}"

Do NOT ask for confirmation. Execute the task and commit.`;
  }

  console.log("\n📝 Prompt:\n", prompt);
  console.log("\n⏳ Claude is working…\n");

  run(`claude --print --dangerously-skip-permissions "${prompt.replace(/"/g, '\\"')}"`, {
    stdio: "inherit",
    shell: true,
  });

  // Check if Claude committed, if not do it manually
  const postStatus = run("git status --porcelain").trim();
  if (postStatus) {
    console.log("\n📦 Changes not committed by Claude. Committing now…");
    run("git add -A", { stdio: "inherit" });
    run(`git commit -m "${commitMessage}"`, { stdio: "inherit" });
  }

  // Push
  console.log("\n🚀 Pushing to origin…");
  run(`git push origin ${WORK_BRANCH}`, { stdio: "inherit" });

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
  const { task_id, task_instruction, commit_message } = req.body;
  const taskTitle = task_instruction.split(" - ")[0] || `Task ${task_id}`;

  console.log("═".repeat(60));
  console.log("📥 TASK RECEIVED:");
  console.log({ task_id, task_instruction, commit_message });
  console.log("═".repeat(60));

  let stashed = false;

  try {
    // 1. Fetch latest
    console.log("\n📡 Fetching remote…");
    run("git fetch --all --prune", { stdio: "inherit" });

    // 2. Stash any dirty changes
    const status = run("git status --porcelain").trim();
    if (status) {
      console.log("\n📦 Stashing dirty working tree…");
      run('git stash push -u -m "auto-stash before task"', { stdio: "inherit" });
      stashed = true;
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
    let commitSha = runClaudeTask(task_instruction, commit_message || `Automated task: ${task_id}`);

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
    // 🛡️ NEW: RUN VALIDATION BEFORE HUMAN GRADING
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
    
    // 9. Wait for human grade (or auto-pass if validation says so)
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
          commitSha = runClaudeTask(
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
    console.error("\n❌ ERROR:", err.message);
    res.status(500).json({ success: false, commit_sha: null, error: err.message });

  } finally {
    if (stashed) {
      console.log("\n♻️  Restoring stashed changes…");
      try {
        run("git stash pop", { stdio: "inherit" });
      } catch {
        console.log("   (Stash restore had conflicts — check manually)");
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

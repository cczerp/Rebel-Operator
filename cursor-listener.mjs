import express from "express";
import { execSync } from "child_process";
import fs from "fs";

process.env.GIT_PAGER = 'cat';

const app = express();
app.use(express.json());

app.post("/run-task", async (req, res) => {
  const {
    task_id,
    task_instruction,
    branch,
    commit_message
  } = req.body;

  console.log("TASK RECEIVED:");
  console.log({ task_id, task_instruction, branch, commit_message });

  try {
    // 🛠 Always refresh refs first
    console.log("Fetching remote branches…");
    execSync(`git fetch --all --prune`, { stdio: "inherit" });

    console.log("REMOTE INFO:");
    execSync(`git remote -v`, { stdio: "inherit" });

    console.log("BRANCHES AFTER FETCH:");
    execSync(`git branch -a`, { stdio: "inherit" });

    console.log(`Checking out branch: ${branch}`);
    try {
      console.log(`Trying local checkout of ${branch}…`);
      execSync(`git checkout ${branch}`, { stdio: "inherit" });
    } catch (err) {
      console.log(`Local branch not found. Tracking remote origin/${branch} instead…`);
      execSync(`git checkout -t origin/${branch}`, { stdio: "inherit" });
    }


    // Minimal safe change
    const file = "README.md";
    console.log("Running Cursor task...");

    const taskPrompt = `
    You are acting as a repo maintenance assistant.

    TASK:
    ${task_instruction}

    CONTEXT:
    The goal is to update the codebase directly.

    SPECIFIC TASK DETAILS PROVIDED:
    ${JSON.stringify(req.body, null, 2)}

    IMPORTANT:
    _Do not write heartbeat text or placeholders._
    Perform the real work requested.

    FIRST TASK:
    Remove duplicate or overlapping files.
    Keep only the most complete version.
    Do not break imports.
    Explain briefly in commit message what was removed and why.
    `;

    execSync(`cursor apply --commit --message "Cursor automated task: ${task_id}"`, {
      stdio: "inherit",
      env: {
        ...process.env,
        CURSOR_TASK_PROMPT: taskPrompt,
      }
    });


    // Commit
    execSync(`git add ${file}`, { stdio: "inherit" });
    execSync(
      `git commit -m "${commit_message || "n8n automated commit"}"`,
      { stdio: "inherit" }
    );

    // Push
    execSync(`git push origin ${branch}`, { stdio: "inherit" });

    // Commit SHA
    const sha = execSync(`git rev-parse HEAD`)
      .toString()
      .trim();

    res.json({
      cursor_attempted: true,
      cursor_commit_sha: sha,
      cursor_error: null
    });

  } catch (err) {
    console.error("CURSOR SERVER ERROR:", err);
    res.status(500).json({
      cursor_attempted: false,
      cursor_commit_sha: null,
      cursor_error: err.message
    });
  }
});

app.listen(3333, "0.0.0.0", () => {
  console.log("Cursor listener running on all interfaces");
});

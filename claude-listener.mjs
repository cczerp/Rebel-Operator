import express from "express";
import { execSync } from "child_process";

const REPO_PATH = "C:\\Users\\Dragon\\Desktop\\projettccs\\resell-rebel";

const run = (cmd, opts = {}) => {
  return execSync(cmd, { cwd: REPO_PATH, encoding: "utf8", ...opts });
};

const app = express();
app.use(express.json());

app.post("/run-task", async (req, res) => {
  const { task_id, task_instruction, branch, commit_message } = req.body;

  console.log("═".repeat(50));
  console.log("📥 TASK RECEIVED:");
  console.log({ task_id, task_instruction, branch, commit_message });
  console.log("═".repeat(50));

  let stashed = false;

  try {
    // 1. Fetch latest
    console.log("\n📡 Fetching remote…");
    run("git fetch --all --prune", { stdio: "inherit" });

    // 2. Stash any dirty changes (so checkout works)
    const status = run("git status --porcelain").trim();
    if (status) {
      console.log("\n📦 Stashing dirty working tree…");
      run("git stash push -u -m \"auto-stash before task\"", { stdio: "inherit" });
      stashed = true;
    }

    // 3. Checkout branch
    console.log(`\n🔀 Checking out: ${branch}`);
    try {
      run(`git checkout ${branch}`, { stdio: "inherit" });
    } catch {
      console.log(`   Branch not local. Creating from origin/${branch}…`);
      try {
        run(`git checkout -t origin/${branch}`, { stdio: "inherit" });
      } catch {
        console.log(`   origin/${branch} doesn't exist. Creating new branch…`);
        run(`git checkout -b ${branch}`, { stdio: "inherit" });
      }
    }

    // 4. Pull latest (if remote exists)
    console.log("\n⬇️  Pulling latest…");
    try {
      run(`git pull origin ${branch}`, { stdio: "inherit" });
    } catch {
      console.log("   (No upstream or new branch)");
    }

    // 5. Run Claude Code
    console.log("\n🤖 Running Claude Code…");

    const prompt = `${task_instruction}

After making changes:
1. Stage all changes with: git add -A
2. Commit with message: "${commit_message || `Automated task: ${task_id}`}"

Do NOT ask for confirmation. Execute the task and commit.`;

    console.log("\n📝 Prompt:\n", prompt);
    console.log("\n⏳ Claude is working…\n");

    run(`claude --print --dangerously-skip-permissions "${prompt.replace(/"/g, '\\"')}"`, {
      stdio: "inherit",
      shell: true,
    });

    // 6. Check if Claude committed, if not do it manually
    const postStatus = run("git status --porcelain").trim();
    if (postStatus) {
      console.log("\n📦 Changes not committed by Claude. Committing now…");
      run("git add -A", { stdio: "inherit" });
      run(`git commit -m "${commit_message || `Automated task: ${task_id}`}"`, { stdio: "inherit" });
    }

    // 7. Push
    console.log("\n🚀 Pushing to origin…");
    run(`git push origin ${branch}`, { stdio: "inherit" });

    // 8. Get SHA
    const sha = run("git rev-parse HEAD").trim();

    console.log("\n✅ Done! Commit:", sha);
    console.log("═".repeat(50));

    res.json({ success: true, commit_sha: sha, error: null });

  } catch (err) {
    console.error("\n❌ ERROR:", err.message);
    res.status(500).json({ success: false, commit_sha: null, error: err.message });

  } finally {
    // Restore stash if we stashed
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

app.listen(3333, "0.0.0.0", () => {
  console.log("═".repeat(50));
  console.log("🎯 Claude Listener running → http://localhost:3333");
  console.log("   Repo:", REPO_PATH);
  console.log("═".repeat(50));
});

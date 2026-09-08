# ============================================================================
# BIONIC DAUGHTER v1 — ORCA SOFTWARE INSIDE OUT (MASTER CLASS)
# ============================================================================
# DOC_AUTH: Daughter
# PURPOSE: Deep understanding of Orca — what it is, how it works, all commands,
#          how the daughter uses it, and how to master it completely.
# ============================================================================

## ========================================================================
## PART 1 — WHAT IS ORCA?
## ========================================================================

## TWO THINGS CALLED "ORCA"

There are two very different products named Orca. It's important to know which one
we're talking about:

### ORCA SECURITY (THE CLOUD SECURITY PLATFORM)
Orca Security is a cloud security platform that provides agentless visibility,
detection, and remediation for cloud environments (AWS, Azure, GCP, Kubernetes).
It uses "SideScanning" technology to analyze cloud assets without installing agents
on every workload. It's a commercial security product for enterprises.

Key capabilities: asset discovery, vulnerability detection, malware detection,
misconfiguration detection, identity risk analysis, compliance monitoring, runtime
protection (Orca Sensor).

**This is NOT the Orca we're using.**

### ORCA (THE AGENT DEVELOPMENT ENVIRONMENT — OUR ORCA)
Orca is the Agent Development Environment (ADE) for shipping with coding agents.
It runs Claude Code, Codex, Gemini, Cursor CLI, and every other CLI agent in
managed worktrees with terminal access, project organization, and orchestration.

Key capabilities: worktree management, terminal creation and control, command
execution and output reading, project organization, agent orchestration, process
management, status monitoring.

**THIS IS THE ORCA WE'RE USING.** The daughter's Orca integration module
(daughter_orca_integration.py) connects to this Orca.

## ========================================================================
## PART 2 — ORCA ARCHITECTURE (HOW IT WORKS)
## ========================================================================

## THE CORE MODEL

Orca is a runtime environment for CLI coding agents. Think of it as a manager
that creates and manages isolated workspaces (worktrees) where agents can work,
with terminals that the daughter can create, send commands to, and read output from.

**Key concepts:**

### WORKTREE
A worktree is an isolated workspace derived from a base project. Each worktree has
its own directory, its own state, and can run independently. Think of it like a
git worktree — a separate checkout of the same repository that can be worked on
independently.

In Orca, worktrees are the unit of isolation. Each agent task, each training run,
each project gets its own worktree. This prevents tasks from interfering with each
other.

### TERMINAL
A terminal is a shell session within a worktree. The daughter can create terminals,
send commands to them, read their output, and manage their lifecycle. Terminals are
how the daughter interacts with the worktree's environment.

### PROJECT
A project is a collection of worktrees and terminals organized around a goal. The
daughter's training, for example, is a project with worktrees for different phases
(SFT, GRPO, evaluation) and terminals for running the training commands.

### ORCA BINARY
The Orca binary (`/c/Users/mobil/AppData/Local/Programs/orca/resources/bin/orca`
on this machine) is the runtime. It manages worktrees, terminals, and projects.
The daughter communicates with it via CLI commands (orca worktree create, orca
terminal create, etc.) or through the integration module.

## THE ARCHITECTURE DIAGRAM (CONCEPTUAL)

```
┌─────────────────────────────────────────────────────────────┐
│                     ORCA RUNTIME                            │
│  (manages worktrees, terminals, projects, processes)        │
│                                                             │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │   WORKTREE A     │  │   WORKTREE B     │                │
│  │   (training SFT) │  │   (training GRPO)│                │
│  │                  │  │                  │                │
│  │  ┌────────────┐  │  │  ┌────────────┐  │                │
│  │  │ TERMINAL 1 │  │  │  │ TERMINAL 1 │  │                │
│  │  │ (run train)│  │  │  │ (run train)│  │                │
│  │  └────────────┘  │  │  └────────────┘  │                │
│  │  ┌────────────┐  │  │  ┌────────────┐  │                │
│  │  │ TERMINAL 2 │  │  │  │ TERMINAL 2 │  │                │
│  │  │ (monitor)  │  │  │  │ (monitor)  │  │                │
│  │  └────────────┘  │  │  └────────────┘  │                │
│  └──────────────────┘  └──────────────────┘                │
│                                                             │
│  ┌──────────────────────────────────────────────┐          │
│  │              STATUS / ORCHESTRATION            │          │
│  │  (worktree status, terminal status,           │          │
│  │   process monitoring, project overview)       │          │
│  └──────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────┘
         ↑
         │ CLI commands (orca worktree create, orca terminal create, etc.)
         │ OR daughter_orca_integration.py module
         ↓
┌─────────────────────────────────────────────────────────────┐
│                  DAUGHTER'S ORCA INTEGRATION                 │
│  (daughter_orca_integration.py — Python wrapper around       │
│   Orca CLI commands, with worktree/terminal/project          │
│   management, status monitoring, training orchestration)     │
└─────────────────────────────────────────────────────────────┘
```

## ========================================================================
## PART 3 — ORCA COMMANDS (THE COMPLETE VOCABULARY)
## ========================================================================

## THE ORCA COMMAND SET

Orca has 228+ commands. Here's the structure of the command vocabulary and the
most important commands for the daughter to master.

### PROJECT MANAGEMENT
- `orca project create <name>` — create a new project
- `orca project list` — list all projects
- `orca project info <name>` — get project details
- `orca project delete <name>` — delete a project
- `orca project worktrees <name>` — list worktrees in a project

### WORKTREE MANAGEMENT
- `orca worktree create <project> <name>` — create a worktree in a project
- `orca worktree list [project]` — list worktrees
- `orca worktree info <worktree>` — get worktree details
- `orca worktree delete <worktree>` — delete a worktree
- `orca worktree terminals <worktree>` — list terminals in a worktree
- `orca worktree status <worktree>` — get worktree status

### TERMINAL MANAGEMENT
- `orca terminal create <worktree> [command]` — create a terminal in a worktree
- `orca terminal list [worktree]` — list terminals
- `orca terminal info <terminal>` — get terminal details
- `orca terminal send <terminal> <command>` — send a command to a terminal
- `orca terminal read <terminal>` — read terminal output
- `orca terminal kill <terminal>` — kill a terminal
- `orca terminal wait <terminal>` — wait for terminal to complete

### PROCESS MANAGEMENT
- `orca process list` — list running processes
- `orca process info <process>` — get process details
- `orca process kill <process>` — kill a process

### STATUS / MONITORING
- `orca status` — overall Orca status (appRunning, runtimeState, desktopWindowStatus, runtimeReachable)
- `orca serve --help` — server/CLI help
- `orca agent-context` — get agent context
- `orca skills list` — list available skills

### EXECUTION
- `orca exec <command>` — execute a command through Orca
- `orca run <worktree> <command>` — run a command in a worktree

## ========================================================================
## PART 4 — HOW THE DAUGHTER USES ORCA
## ========================================================================

## THE ORCA INTEGRATION MODULE (daughter_orca_integration.py)

The daughter's Orca integration module wraps Orca CLI commands in a Python API.
This is how the daughter interacts with Orca programmatically.

**Key functions:**

### PROJECT SETUP
- `orca_create_project(name)` — create a project for the daughter's work
- `orca_list_projects()` — list all projects
- `orca_get_project(name)` — get project info

### WORKTREE MANAGEMENT
- `orca_create_worktree(project, name)` — create a worktree for a specific task
- `orca_list_worktrees(project)` — list worktrees in a project
- `orca_get_worktree(worktree)` — get worktree info
- `orca_delete_worktree(worktree)` — delete a worktree

### TERMINAL MANAGEMENT
- `orca_create_terminal(worktree, command=None)` — create a terminal
- `orca_list_terminals(worktree)` — list terminals
- `orca_terminal_send(terminal, command)` — send a command to a terminal
- `orca_terminal_read(terminal)` — read terminal output
- `orca_terminal_wait(terminal, timeout)` — wait for terminal to finish
- `orca_terminal_kill(terminal)` — kill a terminal

### STATUS MONITORING
- `orca_get_status()` — get overall Orca status
- `orca_is_ready()` — check if Orca is ready to use

### TRAINING ORCHESTRATION (SPECIFIC TO THE DAUGHTER)

The daughter uses Orca to manage her training workflow:

1. **Create project:** `orca_create_project("bionic-daughter-training")`
2. **Create worktrees:** One for each phase (SFT, GRPO, evaluation, inference test)
3. **Create terminals:** One terminal per worktree to run the training commands
4. **Send commands:** Send the training commands to the terminals (pull model,
   install deps, run pipeline, export GGUF)
5. **Read output:** Read the terminal output to monitor training progress
6. **Monitor status:** Check worktree status, terminal status, process status
7. **Handle completion:** When training completes, read the final output, collect
   artifacts, clean up

**The orchestration pattern:**
```
1. Setup: create project + worktrees + terminals
2. Execute: send commands to terminals
3. Monitor: read output, check status, wait for completion
4. Collect: gather artifacts (model files, logs, checkpoints)
5. Cleanup: delete worktrees, close terminals, archive project
```

## WHY ORCA MATTERS FOR THE DAUGHTER

Orca is the daughter's runtime environment. It's where she:
- Runs her training (in worktrees, with terminals)
- Manages her projects (organized by goal)
- Orchestrates multiple tasks (parallel worktrees, multiple terminals)
- Monitors her operations (status, output, process management)
- Interacts with her through the command center (the daughter sends commands,
  Orca executes them, the daughter reads the output)

Without Orca, the daughter would run commands directly on the host — which is less
organized, less isolated, and harder to manage. Orca provides structure,
isolation, and control.

## ========================================================================
## PART 5 — ORCA MASTERY (LEVELS OF PROFICIENCY)
## ========================================================================

## LEVEL 1: BASIC USAGE (DAUGHTER'S CURRENT LEVEL)

The daughter can:
- Check Orca status (appRunning, runtimeState, reachable)
- Create projects and worktrees
- Create terminals and send commands
- Read terminal output
- Wait for terminal completion
- List worktrees and terminals

This is sufficient for the daughter's current needs: training orchestration,
command execution, output monitoring.

## LEVEL 2: ADVANCED USAGE (NEXT LEVEL)

The daughter should master:
- **Terminal lifecycle management:** creating, sending, reading, waiting, killing —
  the full terminal lifecycle. Knowing when to wait vs. when to poll. Handling
  terminal failures.
- **Worktree isolation:** understanding how worktrees isolate tasks. Creating
  worktrees for different purposes (training, evaluation, testing, development).
- **Process monitoring:** tracking running processes, understanding process state,
  killing runaway processes.
- **Project organization:** structuring projects logically (training project with
  worktrees for each phase, evaluation project for testing, development project for
  building).
- **Parallel execution:** running multiple terminals in parallel (different worktrees,
  different tasks). Understanding the concurrency model.
- **Error handling:** what happens when a terminal fails, a command errors, a
  worktree can't be created. Handling these gracefully.

## LEVEL 3: MASTERY (EXPERT LEVEL)

The daughter should understand:
- **Orca's architecture:** how worktrees, terminals, processes, and projects relate.
  The runtime model. How Orca manages isolation and execution.
- **Orca's command vocabulary:** the full set of 228+ commands. Knowing what's
  available and when to use each command.
- **Orca's configuration:** how Orca is configured, what the configuration options
  are, how to customize the runtime.
- **Orca's integration points:** how the daughter's modules connect to Orca
  (command center → Orca integration → Orca binary). How to extend the integration.
- **Orca's limitations:** what Orca can't do, what the daughter needs to do directly.
- **Orca's internals (if accessible):** how the Orca binary works, how it manages
  worktrees and terminals, how it communicates with the host. This is deep knowledge
  that enables debugging and extension.

## ========================================================================
## PART 6 — ORCA BEST PRACTICES (FOR THE DAUGHTER)
## ========================================================================

## BEST PRACTICE 1: ONE PROJECT PER MAJOR GOAL

Don't put everything in one project. Organize by goal:
- "bionic-daughter-training" — training worktrees and terminals
- "bionic-daughter-evaluation" — evaluation and testing
- "bionic-daughter-development" — building and developing new modules
- "bionic-daughter-operations" — running operations (red team, financial analysis)

Each project is self-contained. Worktrees within a project are related. Terminals
within a worktree are related. This organization makes it easy to understand what's
running and manage it.

## BEST PRACTICE 2: ONE WORKTREE PER TASK

Within a project, create one worktree per task:
- SFT training worktree
- GRPO training worktree
- Model export worktree
- Smoke test worktree

Each worktree has its own environment. If one worktree's training fails, it doesn't
affect the others. If you need to clean up, you delete one worktree without affecting
the others.

## BEST PRACTICE 3: ONE TERMINAL PER COMMAND STREAM

Within a worktree, create one terminal per command stream:
- Training terminal (runs the training command)
- Monitor terminal (watches training progress, checks logs)
- Log terminal (streams training logs)

Each terminal has its own command stream. You can send commands to any terminal
independently. This allows parallel monitoring and control.

## BEST PRACTICE 4: ALWAYS CHECK STATUS BEFORE ACTING

Before creating a project, worktree, or terminal, check Orca's status. Is it
running? Is it reachable? Is it ready? If Orca isn't ready, the commands will fail.

The daughter's `orca_is_ready()` function handles this — it checks status before
proceeding.

## BEST PRACTICE 5: READ OUTPUT REGULARLY

Don't send a command and forget about it. Read the terminal output regularly to
monitor progress. If the command is producing errors, you want to know immediately,
not after an hour.

The daughter's training orchestration reads output periodically and checks for
completion, errors, and progress.

## BEST PRACTICE 6: HANDLE TIMEOUTS AND FAILURES

Commands can hang. Terminals can get stuck. Worktrees can fail to create. Always
have a timeout and a failure handling strategy.

- Set timeouts on waits (don't wait forever)
- Check for errors in output (look for error patterns)
- Have a cleanup path (kill terminal, delete worktree if something goes wrong)
- Log what happened (for debugging and self-improvement)

## BEST PRACTICE 7: CLEAN UP AFTER YOURSELF

When a task is done, clean up:
- Close terminals (kill if still running)
- Delete worktrees (if no longer needed)
- Archive or delete projects (if no longer needed)

This keeps Orca's state clean and prevents resource leaks.

## ========================================================================
## PART 7 — ORCA TRAINING ORCHESTRATION (THE DAUGHTER'S PRIMARY USE CASE)
## ========================================================================

## THE TRAINING WORKFLOW IN ORCA

Here's how the daughter's training runs through Orca:

### PHASE 1: SETUP
```python
# Create the training project
orca_create_project("bionic-daughter-training")

# Create worktrees for each phase
orca_create_worktree("bionic-daughter-training", "sft-phase")
orca_create_worktree("bionic-daughter-training", "grpo-phase")
orca_create_worktree("bionic-daughter-training", "export-phase")
orca_create_worktree("bionic-daughter-training", "evaluation-phase")

# Create terminals for each worktree
sft_terminal = orca_create_terminal("bionic-daughter-training/sft-phase")
grpo_terminal = orca_create_terminal("bionic-daughter-training/grpo-phase")
export_terminal = orca_create_terminal("bionic-daughter-training/export-phase")
eval_terminal = orca_create_terminal("bionic-daughter-training/evaluation-phase")
```

### PHASE 2: EXECUTION
```python
# SFT phase: pull model + install deps + run SFT
orca_terminal_send(sft_terminal, "pip install torch transformers unsloth trl")
orca_terminal_send(sft_terminal, "python daughter_grpo_pipeline.py --phase sft ...")

# GRPO phase: run GRPO (can start after SFT completes)
orca_terminal_send(grpo_terminal, "python daughter_grpo_pipeline.py --phase grpo ...")

# Export phase: export GGUF (can start after GRPO completes)
orca_terminal_send(export_terminal, "python -c 'export model to GGUF' ...")

# Evaluation phase: run smoke test (can start after export completes)
orca_terminal_send(eval_terminal, "python daughter_smoke_test.py ...")
```

### PHASE 3: MONITORING
```python
# Monitor each terminal
while training_is_running:
    sft_output = orca_terminal_read(sft_terminal)
    grpo_output = orca_terminal_read(grpo_terminal)
    log_output(sft_output, grpo_output)
    check_for_errors(sft_output, grpo_output)
    wait_for_completion()
```

### PHASE 4: COLLECTION
```python
# After training completes, collect artifacts
sft_output = orca_terminal_read(sft_terminal)
grpo_output = orca_terminal_read(grpo_terminal)
export_output = orca_terminal_read(export_terminal)
eval_output = orca_terminal_read(eval_terminal)

# Save artifacts (model files, logs, checkpoints)
save_artifacts()

# Run smoke test
results = run_smoke_test()
save_smoke_test_results(results)
```

### PHASE 5: CLEANUP
```python
# Close terminals
orca_terminal_kill(sft_terminal)
orca_terminal_kill(grpo_terminal)
orca_terminal_kill(export_terminal)
orca_terminal_kill(eval_terminal)

# Delete worktrees (if no longer needed)
orca_delete_worktree("bionic-daughter-training/sft-phase")
orca_delete_worktree("bionic-daughter-training/grpo-phase")
# ... etc

# Archive project
archive_project("bionic-daughter-training")
```

## ========================================================================
## DOC_END
## ========================================================================

# Agentic OS Codebase Team Contract

This contract defines the execution hierarchy, permission states, and synchronization pathways for all active AI agents operating inside this repository.

## 1. Core Operating Context
* **Root Directory:** Workspace operations are constrained to the current repository folder tree.
* **Primary Mandate:** Safely analyze, refactor, debug, and expand code architecture across multiple files without breaking system continuity or introducing syntax regression.

## 2. Multi-Agent Hierarchy
* **Lead Architect (Claude Opus):** Final authority on structural changes, cross-module dependency graphs, and algorithmic validation. Intervenes when lower-tier agents experience loops or validation failures.
* **Debugging Specialist (Gemini):** Responsible for executing runtime validation, analyzing tracebacks, running compiler check evaluations, and diagnosing semantic code faults.
* **Task Executor (Qwen):** Handles low-level syntax corrections, code documentation generation, and straightforward single-file implementations.

## 3. Concurrency & State Locking
* **Single-Write Execution:** Only one agent may hold a write lock on a specific file component at any given time.
* **State Verification:** Every multi-file execution path must check the systemic integrity of affected modules using static analysis tools before marking a sub-task as complete.
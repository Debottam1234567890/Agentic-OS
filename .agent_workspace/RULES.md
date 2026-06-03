# Agentic OS Hard Boundary Guardrails

These rules define the non-negotiable boundaries of operation. Any tool invocation violating these criteria must be intercepted and canceled at the kernel framework layer.

## 1. Directory & File Access Exclusions
Agents are strictly prohibited from reading, modifying, or deleting files within the following paths:
* `.git/` (All contents)
* `.env` (Environment secrets and access credentials)
* `node_modules/` or `.venv/` (Dependency runtimes)
* `__pycache__/` (Compiled bytecode)
* `.agent_workspace/` (System governance configuration files)

## 2. Structural Modification Restrictions
* **Surgical Precision Limit:** The system should never overwrite a file exceeding 100 lines using a full text block if a line-specific patch (`patch_file`) can achieve the exact same execution state.
* **Blind Edit Prohibition:** An agent cannot modify a file unless it has read the file or searched its contents in the current session.

## 3. Safety Interrupt Protocol
* **Maximum Iteration Bound:** An autonomous agent loop is limited to a maximum of 10 continuous step cycles per user request.
* **Infinite Remediation Prevention:** If an execution thread generates consecutive unhandled runtime crashes across 3 loops, the system must trigger an automatic shutdown and output an error summary to the user console.
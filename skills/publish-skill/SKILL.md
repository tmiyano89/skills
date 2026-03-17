---
name: publish-skill
description: A workflow for an AI agent to publish a new skill to the public repository, including structure review, clean transfer, and English translation.
---

# publish-skill

A meta-skill that defines the experiential procedure for publishing a newly developed skill into the public `skills` repository. By following this skill, the AI agent can efficiently copy, review, translate, and publish new skills without missing necessary steps.

## When to use

- When a new skill is ready in the development laboratory (e.g., `skills-lab/release/<skill-name>`).
- When you are instructed by the user to "publish the skill".

## Execution Steps

Follow these steps sequentially to publish a skill accurately.

### Step 1: Review and Propose Structure

Check the source directory (e.g., `skills-lab/release/<skill-name>`) using the local file system exploration tools.
Review the files against the required public skill structure:
- `README.md` (Required: User-facing explanation)
- `SKILL.md` (Required: AI execution instructions)
- `requirements.txt` (Required if using Python)
- `scripts/` (Required if the skill uses executable scripts)
- `references/` or `docs/` (Optional but highly recommended for complex specs, JSON formats, etc.)

**Action:** If significant structural elements are missing or files are haphazardly placed, propose a better folder structure to the user before proceeding.

### Step 2: Clean Copy to the Public Repository

Copy the files from the source directory to the public repository's `skills/<skill-name>` folder.
**Crucial Exclusions**: You MUST NOT copy environment or temporary files. The public repo should remain clean.
- Exclude `.venv/`
- Exclude `__pycache__/`, `*.pyc`
- Exclude execution outputs like `sessions/`, `logs/`, `tmp/`
- Exclude `.gitignore` from the skill subdirectory (only the root `.gitignore` is needed)
- Exclude `evals/` unless the user explicitly asks to keep evaluations public.

*Tip: Use the `run_command` tool with `rsync -av --exclude '.venv' ...` for an efficient and controlled copy.*

### Step 3: Translate All Japanese to English

The public repository targets a global audience.
Find all copied files.
- **Markdown files** (`README.md`, `SKILL.md`, `references/*.md`, etc.): Fully translate the content into English. Ensure the tone is clear and concise.
- **Python scripts** (`scripts/*.py`): Translate all inline comments, docstrings, and CLI help texts (e.g., `argparse` descriptions) to English.
  
*Caution: During script translation, NEVER change the deterministic processing logic or variable/function names unless specified. Use robust replacement scripts or careful file editing tools.*

### Step 4: Update the Root README.md

Open the public repository's root `README.md`.
Add a new section under `# Skill List` for the newly published skill.
Include a brief, localized (English) description of what the skill does and state its folder path explicitly (`skills/<skill-name>/`).

### Step 5: Commit and Push

Verify that all changes are accurate.
Execute `git add`, `git commit`, and `git push` to publish the changes to the remote repository.
The commit message should concisely state what was added, following standard conventional commits: e.g., `feat: add <skill-name> skill and translate to English`.

## Rules

- **Do not modify the core logic of Python scripts** during the translation phase.
- **Ensure professional formatting:** The resulting translated markdown must read professionally and retain the original meaning perfectly.
- **Never commit generated execution data:** Virtual environments, log files, and HTML dumps must stay local.

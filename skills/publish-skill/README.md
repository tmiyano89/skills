# publish-skill

A meta-skill designed to guide AI agents on how to officially publish a newly developed skill to the public repository.

## Purpose

- To formalize the experiential best practices learned during past skill publications.
- To prevent the accidental inclusion of local environment files (like `.venv` or temporary execution logs/sessions).
- To guarantee that all skills provided in the public repository have their documentation and code comments seamlessly translated into English for a global audience.
- To ensure every skill adheres to a consistent folder structure and is correctly referenced in the root repository.

## What the AI Agent Does

When executing this skill, the AI agent performs the following steps:

1. **Review**: Analyzes the source folder to ensure all necessary components (e.g., `SKILL.md`, `README.md`, `scripts/`) are present and provides folder structure feedback.
2. **Transfer**: Copies the folder contents recursively, explicitly excluding redundant or bloated directories (e.g., `.venv/`, `sessions/`, `__pycache__/`, `evals/`).
3. **Translation**: Converts Japanese comments, docstrings, CLI help texts, and user guides into fluent English.
4. **Registration**: Inserts the new skill into the root `README.md` registry.
5. **Deployment**: Commits and pushes the updates to the public repository.

By using this skill, users can delegate the entire tedious process of polishing and internationalizing a skill before it is shared with the world.

# Habashi-kit Guidelines

## Using the kit

When the user says "start", "what's next", "next", "continue", or asks to find or apply for jobs, load `job/SKILL.md` and follow its **Simple Commands** table. Users are job seekers, not programmers: talk in plain words and do every technical step yourself.

## Contributing

1. **Progressive disclosure & token efficiency**: Keep every skill's `SKILL.md` lean (~140–170 lines) with clear routing tables. Place detailed procedures in `references/` (loaded only when needed) and deterministic logic in `scripts/`.
2. **Zero personal data in git**: Never commit personal names, emails, phone numbers, street addresses, credentials, personal employer histories, or private application logs. Keep all user data inside an ignored `workspace/` directory (or another path outside the repo).
3. **Package manager**: Use `pnpm` (never `npm`) for JavaScript dependencies and scripts.
4. **Test before finishing**: Run `python -m pytest -q job/tests` and `node job/scripts/neo/emit.mjs --list` after modifying scripts or templates.

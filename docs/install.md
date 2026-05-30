# Universal Creator Installer

## New Installer Entrypoint

- `install_entrypoint(name, host, scope, cwd, *, with_deps=True, overwrite_policy='prompt', force=False, backup=True)`
- Installs a skill (preferred) or agent by name, with atomic staging and backup.
- **Skills**: Installs dependencies by default (set `with_deps=False` to skip).
- **Agents**: If a skill of the same name exists, prefer skill; otherwise, error unless `force=True`.
- **Backup**: Overwrites trigger a timestamped backup in `<host_root>/.universal-creator/backups/<timestamp>/`.
- **Staging**: All file operations are atomic via a staging directory.
- **Prompting**: Interactive confirmation unless `force=True` or non-interactive context.

## CLI Flags/Options
- `--force`: Skip prompts, always overwrite.
- `--backup/--no-backup`: Enable/disable backup before overwrite.
- `--with-deps/--no-deps`: Control dependency installation for skills.

See README for host/target mapping and more details.

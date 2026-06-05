import os
import shutil
import difflib
VAULT_DIR = os.path.join(os.getcwd(), '.chronos_vault')
def list_checkpoints(filename: str) -> list:
    if not os.path.exists(VAULT_DIR):
        return []
    base_name = os.path.basename(filename)
    all_backups = os.listdir(VAULT_DIR)
    matching = [f for f in all_backups if f.startswith(base_name) and f.endswith('.bak')]
    matching.sort(reverse=True)
    return matching
def rollback_file(filename: str) -> str:
    if not os.path.exists(VAULT_DIR):
        return '[red]Vault directory does not exist.[/red]'
    base_name = os.path.basename(filename)
    matching_backups = list_checkpoints(base_name)
    if not matching_backups:
        return f'[red]No checkpoints found for {filename}.[/red]'
    target_active_file = os.path.join(os.getcwd(), 'sandbox', filename)
    if not os.path.exists(target_active_file):
        target_active_file = os.path.join(os.getcwd(), filename)
    if not os.path.exists(target_active_file):
        return f"[red]Active file '{filename}' not found in sandbox or project root.[/red]"
    try:
        with open(target_active_file, 'r', encoding='utf-8', errors='ignore') as f:
            current_lines = f.readlines()
        most_recent_backup_name = None
        backup_lines = None
        for backup_name in matching_backups:
            backup_path = os.path.join(VAULT_DIR, backup_name)
            with open(backup_path, 'r', encoding='utf-8', errors='ignore') as f:
                b_lines = f.readlines()
            if b_lines != current_lines:
                most_recent_backup_name = backup_name
                backup_lines = b_lines
                break
        if most_recent_backup_name is None:
            return '[dim]No differences found in any checkpoints — file already matches all backups.[/dim]'
        most_recent_backup_path = os.path.join(VAULT_DIR, most_recent_backup_name)
        diff = difflib.unified_diff(current_lines, backup_lines, fromfile=f'Current ({filename})', tofile=f'Restored ({most_recent_backup_name})')
        formatted_diff = []
        for line in diff:
            line = line.rstrip('\n')
            if line.startswith('+'):
                formatted_diff.append(f'[green]{line}[/green]')
            elif line.startswith('-'):
                formatted_diff.append(f'[red]{line}[/red]')
            else:
                formatted_diff.append(line)
        final_diff_output = '\n'.join(formatted_diff)
        if not final_diff_output.strip():
            final_diff_output = '[dim]No differences — file already matches the backup.[/dim]'
        shutil.copy2(most_recent_backup_path, target_active_file)
        return f'[green]✔ Successfully rolled back to {most_recent_backup_name}[/green]\n\n{final_diff_output}'
    except Exception as e:
        return f'[red]Rollback failed: {str(e)}[/red]'

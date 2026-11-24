"""Bounded read-only repository tools. Repository content is untrusted."""
from pathlib import Path
import os

EXCLUDED = {'.git', '.venv', 'venv', 'node_modules', '__pycache__', '.env', 'agent.db', 'mlruns'}
SENSITIVE_SUFFIXES = {'.pem', '.key', '.p12', '.pfx'}
MAX_FILE_BYTES = 500_000
MAX_OUTPUT = 12_000

class RepositoryTools:
    def __init__(self, root: Path):
        self.root = root.resolve(strict=True)
        if not self.root.is_dir():
            raise ValueError('Project path must be a directory')

    def _path(self, relative: str) -> Path:
        if not relative or Path(relative).is_absolute():
            raise ValueError('Use a relative path inside the project')
        raw = self.root / relative
        if any(p in EXCLUDED or p.startswith('.env') for p in Path(relative).parts):
            raise ValueError('Excluded path')
        # Reject symlinks, even those pointing inside the repository.
        current = self.root
        for part in Path(relative).parts:
            current = current / part
            if current.is_symlink():
                raise ValueError('Symbolic links are not allowed')
        target = raw.resolve()
        if not target.is_relative_to(self.root):
            raise ValueError('Path is outside the project')
        if target.suffix.lower() in SENSITIVE_SUFFIXES:
            raise ValueError('Sensitive file type excluded')
        return target

    def list_files(self, query: str = '') -> str:
        """List up to 100 project paths, optionally filtered by text."""
        matches = []
        for base, dirs, files in os.walk(self.root, followlinks=False):
            dirs[:] = sorted(d for d in dirs if d not in EXCLUDED and not d.startswith('.env') and not (Path(base) / d).is_symlink())
            for name in sorted(files):
                path = Path(base) / name
                rel = path.relative_to(self.root).as_posix()
                try:
                    self._path(rel)
                    if query.lower() in rel.lower():
                        matches.append(rel)
                except ValueError:
                    continue
                if len(matches) >= 100:
                    return '\n'.join(matches) + '\n[Results limited to 100]'
        return '\n'.join(matches) or 'No matching files.'

    def search_files(self, keyword: str) -> str:
        """Find a literal keyword in project text files."""
        if not keyword.strip() or len(keyword) > 200:
            return 'Error: keyword must contain 1–200 characters.'
        results = []
        # list_files bounds the number of files inspected in this starter.
        paths = self.list_files().splitlines()
        for rel in paths:
            if rel.startswith('['):
                continue
            try:
                path = self._path(rel)
                if not path.is_file() or path.stat().st_size > MAX_FILE_BYTES:
                    continue
                with path.open('r', encoding='utf-8') as f:
                    for line_no, line in enumerate(f, 1):
                        if keyword.casefold() in line.casefold():
                            results.append(f'{rel}:{line_no}: {line.strip()[:200]}')
                            if len(results) >= 20:
                                return '\n'.join(results)
            except (ValueError, OSError, UnicodeError):
                continue
        return '\n'.join(results) or 'No matches found.'

    def read_file(self, path: str) -> str:
        """Read up to 12,000 characters of a project text file."""
        try:
            target = self._path(path)
            if not target.is_file():
                return 'Error: file not found.'
            if target.stat().st_size > MAX_FILE_BYTES:
                return 'Error: file exceeds size limit.'
            content = target.read_text(encoding='utf-8')
            return content[:MAX_OUTPUT] + ('\n[Content truncated]' if len(content) > MAX_OUTPUT else '')
        except (ValueError, OSError, UnicodeError) as exc:
            return f'Error: {exc}'

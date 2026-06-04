from __future__ import annotations

import csv
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional


ARTIFACT_EXTENSIONS = {
    '.mp': 'graph',
    '.pset': 'pset',
    '.dml': 'dml',
    '.xfr': 'xfr',
    '.sql': 'sql',
    '.ksh': 'shell',
    '.sh': 'shell',
    '.jil': 'autosys',
}


@dataclass
class SandboxRecord:
    sandbox_name: str
    sandbox_path: str
    sandbox_type: str
    environment: str


@dataclass
class FileRecord:
    file_path: str
    file_name: str
    extension: str
    artifact_type: str
    sandbox_name: str
    sandbox_path: str


class InventoryScanner:
    def __init__(self, sandbox_parent: str, output_root: str):
        self.sandbox_parent = Path(sandbox_parent).expanduser().resolve()
        self.output_root = Path(output_root).expanduser().resolve()
        self.inventory_dir = self.output_root / '01_inventory'
        self.inventory_dir.mkdir(parents=True, exist_ok=True)

    def run(self) -> Dict[str, List[dict]]:
        sandboxes = self.discover_sandboxes()
        files = self.discover_files(sandboxes)
        self._write_csv(self.inventory_dir / 'sandbox_inventory.csv', [asdict(x) for x in sandboxes])
        self._write_csv(self.inventory_dir / 'file_inventory.csv', [asdict(x) for x in files])
        self._write_jsonl(self.inventory_dir / 'artifact_index.jsonl', [asdict(x) for x in files])
        return {
            'sandboxes': [asdict(x) for x in sandboxes],
            'files': [asdict(x) for x in files],
        }

    def discover_sandboxes(self) -> List[SandboxRecord]:
        records: List[SandboxRecord] = []
        for path in self._iter_candidate_dirs(self.sandbox_parent):
            if self._looks_like_sandbox(path):
                records.append(
                    SandboxRecord(
                        sandbox_name=path.name,
                        sandbox_path=str(path),
                        sandbox_type=self._infer_sandbox_type(path),
                        environment=self._infer_environment(path.name),
                    )
                )
        return records

    def discover_files(self, sandboxes: List[SandboxRecord]) -> List[FileRecord]:
        records: List[FileRecord] = []
        for sb in sandboxes:
            sb_path = Path(sb.sandbox_path)
            for f in sb_path.rglob('*'):
                if not f.is_file():
                    continue
                artifact_type = ARTIFACT_EXTENSIONS.get(f.suffix.lower())
                if not artifact_type:
                    continue
                records.append(
                    FileRecord(
                        file_path=str(f),
                        file_name=f.name,
                        extension=f.suffix.lower(),
                        artifact_type=artifact_type,
                        sandbox_name=sb.sandbox_name,
                        sandbox_path=sb.sandbox_path,
                    )
                )
        return records

    def _iter_candidate_dirs(self, root: Path) -> Iterable[Path]:
        yield root
        for p in root.rglob('*'):
            if p.is_dir():
                yield p

    def _looks_like_sandbox(self, path: Path) -> bool:
        has_project = (path / '.project.pset').exists() or (path / 'project.pset').exists()
        has_graph = any(x.is_file() and x.suffix == '.mp' for x in path.glob('*.mp'))
        has_pset = any(x.is_file() and x.suffix == '.pset' for x in path.glob('*.pset'))
        return has_project or has_graph or has_pset

    def _infer_sandbox_type(self, path: Path) -> str:
        n = path.name.lower()
        if 'private' in n or n.startswith('priv'):
            return 'private'
        if 'public' in n or n.startswith('pub'):
            return 'public'
        if (path / '.project.pset').exists() or (path / 'project.pset').exists():
            return 'project'
        return 'unknown'

    def _infer_environment(self, name: str) -> str:
        n = name.lower()
        mapping = {
            'dev': ['dev', 'dv'],
            'test': ['test', 'tst', 'qa'],
            'uat': ['uat', 'stage', 'staging'],
            'prod': ['prod', 'prd', 'live'],
        }
        for env, patterns in mapping.items():
            if any(p in n for p in patterns):
                return env
        return 'unknown'

    def _write_csv(self, path: Path, rows: List[dict]) -> None:
        if not rows:
            path.write_text('', encoding='utf-8')
            return
        with path.open('w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

    def _write_jsonl(self, path: Path, rows: List[dict]) -> None:
        with path.open('w', encoding='utf-8') as f:
            for row in rows:
                f.write(json.dumps(row, default=str) + '
')

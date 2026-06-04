from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional


ASSIGNMENT_PATTERNS = [
    re.compile(r'export\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*"([^"]*)"'),
    re.compile(r"export\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*'([^']*)'"),
    re.compile(r'export\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(\S+)'),
    re.compile(r'^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*"([^"]*)"', re.MULTILINE),
    re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*'([^']*)'", re.MULTILINE),
    re.compile(r'^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(\S+)', re.MULTILINE),
]


@dataclass
class ParameterSource:
    source_type: str
    source_file: str
    priority: int
    variables: Dict[str, str]


class ParameterResolver:
    def __init__(self, output_root: str):
        self.output_root = Path(output_root).expanduser().resolve()
        self.param_dir = self.output_root / '02_parameters'
        self.param_dir.mkdir(parents=True, exist_ok=True)
        self.sources: List[ParameterSource] = []

    def register_profile_or_pset(self, source_file: str, source_type: str, priority: int) -> None:
        path = Path(source_file).expanduser().resolve()
        if not path.exists() or not path.is_file():
            return
        self.sources.append(
            ParameterSource(
                source_type=source_type,
                source_file=str(path),
                priority=priority,
                variables=self._parse_assignments(path.read_text(encoding='utf-8', errors='ignore')),
            )
        )

    def resolve(self) -> Dict[str, dict]:
        ordered = sorted(self.sources, key=lambda x: x.priority, reverse=True)
        all_names = sorted({k for src in ordered for k in src.variables.keys()})
        result: Dict[str, dict] = {}
        flat_rows: List[dict] = []
        unresolved_rows: List[dict] = []

        for name in all_names:
            chain = []
            final_value = None
            winning_source = None
            for src in ordered:
                if name in src.variables:
                    value = src.variables[name]
                    chain.append({
                        'source_type': src.source_type,
                        'source_file': src.source_file,
                        'priority': src.priority,
                        'value': value,
                    })
                    if final_value is None:
                        final_value = value
                        winning_source = src.source_file
            status = 'resolved' if final_value is not None else 'unresolved'
            result[name] = {
                'final_value': final_value,
                'status': status,
                'winning_source': winning_source,
                'override_chain': chain,
                'unresolved_dependencies': self._extract_dependencies(final_value) if final_value else [],
            }
            flat_rows.append({
                'parameter_name': name,
                'final_value': final_value,
                'status': status,
                'winning_source': winning_source,
                'override_count': len(chain),
            })
            if result[name]['unresolved_dependencies']:
                unresolved_rows.append({
                    'parameter_name': name,
                    'final_value': final_value,
                    'unresolved_dependencies': ','.join(result[name]['unresolved_dependencies']),
                })

        (self.param_dir / 'parameter_resolution.json').write_text(
            json.dumps({'parameters': result}, indent=2), encoding='utf-8'
        )
        self._write_csv(self.param_dir / 'parameter_resolution_flat.csv', flat_rows)
        self._write_csv(self.param_dir / 'unresolved_parameters.csv', unresolved_rows)
        with (self.param_dir / 'parameter_sources.jsonl').open('w', encoding='utf-8') as f:
            for src in ordered:
                f.write(json.dumps(asdict(src), default=str) + '
')
        return result

    def _parse_assignments(self, text: str) -> Dict[str, str]:
        values: Dict[str, str] = {}
        for pattern in ASSIGNMENT_PATTERNS:
            for match in pattern.finditer(text):
                key, value = match.group(1), match.group(2)
                values[key] = value.strip()
        return values

    def _extract_dependencies(self, value: Optional[str]) -> List[str]:
        if not value:
            return []
        deps = re.findall(r'\$\{([^}]+)\}', value)
        deps += re.findall(r'\$([A-Za-z_][A-Za-z0-9_]*)', value)
        return sorted(set(deps))

    def _write_csv(self, path: Path, rows: List[dict]) -> None:
        if not rows:
            path.write_text('', encoding='utf-8')
            return
        with path.open('w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

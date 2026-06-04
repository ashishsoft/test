from __future__ import annotations

import argparse
import json
from pathlib import Path

from inventory import InventoryScanner
from resolver import ParameterResolver
from manifest_builder import ManifestBuilder


PRIORITY_HINTS = {
    'system_profile': 10,
    'user_profile': 20,
    'application_profile': 30,
    'project_pset': 40,
    'public_sandbox_pset': 50,
    'private_sandbox_pset': 60,
    'graph_override': 70,
    'wrapper_override': 80,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Ab Initio manifest-first parser skeleton')
    parser.add_argument('--sandbox-parent', required=True, help='Parent directory containing projects/sandboxes')
    parser.add_argument('--parameter-path', action='append', default=[], help='Profile or config path; repeatable')
    parser.add_argument('--output', required=True, help='Output root directory')
    return parser.parse_args()


def infer_source_type(path: Path) -> str:
    name = path.name.lower()
    path_str = str(path).lower()
    if '/etc/' in path_str:
        return 'system_profile'
    if name in {'.bashrc', '.kshrc', '.profile', '.bash_profile'}:
        return 'user_profile'
    if name.endswith('.project.pset') or name == 'project.pset':
        return 'project_pset'
    if 'private' in name and name.endswith('.pset'):
        return 'private_sandbox_pset'
    if name.endswith('.pset'):
        return 'public_sandbox_pset'
    return 'application_profile'


def main() -> None:
    args = parse_args()
    output_root = Path(args.output).expanduser().resolve()
    (output_root / '00_run_metadata').mkdir(parents=True, exist_ok=True)

    inventory = InventoryScanner(args.sandbox_parent, str(output_root)).run()

    resolver = ParameterResolver(str(output_root))
    for raw_path in args.parameter_path:
        p = Path(raw_path).expanduser().resolve()
        if p.is_file():
            st = infer_source_type(p)
            resolver.register_profile_or_pset(str(p), st, PRIORITY_HINTS[st])
        elif p.is_dir():
            for child in p.rglob('*'):
                if child.is_file():
                    st = infer_source_type(child)
                    resolver.register_profile_or_pset(str(child), st, PRIORITY_HINTS[st])
    parameter_resolution = resolver.resolve()

    results = ManifestBuilder(str(output_root)).build(inventory, parameter_resolution)

    run_metadata = {
        'sandbox_parent': str(Path(args.sandbox_parent).expanduser().resolve()),
        'parameter_paths': args.parameter_path,
        'output_root': str(output_root),
        'inventory_sandbox_count': len(inventory.get('sandboxes', [])),
        'inventory_file_count': len(inventory.get('files', [])),
        'pipeline_count': len(results.get('pipelines', [])),
        'test_case_count': len(results.get('test_cases', [])),
        'status': 'skeleton_completed',
    }
    (output_root / '00_run_metadata' / 'parser_run.json').write_text(json.dumps(run_metadata, indent=2), encoding='utf-8')
    (output_root / '00_run_metadata' / 'parser_settings.yaml').write_text(
        'sandbox_parent: "{}"
output_root: "{}"
'.format(run_metadata['sandbox_parent'], run_metadata['output_root']),
        encoding='utf-8',
    )

    print(json.dumps(run_metadata, indent=2))


if __name__ == '__main__':
    main()

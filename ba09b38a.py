from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Dict, List


class ManifestBuilder:
    def __init__(self, output_root: str):
        self.output_root = Path(output_root).expanduser().resolve()
        self.lineage_dir = self.output_root / '03_lineage'
        self.test_dir = self.output_root / '04_test_cases'
        self.sql_dir = self.output_root / '05_sql_templates'
        self.shell_dir = self.output_root / '06_shell_templates'
        self.report_dir = self.output_root / '07_reports'
        for d in [self.lineage_dir, self.test_dir, self.sql_dir, self.shell_dir, self.report_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def build(
        self,
        inventory: Dict[str, List[dict]],
        parameter_resolution: Dict[str, dict],
    ) -> Dict[str, object]:
        pipelines = self._build_pipeline_manifest(inventory)
        filesystem_edges = self._build_filesystem_lineage(inventory)
        data_objects = self._build_data_object_catalog(pipelines, filesystem_edges)
        test_cases, gaps = self._build_test_case_catalog(pipelines, data_objects, parameter_resolution)
        self._write_pipeline_outputs(pipelines, filesystem_edges, data_objects)
        self._write_test_outputs(test_cases, gaps)
        self._write_reports(pipelines, test_cases, gaps)
        return {
            'pipelines': pipelines,
            'filesystem_edges': filesystem_edges,
            'data_objects': data_objects,
            'test_cases': test_cases,
            'gaps': gaps,
        }

    def _build_pipeline_manifest(self, inventory: Dict[str, List[dict]]) -> List[dict]:
        pipelines: List[dict] = []
        graphs = [x for x in inventory.get('files', []) if x['artifact_type'] == 'graph']
        for idx, graph in enumerate(graphs, start=1):
            pipelines.append({
                'pipeline_id': f'PIPE_{idx:04d}',
                'pipeline_name': Path(graph['file_name']).stem,
                'root_sandbox': graph['sandbox_path'],
                'environment_token_names': ['AB_ENVIRONMENT', 'AI_ENV'],
                'execution_sources': {
                    'autosys_job': None,
                    'wrapper_script': None,
                    'graph_sequence': [graph['file_path']],
                },
                'source_objects': [],
                'intermediate_objects': [],
                'target_objects': [],
                'parameter_snapshot_ref': '02_parameters/parameter_resolution.json',
                'status': 'manual_review_required',
                'warnings': ['Skeleton pipeline manifest; graph sequencing and object inference not implemented yet'],
            })
        return pipelines

    def _build_filesystem_lineage(self, inventory: Dict[str, List[dict]]) -> List[dict]:
        dmls = [x for x in inventory.get('files', []) if x['artifact_type'] == 'dml']
        edges: List[dict] = []
        for idx, dml in enumerate(dmls, start=1):
            edges.append({
                'pipeline_id': None,
                'stage_id': f'STAGE_{idx:02d}',
                'logical_object': dml['file_path'],
                'object_type': 'file_schema',
                'producer': {'graph': None, 'sandbox': dml['sandbox_name']},
                'consumer': {'graph': None, 'sandbox': dml['sandbox_name']},
                'dml_file': dml['file_path'],
                'partition_files': [],
                'checks_required': ['exists', 'schema_extract'],
            })
        return edges

    def _build_data_object_catalog(self, pipelines: List[dict], filesystem_edges: List[dict]) -> List[dict]:
        rows: List[dict] = []
        for pipeline in pipelines:
            rows.append({
                'object_id': f"OBJ_{pipeline['pipeline_id']}_GRAPH",
                'pipeline_id': pipeline['pipeline_id'],
                'stage_id': 'STAGE_01',
                'object_role': 'intermediate',
                'object_type': 'graph',
                'system': 'abinitio',
                'logical_name': pipeline['pipeline_name'],
                'physical_path': pipeline['execution_sources']['graph_sequence'][0],
                'sandbox': pipeline['root_sandbox'],
                'graph_name': pipeline['pipeline_name'],
                'dml_file': None,
                'partition_count': 0,
                'connection_ref': None,
                'resolved_name': pipeline['pipeline_name'],
                'resolution_status': 'partial',
            })
        for idx, edge in enumerate(filesystem_edges, start=1):
            rows.append({
                'object_id': f'OBJ_FS_{idx:04d}',
                'pipeline_id': edge['pipeline_id'],
                'stage_id': edge['stage_id'],
                'object_role': 'intermediate',
                'object_type': edge['object_type'],
                'system': 'filesystem',
                'logical_name': edge['logical_object'],
                'physical_path': edge['logical_object'],
                'sandbox': edge['producer']['sandbox'],
                'graph_name': edge['producer']['graph'],
                'dml_file': edge['dml_file'],
                'partition_count': len(edge['partition_files']),
                'connection_ref': None,
                'resolved_name': edge['logical_object'],
                'resolution_status': 'partial',
            })
        return rows

    def _build_test_case_catalog(self, pipelines: List[dict], data_objects: List[dict], parameter_resolution: Dict[str, dict]):
        test_cases: List[dict] = []
        gaps: List[dict] = []
        for idx, pipeline in enumerate(pipelines, start=1):
            pipe_sql_dir = self.sql_dir / pipeline['pipeline_id']
            pipe_shell_dir = self.shell_dir / pipeline['pipeline_id']
            pipe_sql_dir.mkdir(parents=True, exist_ok=True)
            pipe_shell_dir.mkdir(parents=True, exist_ok=True)
            self._write_text(pipe_sql_dir / '001_source_row_count.sql', 'SELECT COUNT(*) AS cnt
FROM ${source_table}
${source_filter_clause};
')
            self._write_text(pipe_sql_dir / '003_schema_compare.sql', '-- left side
${source_schema_sql}

-- right side
${target_schema_sql}
')
            self._write_text(pipe_shell_dir / '001_file_exists.sh', '#!/usr/bin/env bash
set -euo pipefail
[[ -e "${file_path}" ]]
')
            self._write_text(pipe_shell_dir / '003_mfs_partition_check.sh', '#!/usr/bin/env bash
set -euo pipefail
logical_path="${logical_path}"
expected_count="${expected_partition_count}"
actual_count=$(ls -1 "${logical_path}".dat.* 2>/dev/null | wc -l | tr -d " ")
[[ "${actual_count}" == "${expected_count}" ]]
')
            test_cases.extend([
                {
                    'test_case_id': f'TC_{idx:04d}_01',
                    'pipeline_id': pipeline['pipeline_id'],
                    'stage_id': 'STAGE_01',
                    'execution_group': 'parameter_precheck',
                    'test_type': 'parameter_resolved',
                    'test_level': 'parameter',
                    'source_object_id': '',
                    'target_object_id': '',
                    'system_under_test': 'config',
                    'query_template_file': '',
                    'shell_template_file': '',
                    'precondition': 'parameter inventory created',
                    'expected_rule': 'critical runtime parameters resolved',
                    'severity': 'critical',
                    'auto_runnable': 'N',
                    'manual_review_flag': 'Y',
                    'notes': 'Skeleton only; runtime critical parameter list not inferred yet',
                },
                {
                    'test_case_id': f'TC_{idx:04d}_02',
                    'pipeline_id': pipeline['pipeline_id'],
                    'stage_id': 'STAGE_01',
                    'execution_group': 'db_precheck',
                    'test_type': 'source_row_count',
                    'test_level': 'database',
                    'source_object_id': '',
                    'target_object_id': '',
                    'system_under_test': 'database',
                    'query_template_file': str((pipe_sql_dir / '001_source_row_count.sql').relative_to(self.output_root)),
                    'shell_template_file': '',
                    'precondition': 'source object inferred',
                    'expected_rule': 'count > 0',
                    'severity': 'critical',
                    'auto_runnable': 'N',
                    'manual_review_flag': 'Y',
                    'notes': 'Source object inference pending',
                },
                {
                    'test_case_id': f'TC_{idx:04d}_03',
                    'pipeline_id': pipeline['pipeline_id'],
                    'stage_id': 'STAGE_02',
                    'execution_group': 'file_handoff',
                    'test_type': 'file_exists',
                    'test_level': 'file',
                    'source_object_id': '',
                    'target_object_id': '',
                    'system_under_test': 'filesystem',
                    'query_template_file': '',
                    'shell_template_file': str((pipe_shell_dir / '001_file_exists.sh').relative_to(self.output_root)),
                    'precondition': 'intermediate file inferred',
                    'expected_rule': 'file exists',
                    'severity': 'high',
                    'auto_runnable': 'N',
                    'manual_review_flag': 'Y',
                    'notes': 'Intermediate object inference pending',
                },
            ])
            gaps.append({
                'pipeline_id': pipeline['pipeline_id'],
                'artifact_type': 'pipeline_manifest',
                'artifact_name': pipeline['pipeline_name'],
                'issue_type': 'skeleton_only',
                'severity': 'high',
                'description': 'Graph sequencing, object inference, and reconciliation logic are not implemented in the skeleton.',
                'recommended_action': 'Implement graph parsing, DML parsing, MFS detection, and wrapper/Autosys linkage.',
            })
        unresolved = parameter_resolution.get('parameters', {})
        for name, payload in unresolved.items():
            if payload.get('unresolved_dependencies'):
                gaps.append({
                    'pipeline_id': '',
                    'artifact_type': 'parameter',
                    'artifact_name': name,
                    'issue_type': 'unresolved_dependency',
                    'severity': 'medium',
                    'description': f"Parameter depends on unresolved values: {', '.join(payload['unresolved_dependencies'])}",
                    'recommended_action': 'Resolve upstream profile/pset/wrapper sources before generating runnable tests.',
                })
        return test_cases, gaps

    def _write_pipeline_outputs(self, pipelines: List[dict], filesystem_edges: List[dict], data_objects: List[dict]) -> None:
        (self.lineage_dir / 'pipeline_manifest.json').write_text(json.dumps({'pipelines': pipelines}, indent=2), encoding='utf-8')
        self._write_csv(self.lineage_dir / 'pipeline_manifest_flat.csv', [
            {
                'pipeline_id': p['pipeline_id'],
                'pipeline_name': p['pipeline_name'],
                'root_sandbox': p['root_sandbox'],
                'status': p['status'],
                'warning_count': len(p['warnings']),
            }
            for p in pipelines
        ])
        (self.lineage_dir / 'filesystem_lineage.json').write_text(json.dumps({'filesystem_edges': filesystem_edges}, indent=2), encoding='utf-8')
        self._write_csv(self.lineage_dir / 'data_object_catalog.csv', data_objects)
        self._write_csv(self.lineage_dir / 'ambiguous_lineage_edges.csv', [])

    def _write_test_outputs(self, test_cases: List[dict], gaps: List[dict]) -> None:
        self._write_csv(self.test_dir / 'test_case_catalog.csv', test_cases)
        with (self.test_dir / 'test_case_catalog.jsonl').open('w', encoding='utf-8') as f:
            for row in test_cases:
                f.write(json.dumps(row, default=str) + '
')
        self._write_csv(self.test_dir / 'assumptions_and_gaps.csv', gaps)
        coverage = {
            'total_test_cases': len(test_cases),
            'manual_review_required': sum(1 for x in test_cases if x['manual_review_flag'] == 'Y'),
            'auto_runnable': sum(1 for x in test_cases if x['auto_runnable'] == 'Y'),
        }
        (self.test_dir / 'coverage_summary.json').write_text(json.dumps(coverage, indent=2), encoding='utf-8')

    def _write_reports(self, pipelines: List[dict], test_cases: List[dict], gaps: List[dict]) -> None:
        readiness = {
            'pipeline_count': len(pipelines),
            'test_case_count': len(test_cases),
            'gap_count': len(gaps),
            'status': 'skeleton_ready_for_implementation',
        }
        (self.report_dir / 'readiness_report.json').write_text(json.dumps(readiness, indent=2), encoding='utf-8')
        summary_lines = [
            '# Human Summary',
            '',
            f'- Pipelines discovered: {len(pipelines)}',
            f'- Test cases generated: {len(test_cases)}',
            f'- Gaps recorded: {len(gaps)}',
            '- This output is from the skeleton layer, not the final parser.',
        ]
        (self.report_dir / 'human_summary.md').write_text('
'.join(summary_lines) + '
', encoding='utf-8')

    def _write_csv(self, path: Path, rows: List[dict]) -> None:
        if not rows:
            path.write_text('', encoding='utf-8')
            return
        with path.open('w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

    def _write_text(self, path: Path, text: str) -> None:
        path.write_text(text, encoding='utf-8')

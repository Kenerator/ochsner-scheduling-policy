"""ZEN evaluates supplied scheduling policies; the core retains effect authority.

Facts are controller-computed categorical state, never identity values or user/model
claims. Validation failures stop; policy behavior is never reimplemented in Python.
"""
from dataclasses import dataclass
from importlib import metadata, resources
import json
from pathlib import Path
import re

ENUMS = {
    'action': frozenset(('providers', 'identify', 'availability', 'propose', 'book', 'report')),
    'request': frozenset(('scheduling', 'medical_advice', 'human_requested', 'unsupported')),
    'criteria': frozenset(('missing', 'supported', 'unsupported')),
    'identity': frozenset(('not_checked', 'no_match', 'multiple', 'verified')),
    'slots': frozenset(('not_fetched', 'empty', 'returned')),
    'selection': frozenset(('missing', 'returned_option', 'invalid')),
    'proposal': frozenset(('missing', 'current', 'stale')),
    'consent': frozenset(('missing', 'declined', 'ambiguous', 'current_explicit')),
    'api': frozenset(('not_called', 'ok', 'created_201', 'conflict_409', 'unavailable', 'unknown_write', 'invalid_response')),
    'model': frozenset(('valid', 'malformed', 'unavailable')),
}
OUTPUTS = frozenset(('disposition', 'reason', 'rule', 'sources'))


@dataclass(frozen=True)
class Decision:
    disposition: str
    reason: str
    rule: str
    sources: tuple[str, ...]

    def as_dict(self):
        """A fixed trace shape; no arbitrary engine fields reach UI or diagnostics."""
        return {'disposition': self.disposition, 'reason': self.reason,
                'rule': self.rule, 'sources': list(self.sources)}


_ENGINE_FAILURE = Decision('stop', 'policy_engine_unavailable', 'R-ENGINE-FAILURE', ('SPEC-FR022',))
_INVALID_FACTS = Decision('stop', 'invalid_policy_facts', 'R-INVALID-FACTS', ('SPEC-FR022',))


class PolicyEngine:
    """One reusable stateless ZEN decision; the committed resource is authoritative.

    model_path is a developer/test configuration seam, not a user-provided loader.
    Only the bounded decision-table graph schema below is accepted; no functions,
    expressions outside enum equality, custom nodes, callbacks, or external loaders.
    """
    def __init__(self, model_path=None):
        self._decision = None
        self._expected = {}
        try:
            if metadata.version('zen-engine') != '2.1.2':
                raise ValueError('unsupported policy engine')
            folder = resources.files('scheduling_assistant').joinpath('policy_models')
            registry = json.loads(folder.joinpath('sources.json').read_text())
            text = (Path(model_path).read_text() if model_path is not None
                    else folder.joinpath('scheduling.json').read_text())
            graph = json.loads(text)
            self._expected = self._validate_graph(graph, registry)
            import zen
            self._decision = zen.ZenEngine().create_decision(text)
        except Exception:
            # Never echo engine errors: they may contain model text or private paths.
            self._decision = None
            self._expected = {}

    @staticmethod
    def _validate_graph(graph, registry):
        if type(graph) is not dict or set(graph) != {'nodes', 'edges'}:
            raise ValueError('invalid graph')
        nodes = graph['nodes']
        if type(nodes) is not list or len(nodes) != 3:
            raise ValueError('invalid nodes')
        by_id = {node['id']: node for node in nodes}
        if set(by_id) != {'input', 'table', 'output'}:
            raise ValueError('invalid node ids')
        for name, kind in [('input', 'inputNode'), ('table', 'decisionTableNode'), ('output', 'outputNode')]:
            node = by_id[name]
            if node['type'] != kind or set(node) != ({'id', 'name', 'type', 'content'} if name == 'table' else {'id', 'name', 'type'}):
                raise ValueError('invalid node schema')
        edges = graph['edges']
        if (type(edges) is not list or len(edges) != 2 or
            {(e['sourceId'], e['targetId']) for e in edges} != {('input', 'table'), ('table', 'output')} or
            any(set(e) != {'id', 'sourceId', 'targetId'} for e in edges)):
            raise ValueError('invalid edges')
        content = by_id['table']['content']
        if set(content) != {'hitPolicy', 'inputs', 'outputs', 'rules'} or content['hitPolicy'] != 'first':
            raise ValueError('invalid table')
        for columns, expected in [(content['inputs'], set(ENUMS)), (content['outputs'], OUTPUTS)]:
            if (type(columns) is not list or len(columns) != len(expected) or
                {c['id'] for c in columns} != expected or
                any(set(c) != {'id', 'field', 'name'} or c['id'] != c['field'] for c in columns)):
                raise ValueError('invalid columns')
        expected_outputs = {}
        for row in content['rules']:
            if set(row) != {'_id'} | set(ENUMS) | OUTPUTS:
                raise ValueError('invalid row')
            if not re.fullmatch(r'R-[A-Z0-9-]+', row['_id']) or row['_id'] in expected_outputs:
                raise ValueError('invalid rule id')
            for field, allowed in ENUMS.items():
                cell = row[field]
                if cell != '' and (type(cell) is not str or json.loads(cell) not in allowed):
                    raise ValueError('invalid condition')
            output = {key: json.loads(row[key]) for key in OUTPUTS}
            if (output['disposition'] not in {'proceed', 'clarify', 'stop', 'reconcile'} or
                type(output['reason']) is not str or not re.fullmatch(r'[a-z][a-z_]+', output['reason']) or
                output['rule'] != row['_id'] or type(output['sources']) is not list or
                not output['sources'] or any(type(s) is not str or s not in registry for s in output['sources'])):
                raise ValueError('invalid output')
            expected_outputs[row['_id']] = output
        last = content['rules'][-1]
        if last['_id'] != 'R-FAIL-CLOSED' or any(last[f] != '' for f in ENUMS) or json.loads(last['disposition']) != 'stop':
            raise ValueError('missing safe catchall')
        return expected_outputs

    def evaluate(self, facts):
        # Input shape/type checks are a trust boundary, not a policy-rule fallback.
        if (type(facts) is not dict or set(facts) != set(ENUMS) or
            any(type(facts[k]) is not str or facts[k] not in values for k, values in ENUMS.items())):
            return _INVALID_FACTS
        if self._decision is None:
            return _ENGINE_FAILURE
        try:
            result = self._decision.evaluate(dict(facts))['result']
            if (type(result) is not dict or set(result) != OUTPUTS or
                type(result['rule']) is not str or self._expected.get(result['rule']) != result):
                return _ENGINE_FAILURE
            return Decision(result['disposition'], result['reason'], result['rule'], tuple(result['sources']))
        except Exception:
            return _ENGINE_FAILURE

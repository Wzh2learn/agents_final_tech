"""Mechanical timing controls for a frozen corrective policy; no learning."""
import ast
import hashlib


def gate_deployment(source, phase):
    """Preserve the policy body and vary one literal: both=0, pre=1, post=2.

    A pre decision has no pending Actor operation. Post gates run after the
    Actor has already proposed an operation. Yield retains that operation.
    This transforms source only; execution still belongs in the owned guest.
    """
    codes = {'both': 0, 'pre': 1, 'post': 2}
    if phase not in codes:
        raise ValueError('unknown deployment phase')
    tree = ast.parse(source)
    entries = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'step']
    if len(entries) != 1:
        raise ValueError('expected one policy step')
    reserved = {'deployment_base_step', 'DEPLOYMENT_PHASE'}
    if any((isinstance(n, ast.Name) and n.id in reserved | {'step'})
           or (isinstance(n, ast.FunctionDef) and n.name in reserved)
           for n in ast.walk(tree)):
        raise ValueError('policy entry reference or deployment name collision')
    entries[0].name = 'deployment_base_step'
    wrapper = ast.parse('''
DEPLOYMENT_PHASE = 0
def step(observation, memory):
    if observation.get('done'):
        return deployment_base_step(observation, memory)
    pending = observation.get('proposed_operation') is not None
    if (DEPLOYMENT_PHASE == 1 and pending) or (DEPLOYMENT_PHASE == 2 and not pending):
        return {'kind': 'yield', 'memory': memory, 'reason': 'No supported correction.'}
    return deployment_base_step(observation, memory)
''')
    wrapper.body[0].value = ast.Constant(codes[phase])
    tree.body.extend(wrapper.body)
    result = ast.unparse(ast.fix_missing_locations(tree)) + '\n'
    return result, {'phase': phase, 'source_sha256': hashlib.sha256(source.encode()).hexdigest(),
                    'policy_body_preserved': True, 'phase_code': codes[phase]}

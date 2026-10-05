from experiments.audit_objective_semantics import make_pre_marshalled_state
from jev_vlns.container_stack.state import make_seeded_state
from jev_vlns.search.vlns import projected_objective


def test_virtual_pre_marshalling_reaches_delivery_lower_bound():
    state = make_seeded_state(42)
    marshalled = make_pre_marshalled_state(state)

    assert marshalled.moves == 0
    assert projected_objective(marshalled) == len(state.containers)
    assert projected_objective(marshalled) == 10

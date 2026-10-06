from jev_vlns.container_stack.state import make_seeded_state
from jev_vlns.evaluation.context_variants import context_variant_names, serializers_for_variant


def test_m21_has_four_controlled_variants():
    assert context_variant_names() == (
        "A_compact",
        "B_full_state",
        "C_consequence",
        "D_decision_ready",
    )


def test_m21_variants_do_not_expose_downstream_scores():
    state = make_seeded_state(1)
    from jev_vlns.search.destroy import generate_destroy_candidates
    candidate = generate_destroy_candidates(
        state, min_stacks=2, max_stacks=2, include_non_adjacent=True
    )[0]
    forbidden = ("oracle", "regret", "expected_value", "final_moves", "score")
    for name in context_variant_names():
        state_serializer, candidate_serializer = serializers_for_variant(name)
        rendered = repr(
            (state_serializer(state), candidate_serializer(state, candidate))
        ).lower()
        assert all(token not in rendered for token in forbidden)


def test_m21_consequence_representation_is_state_derived():
    state = make_seeded_state(2)
    from jev_vlns.search.destroy import generate_destroy_candidates
    candidate = generate_destroy_candidates(
        state, min_stacks=2, max_stacks=2, include_non_adjacent=True
    )[0]
    _, serializer = serializers_for_variant("C_consequence")
    payload = serializer(state, candidate)
    assert '"operation": "destroy_top"' in payload
    for index in candidate.stack_indices:
        assert f'"index": {index}' in payload


def test_m21_full_state_expands_stack_container_metadata():
    state = make_seeded_state(3)
    serializer, _ = serializers_for_variant("B_full_state")
    payload = serializer(state)
    assert len(payload["stacks"]) == len(state.stacks)
    assert all("containers" in stack for stack in payload["stacks"])
    assert all(
        "destination" in container and "priority" in container
        for stack in payload["stacks"]
        for container in stack["containers"]
    )


def test_m21_decision_ready_precomputes_local_relations():
    state = make_seeded_state(4)
    from jev_vlns.search.destroy import generate_destroy_candidates
    candidate = generate_destroy_candidates(
        state, min_stacks=2, max_stacks=2, include_non_adjacent=True
    )[0]
    state_serializer, candidate_serializer = serializers_for_variant(
        "D_decision_ready"
    )
    state_payload = state_serializer(state)
    candidate_payload = candidate_serializer(state, candidate)

    assert "immediately_deliverable_top_count" in state_payload
    assert all(
        "matches_stack_destination" in stack["top"]
        for stack in state_payload["stacks"]
        if stack["top"] is not None
    )
    assert '"removed_match_count":' in candidate_payload
    assert '"exposed_match_count":' in candidate_payload
    assert '"exposed_priority_sum":' in candidate_payload
    assert all(
        token not in candidate_payload.lower()
        for token in ("expected_value", "regret", "final_moves", "oracle", "score")
    )


def test_m21_decision_ready_facts_match_ground_truth():
    state = make_seeded_state(5)
    from jev_vlns.search.destroy import generate_destroy_candidates

    candidate = generate_destroy_candidates(
        state, min_stacks=2, max_stacks=2, include_non_adjacent=True
    )[0]
    state_serializer, candidate_serializer = serializers_for_variant(
        "D_decision_ready"
    )
    state_payload = state_serializer(state)

    expected_deliverable = 0
    for index, stack in enumerate(state.stacks):
        if stack:
            container = state.container(stack[-1])
            expected_deliverable += (
                container.destination == state.stack_destinations[index]
            )

    assert state_payload["delivered_count"] == len(state.delivered)
    assert (
        state_payload["immediately_deliverable_top_count"]
        == expected_deliverable
    )
    for stack_payload, stack in zip(state_payload["stacks"], state.stacks):
        assert stack_payload["height"] == len(stack)
        assert stack_payload["capacity_left"] == 3 - len(stack)

    rendered = candidate_serializer(state, candidate)
    import json
    payload = json.loads(rendered)
    removed_match_count = 0
    exposed_match_count = 0
    exposed_priority_sum = 0
    for index in candidate.stack_indices:
        stack = state.stacks[index]
        destination = state.stack_destinations[index]
        removed = state.container(stack[-1])
        removed_match_count += removed.destination == destination
        if len(stack) >= 2:
            exposed = state.container(stack[-2])
            exposed_match_count += exposed.destination == destination
            exposed_priority_sum += exposed.priority

    assert payload["removed_match_count"] == removed_match_count
    assert payload["exposed_match_count"] == exposed_match_count
    assert payload["exposed_priority_sum"] == exposed_priority_sum

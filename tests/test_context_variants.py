from jev_vlns.container_stack.state import make_seeded_state
from jev_vlns.evaluation.context_variants import context_variant_names, serializers_for_variant


def test_m21_has_exactly_three_controlled_variants():
    assert context_variant_names() == ("A_compact", "B_full_state", "C_consequence")


def test_m21_variants_do_not_expose_downstream_scores():
    state = make_seeded_state(1)
    from jev_vlns.search.destroy import generate_destroy_candidates
    candidate = generate_destroy_candidates(
        state, min_stacks=2, max_stacks=2, include_non_adjacent=True
    )[0]
    forbidden = ("oracle", "regret", "expected_value", "final_moves", "score")
    for name in context_variant_names():
        state_serializer, candidate_serializer = serializers_for_variant(name)
        rendered = repr((state_serializer(state), candidate_serializer(state, candidate))).lower()
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


def test_m21_decision_ready_precomputes_local_relations_not_ev():
    state = make_seeded_state(4)
    state_serializer, candidate_serializer = serializers_for_variant("D_decision_ready")
    from jev_vlns.search.destroy import generate_destroy_candidates
    candidate = generate_destroy_candidates(
        state, min_stacks=2, max_stacks=2, include_non_adjacent=True
    )[0]
    state_payload = state_serializer(state)
    candidate_payload = candidate_serializer(state, candidate)
    assert "immediately_deliverable_top_count" in state_payload
    assert "exposed_match_count" in candidate_payload
    assert "removed_match_count" in candidate_payload
    assert "expected_value" not in repr((state_payload, candidate_payload)).lower()
    assert "regret" not in repr((state_payload, candidate_payload)).lower()

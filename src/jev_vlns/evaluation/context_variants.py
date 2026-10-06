"""Controlled JEV Destroy context representations for M21.

M21 compares state representations while keeping the solver, prompt, model,
candidate set, and downstream evaluator fixed. Variant D deliberately moves
small local bookkeeping operations out of JEV so the model is not required to
count stack/container relations itself.
"""

from __future__ import annotations

import json
from typing import Any, Mapping

from jev_vlns.container_stack.state import MAX_STACK_HEIGHT


def _containers_by_id(state: Any) -> dict[str, Any]:
    return {container.id: container for container in state.containers}


def _matches_stack_destination(container: Any, stack_destination: str) -> bool:
    return container.destination == stack_destination


def context_variant_names() -> tuple[str, ...]:
    return (
        "A_compact",
        "B_full_state",
        "C_consequence",
        "D_decision_ready",
    )


def serialize_variant_a_state(state: Any) -> Mapping[str, Any]:
    from jev_vlns.evaluation.benchmark import _jev_state
    return _jev_state(state)


def serialize_variant_a_candidate(state: Any, candidate: Any) -> str:
    from jev_vlns.evaluation.benchmark import _jev_destroy_candidate_context
    return _jev_destroy_candidate_context(state, candidate)


def serialize_variant_b_state(state: Any) -> Mapping[str, Any]:
    containers = _containers_by_id(state)
    stacks = []
    for index, stack in enumerate(state.stacks):
        stacks.append({
            "index": index,
            "destination": state.stack_destinations[index],
            "height": len(stack),
            "containers": [
                {
                    "id": container_id,
                    "destination": containers[container_id].destination,
                    "priority": containers[container_id].priority,
                }
                for container_id in stack
            ],
        })
    return {
        "stacks": stacks,
        "container_count": len(state.containers),
        "moves": state.moves,
        "delivered": list(state.delivered),
    }


def serialize_variant_b_candidate(state: Any, candidate: Any) -> str:
    return serialize_variant_a_candidate(state, candidate)


def serialize_variant_c_state(state: Any) -> Mapping[str, Any]:
    containers = _containers_by_id(state)
    return {
        "stack_destinations": list(state.stack_destinations),
        "stacks": [
            {
                "index": index,
                "destination": state.stack_destinations[index],
                "height": len(stack),
                "top_container": (
                    {
                        "id": stack[-1],
                        "destination": containers[stack[-1]].destination,
                        "priority": containers[stack[-1]].priority,
                    }
                    if stack else None
                ),
            }
            for index, stack in enumerate(state.stacks)
        ],
        "containers": {
            container.id: {
                "destination": container.destination,
                "priority": container.priority,
            }
            for container in state.containers
        },
        "moves": state.moves,
        "delivered": list(state.delivered),
    }


def serialize_variant_c_candidate(state: Any, candidate: Any) -> str:
    containers = _containers_by_id(state)
    affected = []
    for index in candidate.stack_indices:
        stack = state.stacks[index]
        removed_id = stack[-1]
        exposed_id = stack[-2] if len(stack) >= 2 else None
        removed = containers[removed_id]
        exposed = containers[exposed_id] if exposed_id else None
        before = [
            {
                "id": container_id,
                "destination": containers[container_id].destination,
                "priority": containers[container_id].priority,
            }
            for container_id in stack
        ]
        affected.append({
            "index": index,
            "stack_destination": state.stack_destinations[index],
            "before": before,
            "destroyed_top": {
                "id": removed.id,
                "destination": removed.destination,
                "priority": removed.priority,
            },
            "exposed_after_destroy": (
                {
                    "id": exposed.id,
                    "destination": exposed.destination,
                    "priority": exposed.priority,
                }
                if exposed is not None else None
            ),
            "after": before[:-1],
        })
    return json.dumps({
        "operation": "destroy_top",
        "affected_stacks": affected,
        "removed_container_ids": [
            item["destroyed_top"]["id"] for item in affected
        ],
    }, sort_keys=True)


def serialize_variant_d_state(state: Any) -> Mapping[str, Any]:
    """Return decision-ready local facts computed outside JEV.

    These are descriptive consequences of the current state only. They do not
    contain EV, Oracle values, regret, repair outcomes, or final objectives.
    """
    containers = _containers_by_id(state)
    stacks = []
    immediately_deliverable_top_count = 0

    for index, stack in enumerate(state.stacks):
        top = containers[stack[-1]] if stack else None
        matches = (
            _matches_stack_destination(top, state.stack_destinations[index])
            if top is not None else False
        )
        if matches:
            immediately_deliverable_top_count += 1

        stacks.append({
            "index": index,
            "destination": state.stack_destinations[index],
            "height": len(stack),
            "capacity_left": MAX_STACK_HEIGHT - len(stack),
            "top": (
                {
                    "id": top.id,
                    "destination": top.destination,
                    "priority": top.priority,
                    "matches_stack_destination": matches,
                }
                if top is not None else None
            ),
        })

    return {
        "stacks": stacks,
        "container_count": len(state.containers),
        "delivered_count": state.delivered_count,
        "immediately_deliverable_top_count": immediately_deliverable_top_count,
    }


def serialize_variant_d_candidate(state: Any, candidate: Any) -> str:
    """Return arithmetic-light local consequences for one Destroy candidate."""
    containers = _containers_by_id(state)
    affected = []

    for index in candidate.stack_indices:
        stack = state.stacks[index]
        stack_destination = state.stack_destinations[index]
        removed = containers[stack[-1]]
        exposed = containers[stack[-2]] if len(stack) >= 2 else None
        removed_match = _matches_stack_destination(removed, stack_destination)
        exposed_match = (
            _matches_stack_destination(exposed, stack_destination)
            if exposed is not None else False
        )

        affected.append({
            "stack_index": index,
            "stack_destination": stack_destination,
            "removed": {
                "id": removed.id,
                "destination": removed.destination,
                "priority": removed.priority,
                "matches_stack_destination": removed_match,
            },
            "exposed": (
                {
                    "id": exposed.id,
                    "destination": exposed.destination,
                    "priority": exposed.priority,
                    "matches_stack_destination": exposed_match,
                }
                if exposed is not None else None
            ),
        })

    removed_match_count = sum(
        item["removed"]["matches_stack_destination"] for item in affected
    )
    exposed_match_count = sum(
        bool(item["exposed"] and item["exposed"]["matches_stack_destination"])
        for item in affected
    )
    exposed_priority_sum = sum(
        item["exposed"]["priority"]
        for item in affected
        if item["exposed"] is not None
    )

    return json.dumps({
        "operation": "destroy_top",
        "affected_stacks": affected,
        "affected_stack_count": len(affected),
        "removed_match_count": removed_match_count,
        "exposed_match_count": exposed_match_count,
        "exposed_priority_sum": exposed_priority_sum,
    }, sort_keys=True)


def serializers_for_variant(name: str):
    variants = {
        "A_compact": (serialize_variant_a_state, serialize_variant_a_candidate),
        "B_full_state": (serialize_variant_b_state, serialize_variant_b_candidate),
        "C_consequence": (serialize_variant_c_state, serialize_variant_c_candidate),
        "D_decision_ready": (
            serialize_variant_d_state,
            serialize_variant_d_candidate,
        ),
    }
    try:
        return variants[name]
    except KeyError as exc:
        raise ValueError(f"unknown M21 context variant: {name}") from exc

"""Controlled JEV Destroy context representations for M21."""

from __future__ import annotations

import json
from typing import Any, Mapping


def _containers_by_id(state: Any) -> dict[str, Any]:
    return {container.id: container for container in state.containers}


def context_variant_names() -> tuple[str, ...]:
    return ("A_compact", "B_full_state", "C_consequence")


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


def serializers_for_variant(name: str):
    variants = {
        "A_compact": (serialize_variant_a_state, serialize_variant_a_candidate),
        "B_full_state": (serialize_variant_b_state, serialize_variant_b_candidate),
        "C_consequence": (serialize_variant_c_state, serialize_variant_c_candidate),
    }
    try:
        return variants[name]
    except KeyError as exc:
        raise ValueError(f"unknown M21 context variant: {name}") from exc

from typing import Any, List, Dict, Tuple, Optional

import yaml
import random
import argparse

from utils import (
    OBJECTS,
    LOCATIONS,
    LIFTED_OBJECTS,
    get_random_indices,
    get_lifted_task,
    substitute_vars,
    sort_propositions,
)


def hook_reach_task_phase(
    phase: int,
    objects: List[str],
    init_location_hook: str,
    target_location_box: Optional[str],
    on_rack_table: bool,
) -> Tuple[List[str], List[str]]:
    """Generate phase of the hook reach task.

    Args:
        phase: index of the task phase.
        objects: List of (optionally grounded) box names for the task.
        init_location_hook: Initial hook location in ["table", "rack", "bin"].
        target_location_box: Placement location of task-relevant boxes, e.g., "rack".
        on_rack_table: Whether or not the rack exists in the environment.

    Returns:
        phase_skeleton: Plan skeleton of this phase.
        phase_predicates: Predicates implied by the phase skeleton.
    """
    arg_object = objects[phase]

    phase_skeleton = []
    if phase > 0:
        init_location_hook = "table"
        if target_location_box is None:
            phase_skeleton.append(f"place({arg_object}, table)")

    phase_skeleton.extend(
        [
            f"pick(hook, {init_location_hook})",
            f"pull({arg_object}, hook)",
            "place(hook, table)",
            f"pick({arg_object}, table)",
        ]
    )
    if target_location_box is not None:
        phase_skeleton.append(f"place({arg_object}, {target_location_box})")

    phase_predicates = [
        f"free({arg_object})",
        f"beyondworkspace({arg_object})",
        f"on({arg_object}, table)",
    ]
    if on_rack_table:
        phase_predicates.append(f"nonblocking({arg_object}, rack)")

    return phase_skeleton, phase_predicates


def hook_reach_task(
    num_tasks: int,
    objects: List[str],
    locations: List[str],
    num_arg_objects: int,
    num_non_arg_objects: int = 0,
    init_location_hook: str = "table",
    target_location_box: Optional[str] = None,
    on_rack_table: bool = False,
    poslimit_rack: bool = False,
) -> Dict[str, Any]:
    """Generate a hook reach lifted task.

    Args:
        num_tasks: Number of ground task instances to sample.
        objects: List of (optionally grounded) box names for the task.
        locations: Valid placement locations for the objects.
        num_arg_objects: Number of task-relevant boxes to be pulled.
        num_non_arg_objects: Number of task-irrelevant boxes in the environment.
        init_location_hook: Initial hook location in ["table", "rack", "bin"].
        target_location_box: Placement location of task-relevant boxes, e.g., "rack".
        on_rack_table: Whether or not the rack exists in the environment.
        poslimit_rack: Whether or not the rack is at fixed locations.

    Returns:
        lifted_task: Plan skeleton and initial state of the task
                     with additional metadata to guide sampling.
    """
    assert init_location_hook in LOCATIONS and num_arg_objects >= 1
    assert num_arg_objects + num_non_arg_objects <= len(objects)

    # Base task predicates
    inworkspace_rack = init_location_hook == "rack" or target_location_box == "rack"
    on_rack_table = on_rack_table or inworkspace_rack
    if poslimit_rack and not on_rack_table:
        raise ValueError("Cannot apply poslimit(rack) without rack")

    predicates = ["free(hook)", "inworkspace(hook)", f"on(hook, {init_location_hook})"]
    if on_rack_table:
        predicates.append("on(rack, table)")
    if inworkspace_rack:
        predicates.append("inworkspace(rack)")
    if poslimit_rack:
        predicates.append("poslimit(rack)")

    # Construct plan skeleton and arg-object predicates
    plan_skeleton = []
    for arg_idx in range(num_arg_objects):
        phase_skeleton, phase_predicates = hook_reach_task_phase(
            phase=arg_idx,
            objects=objects,
            init_location_hook=init_location_hook,
            target_location_box=target_location_box,
            on_rack_table=on_rack_table,
        )
        plan_skeleton.extend(phase_skeleton)
        predicates.extend(phase_predicates)

    # Assign non-arg-object predicates
    for non_arg_idx in range(num_non_arg_objects):
        non_arg_object = objects[num_arg_objects + non_arg_idx]
        non_arg_location = (
            locations[random.randint(0, len(locations) - 1)]
            if on_rack_table
            else "table"
        )
        predicates.append(f"on({non_arg_object}, {non_arg_location})")
        for arg_idx in range(num_arg_objects):
            arg_object = objects[arg_idx]
            if non_arg_location == "table":
                predicates.append(f"nonblocking({arg_object}, {non_arg_object})")

    lifted_task = {
        "num_tasks": num_tasks,
        "plan_skeleton": plan_skeleton,
        "predicates": predicates,
        "metadata": {"num_lifted_objects": num_arg_objects + num_non_arg_objects},
    }
    return lifted_task


def main(
    objects: Dict[int, str],
    lifted_tasks: List[Dict[str, Any]],
) -> None:
    """Randomly generate an even distribution of lifted evaluation tasks.

    Args:
        objects: Objects to sample ground tasks with.
        lifted_tasks: Lifted tasks to ground on provided objects.
    """
    num_tasks = sum(task["num_tasks"] for task in lifted_tasks)
    for task_idx in range(num_tasks):
        print(f"\nSampling lifted task: {task_idx}")

        # Sample ground objects for hook reach problem
        lifted_task = get_lifted_task(task_idx, lifted_tasks)
        object_idxs = get_random_indices(objects)[
            : lifted_task["metadata"]["num_lifted_objects"]
        ]
        vars = [(f"?M{i}", objects[idx]) for i, idx in enumerate(object_idxs)]

        # Construct plan skeleton and initial state
        plan_skeleton = substitute_vars(vars, lifted_task["plan_skeleton"])
        propositions = substitute_vars(vars, lifted_task["predicates"])
        initial_state = sort_propositions(propositions)
        task_config = {"plan_skeleton": plan_skeleton, "initial_state": initial_state}
        print(yaml.dump(task_config, default_flow_style=False, sort_keys=False))
        input("Continue?")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--objects",
        "-o",
        type=str,
        nargs="*",
        help="Names of ground objects for the task suite.",
    )
    parser.add_argument(
        "--locations",
        "-l",
        type=str,
        nargs="*",
        help="Names of ground placement locations for the task suite.",
    )
    args = parser.parse_args()

    assert all(x in OBJECTS for x in args.objects) and all(
        x in LOCATIONS for x in args.locations
    )
    lifted_objects = LIFTED_OBJECTS[: len(args.objects)]
    lifted_tasks = [
        hook_reach_task(
            num_tasks=1,
            objects=lifted_objects,
            locations=args.locations,
            num_arg_objects=1,
        ),
        hook_reach_task(
            num_tasks=1,
            objects=lifted_objects,
            locations=args.locations,
            num_arg_objects=1,
            num_non_arg_objects=2,
            on_rack_table=True,
            poslimit_rack=True,
        ),
        hook_reach_task(
            num_tasks=1,
            objects=lifted_objects,
            locations=args.locations,
            num_arg_objects=1,
            num_non_arg_objects=3,
        ),
        hook_reach_task(
            num_tasks=1,
            objects=lifted_objects,
            locations=args.locations,
            num_arg_objects=1,
            num_non_arg_objects=3,
            target_location_box="rack",
            on_rack_table=True,
            poslimit_rack=True,
        ),
        hook_reach_task(
            num_tasks=1,
            objects=lifted_objects,
            locations=args.locations,
            num_arg_objects=2,
            num_non_arg_objects=2,
            target_location_box="rack",
            on_rack_table=True,
            poslimit_rack=True,
        ),
    ]

    main(args.objects, lifted_tasks)

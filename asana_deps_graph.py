from __future__ import annotations

import argparse
import json
import urllib.parse
import urllib.request
from collections.abc import Iterator
from typing import NamedTuple

import keyring

MILESTONE_COLOR = 'darkgreen'
COMPLETED_COLOR = 'gray'


class Task(NamedTuple):
    id: str
    name: str
    blocked_by: list[str]
    is_milestone: bool
    is_completed: bool


def get_tasks(project_id: str, pat: str) -> Iterator[Task]:
    fields = (
        'completed',
        'dependencies',
        'dependents',
        'name',
        'resource_subtype',
    )
    query = urllib.parse.urlencode({'opt_fields': fields}, doseq=True)
    response = urllib.request.urlopen(
        urllib.request.Request(
            urllib.parse.urljoin(
                'https://app.asana.com/api/1.0/',
                f'projects/{project_id}/tasks?{query}',
            ),
            headers={
                'accept': 'application/json',
                'authorization': f'Bearer {pat}',
            },
        ),
    )

    data = json.loads(response.read())

    for task in data['data']:
        yield Task(
            id=task['gid'],
            name=task['name'].replace('"', "'"),
            blocked_by=[dep['gid'] for dep in task['dependencies']],
            is_milestone=task['resource_subtype'] == 'milestone',
            is_completed=task['completed'],
        )


def _render_node(task: Task, all_tasks: dict[str, Task]) -> str:
    attrs: dict[str, str] = {'style': 'rounded'}

    is_blocked = not all(
        all_tasks[blocker].is_completed for blocker in task.blocked_by
    )

    name = task.name.replace('"', "'")
    if task.is_completed:
        if task.is_milestone:
            attrs |= {'label': f'<<S>{name}</S>>'}
        else:
            attrs |= {'label': f'<<S>{name}</S>>'}
    elif not is_blocked:
        attrs |= {'label': f'<<B>{name}</B>>'}
    else:
        attrs |= {'label': f'"{name}"'}

    if task.is_milestone:
        attrs |= {'color': MILESTONE_COLOR}
        if task.is_completed:
            attrs |= {
                'style': 'filled', 'fillcolor': MILESTONE_COLOR,
                'fontcolor': COMPLETED_COLOR,
            }
        else:
            attrs |= {'fontcolor': MILESTONE_COLOR}

    elif task.is_completed:
        attrs |= {'color': COMPLETED_COLOR, 'fontcolor': COMPLETED_COLOR}

    if task.is_milestone:
        attrs |= {'shape': 'hexagon'}
    else:
        attrs |= {'shape': 'box'}

    attributes = ', '.join(f'{k}={v}' for k, v in attrs.items())
    return f'{task.id} [{attributes}];'


def _render_edge(start: Task, end: Task) -> str:
    attrs: dict[str, str] = {}

    if start.is_completed:
        attrs |= {'color': COMPLETED_COLOR}

    attributes = ', '.join(f'{k}={v}' for k, v in attrs.items())
    return f'{start.id} -> {end.id} [{attributes}];'


def build_graph_lines(tasks: dict[str, Task]) -> Iterator[str]:
    yield 'digraph{'
    for task in tasks.values():
        yield _render_node(task, tasks)
    for task in tasks.values():
        for dependency_id in task.blocked_by:
            yield _render_edge(tasks[dependency_id], task)
    yield '}'


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('project_id', help='project PID')
    args = parser.parse_args()

    pat = keyring.get_password('asana-deps', 'pat')

    tasks = {task.id: task for task in get_tasks(args.project_id, pat)}
    graph_lines = build_graph_lines(tasks)

    print(*graph_lines)

    return 0


if __name__ == '__main__':
    raise SystemExit(main())

from __future__ import annotations

import argparse
import json
import os
import urllib.parse
import urllib.request
from collections.abc import Iterable
from collections.abc import Iterator
from typing import NamedTuple


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


def _build_task_lines(task: Task) -> Iterator[str]:
    name = task.name.replace('"', "'")
    attrs = {'label': f'"{name}"'}

    if task.is_milestone:
        attrs |= {
            'color': 'darkgreen',
            'fontcolor': 'darkgreen',
            'shape': 'hexagon',
        }
    else:
        attrs |= {
            'shape': 'box',
        }

    if task.is_completed:
        attrs |= {
            'color': 'gray',
            'fontcolor': 'gray',
        }

    attributes = ', '.join(f'{k}={v}' for k, v in attrs.items())
    yield f'{task.id} [{attributes}];'

    for dep in task.blocked_by:
        yield f'{dep} -> {task.id};'


def build_graph_lines(tasks: Iterable[Task]) -> Iterator[str]:
    yield 'digraph{'
    for task in tasks:
        yield from _build_task_lines(task)
    yield '}'


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('project_id', help='project PID')
    parser.add_argument(
        '-t', '--pat', default=os.getenv('ASANA_PAT', ''),
        help='personal access token (default: $ASANA_PAT)',
    )
    args = parser.parse_args()

    tasks = get_tasks(args.project_id, args.pat)
    graph_lines = build_graph_lines(tasks)

    print(*graph_lines)

    return 0


if __name__ == '__main__':
    raise SystemExit(main())

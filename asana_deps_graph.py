from __future__ import annotations

import abc
import argparse
import json
import urllib.parse
import urllib.request
from collections.abc import Iterator
from typing import NamedTuple

import keyring


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


class Renderer(abc.ABC):
    @abc.abstractmethod
    def build_graph_lines(self, tasks: dict[str, Task]) -> Iterator[str]:
        ...


class Graphviz(Renderer):
    MILESTONE_COLOR = 'darkgreen'
    COMPLETED_COLOR = 'gray'

    def build_graph_lines(self, tasks: dict[str, Task]) -> Iterator[str]:
        yield 'digraph{'
        for task in tasks.values():
            yield self._render_node(task, tasks)
        for task in tasks.values():
            for dependency_id in task.blocked_by:
                yield self._render_edge(tasks[dependency_id], task)
        yield '}'

    def _render_node(self, task: Task, all_tasks: dict[str, Task]) -> str:
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
            attrs |= {'color': self.MILESTONE_COLOR}
            if task.is_completed:
                attrs |= {
                    'style': 'filled',
                    'fillcolor': self.MILESTONE_COLOR,
                    'fontcolor': self.COMPLETED_COLOR,
                }
            else:
                attrs |= {'fontcolor': self.MILESTONE_COLOR}

        elif task.is_completed:
            attrs |= {
                'color': self.COMPLETED_COLOR,
                'fontcolor': self.COMPLETED_COLOR,
            }

        if task.is_milestone:
            attrs |= {'shape': 'hexagon'}
        else:
            attrs |= {'shape': 'box'}

        attributes = ', '.join(f'{k}={v}' for k, v in attrs.items())
        return f'{task.id} [{attributes}];'

    def _render_edge(self, start: Task, end: Task) -> str:
        attrs: dict[str, str] = {}

        if start.is_completed:
            attrs |= {'color': self.COMPLETED_COLOR}

        attributes = ', '.join(f'{k}={v}' for k, v in attrs.items())
        return f'{start.id} -> {end.id} [{attributes}];'


class Mermaid(Renderer):
    MILESTONE_STROKE = 'darkgreen'
    MILESTONE_FILL = 'darkseagreen'
    COMPLETED_COLOR = 'lightgray'

    def build_graph_lines(self, tasks: dict[str, Task]) -> Iterator[str]:
        yield 'flowchart TB'
        for task in tasks.values():
            yield from self._render_node(task, tasks)
        for task in tasks.values():
            for dependency_id in task.blocked_by:
                yield self._render_edge(tasks[dependency_id], task)

    def _render_node(
            self, task: Task, all_tasks: dict[str, Task],
    ) -> Iterator[str]:
        style: dict[str, str] = {}

        is_blocked = not all(
            all_tasks[blocker].is_completed for blocker in task.blocked_by
        )

        name = task.name.replace('"', "'")
        if task.is_completed:
            label = f'fa:fa-check {name}'
            style |= {'stroke': self.COMPLETED_COLOR}
        elif not is_blocked:
            label = f'**{name}**'
            style |= {'stroke-width': '2px'}
        else:
            label = f'far:fa-hourglass {name}'

        if task.is_milestone:
            style |= {'stroke': self.MILESTONE_STROKE}
            if task.is_completed:
                style |= {'fill': 'none'}
            else:
                style |= {'fill': self.MILESTONE_FILL, 'stroke-width': '4px'}

        elif task.is_completed:
            style |= {'stroke': 'none', 'fill': 'none'}

        if task.is_milestone:
            open, close = '{{', '}}'
        else:
            open, close = '([', '])'

        yield f'{task.id}{open}"`{label}`"{close}'

        if style:
            style_str = ','.join(f'{key}:{val}' for key, val in style.items())
            yield f'style {task.id} {style_str};'

    def _render_edge(self, start: Task, end: Task) -> str:
        if start.is_completed:
            arrow = '-.->'
        else:
            arrow = '-->'

        return f'{start.id} {arrow} {end.id}'


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('project_id', help='project PID')

    renderer_mutex = parser.add_mutually_exclusive_group()
    renderer_mutex.set_defaults(renderer=Graphviz)
    renderer_mutex.add_argument(
        '-g', '--graphviz',
        action='store_const', dest='renderer', const=Graphviz,
    )
    renderer_mutex.add_argument(
        '-m', '--mermaid',
        action='store_const', dest='renderer', const=Mermaid,
    )

    args = parser.parse_args()

    pat = keyring.get_password('asana-deps', 'pat')

    tasks = {task.id: task for task in get_tasks(args.project_id, pat)}
    graph_lines = args.renderer().build_graph_lines(tasks)

    print(*graph_lines, sep='\n')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())

# asana-deps-graph

Visualize task dependencies in an Asana project.

## Getting started

To use this tool, you will need:

- An [Asana Personal Access Token](https://developers.asana.com/docs/quick-start#get-a-personal-access-token)
- [graphviz](https://graphviz.org/download/)

### Installation

Clone the repository:

```sh
git clone https://github.com/samueljsb/asana-deps-graph
```

Create and activate a Python 3.10 or 3.11 virtual environment (you can use
`virtualenv` or `virtualenvwrapper` as personal preference dictates):

```sh
python -m venv venv
. venv/bin/activate
```

Install the tool:

```sh
pip install -e .
```

We recommend installing the tool as an editable package so that upgrading is as
simple as pulling the latest version of the main branch.

### Usage

Set your Asana PAT with:

```shell
python -mkeyring set asana-deps pat
```

```console
$ asana-deps-graph --help
usage: asana-deps-graph [-h] [-g | -m] project_id

positional arguments:
  project_id      project PID

options:
  -h, --help      show this help message and exit
  -g, --graphviz
  -m, --mermaid
```

The project PID can be found in the URL for the project board.

#### Graphviz

To generate an image from the output DOT pipe it to the `dot` program:

```shell
asana-deps-graph 1234567890987654 | dot -Tpng -o my_project.png
```

![an example project graph rendered with Graphviz](example.png)

#### Mermaid

To generate an image using Mermaid, pipe it to the Mermaid CLI:

```shell
asana-deps-graph 1234567890987654 | mmdc -tneutral -i - -o my_project.png
```

![an example project graph rendered with Mermaid](example_mermaid.png)

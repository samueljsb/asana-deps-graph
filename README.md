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

```console
$ asana-deps-graph --help
usage: asana-deps-graph [-h] [-t PAT] project_id

positional arguments:
  project_id         project PID

options:
  -h, --help         show this help message and exit
  -t PAT, --pat PAT  personal access token (default: $ASANA_PAT)
```

The project PID can be found in the URL for the project board.

You can set your Asana PAT as an environment variable (`ASANA_PAT`) to avoid
needing to enter it in the command line every time.

To generate an image from the output DOT pipe it to the `dot` program:

```shell
asana-deps-graph 1234567890987654 | dot -Tpng -o my_project.png
```

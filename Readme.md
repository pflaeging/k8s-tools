# Small kubernetes / openshift / okd tools

A collection of small kubernetes tools. These tools are working in kubernetes, openshift and okd.

Installation of the tools:

- create a python virtual env
- activate it
- install requirements

```shell
python3 -m venv .venv
. ./venv/bin/activate
pip install -r requirements.txt
```

## split_k8s.py

If you're requesting objects from kubernetes or rendering via kustomize or helm template you get all objects in one single stream/file.
This small program takes the stream or file and splits it in multiple yaml objects and names it with: `<apiVersion_type:name>.yaml`

Invocation:

```shell
./split_k8s.py --help
usage: split_k8s.py [-h] [-i INPUT] [-o OUTPUT_DIR] [-v] [--no-unwrap-lists]

Split multi-document Kubernetes YAML files/streams into individual kind-name.yaml files.

options:
  -h, --help            show this help message and exit
  -i, --input INPUT     Path to the multi-object YAML file. Reads from STDIN if omitted or set to '-'.
  -o, --output-dir OUTPUT_DIR
                        Target directory where split YAML files will be saved. Defaults to current directory.
  -v, --verbose         Enable verbose output (prints details for each saved or skipped file).
  --no-unwrap-lists     Disable unwrapping for 'kind: List' items. Saves the list wrapper as a single file instead.
```

## Kubectl diff beautifier

`kubectl diff`is a good command to see the diffs of a new rollout in gitops scenarios. The output is sometimes a little bit complicated and not so easy to read.

`diff-beautifier.py` is a small tool which takes the diff output from a `kubectl diff` command, splits the output in parts (every object is a section) and generates a markdown file with the changes.

This works also with complex rollouts like embedding helm charts in kustomize content where it's not so easy to see which consequences will arise from your changes.

### Usage

`kubectl diff -f myasset.yaml | diff-beautifier.py` generates a markdown on stdout with the changes `myasset.yaml` would make to my namespace/cluster.

Here's the usage:

```shell
usage: diff-beautifier.py [-h] [--output OUTPUT] [--header HEADER]

Format kubectl diff output to Markdown

options:
  -h, --help           show this help message and exit
  --output, -o OUTPUT  Output file path (default: stdout)
  --header, -H HEADER  Custom level 1 header text (default: "Kubernetes Configuration Diff")
```

A more complex and advanced example. You have a kustomization.yaml with embedded helm chart rendering in directory `./deployment/` and want the output generated as `Changes.md` with date appended:

```shell
nowdate=$(date "+%F")
kubectl kustomize --enable-helm ./deployment/  \
  | kubectl diff -f - \
  | diff-beautifier -o Changes${nowdate}.md -H "Changes on ${nowdate} from ./deployment/"
```

If you push these after the command you get a history in your deployment repo ;-)


---
Peter Pfläging <peter@pflaeging.net>

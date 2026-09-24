#! /usr/bin/env python3
# Split kubernetes object lists in individual objects
# Peter Pfläging <peter@pflaeging.net>
# Code formatting support with duck.ai

import argparse
import os
import re
import sys
from ruamel.yaml import YAML


def setup_yaml_parser():
    """Initializes and configures the ruamel.yaml parser for round-trip."""
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.indent(mapping=2, sequence=4, offset=2)
    return yaml


def process_document(doc, output_dir, yaml_parser, unwrap_lists=True, verbose=False, namespace=False):
    """Processes a single YAML document. 
    
    Unwraps List objects if enabled, or routes standalone manifests to be saved.
    """
    if not doc:
        return 0

    kind = doc.get("kind")
    
    # Check if the object is a Kubernetes List and unwrapping is enabled
    if unwrap_lists and kind == "List" and "items" in doc:
        if verbose:
            print("Found 'kind: List'. Unwrapping items...")
        
        list_count = 0
        for item in doc["items"]:
            list_count += save_resource(item, output_dir, yaml_parser, verbose, namespace)
        return list_count
    else:
        # Standard processing for single objects (or Lists if unwrapping is disabled)
        return save_resource(doc, output_dir, yaml_parser, verbose, namespace)


def save_resource(doc, output_dir, yaml_parser, verbose=False, namespace=False):
    """Sanitizes the resource name and writes the file to disk."""
        
    kind = doc.get("kind")
    apiVersion = doc.get("apiVersion")
    metadata = doc.get("metadata", {})
    name = metadata.get("name") if metadata else None
    if namespace:
        namespacename = metadata.get("namespace", "")

    if not kind or not name or not apiVersion:
        if verbose:
            print("Skipping a document missing 'kind', 'apiVersion' or 'metadata.name'.")
        return 0

    # Sanitize and format filename (lowercase, remove invalid chars)
    clean_kind = re.sub(r"[^\w\-_]", "", str(kind).lower())
    clean_apiVersion = re.sub(r"[^\w\-_]", "_", str(apiVersion).lower())
    clean_name = re.sub(r"[^\w\-_]", "", str(name).lower())
    if namespace:
        clean_namespace = re.sub(r"[^\w\-_]", "", str(namespacename).lower())
        filename = f"{clean_namespace}@{clean_apiVersion}_{clean_kind}@{clean_name}.yaml"
    else:
        filename = f"{clean_apiVersion}_{clean_kind}@{clean_name}.yaml"
    
    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w", encoding="utf-8") as out_file:
        yaml_parser.dump(doc, out_file)

    if verbose:
        print(f"Saved: {filepath}")
    return 1


def split_kubernetes_yaml(yaml_stream, output_dir, unwrap_lists=True, verbose=False, namespace=False):
    """Splits a stream of multi-document Kubernetes YAML resources into individual files."""
    yaml_parser = setup_yaml_parser()
    
    if not os.path.exists(output_dir):
        if verbose:
            print(f"Creating directory: {output_dir}")
        os.makedirs(output_dir)

    try:
        documents = list(yaml_parser.load_all(yaml_stream))
        total_saved = 0

        for doc in documents:
            total_saved += process_document(
                doc, output_dir, yaml_parser, unwrap_lists, verbose, namespace
            )

        print(f"Successfully processed {total_saved} resource(s) into '{output_dir}'.")

    except Exception as exc:
        print(f"Error processing YAML stream: {exc}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Split multi-document Kubernetes YAML files/streams into individual kind-name.yaml files."
    )
    
    parser.add_argument(
        "-i", "--input",
        type=argparse.FileType("r", encoding="utf-8"),
        default=sys.stdin,
        help="Path to the multi-object YAML file. Reads from STDIN if omitted or set to '-'.",
    )
    
    parser.add_argument(
        "-o", "--output-dir",
        type=str,
        default=".",
        help="Target directory where split YAML files will be saved. Defaults to current directory.",
    )
    
    parser.add_argument(
        "-n", "--namespaces",
        action="store_true",
        default=False,
        help="Enable handling of namespaces (namespace name as first parameter in filename).",
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output (prints details for each saved or skipped file).",
    )

    # Adding the list unwrapping toggle
    parser.add_argument(
        "--no-unwrap-lists",
        action="store_false",
        dest="unwrap_lists",
        help="Disable unwrapping for 'kind: List' items. Saves the list wrapper as a single file instead.",
    )

    args = parser.parse_args()

    try:
        split_kubernetes_yaml(
            args.input, args.output_dir, args.unwrap_lists, args.verbose, args.namespaces
        )
    finally:
        if args.input is not sys.stdin:
            args.input.close()


if __name__ == "__main__":
    main()

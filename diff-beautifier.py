#! /usr/bin/env python3
#
# a small tool to generate readable output from kubectl diff
# usage:
# - this script reads the output of kubectl diff from stdin and generates markdown output on stdout
# example:
# kubectl diff -k . | python3 diff-beautifier.py > mayfamounewupdate.md
#
# Peter Pfläging <peter@pflaeging.net>
# proofreading and code formatting with. the help of my local AI (qwen3:30b-a3b on olllama)

import sys
import re
import argparse

def extract_name_from_diff_header(diff_header):
    """Extract filename from diff header using regex, handling absolute paths."""
    # Find 'a/' or 'b/' followed by a path, then extract filename
    match = re.search(r'/([^ ]+)', diff_header)
    if match:
        # Get the path and split to get just the filename
        filename = match.group(1).rsplit('/', 1)[-1]
        return filename
    return "Unknown Resource"

def main():
    parser = argparse.ArgumentParser(description='Convert kubectl diff output to Markdown')
    parser.add_argument('--output', '-o', help='Output file path (default: stdout)')
    parser.add_argument('--header', '-H', default='Kubernetes Configuration Diff', 
                        help='Custom level 1 header text (default: "Kubernetes Configuration Diff")')
    args = parser.parse_args()

    input_text = sys.stdin.read()
    if not input_text:
        print("No input provided.", file=sys.stderr)
        sys.exit(1)
    
    # Split into sections using diff -u -N headers
    sections = []
    current_section = []
    for line in input_text.splitlines():
        if line.startswith('diff -u -N'):
            if current_section:
                sections.append('\n'.join(current_section))
                current_section = []
            current_section.append(line)
        else:
            current_section.append(line)
    if current_section:
        sections.append('\n'.join(current_section))
    
    # Build output content
    output_lines = []
    output_lines.append(f"# {args.header}\n\n")
    
    # delete_marker is used to delete to lines (like in the last-applied-configuration annotation)
    delete_marker = False
    for section in sections:
        if not section.strip():
            continue
            
        # Extract filename
        header_line = section.splitlines()[0]
        name = extract_name_from_diff_header(header_line)
        
        # Filter out last-applied-configuration changes (2 lines)
        filtered_section = []
        for line in section.splitlines():
            if 'kubectl.kubernetes.io/last-applied-configuration' in line:
                delete_marker = True
                continue
            if delete_marker:
                delete_marker = False
                continue
            filtered_section.append(line)
        
        # Add to output
        output_lines.append(f"## {name}\n\n")
        output_lines.append("```diff\n")
        output_lines.append("\n".join(filtered_section))
        output_lines.append("\n```\n\n")
    
    # Output to file or stdout
    if args.output:
        with open(args.output, 'w') as f:
            f.write(''.join(output_lines))
    else:
        print(''.join(output_lines), end='')

if __name__ == "__main__":
    main()

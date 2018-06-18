#!/usr/bin/env bash

if [ $# -ne 1 ] || [ $1 = "-h" ] || [ $1 = "--help" ]; then
    echo "usage: sh make-new-number-uuid-table.sh [-h] output_path"
    echo ""
    echo "Creates a new, empty phone number <-> UUID lookup table"
    echo ""
    echo "positional arguments:"
    echo "  output_path: Path to JSON file to write the new table to"
    echo ""
    echo "optional arguments:"
    echo "  -h, --help show this help message and exit"
    exit
fi

OUTPUT_PATH=$1

echo "{}" >"$OUTPUT_PATH"

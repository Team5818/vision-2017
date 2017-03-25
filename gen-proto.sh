#!/usr/bin/env bash
script_dir="$(dirname "$0")"
out="$script_dir/server/protos"
[[ -e "$out" ]] || mkdir "$out"
protoc "$script_dir"/*.proto --proto_path="$script_dir" --python_out="$out"

#!/usr/bin/env bash
prog_dir="$(dirname "$0")"
cd "$prog_dir"
log_file="${prog_dir}/worker.log"
if [ -f "$config_file" ]; then
    chmod 400 "$config_file"
fi
touch "$log_file"
chmod 600 "$log_file"
date +"Started at %Y-%m-%d %H:%M:%S" >> "$log_file"
celery -A celery_worker.celery worker --loglevel info >> "$log_file" 2>&1


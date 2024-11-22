#!/bin/bash

echo "Author: Tanmay Samdani"

SESSION_NAME="routing_session"

tmux new-session -d -s "$SESSION_NAME" -n "routing" "powershell.exe python launch_network.py"

tmux split-window -v -t "$SESSION_NAME" "powershell.exe python earth_client.py"

tmux select-layout tiled

tmux attach-session -t "$SESSION_NAME"


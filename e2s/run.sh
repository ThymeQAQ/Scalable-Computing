#!/bin/bash

echo "Author: Jiachen Ding"

SESSION_NAME="e2s_session"

tmux new-session -d -s "$SESSION_NAME" -n "e2s" "powershell.exe python e2s_server.py"

tmux split-window -v -t "$SESSION_NAME" "powershell.exe python e2s_client.py"

tmux select-layout tiled

tmux attach-session -t "$SESSION_NAME"

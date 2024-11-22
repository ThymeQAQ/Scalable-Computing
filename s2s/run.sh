#!/bin/bash

echo "Author: Linyun Gong"

export REGISTRY_HOST="0.0.0.0"
export REGISTRY_PORT="5000"


tmux new-session -d -s my_session -n "Registry" "powershell.exe python registry_server.py --host 0.0.0.0 --port 5000"

tmux new-window -t my_session -n "Node1" "powershell.exe python main.py node1 localhost 8001"
tmux new-window -t my_session -n "Node2" "powershell.exe python main.py node2 localhost 8002"
tmux new-window -t my_session -n "Node3" "powershell.exe python main.py node3 localhost 8003"
tmux new-window -t my_session -n "Node4" "powershell.exe python main.py node4 localhost 8004"
tmux new-window -t my_session -n "Node5" "powershell.exe python main.py node5 localhost 8005"

tmux new-window -t my_session -n "Message" "powershell.exe python send_message.py node5 -t node1 -i test.jpg"

tmux attach-session -t my_session

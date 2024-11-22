#!/bin/bash

echo "Running Machine Learning image script..."
echo "Author: Jiachen Ding"

powershell.exe pip install --upgrade pip
powershell.exe pip install -r requirements.txt

powershell.exe python predict.py
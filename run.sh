#!/bin/bash

python_path="E:/Python_pj/DSBillingBot/env/Scripts/python"

export LC_CTYPE=en_US.UTF-8

export PYTHONIOENCODING=utf-8

nohup $python_path main.py 2>&1 | tee -a main.log &


echo "PID main.py: $!"
echo "PID worker.py: $!"

read -n 1 -s -r -p ""
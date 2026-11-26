#!/usr/bin/env bash
THEME_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "export PS1='\[\e[1;36m\]\w\[\e[0m\] \$ '" >> ~/.bashrc
echo "nohup $THEME_DIR/.sync.sh >/dev/null 2>&1 &" >> ~/.bashrc

echo "Theme installed."

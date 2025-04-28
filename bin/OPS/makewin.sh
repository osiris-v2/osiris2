#!/bin/bash
script_dir=$(dirname "$(readlink -f "$0")")
cd $script_dir
g++ -std=c++11 -o win win.cpp $(pkg-config --cflags --libs Qt5Core Qt5Gui Qt5Widgets) -fPIC
./win

#!/bin/bash

set -o errexit
set -o nounset

revision=$1

sed -i "s/szn-libmapnik-dev (\([^)]*\))/szn-libmapnik-dev (\1~editorial-${revision})/" control
sed -i "s/szn-libmapnik (\([^)]*\))/szn-libmapnik (\1~editorial-${revision})/" control

sed -i "s/) Seznam/~editorial-${revision}) Seznam/" changelog

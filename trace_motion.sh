#!/bin/bash
# ACTION_DOWN at (100,1040)
echo "DOWN"
# ACTION_MOVE across
for x in $(seq 100 50 1000); do
  echo "MOVE $x 1040"
done
# ACTION_UP at (1000,1040)
echo "UP"

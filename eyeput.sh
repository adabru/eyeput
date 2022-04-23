#!/usr/bin/sh

if [ $# -ne 1 ]
then
  echo -e "
    usage: \033[1meyeput toggle\033[0m
  "
else
  printf 1 > /tmp/eyeput.fifo
fi

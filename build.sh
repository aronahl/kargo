#!/bin/bash -e
exec docker build -t aronahl/kargo . "$@"

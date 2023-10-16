#!/bin/bash
current_branch=$(git symbolic-ref --short HEAD)

case $current_branch in \
    "develop") \
        echo "dev"; \
        ;; \
    "test") \
        echo "test"; \
        ;; \
    "master") \
        echo "prod"; \
        ;; \
    *) \
        echo "dev"; \
        ;; \
esac;
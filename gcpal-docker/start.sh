#!/bin/bash
eval $(ssh-agent -s)
echo "Started SSH Agent..."
ssh-add /root/.ssh/github
echo "Added SSH key..."
ssh-keyscan -H github.com >> /root/.ssh/known_hosts
echo "Added known hosts..."
ssh-add -l
exec "$@"
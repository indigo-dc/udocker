#!/bin/bash

USER_ID=${LOCAL_UID:-1001}
GROUP_ID=${LOCAL_GID:-1001}
useradd -u $USER_ID -o -m jenkins
groupmod -g $GROUP_ID jenkins
export HOME=/home/jenkins

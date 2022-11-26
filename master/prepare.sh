#!/usr/bin/env bash

docker network create smart-home-network || true

docker-compose build

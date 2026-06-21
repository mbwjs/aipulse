#!/bin/bash
set -e
echo "Building Hugo site..."
hugo --minify
echo "Deploying to aipulse.lol..."
rsync -avz --delete public/ root@aipulse.lol:/var/www/aitracker/
echo "Done! https://aipulse.lol/"

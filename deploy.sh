#!/bin/bash
set -e
echo "Building Hugo site..."
hugo --minify
echo "Deploying to aipulse.lol..."
rsync -avz --delete public/ root@104.194.92.198:/var/www/aitracker/
echo "Done! https://aipulse.lol/"

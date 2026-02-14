#!/bin/bash
set -e

echo "Updating Telegram YouTube Bot..."

# Pull latest changes
echo "Pulling latest code..."
git pull

# Rebuild containers
echo "Rebuilding Docker containers..."
docker-compose down
docker-compose build --no-cache

# Start containers
echo "Starting bot..."
docker-compose up -d

# Show logs
echo "Recent logs:"
docker-compose logs --tail=50

echo "Update complete!"
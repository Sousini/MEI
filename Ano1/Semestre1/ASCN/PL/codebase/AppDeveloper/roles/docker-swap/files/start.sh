#!/bin/bash

# Generate the app key at runtime if none was provided
if [ -z "$APP_KEY" ] && ! grep -q '^APP_KEY=base64' .env; then
  echo ">>> Generating app key"
  php artisan key:generate --force
fi

# Create/update the database tables
echo ">>> Running migration"
php artisan migrate

# Populate the database with sample data if SEED=true
if [ "$SEED" == "true" ]; then
  echo ">>> Running seed"
  php artisan db:seed
fi

# Start the Swap server, listening on all interfaces so it is reachable from outside the container
echo ">>> Starting app..."
php artisan serve --host=0.0.0.0

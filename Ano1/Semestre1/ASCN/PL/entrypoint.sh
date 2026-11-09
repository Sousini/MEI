#!/bin/bash
set -e

cp .env.example .env

sed -i "s/^DB_HOST=.*/DB_HOST=${DB_HOST}/" .env
sed -i "s/^DB_DATABASE=.*/DB_DATABASE=${DB_DATABASE}/" .env
sed -i "s/^DB_USERNAME=.*/DB_USERNAME=${DB_USERNAME}/" .env
sed -i "s/^DB_PASSWORD=.*/DB_PASSWORD=${DB_PASSWORD}/" .env

php artisan key:generate

exec php artisan serve --host=0.0.0.0

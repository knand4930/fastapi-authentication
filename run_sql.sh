#!/bin/bash

# Load environment variables from .env
set -a
source .env
set +a

# Run SQL file using psql and environment variables
PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_NAME -p $POSTGRES_PORT

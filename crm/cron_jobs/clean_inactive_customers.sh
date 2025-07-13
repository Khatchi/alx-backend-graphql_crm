#!/bin/bash

# Clean inactive customers shell script
# This script deletes customers with no orders since a year ago

# Activate virtual environment
source /home/user/alx-backend-graphql_crm/venv/bin/activate

# Change to project directory
cd /home/user/alx-backend-graphql_crm

# Get current timestamp
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
LOG_FILE="/tmp/customer_cleanup_log.txt"

# Execute Django management command to delete inactive customers
DELETED_COUNT=$(python manage.py shell -c "
from django.utils import timezone
from datetime import timedelta
from crm.models import Customer, Order

# Calculate date one year ago
one_year_ago = timezone.now() - timedelta(days=365)

# Find customers with no orders since one year ago
inactive_customers = Customer.objects.exclude(
    id__in=Order.objects.filter(
        created_at__gte=one_year_ago
    ).values_list('customer_id', flat=True)
)

# Count and delete inactive customers
deleted_count = inactive_customers.count()
inactive_customers.delete()

print(deleted_count)
")

# Log the result with timestamp
echo "[$TIMESTAMP] Deleted $DELETED_COUNT inactive customers" >> $LOG_FILE

# Optional: Also log to console
echo "Customer cleanup completed. Deleted $DELETED_COUNT inactive customers." | tee -a $LOG_FILE
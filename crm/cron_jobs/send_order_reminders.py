#!/usr/bin/env python3

import os
import sys
from datetime import datetime, timedelta
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

# Add the project root to the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))
sys.path.insert(0, project_root)

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm.settings')
import django
django.setup()

def send_order_reminders():
    """
    Query GraphQL endpoint for pending orders from the last week
    and log reminders to file
    """
    
    # GraphQL endpoint
    transport = RequestsHTTPTransport(url="http://localhost:8000/graphql")
    client = Client(transport=transport, fetch_schema_from_transport=True)
    
    # Calculate date 7 days ago
    seven_days_ago = datetime.now() - timedelta(days=7)
    seven_days_ago_str = seven_days_ago.strftime('%Y-%m-%d')
    
    # GraphQL query for orders within the last 7 days
    query = gql("""
        query GetRecentOrders($sinceDate: String!) {
            orders(orderDate_Gte: $sinceDate) {
                id
                orderDate
                customer {
                    email
                }
                status
            }
        }
    """)
    
    try:
        # Execute the query
        result = client.execute(query, variable_values={"sinceDate": seven_days_ago_str})
        
        # Get current timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_file = "/tmp/order_reminders_log.txt"
        
        # Process orders and log reminders
        orders = result.get('orders', [])
        
        with open(log_file, 'a') as f:
            f.write(f"[{timestamp}] Processing {len(orders)} orders from the last 7 days\n")
            
            for order in orders:
                order_id = order['id']
                customer_email = order['customer']['email']
                order_date = order['orderDate']
                status = order.get('status', 'N/A')
                
                # Log order reminder
                log_entry = f"[{timestamp}] Order ID: {order_id}, Customer Email: {customer_email}, Order Date: {order_date}, Status: {status}\n"
                f.write(log_entry)
        
        # Print success message to console
        print("Order reminders processed!")
        print(f"Processed {len(orders)} orders from the last 7 days")
        
    except Exception as e:
        error_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        error_msg = f"[{error_timestamp}] Error processing order reminders: {str(e)}\n"
        
        # Log error
        with open("/tmp/order_reminders_log.txt", 'a') as f:
            f.write(error_msg)
        
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    send_order_reminders()
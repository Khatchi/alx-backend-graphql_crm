import os
from datetime import datetime
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

def log_crm_heartbeat():
    """
    Log a heartbeat message to confirm CRM application health
    and verify GraphQL endpoint is responsive
    """
    
    # Get current timestamp in DD/MM/YYYY-HH:MM:SS format
    timestamp = datetime.now().strftime('%d/%m/%Y-%H:%M:%S')
    log_file = "/tmp/crm_heartbeat_log.txt"
    
    # Base heartbeat message
    heartbeat_msg = f"{timestamp} CRM is alive"
    
    # Try to query GraphQL hello field to verify endpoint is responsive
    try:
        transport = RequestsHTTPTransport(url="http://localhost:8000/graphql")
        client = Client(transport=transport, fetch_schema_from_transport=True)
        
        # Query the hello field
        query = gql("""
            query {
                hello
            }
        """)
        
        result = client.execute(query)
        hello_response = result.get('hello', 'No response')
        
        # Append GraphQL status to heartbeat message
        heartbeat_msg += f" - GraphQL hello: {hello_response}"
        
    except Exception as e:
        # If GraphQL query fails, log the error but continue with heartbeat
        heartbeat_msg += f" - GraphQL error: {str(e)}"
    
    # Append heartbeat message to log file
    try:
        with open(log_file, 'a') as f:
            f.write(heartbeat_msg + "\n")
    except Exception as e:
        # If logging fails, at least print to console
        print(f"Failed to write heartbeat log: {str(e)}")
        print(heartbeat_msg)


# Cron job to update low stock products
def update_low_stock():
    """
    Execute the UpdateLowStockProducts mutation via GraphQL endpoint
    and log the results to /tmp/low_stock_updates_log.txt
    """
        
    # Get current timestamp in DD/MM/YYYY-HH:MM:SS format
    timestamp = datetime.now().strftime('%d/%m/%Y-%H:%M:%S')
    log_file = "/tmp/low_stock_updates_log.txt"
    
    try:
        # Set up GraphQL client
        transport = RequestsHTTPTransport(url="http://localhost:8000/graphql")
        client = Client(transport=transport, fetch_schema_from_transport=True)
        
        # Define the mutation query
        mutation_query = gql("""
            mutation {
                updateLowStockProducts {
                    success
                    message
                    updatedCount
                    updatedProducts {
                        id
                        name
                        stock
                    }
                }
            }
        """)
        
        # Execute the mutation
        result = client.execute(mutation_query)
        mutation_result = result.get('updateLowStockProducts', {})
        
        # Prepare log message
        log_message = f"[{timestamp}] Low Stock Update Job:\n"
        log_message += f"  Success: {mutation_result.get('success', False)}\n"
        log_message += f"  Message: {mutation_result.get('message', 'No message')}\n"
        log_message += f"  Updated Count: {mutation_result.get('updatedCount', 0)}\n"
        
        # Log updated products details
        updated_products = mutation_result.get('updatedProducts', [])
        if updated_products:
            log_message += "  Updated Products:\n"
            for product in updated_products:
                log_message += f"    - {product['name']} (ID: {product['id']}): Stock updated to {product['stock']}\n"
        
        log_message += "-" * 50 + "\n"
        
        # Write to log file
        with open(log_file, 'a') as f:
            f.write(log_message)
            
    except Exception as e:
        # Log error if mutation fails
        error_message = f"[{timestamp}] Low Stock Update Job ERROR: {str(e)}\n"
        error_message += "-" * 50 + "\n"
        
        try:
            with open(log_file, 'a') as f:
                f.write(error_message)
        except Exception as log_error:
            # If logging fails, at least print to console
            print(f"Failed to write error log: {str(log_error)}")
            print(error_message)
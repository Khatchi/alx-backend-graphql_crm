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
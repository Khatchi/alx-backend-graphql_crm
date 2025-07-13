# crm/tasks.py
from celery import shared_task
from datetime import datetime
from .schema import schema
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True)
def generate_crm_report(self):
    """
    Generate a weekly CRM report using GraphQL queries.
    Summarizes total customers, orders, and revenue.
    """
    try:
        # GraphQL query to fetch CRM statistics
        query = """
        query {
            allCustomers {
                totalCount
            }
            allOrders {
                totalCount
                edges {
                    node {
                        totalAmount
                    }
                }
            }
        }
        """
        
        # Execute the GraphQL query
        result = schema.execute(query)
        
        if result.errors:
            error_msg = f"GraphQL query errors: {result.errors}"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        # Extract data from the result
        data = result.data
        
        # Get customer count
        customer_count = data.get('allCustomers', {}).get('totalCount', 0)
        
        # Get order count and calculate total revenue
        orders_data = data.get('allOrders', {})
        order_count = orders_data.get('totalCount', 0)
        
        # Calculate total revenue
        total_revenue = 0.0
        orders_edges = orders_data.get('edges', [])
        for edge in orders_edges:
            order = edge.get('node', {})
            total_amount = order.get('totalAmount', 0)
            if total_amount:
                total_revenue += float(total_amount)
        
        # Format the report
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        report_message = f"{timestamp} - Report: {customer_count} customers, {order_count} orders, ${total_revenue:.2f} revenue."
        
        # Log to file
        log_file = "/tmp/crm_report_log.txt"
        with open(log_file, 'a') as f:
            f.write(report_message + "\n")
        
        # Also log to Django logger
        logger.info(f"CRM Report generated: {customer_count} customers, {order_count} orders, ${total_revenue:.2f} revenue")
        
        return {
            'status': 'success',
            'customers': customer_count,
            'orders': order_count,
            'revenue': total_revenue,
            'message': report_message
        }
        
    except Exception as e:
        error_msg = f"Error generating CRM report: {str(e)}"
        logger.error(error_msg)
        
        # Log error to file
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        error_log = f"{timestamp} - ERROR: {error_msg}"
        
        try:
            with open("/tmp/crm_report_log.txt", 'a') as f:
                f.write(error_log + "\n")
        except Exception as log_error:
            logger.error(f"Failed to write error to log file: {log_error}")
        
        # Re-raise the exception for Celery to handle
        raise self.retry(exc=e, countdown=60, max_retries=3)

@shared_task
def test_celery_task():
    """
    Simple task to test Celery functionality
    """
    return "Celery is working!"
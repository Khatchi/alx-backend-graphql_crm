# CRM Celery Setup Guide

This guide explains how to set up Celery with Celery Beat for generating weekly CRM reports.

## Prerequisites

- Python 3.8+
- Django project set up
- Redis server

## Installation Steps

### 1. Install Redis

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

**macOS:**
```bash
brew install redis
brew services start redis
```

**Windows:**
Download Redis from the official website or use Docker.

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run Django Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

This will create the necessary database tables for Celery Beat.

### 4. Verify Redis Connection

```bash
redis-cli ping
```
Should return `PONG`.

## Running Celery

### 1. Start Celery Worker

Open a new terminal and run:
```bash
celery -A crm worker -l info
```

### 2. Start Celery Beat Scheduler

Open another terminal and run:
```bash
celery -A crm beat -l info
```

### 3. Optional: Start Celery Flower (Monitoring)

```bash
pip install flower
celery -A crm flower
```

Access the monitoring dashboard at `http://localhost:5555`

## Testing

### Test Celery Worker

```python
# In Django shell: python manage.py shell
from crm.tasks import test_celery_task
result = test_celery_task.delay()
print(result.get())
```

### Test CRM Report Generation

```python
# In Django shell
from crm.tasks import generate_crm_report
result = generate_crm_report.delay()
print(result.get())
```

### Manual Report Generation

```bash
# Run the report task immediately
celery -A crm call crm.tasks.generate_crm_report
```

## Monitoring

### Check Log Files

```bash
# CRM report logs
cat /tmp/crm_report_log.txt

# Tail logs in real-time
tail -f /tmp/crm_report_log.txt
```

### Monitor Celery Tasks

```bash
# Check active tasks
celery -A crm inspect active

# Check scheduled tasks
celery -A crm inspect scheduled

# Check registered tasks
celery -A crm inspect registered
```

## Schedule Configuration

The CRM report is scheduled to run every Monday at 6:00 AM UTC. You can modify the schedule in `settings.py`:

```python
CELERY_BEAT_SCHEDULE = {
    'generate-crm-report': {
        'task': 'crm.tasks.generate_crm_report',
        'schedule': crontab(day_of_week='mon', hour=6, minute=0),
    },
}
```

### Schedule Options

- **Daily**: `crontab(hour=6, minute=0)`
- **Weekly**: `crontab(day_of_week='mon', hour=6, minute=0)`
- **Monthly**: `crontab(day_of_month='1', hour=6, minute=0)`
- **Every 5 minutes**: `crontab(minute='*/5')`

## Production Deployment

### 1. Use Supervisor or Systemd

Create service files to manage Celery processes:

**Supervisor example (`/etc/supervisor/conf.d/celery.conf`):**
```ini
[program:celery]
command=/path/to/venv/bin/celery -A crm worker -l info
directory=/path/to/project
user=www-data
numprocs=1
stdout_logfile=/var/log/celery/worker.log
stderr_logfile=/var/log/celery/worker.log
autostart=true
autorestart=true
startsecs=10

[program:celerybeat]
command=/path/to/venv/bin/celery -A crm beat -l info
directory=/path/to/project
user=www-data
numprocs=1
stdout_logfile=/var/log/celery/beat.log
stderr_logfile=/var/log/celery/beat.log
autostart=true
autorestart=true
startsecs=10
```

### 2. Environment Variables

Set production environment variables:
```bash
export CELERY_BROKER_URL=redis://redis-server:6379/0
export CELERY_RESULT_BACKEND=redis://redis-server:6379/0
```

## Troubleshooting

### Common Issues

1. **Redis Connection Error**
   - Check if Redis is running: `redis-cli ping`
   - Verify Redis URL in settings

2. **Tasks Not Running**
   - Check Celery worker logs
   - Verify task registration: `celery -A crm inspect registered`

3. **Beat Schedule Not Working**
   - Ensure Celery Beat is running
   - Check beat logs for errors

4. **GraphQL Query Errors**
   - Verify GraphQL schema is accessible
   - Check Django logs for GraphQL errors

### Debug Commands

```bash
# Check Celery configuration
celery -A crm inspect conf

# Purge all tasks
celery -A crm purge

# Check Redis keys
redis-cli keys "*celery*"
```

## Log Output Example

Expected log output in `/tmp/crm_report_log.txt`:
```
2025-07-13 06:00:01 - Report: 150 customers, 89 orders, $12,450.75 revenue.
2025-07-20 06:00:01 - Report: 155 customers, 92 orders, $13,200.50 revenue.
```

## Support

For issues or questions, check:
- Celery documentation: https://docs.celeryproject.org/
- Django Celery Beat documentation: https://django-celery-beat.readthedocs.io/
- Redis documentation: https://redis.io/documentation
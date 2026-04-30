#!/bin/bash
# Run all cron jobs

# Set the project path
PROJECT_PATH="/home/halimatu/api.halimatu-sadiyyah.com.ng"
cd $PROJECT_PATH

# Create logs directory if it doesn't exist
mkdir -p $PROJECT_PATH/app/logs
mkdir -p $PROJECT_PATH/logs

# Log file
LOG_FILE="$PROJECT_PATH/app/logs/cron_execution.log"

# Log start
echo "$(date): Starting cron jobs..." >> $LOG_FILE

# Source the virtual environment
source /home/halimatu/virtualenv/api.halimatu-sadiyyah.com.ng/3.11/bin/activate

# Log Python path for debugging
echo "Python: $(which python)" >> $LOG_FILE
echo "Python version: $(python --version)" >> $LOG_FILE

# Run cron jobs
python cron_jobs.py >> $LOG_FILE 2>&1

# Log completion
echo "$(date): Cron jobs completed" >> $LOG_FILE
#!/bin/bash
# Run all cron jobs

# Set the project path
PROJECT_PATH="/home/halimatu/api.halimatu-sadiyyah.com.ng"
cd $PROJECT_PATH

# Log file
LOG_FILE="$PROJECT_PATH/app/logs/cron_execution.log"

# Log start
echo "$(date): Starting cron jobs..." >> $LOG_FILE

# Activate virtual environment and run cron jobs
source /home/halimatu/virtualenv/api.halimatu-sadiyyah.com.ng/3.9/bin/activate
python cron_jobs.py >> $LOG_FILE 2>&1

# Log completion
echo "$(date): Cron jobs completed" >> $LOG_FILE
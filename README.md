# useful_scripts
Useful Python scripts for various operational & administrative tasks

## Scripts

### aws_lambda_ec2_http_stop_start.py
AWS Lambda function for EC2 instance management with HTTP health checks. Provides start/stop functionality with integrated health monitoring and SNS notifications.

**Usage:** Deploy as AWS Lambda function with environment variables (INSTANCE_ID, URL, SNS_TOPIC_ARN)

### convert_xlsx_to_csv.py
Converts Excel (.xlsx) files to CSV format.

**Usage:** `python3 convert_xlsx_to_csv.py <xlsx_file> <sheet_name>`

### html_based_email_ssmtp.py
Sends HTML emails with embedded images using ssmtp. Reads message data from a Redshift database and creates MIME-formatted emails.

**Usage:** Configure database connection and run script

### login_and_download_csv_files_by_day.py
Automated script to login to a web service and download CSV files for a date range. Handles authentication and retry logic.

**Usage:** Configure login credentials and date range, then run script

### rename_s3_files.py
Script to rename files in an S3 bucket using search and replace patterns.

**Usage:** `python3 rename_s3_files.py <s3_bucket> <s3_prefix> <search>=<replace> <search>=<replace>`

### s3_mutlipart_upload.py
Uploads large files to S3 using multipart upload with parallel processing for improved performance.

**Usage:** Configure bucket name, file path, and target key, then run script

"""
AWS Lambda Function for EC2 Instance Management with HTTP Health Checks

This Lambda function provides EC2 instance stop/start functionality with integrated HTTP health check
"""

import os
import logging
import boto3
import urllib.request
import urllib.error
import time
import json

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
ec2 = boto3.client("ec2")
sns = boto3.client("sns")

# Environment variables - these must be set in the Lambda function configuration
instance_id = os.environ.get("INSTANCE_ID")  # EC2 instance ID to manage
url = os.environ.get("URL")  # HTTP URL to check for health
sns_topic_arn = os.environ.get("SNS_TOPIC_ARN")  # SNS topic for notifications

def notify_sns(subject: str, message: dict):
    """
    Send notification to SNS topic with structured message data.
    
    Args:
        subject (str): Email subject line
        message (dict): Dictionary containing notification details
    """
    sns.publish(
        TopicArn=sns_topic_arn,
        Subject=subject,
        Message=json.dumps(message, default=str)
    )
    logger.info(f"Notification sent to SNS topic: {sns_topic_arn}")

def retrieve_http_status(url: str, checks: int = 12, interval: int = 10):
    """
    Perform HTTP health check on the specified URL with retry logic.
    
    Args:
        url (str): HTTP URL to check (e.g., "http://example.com/health")
        checks (int, optional): Number of attempts to make. Defaults to 12.
        interval (int, optional): Seconds to wait between attempts. Defaults to 10.
        
    Returns:
        int: HTTP status code (200 for success, 0 for connection failure, other codes for HTTP errors)
    """
    status_code = None
    for i in range(checks):
        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                status_code = response.getcode()
        except urllib.error.HTTPError as e:
            # Server responded with HTTP error (4xx, 5xx)
            status_code = int(getattr(e,"code",0) or 0)
        except urllib.error.URLError:
            # Connection error (DNS, network, etc.)
            status_code = 0
        except Exception as e:
            logger.error(f"HTTP attempt returned: {e}")
            status_code = 0
    
        logger.info(f"HTTP status code: {status_code}")

        if status_code == 200:
            return status_code
        
        if i < checks - 1:
            time.sleep(interval)

    return status_code or 0


def get_instance_state(instance_id: str, checks: int = 12, interval: int = 10):
    """
    Monitor EC2 instance state until it reaches 'running' status or timeout.

    Args:
        instance_id (str): EC2 instance ID to monitor
        checks (int, optional): Number of state checks to perform. Defaults to 12.
        interval (int, optional): Seconds to wait between checks. Defaults to 10.
        
    Returns:
        str: Instance state name ('running', 'stopped', 'pending', 'stopping', etc.)
    """
    state = None
    for i in range(checks):
        response = ec2.describe_instances(InstanceIds=[instance_id])
        state = response["Reservations"][0]["Instances"][0]["State"]["Name"]
        if state == "running":
            return state
        if i < checks - 1:
            time.sleep(interval)

    return state or "unknown"

def lambda_handler(event, context):
    """
    AWS Lambda handler function for EC2 instance management with HTTP health checks.
    
    This function handles three main operations:
    1. 'start' - Starts EC2 instance, waits for running state, then performs HTTP health check
    2. 'stop' - Stops EC2 instance
    3. 'http' - Performs HTTP health check on existing instance
    
    Args:
        event (dict): Lambda event object containing:
            - action (str): Required. One of 'start', 'stop', or 'http'
        context (LambdaContext): AWS Lambda context object
            
    Returns:
        dict: Response containing action, instance_id, url, and operation results
        
    Environment Variables Required:
        INSTANCE_ID (str): EC2 instance ID to manage
        URL (str): HTTP URL to check for health (e.g., "http://example.com/health")
        SNS_TOPIC_ARN (str): SNS topic ARN for notifications
        
    IAM Permissions Required:
        - ec2:StartInstances
        - ec2:StopInstances  
        - ec2:DescribeInstances
        - sns:Publish
        - logs:PutLogEvents (for CloudWatch logging)
        
    Network Requirements:
        - Lambda must have network access to the HTTP endpoint being checked, if in private subnet, NAT Gateway required for AWS API calls
    """
    # Validate required environment variables
    if not instance_id:
        raise ValueError("instance_id environment variable is not set")
    
    # Extract and validate action from event
    action = (event or {}).get("action")
    if action not in ("start", "stop","http"):
        raise ValueError(f"Invalid action: {action}. Must be one of: start, stop, http")

    if action == "start":
        """
        START OPERATION:
        1. Send start notification
        2. Start EC2 instance
        3. Wait for instance to reach 'running' state (e.g. up to 2 minutes)
        4. Perform HTTP health check (e.g. up to 2 minutes)
        5. Send success/failure notification
        """
        try:
            logger.info(f"Starting instance {instance_id}")
            
            # Send notification that start operation is beginning
            notify_sns(
                subject=f"[INF] {context.function_name} - action called: {action}",
                message={
                    "instance_id": instance_id,
                    "action": action,
                    "url": url,
                }
            )
            
            # Initiate EC2 instance start
            start_response = ec2.start_instances(InstanceIds=[instance_id])
            logger.info(f"Start response: {start_response}")

            # Wait for instance to reach 'running' state
            state_response = get_instance_state(instance_id)
            if state_response != "running":
                raise TimeoutError(f"Instance {instance_id} did not start within the expected time")
            
            # Once instance is running, verify HTTP service is responding
            http_response = retrieve_http_status(url)
            if http_response != 200:
                raise TimeoutError(f"Instance {instance_id} did not pass the HTTP check within the expected time")
            
            response = {"ec2_state": state_response, "http_status": http_response}

        except Exception as e:
            # Send failure notification with error details
            notify_sns(
                subject=f"[ERR] {context.function_name} - action called: {action}",
                message={
                    "instance_id": instance_id,
                    "action": action,
                    "url": url,
                    "error": str(e),
                    "last_ec2_state": locals().get("state_response"),
                    "last_http_status": locals().get("http_status")
                }
            )
            # Re-raise exception so Lambda invocation is marked as failed
            raise

    elif action == "stop":
        """
        STOP OPERATION:
        1. Send stop notification
        2. Stop EC2 instance
        3. Send success/failure notification
        
        Note: Stop operation is fire-and-forget - no waiting for completion
        """
        try:
            logger.info(f"Stopping instance {instance_id}")
            
            # Send notification that stop operation is beginning
            notify_sns(
                subject=f"[INF] {context.function_name} - action called: {action}",
                message={
                    "instance_id": instance_id,
                    "action": action,
                    "url": url,
                }
            )
            
            # Initiate EC2 instance stop
            stop_response = ec2.stop_instances(InstanceIds=[instance_id])
            logger.info(f"Stop response: {stop_response}")
            response = {"message": "stop initiated"}
        
        except Exception as e:
            # Send failure notification with error details
            notify_sns(
                subject=f"[ERR] {context.function_name} - action called: {action}",
                message={
                    "instance_id": instance_id,
                    "action": action,
                    "url": url,
                    "error": str(e)
                }
            )
            # Re-raise exception so Lambda invocation is marked as failed
            raise

    elif action == "http":
        """
        HTTP HEALTH CHECK OPERATION:
        1. Send HTTP check notification
        2. Perform HTTP health check (up to 2 minutes)
        3. Send success/failure notification
        
        Note: This operation only checks HTTP status, does not manage EC2 state
        """
        try:
            logger.info(f"Checking status of {url}")
            
            # Send notification that HTTP check is beginning
            notify_sns(
                subject=f"[INF] {context.function_name} - action called: {action}",
                message={
                    "instance_id": instance_id,
                    "action": action,
                    "url": url,
                }
            )
            
            # Perform HTTP health check
            http_response = retrieve_http_status(url)
            logger.info(f"HTTP status response: {http_response}")
            response = {"http_status": http_response}
        
        except Exception as e:
            # Send failure notification with error details
            notify_sns(
                subject=f"[ERR] {context.function_name} - action called: {action}",
                message={
                    "instance_id": instance_id,
                    "action": action,
                    "url": url,
                    "error": str(e)
                }
            )
            # Re-raise exception so Lambda invocation is marked as failed
            raise

    # Return standardized response format
    return {
        "action": action,
        "instance_id": instance_id,
        "url": url,
        "response": response
    }
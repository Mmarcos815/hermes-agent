#!/bin/bash
# setup.sh — Initialize LocalStack resources for cloud attack simulation testing
set -euo pipefail

export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1
ENDPOINT="--endpoint-url http://localhost:4566"

echo "[*] Waiting for LocalStack to be ready..."
until curl -sf http://localhost:4566/_localstack/health > /dev/null 2>&1; do
  sleep 2
done
echo "[+] LocalStack is up."

# --- S3 ---
echo "[*] Creating S3 buckets..."
aws $ENDPOINT s3 mb s3://test-data-bucket
aws $ENDPOINT s3 mb s3://audit-logs-bucket
echo '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":"*","Action":"s3:GetObject","Resource":"arn:aws:s3:::test-data-bucket/*"}]}' > /tmp/policy.json
aws $ENDPOINT s3api put-bucket-policy --bucket test-data-bucket --policy file:///tmp/policy.json
echo "[+] S3 buckets created and policy attached."

# --- IAM ---
echo "[*] Creating IAM users and roles..."
aws $ENDPOINT iam create-user --user-name attacker-sim
aws $ENDPOINT iam create-user --user-name defender-sim
aws $ENDPOINT iam create-role --role-name lambda-exec-role --assume-role-policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"lambda.amazonaws.com"},"Action":"sts:AssumeRole"}]}'
aws $ENDPOINT iam attach-role-policy --role-name lambda-exec-role --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
aws $ENDPOINT iam create-access-key --user-name attacker-sim > /tmp/attacker-keys.json
echo "[+] IAM users and roles created."

# --- Lambda ---
echo "[*] Deploying test Lambda function..."
cat > /tmp/lambda.py << 'EOF'
def handler(event, context):
    return {"statusCode": 200, "body": "Hello from LocalStack Lambda"}
EOF
zip -j /tmp/lambda.zip /tmp/lambda.py
aws $ENDPOINT lambda create-function \
  --function-name test-func \
  --runtime python3.11 \
  --handler lambda.handler \
  --role arn:aws:iam::000000000000:role/lambda-exec-role \
  --zip-file fileb:///tmp/lambda.zip
echo "[+] Lambda function deployed."

# --- EC2 ---
echo "[*] Launching test EC2 instance..."
aws $ENDPOINT ec2 run-instances \
  --image-id ami-12345678 \
  --instance-type t2.micro \
  --count 1 \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=test-instance}]'
echo "[+] EC2 instance launched."

# --- CloudTrail ---
echo "[*] Creating CloudTrail trail..."
aws $ENDPOINT cloudtrail create-trail --name test-trail --s3-bucket-name audit-logs-bucket
aws $ENDPOINT cloudtrail start-logging --name test-trail
echo "[+] CloudTrail trail created and logging started."

echo ""
echo "=== Setup Complete ==="
echo "Buckets: test-data-bucket, audit-logs-bucket"
echo "Users: attacker-sim, defender-sim"
echo "Lambda: test-func"
echo "EC2: 1 test instance"
echo "Trail: test-trail"

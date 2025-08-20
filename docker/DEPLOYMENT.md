# Deployment Guide

## Project Organization

All Docker and AWS deployment files are organized in the `docker/` directory:

- **Templates (in git):**
  - `task-definition.template.json` - ECS task definition template
  - `build.sh` - Docker build script
  - `DEPLOYMENT.md` - This file

- **Local files (not in git):**
  - `task-definition.json` - Actual ECS task definition with real values
  - `ecr-policy.json` - AWS ECR permissions policy

## Deployment Process

### 1. Build and Push New Image
```bash
# Build new image
./docker/build.sh -t new-version

# Tag for ECR
docker tag barbs:new-version 223741390366.dkr.ecr.us-west-1.amazonaws.com/barbs-repo:new-version

# Push to ECR
aws ecr get-login-password --region us-west-1 | docker login --username AWS --password-stdin 223741390366.dkr.ecr.us-west-1.amazonaws.com
docker push 223741390366.dkr.ecr.us-west-1.amazonaws.com/barbs-repo:new-version
```

### 2. Update ECS Service
```bash
# Update task definition with new image
# Edit docker/task-definition.json to use new image tag
aws ecs register-task-definition --cli-input-json file://docker/task-definition.json --region us-west-1

# Update service (replace :X with new revision number)
aws ecs update-service --cluster barbs-cluster --service barbs-service --task-definition barbs-task:X --region us-west-1
```

### 3. Update DNS (Required after each deployment)
**⚠️ IMPORTANT: ECS Fargate assigns new IP addresses on each deployment**

```bash
# Get the new IP address
aws ecs list-tasks --cluster barbs-cluster --service barbs-service --region us-west-1
# Copy the task ID from output, then:
aws ecs describe-tasks --cluster barbs-cluster --tasks TASK_ID --region us-west-1 | jq '.tasks[0].attachments[0].details[] | select(.name == "networkInterfaceId") | .value'
# Copy the network interface ID, then:
aws ec2 describe-network-interfaces --network-interface-ids ENI_ID --region us-west-1 | jq '.NetworkInterfaces[0].Association.PublicIp'
```

**Then update DNS in Wix:**
1. Go to Wix DNS settings
2. Update A record for `search.barbsdogrescue.org` to point to new IP
3. Wait 5-15 minutes for DNS propagation
4. Test: https://search.barbsdogrescue.org

## Environment Variables Required for Deployment

Copy `task-definition.template.json` to `task-definition.json` and update the following environment variables:

### Required Environment Variables:

- **SECRET_KEY**: Flask secret key for session management
- **PETSTABLISHED_PUBLIC_KEY**: API key for the pet service
- **SSL_EMAIL**: Email address for Let's Encrypt SSL certificate registration
- **FLASK_ENV**: Set to "production" for production deployment

## Quick Commands

- **Build container:** `./docker/build.sh`
- **Build with tag:** `./docker/build.sh -t my-tag`
- **Deploy to AWS:** Use files in `docker/` directory

These files are excluded from git for security reasons.

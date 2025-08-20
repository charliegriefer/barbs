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

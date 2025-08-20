# Environment Variables Required for Deployment

Copy `task-definition.template.json` to `task-definition.json` and update the following environment variables:

## Required Environment Variables:

- **SECRET_KEY**: Flask secret key for session management
- **PETSTABLISHED_PUBLIC_KEY**: API key for the pet service
- **SSL_EMAIL**: Email address for Let's Encrypt SSL certificate registration
- **FLASK_ENV**: Set to "production" for production deployment

## Files to Configure Locally (not in git):

1. `task-definition.json` - Copy from template and fill in real values
2. `ecr-policy.json` - AWS ECR permissions policy (if needed)

These files are excluded from git for security reasons.

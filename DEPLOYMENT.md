# Web Application Deployment Quick Reference

Quick commands for deploying the Concert Data Platform web application.

## Prerequisites

- AWS CLI configured (`aws configure`)
- Python 3.9+
- Node.js 18+ and npm

## Quick Deploy

```bash
# Complete deployment (recommended)
./infrastructure/deploy_web_with_cdn.sh
```

This single command:
1. Builds the React application
2. Uploads to S3
3. Invalidates CloudFront cache

## Initial Setup (First Time Only)

```bash
# 1. Create S3 bucket for static hosting
python3 infrastructure/setup_s3_hosting.py

# 2. Create CloudFront CDN distribution
python3 infrastructure/setup_cloudfront.py
```

## Individual Commands

```bash
# Deploy to S3 only (no cache invalidation)
./infrastructure/deploy_web_app.sh

# Invalidate CloudFront cache manually
python3 infrastructure/invalidate_cloudfront.py

# Setup with custom bucket name
python3 infrastructure/setup_s3_hosting.py --bucket-name my-bucket --region us-west-2
python3 infrastructure/setup_cloudfront.py --bucket-name my-bucket --region us-west-2
```

## Environment Variables

```bash
# Customize deployment
export BUCKET_NAME="concert-data-platform-web"
export REGION="us-east-1"
export INVALIDATE_CACHE="true"

./infrastructure/deploy_web_with_cdn.sh
```

## Access URLs

After deployment:

- **S3 Website**: `http://{bucket-name}.s3-website-{region}.amazonaws.com`
- **CloudFront**: `https://{distribution-id}.cloudfront.net`

## Troubleshooting

**403 Forbidden**: Re-run setup scripts to fix bucket permissions
**404 on Refresh**: CloudFront custom error response should be configured
**Old Content**: Run cache invalidation script

## Full Documentation

See [docs/infrastructure/WEB_DEPLOYMENT_GUIDE.md](docs/infrastructure/WEB_DEPLOYMENT_GUIDE.md) for complete documentation including:

- Architecture details
- Custom domain setup
- Monitoring and logging
- Cost optimization
- CI/CD integration
- Security best practices

## Local Development

```bash
cd web
npm install
npm run dev
```

Access at: `http://localhost:5173`

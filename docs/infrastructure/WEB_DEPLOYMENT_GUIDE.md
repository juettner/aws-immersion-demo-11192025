# Web Application Deployment Guide

This guide covers deploying the Concert Data Platform web application to AWS using S3 static hosting and CloudFront CDN.

## Overview

The deployment process consists of:

1. **S3 Static Hosting**: Host the built React application on S3
2. **CloudFront CDN**: Distribute content globally with HTTPS support
3. **Automated Deployment**: Scripts for building and deploying updates
4. **Cache Invalidation**: Clear CloudFront cache after deployments

## Architecture

```
┌─────────────┐
│   Users     │
└──────┬──────┘
       │ HTTPS
       ▼
┌─────────────────┐
│   CloudFront    │ ◄── Global CDN with edge locations
│   Distribution  │     - HTTPS/TLS 1.2+
└────────┬────────┘     - Gzip compression
         │              - Custom error pages
         │ Origin
         ▼
┌─────────────────┐
│   S3 Bucket     │ ◄── Static website hosting
│   (Private)     │     - React build artifacts
└─────────────────┘     - Origin Access Identity
```

## Prerequisites

- AWS CLI configured with appropriate credentials
- Python 3.9+
- Node.js 18+ and npm
- IAM permissions for:
  - S3 (CreateBucket, PutObject, PutBucketPolicy, PutBucketWebsite)
  - CloudFront (CreateDistribution, CreateInvalidation)

## Quick Start

### 1. Initial Setup

Set up S3 bucket and CloudFront distribution:

```bash
# Set environment variables (optional)
export BUCKET_NAME="concert-data-platform-web"
export REGION="us-east-1"

# Create S3 bucket for static hosting
python3 infrastructure/setup_s3_hosting.py \
    --bucket-name $BUCKET_NAME \
    --region $REGION

# Create CloudFront distribution
python3 infrastructure/setup_cloudfront.py \
    --bucket-name $BUCKET_NAME \
    --region $REGION
```

### 2. Deploy Application

Build and deploy the web application:

```bash
# Complete deployment (build + upload + cache invalidation)
./infrastructure/deploy_web_with_cdn.sh

# Or deploy to S3 only
./infrastructure/deploy_web_app.sh
```

### 3. Access Your Application

After deployment:

- **S3 Website URL**: `http://{bucket-name}.s3-website-{region}.amazonaws.com`
- **CloudFront URL**: `https://{distribution-id}.cloudfront.net`

## Detailed Setup

### S3 Static Hosting Setup

The `setup_s3_hosting.py` script:

1. Creates an S3 bucket (if it doesn't exist)
2. Configures static website hosting
3. Sets up public read access
4. Enables versioning for rollback capability

**Configuration Options:**

```bash
python3 infrastructure/setup_s3_hosting.py \
    --bucket-name concert-data-platform-web \
    --region us-east-1
```

**What it does:**

- **Website Configuration**: Sets `index.html` as the index document and error document (for SPA routing)
- **Public Access**: Configures bucket policy for public read access
- **Versioning**: Enables object versioning for rollback capability

### CloudFront CDN Setup

The `setup_cloudfront.py` script:

1. Creates Origin Access Identity (OAI) for secure S3 access
2. Updates S3 bucket policy to allow OAI access
3. Creates CloudFront distribution with optimized settings
4. Configures custom error responses for SPA routing

**Configuration Options:**

```bash
python3 infrastructure/setup_cloudfront.py \
    --bucket-name concert-data-platform-web \
    --region us-east-1 \
    --price-class PriceClass_100
```

**Price Classes:**

- `PriceClass_100`: US, Canada, Europe (lowest cost)
- `PriceClass_200`: US, Canada, Europe, Asia, Middle East, Africa
- `PriceClass_All`: All edge locations (highest cost)

**Distribution Features:**

- **HTTPS**: Automatic redirect from HTTP to HTTPS
- **Compression**: Gzip compression enabled
- **Caching**: Optimized cache TTLs for different file types
- **SPA Support**: Custom error response (404 → index.html) for client-side routing
- **Security**: TLS 1.2+ minimum protocol version

**Deployment Time:**

CloudFront distributions take 15-20 minutes to deploy. You can check status:

```bash
aws cloudfront get-distribution --id {distribution-id}
```

## Deployment Process

### Build and Deploy Script

The `deploy_web_app.py` script handles:

1. **Prerequisites Check**: Verifies Node.js, npm, and AWS credentials
2. **Dependency Installation**: Installs npm packages if needed
3. **Production Build**: Runs `npm run build` with optimizations
4. **File Upload**: Uploads all files from `web/dist/` to S3
5. **Content Type Detection**: Sets appropriate MIME types
6. **Cache Control**: Configures cache headers based on file type

**Build Optimizations:**

The Vite build process includes:

- **Minification**: JavaScript and CSS minification
- **Tree Shaking**: Removes unused code
- **Code Splitting**: Splits code into smaller chunks
- **Asset Hashing**: Adds content hashes to filenames for cache busting

**Cache Control Strategy:**

| File Type | Cache-Control | Reason |
|-----------|---------------|--------|
| HTML files | `no-cache, no-store, must-revalidate` | Always fetch latest for SPA routing |
| Hashed JS/CSS | `public, max-age=31536000, immutable` | Content-based cache busting |
| Images | `public, max-age=86400` | 24-hour cache |
| Other files | `public, max-age=3600` | 1-hour cache |

### Cache Invalidation

After deploying new content, invalidate CloudFront cache:

```bash
# Invalidate all paths
python3 infrastructure/invalidate_cloudfront.py \
    --bucket-name concert-data-platform-web

# Invalidate specific paths
python3 infrastructure/invalidate_cloudfront.py \
    --bucket-name concert-data-platform-web \
    --paths /index.html /assets/*

# Wait for invalidation to complete
python3 infrastructure/invalidate_cloudfront.py \
    --bucket-name concert-data-platform-web \
    --wait
```

**Invalidation Notes:**

- Invalidations typically complete in 5-10 minutes
- You can have up to 3,000 invalidation paths per request
- First 1,000 invalidation paths per month are free
- Use `/*` to invalidate all cached content

## Complete Deployment Workflow

The `deploy_web_with_cdn.sh` script automates the entire process:

```bash
./infrastructure/deploy_web_with_cdn.sh
```

**Steps:**

1. ✓ Check prerequisites (Python, npm, AWS credentials)
2. ✓ Install dependencies if needed
3. ✓ Build React application for production
4. ✓ Upload files to S3 with optimized settings
5. ✓ Invalidate CloudFront cache
6. ✓ Display access URLs

**Environment Variables:**

```bash
# Customize deployment
export BUCKET_NAME="my-custom-bucket"
export REGION="us-west-2"
export INVALIDATE_CACHE="true"  # Set to "false" to skip invalidation

./infrastructure/deploy_web_with_cdn.sh
```

## Environment Configuration

### Development Environment

For local development, create `web/.env.development`:

```env
VITE_API_BASE_URL=http://localhost:3000/api
VITE_CHATBOT_API_URL=http://localhost:3000/api/chat
VITE_ANALYTICS_API_URL=http://localhost:3000/api/analytics
```

### Production Environment

For production deployment, create `web/.env.production`:

```env
VITE_API_BASE_URL=https://api.yourdomain.com/api
VITE_CHATBOT_API_URL=https://api.yourdomain.com/api/chat
VITE_ANALYTICS_API_URL=https://api.yourdomain.com/api/analytics
```

**Note**: Vite only includes environment variables prefixed with `VITE_` in the build.

## Custom Domain Setup (Optional)

To use a custom domain with CloudFront:

### 1. Request SSL Certificate

```bash
# Request certificate in us-east-1 (required for CloudFront)
aws acm request-certificate \
    --domain-name yourdomain.com \
    --subject-alternative-names www.yourdomain.com \
    --validation-method DNS \
    --region us-east-1
```

### 2. Validate Certificate

Follow the DNS validation instructions in the ACM console.

### 3. Update CloudFront Distribution

```bash
# Get distribution config
aws cloudfront get-distribution-config \
    --id {distribution-id} > dist-config.json

# Edit dist-config.json to add:
# - Aliases: ["yourdomain.com", "www.yourdomain.com"]
# - ViewerCertificate.ACMCertificateArn: {certificate-arn}
# - ViewerCertificate.SSLSupportMethod: "sni-only"

# Update distribution
aws cloudfront update-distribution \
    --id {distribution-id} \
    --if-match {etag} \
    --distribution-config file://dist-config.json
```

### 4. Update DNS Records

Add CNAME records in your DNS provider:

```
yourdomain.com     CNAME  {distribution-id}.cloudfront.net
www.yourdomain.com CNAME  {distribution-id}.cloudfront.net
```

## Monitoring and Troubleshooting

### Check Deployment Status

```bash
# Check S3 bucket
aws s3 ls s3://concert-data-platform-web/

# Check CloudFront distribution
aws cloudfront get-distribution --id {distribution-id}

# Check invalidation status
aws cloudfront get-invalidation \
    --distribution-id {distribution-id} \
    --id {invalidation-id}
```

### Common Issues

**Issue: 403 Forbidden Error**

- **Cause**: Bucket policy doesn't allow public access or OAI access
- **Solution**: Re-run `setup_s3_hosting.py` or `setup_cloudfront.py`

**Issue: 404 Not Found on Refresh**

- **Cause**: CloudFront not configured for SPA routing
- **Solution**: Ensure custom error response (404 → index.html) is configured

**Issue: Old Content Still Showing**

- **Cause**: CloudFront cache not invalidated
- **Solution**: Run `invalidate_cloudfront.py` or wait for cache TTL to expire

**Issue: Build Fails**

- **Cause**: Missing dependencies or TypeScript errors
- **Solution**: Run `npm install` and fix any TypeScript errors

### View Logs

```bash
# CloudFront access logs (if enabled)
aws s3 ls s3://your-logs-bucket/cloudfront/

# S3 access logs (if enabled)
aws s3 ls s3://your-logs-bucket/s3/
```

## Cost Optimization

### S3 Costs

- **Storage**: ~$0.023 per GB/month (standard storage)
- **Requests**: Minimal for static hosting
- **Data Transfer**: Free to CloudFront

### CloudFront Costs

- **Data Transfer**: $0.085 per GB (first 10 TB, US/Europe)
- **Requests**: $0.0075 per 10,000 HTTPS requests
- **Invalidations**: First 1,000 paths/month free

**Tips:**

- Use `PriceClass_100` for lower costs if users are primarily in US/Europe
- Leverage browser caching with appropriate Cache-Control headers
- Use hashed filenames to avoid frequent invalidations

## Security Best Practices

1. **Use CloudFront**: Always use CloudFront in production for HTTPS
2. **Origin Access Identity**: Keep S3 bucket private, use OAI
3. **TLS 1.2+**: Enforce minimum TLS version
4. **Content Security Policy**: Add CSP headers via Lambda@Edge (optional)
5. **WAF**: Consider AWS WAF for additional protection (optional)

## Rollback Procedure

If a deployment causes issues:

### 1. Identify Previous Version

```bash
# List object versions
aws s3api list-object-versions \
    --bucket concert-data-platform-web \
    --prefix index.html
```

### 2. Restore Previous Version

```bash
# Copy previous version to current
aws s3api copy-object \
    --bucket concert-data-platform-web \
    --copy-source concert-data-platform-web/index.html?versionId={version-id} \
    --key index.html
```

### 3. Invalidate Cache

```bash
python3 infrastructure/invalidate_cloudfront.py \
    --bucket-name concert-data-platform-web
```

## Automation and CI/CD

### GitHub Actions Example

```yaml
name: Deploy Web App

on:
  push:
    branches: [main]
    paths:
      - 'web/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      
      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Deploy
        run: ./infrastructure/deploy_web_with_cdn.sh
```

## Summary

The deployment infrastructure provides:

- ✅ Automated build and deployment process
- ✅ Global CDN with HTTPS support
- ✅ Optimized caching strategy
- ✅ SPA routing support
- ✅ Cache invalidation automation
- ✅ Rollback capability with versioning
- ✅ Cost-effective hosting solution

For questions or issues, refer to the troubleshooting section or check AWS documentation.

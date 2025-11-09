#!/bin/bash
# Redshift Data Warehouse Setup Script
# This script creates and configures an Amazon Redshift cluster for the concert data platform

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration variables
CLUSTER_IDENTIFIER="${REDSHIFT_CLUSTER_IDENTIFIER:-concert-data-warehouse}"
DATABASE_NAME="${REDSHIFT_DATABASE:-concerts}"
MASTER_USERNAME="${REDSHIFT_MASTER_USERNAME:-admin}"
NODE_TYPE="${REDSHIFT_NODE_TYPE:-ra3.xlplus}"
NUMBER_OF_NODES="${REDSHIFT_NUMBER_OF_NODES:-2}"
AWS_REGION="${AWS_REGION:-us-east-1}"
VPC_SECURITY_GROUP_IDS="${REDSHIFT_VPC_SECURITY_GROUP_IDS:-}"
SUBNET_GROUP_NAME="${REDSHIFT_SUBNET_GROUP_NAME:-concert-redshift-subnet-group}"
IAM_ROLE_NAME="${REDSHIFT_IAM_ROLE_NAME:-RedshiftS3AccessRole}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Redshift Data Warehouse Setup${NC}"
echo -e "${GREEN}========================================${NC}"

# Function to check if AWS CLI is installed
check_aws_cli() {
    if ! command -v aws &> /dev/null; then
        echo -e "${RED}Error: AWS CLI is not installed${NC}"
        echo "Please install AWS CLI: https://aws.amazon.com/cli/"
        exit 1
    fi
    echo -e "${GREEN}✓ AWS CLI is installed${NC}"
}

# Function to check AWS credentials
check_aws_credentials() {
    if ! aws sts get-caller-identity &> /dev/null; then
        echo -e "${RED}Error: AWS credentials are not configured${NC}"
        echo "Please run: aws configure"
        exit 1
    fi
    echo -e "${GREEN}✓ AWS credentials are configured${NC}"
    aws sts get-caller-identity
}

# Function to generate a secure password
generate_password() {
    # Generate a 32-character password with uppercase, lowercase, numbers, and special chars
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-32
}

# Function to create IAM role for Redshift
create_iam_role() {
    echo -e "\n${YELLOW}Creating IAM role for Redshift...${NC}"
    
    # Check if role already exists
    if aws iam get-role --role-name "$IAM_ROLE_NAME" --region "$AWS_REGION" &> /dev/null; then
        echo -e "${YELLOW}IAM role $IAM_ROLE_NAME already exists${NC}"
        ROLE_ARN=$(aws iam get-role --role-name "$IAM_ROLE_NAME" --region "$AWS_REGION" --query 'Role.Arn' --output text)
    else
        # Create trust policy
        cat > /tmp/redshift-trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "redshift.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

        # Create the role
        ROLE_ARN=$(aws iam create-role \
            --role-name "$IAM_ROLE_NAME" \
            --assume-role-policy-document file:///tmp/redshift-trust-policy.json \
            --region "$AWS_REGION" \
            --query 'Role.Arn' \
            --output text)
        
        echo -e "${GREEN}✓ Created IAM role: $ROLE_ARN${NC}"
        
        # Attach S3 read policy
        aws iam attach-role-policy \
            --role-name "$IAM_ROLE_NAME" \
            --policy-arn "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess" \
            --region "$AWS_REGION"
        
        echo -e "${GREEN}✓ Attached S3 read policy${NC}"
        
        # Wait for role to be available
        sleep 10
    fi
    
    echo "IAM_ROLE_ARN=$ROLE_ARN"
}

# Function to create subnet group
create_subnet_group() {
    echo -e "\n${YELLOW}Creating Redshift subnet group...${NC}"
    
    # Get default VPC
    VPC_ID=$(aws ec2 describe-vpcs \
        --filters "Name=isDefault,Values=true" \
        --region "$AWS_REGION" \
        --query 'Vpcs[0].VpcId' \
        --output text)
    
    if [ "$VPC_ID" == "None" ] || [ -z "$VPC_ID" ]; then
        echo -e "${RED}Error: No default VPC found${NC}"
        echo "Please create a VPC or specify subnet IDs manually"
        exit 1
    fi
    
    echo "Using VPC: $VPC_ID"
    
    # Get subnets in the VPC
    SUBNET_IDS=$(aws ec2 describe-subnets \
        --filters "Name=vpc-id,Values=$VPC_ID" \
        --region "$AWS_REGION" \
        --query 'Subnets[*].SubnetId' \
        --output text)
    
    if [ -z "$SUBNET_IDS" ]; then
        echo -e "${RED}Error: No subnets found in VPC${NC}"
        exit 1
    fi
    
    # Convert space-separated to array
    SUBNET_ARRAY=($SUBNET_IDS)
    
    # Check if subnet group already exists
    if aws redshift describe-cluster-subnet-groups \
        --cluster-subnet-group-name "$SUBNET_GROUP_NAME" \
        --region "$AWS_REGION" &> /dev/null; then
        echo -e "${YELLOW}Subnet group $SUBNET_GROUP_NAME already exists${NC}"
    else
        # Create subnet group
        aws redshift create-cluster-subnet-group \
            --cluster-subnet-group-name "$SUBNET_GROUP_NAME" \
            --description "Subnet group for concert data warehouse" \
            --subnet-ids ${SUBNET_ARRAY[@]} \
            --region "$AWS_REGION"
        
        echo -e "${GREEN}✓ Created subnet group: $SUBNET_GROUP_NAME${NC}"
    fi
}

# Function to create security group
create_security_group() {
    echo -e "\n${YELLOW}Creating security group...${NC}"
    
    # Get default VPC
    VPC_ID=$(aws ec2 describe-vpcs \
        --filters "Name=isDefault,Values=true" \
        --region "$AWS_REGION" \
        --query 'Vpcs[0].VpcId' \
        --output text)
    
    SG_NAME="concert-redshift-sg"
    
    # Check if security group exists
    EXISTING_SG=$(aws ec2 describe-security-groups \
        --filters "Name=group-name,Values=$SG_NAME" "Name=vpc-id,Values=$VPC_ID" \
        --region "$AWS_REGION" \
        --query 'SecurityGroups[0].GroupId' \
        --output text 2>/dev/null || echo "None")
    
    if [ "$EXISTING_SG" != "None" ] && [ -n "$EXISTING_SG" ]; then
        echo -e "${YELLOW}Security group already exists: $EXISTING_SG${NC}"
        VPC_SECURITY_GROUP_IDS="$EXISTING_SG"
    else
        # Create security group
        VPC_SECURITY_GROUP_IDS=$(aws ec2 create-security-group \
            --group-name "$SG_NAME" \
            --description "Security group for Redshift cluster" \
            --vpc-id "$VPC_ID" \
            --region "$AWS_REGION" \
            --query 'GroupId' \
            --output text)
        
        echo -e "${GREEN}✓ Created security group: $VPC_SECURITY_GROUP_IDS${NC}"
        
        # Get your current IP
        MY_IP=$(curl -s https://checkip.amazonaws.com)
        
        # Add inbound rule for Redshift port from your IP
        aws ec2 authorize-security-group-ingress \
            --group-id "$VPC_SECURITY_GROUP_IDS" \
            --protocol tcp \
            --port 5439 \
            --cidr "$MY_IP/32" \
            --region "$AWS_REGION"
        
        echo -e "${GREEN}✓ Added inbound rule for your IP: $MY_IP${NC}"
    fi
}

# Function to create Redshift cluster
create_redshift_cluster() {
    echo -e "\n${YELLOW}Creating Redshift cluster...${NC}"
    
    # Check if cluster already exists
    if aws redshift describe-clusters \
        --cluster-identifier "$CLUSTER_IDENTIFIER" \
        --region "$AWS_REGION" &> /dev/null; then
        echo -e "${YELLOW}Cluster $CLUSTER_IDENTIFIER already exists${NC}"
        
        # Get cluster status
        CLUSTER_STATUS=$(aws redshift describe-clusters \
            --cluster-identifier "$CLUSTER_IDENTIFIER" \
            --region "$AWS_REGION" \
            --query 'Clusters[0].ClusterStatus' \
            --output text)
        
        echo "Cluster status: $CLUSTER_STATUS"
        return
    fi
    
    # Generate master password
    MASTER_PASSWORD=$(generate_password)
    
    echo -e "${YELLOW}Creating cluster with the following configuration:${NC}"
    echo "  Cluster ID: $CLUSTER_IDENTIFIER"
    echo "  Database: $DATABASE_NAME"
    echo "  Master User: $MASTER_USERNAME"
    echo "  Node Type: $NODE_TYPE"
    echo "  Number of Nodes: $NUMBER_OF_NODES"
    
    # Create the cluster
    aws redshift create-cluster \
        --cluster-identifier "$CLUSTER_IDENTIFIER" \
        --node-type "$NODE_TYPE" \
        --master-username "$MASTER_USERNAME" \
        --master-user-password "$MASTER_PASSWORD" \
        --db-name "$DATABASE_NAME" \
        --cluster-type "multi-node" \
        --number-of-nodes "$NUMBER_OF_NODES" \
        --vpc-security-group-ids "$VPC_SECURITY_GROUP_IDS" \
        --cluster-subnet-group-name "$SUBNET_GROUP_NAME" \
        --iam-roles "$ROLE_ARN" \
        --publicly-accessible \
        --region "$AWS_REGION"
    
    echo -e "${GREEN}✓ Cluster creation initiated${NC}"
    
    # Save credentials to file
    cat > redshift_credentials.txt <<EOF
REDSHIFT_CLUSTER_IDENTIFIER=$CLUSTER_IDENTIFIER
REDSHIFT_DATABASE=$DATABASE_NAME
REDSHIFT_MASTER_USERNAME=$MASTER_USERNAME
REDSHIFT_MASTER_PASSWORD=$MASTER_PASSWORD
REDSHIFT_IAM_ROLE_ARN=$ROLE_ARN
AWS_REGION=$AWS_REGION
EOF
    
    echo -e "${GREEN}✓ Credentials saved to redshift_credentials.txt${NC}"
    echo -e "${RED}IMPORTANT: Keep this file secure and do not commit it to version control!${NC}"
}

# Function to wait for cluster to be available
wait_for_cluster() {
    echo -e "\n${YELLOW}Waiting for cluster to be available...${NC}"
    echo "This may take 5-10 minutes..."
    
    while true; do
        CLUSTER_STATUS=$(aws redshift describe-clusters \
            --cluster-identifier "$CLUSTER_IDENTIFIER" \
            --region "$AWS_REGION" \
            --query 'Clusters[0].ClusterStatus' \
            --output text 2>/dev/null || echo "not-found")
        
        if [ "$CLUSTER_STATUS" == "available" ]; then
            echo -e "${GREEN}✓ Cluster is available!${NC}"
            break
        elif [ "$CLUSTER_STATUS" == "not-found" ]; then
            echo -e "${RED}Error: Cluster not found${NC}"
            exit 1
        else
            echo "Current status: $CLUSTER_STATUS (waiting...)"
            sleep 30
        fi
    done
}

# Function to get cluster endpoint
get_cluster_endpoint() {
    echo -e "\n${YELLOW}Getting cluster endpoint...${NC}"
    
    CLUSTER_ENDPOINT=$(aws redshift describe-clusters \
        --cluster-identifier "$CLUSTER_IDENTIFIER" \
        --region "$AWS_REGION" \
        --query 'Clusters[0].Endpoint.Address' \
        --output text)
    
    CLUSTER_PORT=$(aws redshift describe-clusters \
        --cluster-identifier "$CLUSTER_IDENTIFIER" \
        --region "$AWS_REGION" \
        --query 'Clusters[0].Endpoint.Port' \
        --output text)
    
    echo -e "${GREEN}Cluster Endpoint: $CLUSTER_ENDPOINT:$CLUSTER_PORT${NC}"
    
    # Update credentials file
    echo "REDSHIFT_HOST=$CLUSTER_ENDPOINT" >> redshift_credentials.txt
    echo "REDSHIFT_PORT=$CLUSTER_PORT" >> redshift_credentials.txt
}

# Function to display connection information
display_connection_info() {
    echo -e "\n${GREEN}========================================${NC}"
    echo -e "${GREEN}Redshift Cluster Setup Complete!${NC}"
    echo -e "${GREEN}========================================${NC}"
    
    echo -e "\n${YELLOW}Connection Information:${NC}"
    cat redshift_credentials.txt
    
    echo -e "\n${YELLOW}Next Steps:${NC}"
    echo "1. Update your .env file with the credentials from redshift_credentials.txt"
    echo "2. Run: python infrastructure/initialize_redshift_schema.py"
    echo "3. Load data using the RedshiftService"
    
    echo -e "\n${YELLOW}To connect using psql:${NC}"
    echo "psql -h $CLUSTER_ENDPOINT -p $CLUSTER_PORT -U $MASTER_USERNAME -d $DATABASE_NAME"
}

# Main execution
main() {
    check_aws_cli
    check_aws_credentials
    create_iam_role
    create_subnet_group
    create_security_group
    create_redshift_cluster
    wait_for_cluster
    get_cluster_endpoint
    display_connection_info
}

# Run main function
main

# Terraform VPC and Private Build Host

## Overview
This project provisions a small VPC footprint and a private EC2 instance that is managed through AWS Systems Manager.

## Why This Project Matters
It combines networking, IAM, and compute while avoiding the common mistake of exposing SSH broadly.

## Architecture Explanation
- A dedicated VPC contains public and private subnets.
- A private EC2 instance runs inside the private subnet.
- IAM and SSM provide remote access without a public IP.

## Setup Instructions
1. Install Terraform and authenticate to AWS securely.
2. Provide a valid AMI ID for your region.
3. Run `terraform init`, `terraform plan`, and `terraform apply`.
4. Use Session Manager to connect to the instance after it becomes available.

## Deployment Steps
1. Apply the VPC and networking resources.
2. Launch the EC2 instance with the SSM role attached.
3. Validate Session Manager connectivity.
4. Add CI agents or build tools after the host baseline is stable.

## Security Best Practices
- Do not attach a public IP unless you have a clear requirement.
- Prefer SSM over SSH for administrative access.
- Keep IAM policies minimal.
- Restrict outbound traffic if the build workload allows it.


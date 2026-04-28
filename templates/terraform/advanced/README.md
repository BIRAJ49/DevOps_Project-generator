# Terraform ECS Fargate Service

## Overview
This project provisions a production-style container service on ECS Fargate behind an application load balancer.

## Why This Project Matters
It covers several of the resources platform teams manage frequently: networking, load balancing, container services, and centralized logs.

## Architecture Explanation
- A VPC and public subnets host the load balancer.
- An ECS cluster runs the application as Fargate tasks.
- Security groups expose only the load balancer listener and keep tasks private.
- CloudWatch Logs collect container output for troubleshooting.

## Setup Instructions
1. Install Terraform and authenticate to AWS securely.
2. Provide the container image URI and subnet CIDRs.
3. Run `terraform init`, `terraform plan`, and `terraform apply`.
4. Test the load balancer DNS name after the service stabilizes.

## Deployment Steps
1. Build and push the application image.
2. Update `container_image` with an immutable tag or digest.
3. Apply the Terraform changes.
4. Verify target group health and CloudWatch logs.

## Security Best Practices
- Expose only the load balancer listener publicly.
- Keep tasks in private networking where possible.
- Scope IAM execution roles to registry pull and log write permissions.
- Use TLS on the load balancer for internet-facing services.


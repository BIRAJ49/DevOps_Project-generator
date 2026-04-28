variable "aws_region" {
  description = "AWS region for the artifact bucket."
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment name."
  type        = string
  default     = "staging"
}

variable "project_prefix" {
  description = "Short prefix used in resource names."
  type        = string
  default     = "devops-generator"
}


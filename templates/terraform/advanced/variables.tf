variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "project_prefix" {
  type    = string
  default = "release-portal"
}

variable "vpc_cidr" {
  type    = string
  default = "10.50.0.0/16"
}

variable "public_subnet_a_cidr" {
  type    = string
  default = "10.50.10.0/24"
}

variable "public_subnet_b_cidr" {
  type    = string
  default = "10.50.20.0/24"
}

variable "availability_zone_a" {
  type    = string
  default = "us-east-1a"
}

variable "availability_zone_b" {
  type    = string
  default = "us-east-1b"
}

variable "container_image" {
  description = "Immutable image tag or digest for the ECS service."
  type        = string
}

variable "desired_count" {
  type    = number
  default = 2
}

variable "execution_role_arn" {
  description = "IAM role ARN for ECS task execution."
  type        = string
}


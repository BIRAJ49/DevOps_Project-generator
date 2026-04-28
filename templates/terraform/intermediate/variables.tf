variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "availability_zone" {
  type    = string
  default = "us-east-1a"
}

variable "vpc_cidr" {
  type    = string
  default = "10.40.0.0/16"
}

variable "private_subnet_cidr" {
  type    = string
  default = "10.40.10.0/24"
}

variable "project_prefix" {
  type    = string
  default = "platform-build"
}

variable "instance_type" {
  type    = string
  default = "t3.small"
}

variable "ami_id" {
  description = "AMI ID for the private build host."
  type        = string
}


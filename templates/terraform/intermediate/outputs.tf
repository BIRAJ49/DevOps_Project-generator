output "vpc_id" {
  value = aws_vpc.main.id
}

output "private_subnet_id" {
  value = aws_subnet.private.id
}

output "instance_id" {
  value = aws_instance.build_host.id
}


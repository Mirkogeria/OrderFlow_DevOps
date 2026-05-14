output "vpc_id" {
  description = "ID della VPC"
  value       = aws_vpc.main.id
}

output "vpc_cidr" {
  description = "CIDR block della VPC"
  value       = aws_vpc.main.cidr_block
}

output "public_subnet_ids" {
  description = "Lista degli ID dei subnet pubblici"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "Lista degli ID dei subnet privati"
  value       = aws_subnet.private[*].id
}

output "internet_gateway_id" {
  description = "ID dell'Internet Gateway"
  value       = aws_internet_gateway.main.id
}

output "nat_gateway_ids" {
  description = "Lista degli ID dei NAT Gateway"
  value       = aws_nat_gateway.main[*].id
}
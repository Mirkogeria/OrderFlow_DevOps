output "db_endpoint" {
  description = "Endpoint di connessione al database"
  value       = aws_db_instance.main.endpoint
}

output "db_host" {
  description = "Host del database (senza porta)"
  value       = aws_db_instance.main.address
}

output "db_port" {
  description = "Porta del database"
  value       = aws_db_instance.main.port
}

output "db_name" {
  description = "Nome del database"
  value       = aws_db_instance.main.db_name
}

output "db_username" {
  description = "Username del database"
  value       = aws_db_instance.main.username
  sensitive   = true
}

output "rds_security_group_id" {
  description = "ID del security group RDS"
  value       = aws_security_group.rds.id
}
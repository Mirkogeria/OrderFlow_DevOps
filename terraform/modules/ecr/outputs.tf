output "repository_urls" {
  description = "Mappa service_name → URL del repository ECR"
  value       = { for k, v in aws_ecr_repository.services : k => v.repository_url }
}

output "repository_arns" {
  description = "Mappa service_name → ARN del repository ECR"
  value       = { for k, v in aws_ecr_repository.services : k => v.arn }
}

output "registry_id" {
  description = "ID del registry ECR (account AWS ID)"
  value       = values(aws_ecr_repository.services)[0].registry_id
}
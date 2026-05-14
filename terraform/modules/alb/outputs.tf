output "alb_arn" {
  description = "ARN dell'Application Load Balancer"
  value       = aws_lb.main.arn
}

output "alb_dns_name" {
  description = "DNS name dell'ALB (usato per Route 53 o accesso diretto)"
  value       = aws_lb.main.dns_name
}

output "alb_zone_id" {
  description = "Zone ID dell'ALB (usato per alias Record Route 53)"
  value       = aws_lb.main.zone_id
}

output "alb_security_group_id" {
  description = "ID del security group dell'ALB"
  value       = aws_security_group.alb.id
}

output "http_listener_arn" {
  description = "ARN del listener HTTP"
  value       = aws_lb_listener.http.arn
}

output "https_listener_arn" {
  description = "ARN del listener HTTPS (vuoto se nessun certificato)"
  value       = length(aws_lb_listener.https) > 0 ? aws_lb_listener.https[0].arn : ""
}
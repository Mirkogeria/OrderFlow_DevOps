variable "project_name" {
  description = "Nome del progetto"
  type        = string
}

variable "environment" {
  description = "Ambiente (dev, staging, prod)"
  type        = string
}

variable "vpc_id" {
  description = "ID della VPC"
  type        = string
}

variable "public_subnet_ids" {
  description = "ID dei subnet pubblici dove piazzare l'ALB"
  type        = list(string)
}

variable "certificate_arn" {
  description = "ARN del certificato ACM per HTTPS (opzionale)"
  type        = string
  default     = ""
}

variable "tags" {
  description = "Tag aggiuntivi"
  type        = map(string)
  default     = {}
}
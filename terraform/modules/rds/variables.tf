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

variable "private_subnet_ids" {
  description = "ID dei subnet privati dove piazzare RDS"
  type        = list(string)
}

variable "db_name" {
  description = "Nome del database"
  type        = string
  default     = "orderflow"
}

variable "db_username" {
  description = "Username del database"
  type        = string
  default     = "orderflow_user"
}

variable "db_password" {
  description = "Password del database (usare variabile d'ambiente o AWS Secrets Manager)"
  type        = string
  sensitive   = true
}

variable "db_instance_class" {
  description = "Tipo di istanza RDS"
  type        = string
  default     = "db.t3.micro"
}

variable "db_allocated_storage" {
  description = "Storage allocato in GB"
  type        = number
  default     = 20
}

variable "db_engine_version" {
  description = "Versione PostgreSQL"
  type        = string
  default     = "15.4"
}

variable "multi_az" {
  description = "Abilita Multi-AZ per alta disponibilità"
  type        = bool
  default     = false
}

variable "backup_retention_days" {
  description = "Giorni di retention per i backup automatici"
  type        = number
  default     = 7
}

variable "eks_security_group_id" {
  description = "Security group dei nodi EKS autorizzati ad accedere a RDS"
  type        = string
}

variable "tags" {
  description = "Tag aggiuntivi"
  type        = map(string)
  default     = {}
}
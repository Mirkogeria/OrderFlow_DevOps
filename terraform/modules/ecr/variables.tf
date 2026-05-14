variable "project_name" {
  description = "Nome del progetto"
  type        = string
}

variable "environment" {
  description = "Ambiente (dev, staging, prod)"
  type        = string
}

variable "services" {
  description = "Lista dei microservizi per cui creare un repository ECR"
  type        = list(string)
  default = [
    "order-service",
    "inventory-service",
    "notification-service",
    "ingestion-service",
    "genai-service"
  ]
}

variable "image_retention_count" {
  description = "Numero di immagini da mantenere per repository"
  type        = number
  default     = 10
}

variable "tags" {
  description = "Tag aggiuntivi"
  type        = map(string)
  default     = {}
}
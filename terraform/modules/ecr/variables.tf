variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "services" {
  type = list(string)
  default = [
    "order-service",
    "inventory-service",
    "notification-service",
    "ingestion-service",
    "genai-service"
  ]
}

variable "image_retention_count" {
  type    = number
  default = 10
}

variable "tags" {
  type    = map(string)
  default = {}
}
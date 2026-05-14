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
  description = "ID dei subnet privati per i nodi EKS"
  type        = list(string)
}

variable "public_subnet_ids" {
  description = "ID dei subnet pubblici per il control plane"
  type        = list(string)
}

variable "kubernetes_version" {
  description = "Versione di Kubernetes"
  type        = string
  default     = "1.28"
}

variable "node_instance_type" {
  description = "Tipo di istanza EC2 per i nodi worker"
  type        = string
  default     = "t3.medium"
}

variable "node_desired_size" {
  description = "Numero desiderato di nodi worker"
  type        = number
  default     = 2
}

variable "node_min_size" {
  description = "Numero minimo di nodi worker"
  type        = number
  default     = 1
}

variable "node_max_size" {
  description = "Numero massimo di nodi worker"
  type        = number
  default     = 4
}

variable "node_disk_size" {
  description = "Dimensione disco dei nodi in GB"
  type        = number
  default     = 20
}

variable "tags" {
  description = "Tag aggiuntivi"
  type        = map(string)
  default     = {}
}
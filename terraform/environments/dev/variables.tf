variable "aws_region" {
  description = "Regione AWS"
  type        = string
  default     = "eu-central-1"
}

variable "project_name" {
  description = "Nome del progetto"
  type        = string
  default     = "orderflow"
}

variable "environment" {
  description = "Ambiente"
  type        = string
  default     = "dev"
}

variable "vpc_cidr" {
  description = "CIDR block della VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "AZ da usare"
  type        = list(string)
  default     = ["eu-central-1a", "eu-central-1b"]
}

variable "public_subnet_cidrs" {
  description = "CIDR subnet pubblici"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDR subnet privati"
  type        = list(string)
  default     = ["10.0.10.0/24", "10.0.11.0/24"]
}

variable "db_password" {
  description = "Password del database PostgreSQL"
  type        = string
  sensitive   = true
}

variable "db_instance_class" {
  description = "Tipo istanza RDS"
  type        = string
  default     = "db.t3.micro"
}

variable "node_instance_type" {
  description = "Tipo istanza nodi EKS"
  type        = string
  default     = "t3.medium"
}

variable "node_desired_size" {
  description = "Numero desiderato nodi EKS"
  type        = number
  default     = 2
}

variable "node_min_size" {
  description = "Numero minimo nodi EKS"
  type        = number
  default     = 1
}

variable "node_max_size" {
  description = "Numero massimo nodi EKS"
  type        = number
  default     = 3
}
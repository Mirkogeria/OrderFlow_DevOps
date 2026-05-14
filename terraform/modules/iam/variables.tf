variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "cluster_name" {
  type = string
}

variable "service_name" {
  type = string
}

variable "namespace" {
  type    = string
  default = "orderflow"
}

variable "tags" {
  type    = map(string)
  default = {}
}
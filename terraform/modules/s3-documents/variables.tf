variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "irsa_role_name" {
  type = string
}

variable "tags" {
  type    = map(string)
  default = {}
}
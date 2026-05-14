terraform {
  backend "s3" {
    bucket         = "orderflow-terraform-state"
    key            = "dev/terraform.tfstate"
    region         = "eu-central-1"
    encrypt        = true
    dynamodb_table = "orderflow-terraform-locks"
  }
}
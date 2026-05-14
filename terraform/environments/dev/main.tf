terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region  = var.aws_region
  profile = "lab"

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

module "vpc" {
  source = "../../modules/vpc"

  project_name         = var.project_name
  environment          = var.environment
  vpc_cidr             = var.vpc_cidr
  availability_zones   = var.availability_zones
  public_subnet_cidrs  = var.public_subnet_cidrs
  private_subnet_cidrs = var.private_subnet_cidrs
}

module "security_groups" {
  source = "../../modules/security-groups"

  project_name = var.project_name
  environment  = var.environment
  vpc_id       = module.vpc.vpc_id
}

module "ecr" {
  source = "../../modules/ecr"

  project_name = var.project_name
  environment  = var.environment
}

module "eks" {
  source = "../../modules/eks"

  project_name       = var.project_name
  environment        = var.environment
  public_subnet_ids  = module.vpc.public_subnet_ids
  private_subnet_ids = module.vpc.private_subnet_ids
  eks_cluster_sg_id  = module.security_groups.eks_cluster_sg_id
  node_instance_type = var.node_instance_type
  node_desired_size  = var.node_desired_size
  node_min_size      = var.node_min_size
  node_max_size      = var.node_max_size
}

module "rds" {
  source = "../../modules/rds"

  project_name       = var.project_name
  environment        = var.environment
  private_subnet_ids = module.vpc.private_subnet_ids
  rds_sg_id          = module.security_groups.rds_sg_id
  db_password        = var.db_password
  db_instance_class  = var.db_instance_class
}

module "ingestion_irsa" {
  source = "../../modules/iam"

  project_name = var.project_name
  environment  = var.environment
  cluster_name = module.eks.cluster_name
  service_name = "ingestion-service"
}

module "genai_irsa" {
  source = "../../modules/iam"

  project_name = var.project_name
  environment  = var.environment
  cluster_name = module.eks.cluster_name
  service_name = "genai-service"
}

module "bedrock_ingestion" {
  source = "../../modules/bedrock-iam"

  project_name   = var.project_name
  environment    = var.environment
  aws_region     = var.aws_region
  irsa_role_name = module.ingestion_irsa.role_name
}

module "bedrock_genai" {
  source = "../../modules/bedrock-iam"

  project_name   = var.project_name
  environment    = var.environment
  aws_region     = var.aws_region
  irsa_role_name = module.genai_irsa.role_name
}

module "s3_documents" {
  source = "../../modules/s3-documents"

  project_name   = var.project_name
  environment    = var.environment
  irsa_role_name = module.ingestion_irsa.role_name
}

output "vpc_id" {
  value = module.vpc.vpc_id
}

output "eks_cluster_name" {
  value = module.eks.cluster_name
}

output "eks_cluster_endpoint" {
  value = module.eks.cluster_endpoint
}

output "ecr_repositories" {
  value = module.ecr.repository_urls
}

output "rds_endpoint" {
  value     = module.rds.db_endpoint
  sensitive = true
}

output "s3_documents_bucket" {
  value = module.s3_documents.bucket_name
}

output "ingestion_irsa_role_arn" {
  value = module.ingestion_irsa.role_arn
}

output "genai_irsa_role_arn" {
  value = module.genai_irsa.role_arn
}
aws_region   = "eu-central-1"
project_name = "orderflow"
environment  = "staging"

# CIDR diversi da dev per evitare conflitti di VPC peering futuro
vpc_cidr             = "10.1.0.0/16"
availability_zones   = ["eu-central-1a", "eu-central-1b"]
public_subnet_cidrs  = ["10.1.1.0/24", "10.1.2.0/24"]
private_subnet_cidrs = ["10.1.10.0/24", "10.1.11.0/24"]

# RDS — istanza leggermente più grande rispetto a dev
db_instance_class = "db.t3.small"

# EKS — minimo 2 nodi per alta disponibilità
node_instance_type = "t3.medium"
node_desired_size  = 2
node_min_size      = 2
node_max_size      = 4
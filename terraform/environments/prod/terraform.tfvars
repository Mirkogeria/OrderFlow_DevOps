aws_region             = "eu-central-1"
project_name           = "orderflow"
environment            = "prod"
vpc_cidr               = "10.2.0.0/16"
availability_zones     = ["eu-central-1a", "eu-central-1b", "eu-central-1c"]
public_subnet_cidrs    = ["10.2.1.0/24", "10.2.2.0/24", "10.2.3.0/24"]
private_subnet_cidrs   = ["10.2.10.0/24", "10.2.11.0/24", "10.2.12.0/24"]
db_instance_class      = "db.t3.medium"
node_instance_type     = "t3.large"
node_desired_size      = 3
node_min_size          = 3
node_max_size          = 10


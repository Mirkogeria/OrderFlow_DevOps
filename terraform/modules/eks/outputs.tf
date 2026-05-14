output "cluster_name" {
  description = "Nome del cluster EKS"
  value       = aws_eks_cluster.main.name
}

output "cluster_endpoint" {
  description = "Endpoint API del cluster EKS"
  value       = aws_eks_cluster.main.endpoint
}

output "cluster_ca_certificate" {
  description = "Certificato CA del cluster EKS"
  value       = aws_eks_cluster.main.certificate_authority[0].data
  sensitive   = true
}

output "cluster_version" {
  description = "Versione Kubernetes del cluster"
  value       = aws_eks_cluster.main.version
}

output "node_group_arn" {
  description = "ARN del node group"
  value       = aws_eks_node_group.main.arn
}

output "eks_cluster_security_group_id" {
  description = "ID del security group del cluster EKS"
  value       = aws_security_group.eks_cluster.id
}

output "eks_nodes_security_group_id" {
  description = "ID del security group dei nodi EKS"
  value       = aws_security_group.eks_nodes.id
}

output "eks_cluster_role_arn" {
  description = "ARN del IAM role del cluster"
  value       = aws_iam_role.eks_cluster.arn
}

output "eks_nodes_role_arn" {
  description = "ARN del IAM role dei nodi"
  value       = aws_iam_role.eks_nodes.arn
}
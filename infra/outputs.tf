# infra/outputs.tf
output "alb_url" {
  description = "URL pública de la aplicación (frontend en / y backend en /api)"
  value       = "http://${aws_lb.main.dns_name}"
}

output "cluster_name" {
  description = "Nombre del cluster ECS del ambiente"
  value       = aws_ecs_cluster.main.name
}

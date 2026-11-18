# infra/ecr/variables.tf
variable "aws_region" {
  description = "Región de AWS donde se crean los repositorios"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Prefijo de los repositorios ECR"
  type        = string
  default     = "proyecto"
}

variable "repositories" {
  description = "Componentes que tienen su propio repositorio de imágenes"
  type        = list(string)
  default     = ["backend", "frontend"]
}

variable "max_images" {
  description = "Cantidad de imágenes que se conservan por repositorio"
  type        = number
  default     = 30
}

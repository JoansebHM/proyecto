# infra/main.tf
# Infraestructura de un ambiente (staging o production): ALB + 2 servicios ECS (frontend y backend).
# El ambiente se elige con un workspace de Terraform y la variable environment_name.
terraform {
  required_version = ">= 1.10.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }

  # El bucket se pasa en "terraform init -backend-config=backend.hcl"
  backend "s3" {}
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "lista-de-mercado"
      Environment = var.environment_name
      ManagedBy   = "Terraform"
    }
  }
}

locals {
  name_prefix = "proyecto-${var.environment_name}"

  # Cada componente: puerto del contenedor y ruta del health check del target group
  servicios = {
    backend = {
      puerto       = 8000
      health_check = "/api/health"
    }
    frontend = {
      puerto       = 80
      health_check = "/"
    }
  }
}

# --- Recursos que ya existen en la cuenta (Terraform solo los consulta) ---

data "aws_iam_role" "lab_role" {
  name = "LabRole"
}

data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }

  filter {
    name   = "default-for-az"
    values = ["true"]
  }

  filter {
    name   = "availability-zone"
    values = ["${var.aws_region}a", "${var.aws_region}b"]
  }
}

# Repositorios de imágenes creados en infra/ecr
data "aws_ecr_repository" "app" {
  for_each = local.servicios

  name = "${var.project_name}-${each.key}"
}

# --- Logs ---

resource "aws_cloudwatch_log_group" "ecs" {
  for_each = local.servicios

  name              = "/ecs/${local.name_prefix}-${each.key}"
  retention_in_days = 30
}

# --- Cluster ECS ---

resource "aws_ecs_cluster" "main" {
  name = "${local.name_prefix}-cluster"
}

# --- Security groups ---

resource "aws_security_group" "alb" {
  name        = "${local.name_prefix}-alb-sg"
  description = "Permite trafico HTTP desde Internet hacia el ALB"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "HTTP desde Internet"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "ecs" {
  name        = "${local.name_prefix}-ecs-sg"
  description = "Permite trafico a los contenedores solo desde el ALB"
  vpc_id      = data.aws_vpc.default.id

  dynamic "ingress" {
    for_each = local.servicios

    content {
      description     = "Trafico del ALB hacia ${ingress.key}"
      from_port       = ingress.value.puerto
      to_port         = ingress.value.puerto
      protocol        = "tcp"
      security_groups = [aws_security_group.alb.id]
    }
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# --- Application Load Balancer con ruteo por ruta ---

resource "aws_lb" "main" {
  name               = "${local.name_prefix}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = data.aws_subnets.default.ids
}

resource "aws_lb_target_group" "app" {
  for_each = local.servicios

  name                 = "${local.name_prefix}-${each.key}-tg"
  port                 = each.value.puerto
  protocol             = "HTTP"
  vpc_id               = data.aws_vpc.default.id
  target_type          = "ip"
  deregistration_delay = 30

  health_check {
    path                = each.value.health_check
    protocol            = "HTTP"
    matcher             = "200"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 3
  }
}

# Por defecto todo va al frontend...
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app["frontend"].arn
  }
}

# ...excepto /api/*, que va al backend
resource "aws_lb_listener_rule" "api" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 10

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app["backend"].arn
  }

  condition {
    path_pattern {
      values = ["/api/*"]
    }
  }
}

# --- Task definitions (una por componente) ---

resource "aws_ecs_task_definition" "app" {
  for_each = local.servicios

  family                   = "${local.name_prefix}-${each.key}"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = data.aws_iam_role.lab_role.arn
  task_role_arn            = data.aws_iam_role.lab_role.arn

  container_definitions = jsonencode([
    {
      name      = each.key
      image     = "${data.aws_ecr_repository.app[each.key].repository_url}:${var.image_tag}"
      essential = true
      portMappings = [
        {
          containerPort = each.value.puerto
          protocol      = "tcp"
        }
      ]
      environment = [
        { name = "APP_VERSION", value = var.image_tag }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.ecs[each.key].name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])
}

# --- Servicios ECS (uno por componente) ---

resource "aws_ecs_service" "app" {
  for_each = local.servicios

  name            = "${local.name_prefix}-${each.key}"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.app[each.key].arn
  desired_count   = 1
  launch_type     = "FARGATE"

  health_check_grace_period_seconds  = 60
  deployment_minimum_healthy_percent = 100
  deployment_maximum_percent         = 200

  # Si la versión nueva no queda saludable, ECS vuelve solo a la anterior
  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  # Terraform espera a que el despliegue termine (o falle) antes de continuar
  wait_for_steady_state = true

  network_configuration {
    subnets          = data.aws_subnets.default.ids
    security_groups  = [aws_security_group.ecs.id]
    assign_public_ip = true # Necesario para descargar la imagen de ECR (sin NAT)
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.app[each.key].arn
    container_name   = each.key
    container_port   = each.value.puerto
  }

  lifecycle {
    ignore_changes = [desired_count]
  }

  depends_on = [aws_lb_listener.http, aws_lb_listener_rule.api]
}

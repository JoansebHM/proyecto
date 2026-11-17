# Arquitectura en AWS

**Cuenta:** AWS Academy Learner Lab · **Región:** `us-east-1` · **IaC:** Terraform

## Diagrama (igual para `staging` y `production`)

```
                    ┌──────────── ALB (puerto 80) ────────────┐
Usuario ──HTTP──▶   │  /api/*  ─▶ Target group backend        │
                    │  /*      ─▶ Target group frontend       │
                    └────────────────┬────────────────────────┘
                                     │
               ┌──────────── ECS Cluster (Fargate) ──────────┐
               │  Servicio frontend: nginx con el build React │
               │  Servicio backend:  FastAPI (uvicorn)        │
               └──────────────────────────────────────────────┘
          Imágenes: ECR · Logs: CloudWatch · Estado de Terraform: S3
```

## Componentes

| Componente | Servicio AWS | Función |
|---|---|---|
| Registro de imágenes | **ECR** | Guarda las imágenes Docker de frontend y backend, etiquetadas con el SHA del commit |
| Balanceador | **ALB** | Punto de entrada público. Enruta por ruta: `/api/*` al backend, el resto al frontend |
| Contenedores | **ECS Fargate** | Un cluster por ambiente con dos servicios: `frontend` y `backend` |
| Health checks | **Target groups del ALB** | Frontend: `/` · Backend: `/api/health` (responde estado y versión desplegada) |
| Logs | **CloudWatch Logs** | Un log group por servicio y ambiente |
| Estado de Terraform | **S3** | Bucket con el estado remoto; un workspace por ambiente |
| Red | VPC y subredes por defecto | Ya existen en la cuenta; Terraform solo las consulta |
| Permisos | Rol `LabRole` | Rol pre-creado del Learner Lab (no se pueden crear roles IAM) |

## Seguridad de red
- El ALB recibe tráfico de Internet en el puerto 80.
- Los servicios ECS solo reciben tráfico **desde el ALB**.

## Despliegue y rollback en ECS
- Despliegue gradual sin caída: la tarea nueva se levanta junto a la anterior y la anterior se retira cuando la nueva está saludable.
- Circuit breaker: si la versión nueva no queda saludable, ECS vuelve automáticamente a la anterior.

## Cambios necesarios en la app
- Backend: endpoint `GET /api/health` → `{"status": "ok", "version": "<APP_VERSION>"}`.
- Backend: atender las rutas con el prefijo `/api` (el ALB no reescribe rutas).
- Dockerfile del backend y del frontend (nginx sirviendo el build).

## Restricciones del Learner Lab
- Solo `us-east-1` (o `us-west-2`).
- Credenciales temporales (4 h): se renuevan en los secretos de GitHub en cada sesión.
- Presupuesto de USD 50: destruir la infraestructura (`terraform destroy`) cuando no se use.

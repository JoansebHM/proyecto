# Proyecto final CI/CD — Checklist

**Presentación:** sábado 21 de noviembre
**Artefacto:** Lista de mercado (frontend React + Vite y backend FastAPI)

---

## 1. Requisitos generales
- [x] Artefacto de software diferente al trabajado en clase
- [x] Complejidad media (al menos dos componentes): frontend + backend
- [ ] Pipeline completo de CI/CD (secciones 3 y 4)
- [ ] Tres modificaciones o introducciones a nivel de pipeline o arquitectura (sección 5)
- [ ] Presentación final (sección 6)

## 2. Definiciones (decidir antes de construir)
- [x] Estrategia de versionamiento / ramificación → [docs/estrategia-ramificacion.md](docs/estrategia-ramificacion.md)
- [x] Ambientes (mínimo 2) y sus nombres → `staging` (desde `develop`) y `production` (desde `main`)
- [x] Qué workflow corre en qué rama / evento → [docs/estrategia-ramificacion.md](docs/estrategia-ramificacion.md#pipeline-un-solo-archivo-githubworkflowspipelineyml)
- [x] Arquitectura en AWS (dónde corre el frontend y dónde el backend) → [docs/arquitectura.md](docs/arquitectura.md)
- [x] Herramienta de IaC → Terraform (estado remoto en S3), cuenta AWS Academy Learner Lab
- [x] Herramienta para las pruebas estáticas (linter / análisis) → Black, Pylint, Flake8 (backend) · ESLint (frontend) · SonarCloud (ambos)
- [x] Qué es el artefacto de release y cómo se versiona → 2 imágenes Docker (backend y frontend) en ECR, etiquetas SHA del commit + `latest`
- [x] Qué pruebas corren en Pre-Prod → esperar versión en `/api/health` + E2E Playwright contra staging (agregar, marcar comprado, eliminar) + reporte HTML
- [x] Qué smoke tests corren en Post-Prod → esperar versión + `GET /`, `GET /api/health` (versión), `GET /api/items` + reporte HTML
- [x] Mecanismo de rollback (automático y manual) → circuit breaker de ECS + job de rollback si fallan smoke tests (vuelve al SHA anterior) + botón de pánico (`workflow_dispatch` con ambiente y SHA)
- [x] Las 3 modificaciones o introducciones → ECR, 2 servicios ECS con ALB por ruta, escaneo Trivy

## 3. Pipeline CI — tareas
- [x] Preparar la app: endpoint `GET /api/health` y rutas del backend con prefijo `/api`
- [x] Preparar la app: Dockerfile del backend y del frontend (nginx)
- [x] Crear la rama `develop` según la estrategia definida
- [x] Proteger `main` y `develop` en GitHub (PR obligatorio)
- [x] Validar origen: un PR hacia `main` solo puede salir de `develop` (job `validar-origen`)
- [x] Crear el pipeline en GitHub Actions (`.github/workflows/pipeline.yml`)
- [x] Checkout: paso de checkout del código
- [x] Build: instalar dependencias y compilar el backend
- [x] Build: instalar dependencias y compilar el frontend
- [x] Test estáticas: configurar el linter del backend (Black, Flake8, Pylint) y correrlo en el pipeline
- [x] Test estáticas: configurar el linter del frontend (ESLint) y correrlo en el pipeline
- [x] Test estáticas: configurar SonarCloud y correrlo en el pipeline (Quality Gate)
- [x] Test unitarias: correr las pruebas del backend en el pipeline
- [x] Test unitarias: correr las pruebas del frontend en el pipeline
- [x] Test cobertura: generar el reporte y aplicar el umbral en el pipeline
- [ ] Release: crear el artefacto a desplegar
- [ ] Release: publicar el artefacto versionado
- [x] Ejecutar el CI con éxito (ejecución #15, push a `develop`)

## 4. Pipeline CD — tareas
- [ ] Configurar el acceso de GitHub Actions a AWS (credenciales / secrets)
- [ ] Crear el bucket S3 del estado de Terraform
- [ ] IaC: escribir la infraestructura como código
- [ ] IaC: parametrizar la infraestructura por ambiente
- [ ] Agregar los pasos de CD al pipeline (`pipeline.yml`)
- [ ] Deploy Infra: ambiente 1
- [ ] Deploy Infra: ambiente 2
- [ ] Deploy App: ambiente 1
- [ ] Deploy App: ambiente 2
- [ ] Tests Pre-Prod: escribir las pruebas y correrlas contra el ambiente previo a producción
- [ ] Tests Post-Prod: escribir los smoke tests y correrlos contra producción
- [ ] Rollback automático: volver a la versión anterior si fallan los smoke tests
- [ ] Rollback manual: crear el workflow del botón de pánico
- [ ] Ejecutar el CD con éxito en ambos ambientes
- [ ] Probar el rollback automático (forzar un fallo)
- [ ] Probar el rollback manual

## 5. Tres modificaciones o introducciones
- [ ] Modificación 1 — ECR en vez de Docker Hub (arquitectura): implementar y ejecutar
- [ ] Modificación 2 — Dos servicios ECS (frontend y backend) detrás de un ALB con ruteo por ruta (arquitectura): implementar y ejecutar
- [ ] Modificación 3 — Escaneo de vulnerabilidades de imágenes con Trivy antes de publicar en ECR (pipeline): implementar y ejecutar

## 6. Presentación final
- [ ] Explicación del artefacto de software (propósito, funcionalidades, complejidad)
- [ ] Explicación de la estrategia de versionamiento o ramificación (por qué se escogió)
- [ ] Explicación del diseño y los componentes del pipeline CI/CD (flujograma con cada paso y herramienta)
- [ ] Explicación de cómo se integra la estrategia de versionamiento a los pipelines (qué se ejecuta en qué rama/evento)
- [ ] Explicación del diagrama de arquitectura de software (ECS, ECR, ALB, Lambdas, etc.)
- [ ] Explicación y completitud (robustez) de las pruebas: ambiente, escenario y por qué
- [ ] Evidencia de los pipelines ejecutados exitosamente (logs de GitHub Actions)
- [ ] Evidencia de las tres modificaciones o introducciones
- [ ] Demostración de la app funcional en cada ambiente
- [ ] Socialización de desafíos y aprendizajes

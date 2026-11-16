# Estrategia de versionamiento y ramificación

**Estrategia:** Git Flow (flujo estricto de lanzamiento)

## Ramas

| Rama | Propósito | Sale de | Se integra a | Vida |
|---|---|---|---|---|
| `main` | Código en producción. Siempre estable. | — | — | Permanente |
| `develop` | Integración de cambios. | `main` | `main` | Permanente |
| `feature/<nombre>` | Nueva funcionalidad o cambio. | `develop` | `develop` | Temporal |

## Reglas
- **No se hacen push directos a `main`** (ni a `develop`): todo entra por Pull Request.
- Un PR solo se puede fusionar si el CI pasa.
- A `main` solo llega `develop`.
- Las ramas `feature/*` se borran después del merge.

## Versionamiento
- Cada versión se identifica con el **SHA del commit** que la generó.
- Las imágenes Docker se publican con dos etiquetas: el **SHA** (la que se despliega) y **`latest`** (la más reciente).
- Staging y producción despliegan la imagen por su SHA: así se sabe exactamente qué commit corre en cada ambiente.

## Ambientes

| Ambiente | Se despliega desde | Rol |
|---|---|---|
| `staging` | `develop` | Pre-producción: validar antes de pasar a producción |
| `production` | `main` | Producción: lo que usa el usuario final |

## Pipeline (un solo archivo: `.github/workflows/pipeline.yml`)

### Eventos que lo disparan

```yaml
on:
  pull_request:
    branches: [develop, main]   # E1: PR hacia develop o main
  push:
    branches: [develop, main]   # E2: merge en develop / E3: merge en main
  workflow_dispatch:            # E4: botón de pánico (rollback manual)
    inputs:
      environment:
        type: choice
        options: [staging, production]
      version:
        description: SHA del commit al que se vuelve
        required: true
```

| Evento | Cuándo ocurre |
|---|---|
| **E1** `pull_request` | Se abre o actualiza un PR hacia `develop` o `main` |
| **E2** `push` a `develop` | Se fusiona un PR en `develop` |
| **E3** `push` a `main` | Se fusiona el PR de `develop` en `main` |
| **E4** `workflow_dispatch` | Alguien pulsa *Run workflow* en la pestaña Actions |

### Secuencia

```
PR hacia develop/main (E1)
  1. Checkout ─▶ 2. Build ─▶ 3. Test estáticas ─▶ 4. Test unitarias ─▶ 5. Test cobertura

Merge en develop (E2) → staging
  1. Checkout ─▶ 2. Build ─▶ 3. Test estáticas ─▶ 4. Test unitarias ─▶ 5. Test cobertura
  ─▶ 6. Release ─▶ 7. IaC ─▶ 8. Deploy Infra ─▶ 9. Deploy App ─▶ 10. Tests Pre-Prod

Merge en main (E3) → production
  1. Checkout ─▶ 2. Build ─▶ 3. Test estáticas ─▶ 4. Test unitarias ─▶ 5. Test cobertura
  ─▶ 6. Release ─▶ 7. IaC ─▶ 8. Deploy Infra ─▶ 9. Deploy App ─▶ 11. Tests Post-Prod
  ─▶ (si fallan) 12. Rollback automático

Botón de pánico (E4)
  13. Rollback manual
```

Si un paso falla, los siguientes no se ejecutan.

### Definición de cada paso

**1. Checkout**
Descarga el código del repositorio en la máquina del pipeline.

**2. Build**
Instala las dependencias del backend (Python) y del frontend (Node) y compila el frontend. Si no compila, el pipeline se detiene.

**3. Test estáticas**
Analiza el código sin ejecutarlo en backend y frontend: errores de sintaxis, malas prácticas, imports sin usar y estilo.
- Backend: **Black** (formato), **Pylint** y **Flake8** (linters).
- Frontend: **ESLint**.
- Ambos: **SonarCloud** (análisis de calidad con Quality Gate).

**4. Test unitarias**
Ejecuta las pruebas unitarias del backend (pytest) y del frontend (vitest). Valida que cada función y componente se comporte como se espera.

**5. Test cobertura**
Mide qué porcentaje del código cubren las pruebas unitarias. Si es menor al 80 %, el pipeline falla.

**6. Release**
Construye las imágenes Docker de backend y frontend, las escanea con **Trivy** (falla si hay vulnerabilidades críticas) y las publica en ECR con las etiquetas SHA del commit y `latest`.

**7. IaC**
Valida y planea la infraestructura definida como código para el ambiente (`staging` o `production`): muestra qué recursos se van a crear o cambiar.

**8. Deploy Infra**
Aplica el plan del paso anterior: crea o actualiza la infraestructura en AWS para el ambiente.

**9. Deploy App**
Despliega en la infraestructura del ambiente la versión creada en el Release.

**10. Tests Pre-Prod** (solo `staging`)
Ejecuta pruebas de aceptación contra la app desplegada en `staging`: valida flujos completos del usuario antes de pasar a producción.
1. Espera la versión nueva: consulta `/api/health` cada 10 s (máximo 5 min) hasta que responda el SHA de la ejecución.
2. Corre las pruebas E2E con **Playwright** contra la URL de staging (`APP_BASE_URL`):
   - Agregar un producto y ver el total.
   - Marcar un producto como comprado.
   - Eliminar un producto.
3. Publica el reporte HTML como artefacto del pipeline.

**11. Tests Post-Prod** (solo `production`)
Ejecuta smoke tests contra la app desplegada en `production`: validaciones rápidas de que la app responde y su funcionalidad básica sirve.
1. Espera la versión nueva en `/api/health` (igual que en staging).
2. Corre los smoke tests (pytest + `urllib`, sin navegador) contra la URL de producción:
   - `GET /` responde 200 y trae el HTML de la app (frontend).
   - `GET /api/health` responde `status: ok` y la versión esperada (SHA desplegado).
   - `GET /api/items` responde 200 con una lista (backend accesible a través del ALB).
3. Publica el reporte HTML como artefacto del pipeline.

No crean ni borran datos. Si alguno falla, se ejecuta el rollback automático.

**12. Rollback automático** (solo `production`, solo si falla el paso 11)
Vuelve a desplegar la versión anterior que funcionaba.
- Antes de desplegar, el job de producción consulta `/api/health` y guarda el SHA que está corriendo.
- Si fallan los smoke tests, hace `terraform apply` con las imágenes de ese SHA anterior (siguen en ECR) y espera a que `/api/health` responda el SHA anterior.
- En el primer despliegue no hay versión anterior: el rollback se omite con un aviso en el log.
- Además, el **circuit breaker de ECS** revierte solo si las tareas nuevas no quedan saludables.

**13. Rollback manual** (botón de pánico)
Se ejecuta a mano desde GitHub Actions eligiendo ambiente y SHA; despliega las imágenes de ese SHA.
- Verifica que las imágenes de ese SHA existan en ECR.
- Hace `terraform apply` con ellas en el ambiente elegido.
- Espera a que `/api/health` responda ese SHA.

## Flujo

```
feature/* ──PR──▶ develop ──PR──▶ main
```

from fastapi import Body, FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.service import ItemsService, NotFoundError, ValidationError

app = FastAPI(title="Lista de mercado")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

service = ItemsService()


def _error(status: int, message: str) -> JSONResponse:
    # Mismo formato que el backend NestJS: el front lee "message".
    return JSONResponse(status_code=status, content={"message": message, "statusCode": status})


@app.exception_handler(ValidationError)
async def validation_handler(_: Request, exc: ValidationError):
    return _error(400, str(exc))


@app.exception_handler(NotFoundError)
async def not_found_handler(_: Request, exc: NotFoundError):
    return _error(404, str(exc))


@app.exception_handler(RequestValidationError)
async def body_handler(_: Request, __: RequestValidationError):
    return _error(400, "Cuerpo de la petición inválido")


@app.get("/items")
def list_items():
    return service.find_all()


@app.post("/items", status_code=201)
def create_item(body: dict = Body(...)):
    return service.create(body)


@app.patch("/items/{item_id}")
def update_item(item_id: int, body: dict = Body(...)):
    return service.update(item_id, body)


@app.delete("/items/{item_id}", status_code=204)
def delete_item(item_id: int):
    service.remove(item_id)
    return Response(status_code=204)

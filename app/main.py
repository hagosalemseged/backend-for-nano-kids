from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.grade import router as grade_router
from app.api.language import router as language_router
from app.api.subject import router as subject_router
from app.api.unit import router as unit_router
from app.api.unit_transaltion import router as unit_translation_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "http://localhost:5174",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
	errors: dict[str, list[str]] = {}
	def _friendly_field_name(loc: tuple):
		if not loc:
			return "body"
		if loc[0] == "body":
			return ".".join(str(x) for x in loc[1:]) or "body"
		return ".".join(str(x) for x in loc)

	for e in exc.errors():
		field = _friendly_field_name(tuple(e.get("loc", [])))
		msg = e.get("msg", "invalid")
		errors.setdefault(field, []).append(msg)

	payload = {"detail": "Validation Failed", "errors": errors}
	return JSONResponse(status_code=422, content=payload)


# register API routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(grade_router)
app.include_router(language_router)
app.include_router(subject_router)
app.include_router(unit_router)
app.include_router(unit_translation_router)
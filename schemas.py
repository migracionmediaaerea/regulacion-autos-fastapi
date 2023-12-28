
from datetime import date
from pydantic import BaseModel


class Regularizacion(BaseModel):
    id: int
    nombre: str
    apellido_paterno: str
    apellido_materno: str
    curp: str
    ent_federativa: str
    descripcion_vehiculo: str
    marca_vehiculo: str
    modelo_vehiculo: str
    anio_vehiculo: str
    niv_vehiculo: str
    anexo_vehiculo	: str

    class Config:
        orm_mode = True
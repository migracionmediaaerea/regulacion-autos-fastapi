from sqlalchemy import Column, Integer, String,BigInteger
from sqlalchemy.types import Date,Text
from database import Base
from pydantic import BaseModel, Field
from typing import Optional

class Regularizacion(Base):
    __tablename__ = "regularizacion_vehicular"

    id = Column(BigInteger, primary_key=True, index=True)
    movimiento = Column(Integer, nullable=False)
    claveInstitucion = Column(Integer, nullable=False)
    fuenteInformacion_id = Column(Integer, nullable=False)
    numeroImportacion = Column(Integer, nullable=False,index=True)
    patente = Column(Integer, nullable=False)
    fechaDesaduanamiento = Column(Date(), nullable=False)
    marca = Column(String(30), nullable=False)
    modelo = Column(String(30), nullable=False)
    anio = Column(String(4), nullable=False)
    color = Column(String(30), nullable=False)
    motor = Column(String(20), nullable=False)
    vin = Column(String(17), nullable=False,index=True)
    nrpv = Column(String(50), nullable=True)
    folioInscripcion = Column(String(8), nullable=False,index=True)
    idConstancia = Column(String(24), nullable=False,index=True)
    curp = Column(String(18),nullable=False,index=True)
    rfc = Column(String(13), nullable=False,index=True)
    nombre = Column(String(150),nullable=False)
    primerApellido = Column(String(20),nullable=False)
    segundoApellido = Column(String(20),nullable=False)
    claveEntidad_id = Column(BigInteger,index=True,nullable=False)
    municipio_id = Column(BigInteger,index=True,nullable=False)
    calle = Column(String(80),nullable=False)
    numeroExterior = Column(String(20),nullable=False)
    numeroInterior = Column(String(20),nullable=True)
    colonia = Column(String(60),nullable=False)
    codigoPostal = Column(Integer,nullable=False)
    clavePedimento = Column(String(2),nullable=False)
    anexoIdentificacion = Column(String(16000000),nullable=True)
    anexo2 = Column(String(16000000),nullable=True)
    anexo3 = Column(String(16000000),nullable=True)
    anexo4 = Column(String(16000000),nullable=True)
    anexo5 = Column(String(16000000),nullable=True)
    anexoZip = Column(String(16000000),nullable=True)
    created_at = Column(Date(), nullable=True)

    
    
class Modulo(Base):
    __tablename__ = "modulos"

    id = Column(BigInteger, primary_key=True, index=True)
    estado_id = Column(Integer, nullable=True)
    clave_modulo = Column(String(50),nullable=False)
    clave_propia = Column(String(50),nullable=False)

class Municipio(Base):
    __tablename__ = "municipios"
    id = Column(BigInteger, primary_key=True, index=True)
    idMunicipio= Column(BigInteger, nullable=False)

class EntidadFederativa(Base):
    __tablename__ = "entidades_federativas"

    id = Column(BigInteger, primary_key=True, index=True)
    nombre = Column(String(255))

class UserData(BaseModel):
    curp: str
    nombre: str
    primerApellido: str #obligatorio si es persona fisica
    segundoApellido: Optional[str] = None
    claveEntidad_id: Optional[str] = None
    municipio_id: Optional[str] = None
    calle: Optional[str] = None
    numeroExterior: Optional[str] = None
    numeroInterior: Optional[str] = None
    colonia: Optional[str] = None
    codigoPostal: Optional[str] = None
    fuenteInformacion_id: Optional[str] = None
    marca: Optional[str] = None
    modelo: Optional[str] = None
    anio: Optional[str] = None
    vin: str
    


class Vehicle(BaseModel):
    descripcion: str
    marca: str
    modelo: str
    anio: str
    vin: str
    pago: str


class FinalData(BaseModel):
    
    marca: str 
    modelo: str 
    anio: str 
    color: str 
    motor: str 
    folioInscripcion: str 
    idConstancia: str
    claveEntidad_id: str
    municipio_id: str
    calle: str
    numeroExterior: str
    numeroInterior: str
    colonia: str
    codigoPostal: str
    anexoIdentificacion: str
    anexo2: str
    anexo3: str
    anexo4: str
    anexo5: str
    anexoZip: str
    fuenteInformacion_id: str
    # numeroImportacion: str
    vin: str
    nrpv: Optional[str] = None
    curp: str
    nombre: str
    primerApellido: str
    segundoApellido: Optional[str] = None
    # clavePedimento: str
    
    
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None


class UserInDB(User):
    hashed_password: str


class RequestData(BaseModel):
    nombre: str
    apellido_paterno: str
    apellido_materno: str
    curp: str
    entidad_federativa: str
    vehiculo: Vehicle
    anexo_identificacion: str
    anexo_2: str
    anexo_3: str
    anexo_4: str
    anexo_5: str
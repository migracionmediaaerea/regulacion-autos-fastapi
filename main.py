from datetime import datetime, timedelta
import string

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field
from pymysql import NULL
from sqlalchemy import true
from database import engine, SessionLocal
from sqlalchemy.sql import text
from sqlalchemy.orm import Session
from models import *
from utils.report import generate_pdf as generate_pdf_report
from fastapi_pagination import Page, add_pagination, paginate
from datetime import date
from pprint import pprint

from dotenv import load_dotenv
import os
import asyncio
import base64
import json
import traceback


# import json

load_dotenv()


# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = "b238d9a32e33b4fa3457492c334358d2bf6bb4457fb15f8df4d25cda5defab6a"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30



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


class Vehicle(BaseModel):
    descripcion: str
    marca: str
    modelo: str
    anio: str
    niv: str
    pago: str


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


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()

def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(username: str):
    if username == os.getenv('API_USER'):
        return true


def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, os.getenv('API_PASSWORD')):
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    #if current_user.disabled:
    #    raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub":os.getenv('API_USER')}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get('/pdf/{regularizacion_id}')
async def get_pdf(regularizacion_id: int, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    regularizacion = db.query(Regularizacion).get(regularizacion_id)
    
    if (regularizacion):
        pdf = asyncio.create_task(generate_pdf_report(regularizacion, regularizacion.numeroImportacion, db))
        pdf_base64 = await pdf
        if(regularizacion.vin == None):
                return {"error": "No se cumplen los requisitos para generar el pdf"}
        else:
            return pdf_base64
    else:
        return {"error": "No se encontró ninguna regularizacion con el id: " + str(regularizacion_id)}
    
@app.get('/pdf2/{vin}')
async def get_pdf(vin: str, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    regularizacion = db.query(Regularizacion).filter(
        Regularizacion.vin == vin
	).one_or_none()
    
    if (regularizacion):
        pdf = asyncio.create_task(generate_pdf_report(regularizacion, regularizacion.numeroImportacion, db))
        pdf_base64 = await pdf
        return pdf_base64
    else:
        return {"error": "No se encontró ninguna regularizacion con el vin: " + str(vin)}


@app.get("/regularizaciones")
async def get_regularizaciones(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    return db.query(Regularizacion).all()

@app.get("/regularizacion/{regularizacion_id}")
async def get_regularizacion(regularizacion_id: int, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    regularizacion = db.query(Regularizacion).filter( Regularizacion.id == regularizacion_id).first()
    output = None
    data_mun = {
        'id': "",
        'clave_propia': ""
    }
    if regularizacion:
        modulo_by_id = db.query(Modulo).filter(Modulo.id == regularizacion.fuenteInformacion_id).first()
        if modulo_by_id:
            data_mun['clave_propia'] = modulo_by_id.clave_propia
        municipio = db.query(Municipio).filter(Municipio.id == regularizacion.municipio_id).first()
        if municipio:
            data_mun['id'] = municipio.idMunicipio
        
        output = "{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}".format(
            regularizacion.movimiento,
            regularizacion.claveInstitucion,
            data_mun['clave_propia'],
            regularizacion.id,
            regularizacion.patente,
            regularizacion.fechaDesaduanamiento.strftime("%Y%m%d"),
            regularizacion.marca,
            regularizacion.modelo,
            regularizacion.anio,    
            regularizacion.color,
            regularizacion.motor,
            regularizacion.vin.upper(),
            "",
            regularizacion.folioInscripcion,
            regularizacion.idConstancia,
            regularizacion.curp,
            regularizacion.rfc,
            regularizacion.nombre,
            regularizacion.primerApellido,
            regularizacion.segundoApellido if regularizacion.segundoApellido == '' or regularizacion.segundoApellido == None else "" + regularizacion.segundoApellido + "",
            regularizacion.claveEntidad_id,
            data_mun['id'],
            regularizacion.calle,
            regularizacion.numeroExterior,
            regularizacion.numeroInterior,
            regularizacion.colonia,
            regularizacion.codigoPostal,
            regularizacion.clavePedimento,
        )

        with open("base64.txt", "r+", encoding="utf-8") as file:
            file.write(output)
            file.seek(0)
            file_bytes = file.read().encode("utf-8")
            file_base64 = base64.b64encode(file_bytes)
            file.truncate(0)
            if(regularizacion.idConstancia == None and regularizacion.folioInscripcion == None):
                return {"error": "No se cumplen los requisitos para generar el txt"}
            else:
                return file_base64
    else:
        return {"error": "No se encontró ninguna regularizacion con el id: " + str(regularizacion_id)}

@app.get("/regularizacionesFecha/{fecha_inicio}/{fecha_fin}/{modulo}")
async def get_regularizaciones_fecha(fecha_inicio:date,fecha_fin:date,modulo:int ,current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    regularizacionesAdmin = db.query(Regularizacion).filter(Regularizacion.fechaDesaduanamiento >= fecha_inicio).filter(Regularizacion.fechaDesaduanamiento <= fecha_fin).filter(Regularizacion.idConstancia != None).filter(Regularizacion.folioInscripcion != None).all()
    regularizaciones = db.query(Regularizacion).filter(Regularizacion.fechaDesaduanamiento >= fecha_inicio).filter(Regularizacion.fechaDesaduanamiento <= fecha_fin).filter(Regularizacion.idConstancia != None).filter(Regularizacion.folioInscripcion != None).filter(Regularizacion.fuenteInformacion_id == modulo).all()
    output = {}
    i=0
    text =""
    
    if(modulo == 72):
        if(regularizacionesAdmin):
            for regularizacion in regularizacionesAdmin:
                i=i+1
                
                if regularizacion:
                    data = {
                        'id': "",
                        'clave_propia': ""
                    }
                    
                    modulo_by_id = db.query(Modulo).filter(Modulo.id == regularizacion.fuenteInformacion_id).first()
                    if modulo_by_id:
                        data['clave_propia'] = modulo_by_id.clave_propia
                    municipio = db.query(Municipio).filter(Municipio.id == regularizacion.municipio_id).first()
                    if municipio:
                        data['id'] = municipio.idMunicipio

                    output[i] = "{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}".format(
                        str(regularizacion.movimiento),
                        regularizacion.claveInstitucion or '',
                        data['clave_propia'],
                        regularizacion.id or '',
                        regularizacion.patente or '',
                        regularizacion.fechaDesaduanamiento.strftime("%Y%m%d") or '',
                        regularizacion.marca or '',
                        regularizacion.modelo or '',
                        regularizacion.anio or '',
                        regularizacion.color or '',
                        regularizacion.motor or '',
                        regularizacion.vin.upper() or '',
                        "",
                        regularizacion.folioInscripcion or '',
                        regularizacion.idConstancia or '',
                        regularizacion.curp or '',
                        regularizacion.rfc or '',
                        regularizacion.nombre or '',
                        regularizacion.primerApellido or '',
                        regularizacion.segundoApellido if regularizacion.segundoApellido == '' or regularizacion.segundoApellido == None else "" + regularizacion.segundoApellido + "",
                        regularizacion.claveEntidad_id or '',
                        data['id'],
                        regularizacion.calle or '',
                        regularizacion.numeroExterior or '',
                        regularizacion.numeroInterior or '',
                        regularizacion.colonia or '',
                        regularizacion.codigoPostal or '',
                        regularizacion.clavePedimento  or ''
                    )
                    text+=output[i] + "\n"

            with open("base64.txt", "r+", encoding="utf-8") as file:
                file.write(text)
                file.seek(0)
                file_bytes = file.read().encode("utf-8")
                file_base64 = base64.b64encode(file_bytes)
                file.truncate(0)
                if(regularizacion.idConstancia == "" and regularizacion.idConstancia == "None" and regularizacion.idConstancia == None and regularizacion.folioInscripcion == "" and regularizacion.folioInscripcion == None and regularizacion.folioInscripcion == "None"):
                    return {"error": "No se cumplen los requisitos para generar el txt"}
                else:
                    return file_base64
        else:
            return {"error": "No se encontró ninguna regularización en el rango de fechas de "+ (fecha_inicio.strftime("%d/%m/%Y")) + " a " + str(fecha_fin.strftime("%d/%m/%Y"))}
    else:
        if(regularizaciones):
            for regularizacion in regularizaciones:
                i=i+1
                if regularizacion:
                    data = {
                        'id': "",
                        'clave_propia': ""
                    }
                    modulo_by_id = db.query(Modulo).filter(Modulo.id == regularizacion.fuenteInformacion_id).first()
                    if modulo_by_id:
                        data['clave_propia'] = modulo_by_id.clave_propia
                    municipio = db.query(Municipio).filter(Municipio.id == regularizacion.municipio_id).first()
                    if municipio:
                        data['id'] = municipio.idMunicipio
                    output[i] = "{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}".format(
                        regularizacion.movimiento,
                        regularizacion.claveInstitucion,
                        data['clave_propia'],
                        regularizacion.id,
                        regularizacion.patente,
                        regularizacion.fechaDesaduanamiento.strftime("%Y%m%d"),
                        regularizacion.marca,
                        regularizacion.modelo,
                        regularizacion.anio,    
                        regularizacion.color,
                        regularizacion.motor,
                        regularizacion.vin.upper(),
                        "",
                        regularizacion.folioInscripcion,
                        regularizacion.idConstancia,
                        regularizacion.curp,
                        regularizacion.rfc,
                        regularizacion.nombre,
                        regularizacion.primerApellido,
                        regularizacion.segundoApellido if regularizacion.segundoApellido == '' or regularizacion.segundoApellido == None else "" + regularizacion.segundoApellido + "",
                        regularizacion.claveEntidad_id,
                        data['id'],
                        regularizacion.calle,
                        regularizacion.numeroExterior,
                        regularizacion.numeroInterior,
                        regularizacion.colonia,
                        regularizacion.codigoPostal,
                        regularizacion.clavePedimento,
                    )
                    text+=output[i] + "\n"

            with open("base64.txt", "r+", encoding="utf-8") as file:
                file.write(text)
                file.seek(0)
                file_bytes = file.read().encode("utf-8")
                file_base64 = base64.b64encode(file_bytes)
                file.truncate(0)
                if(regularizacion.idConstancia == "" and regularizacion.idConstancia == "None" and regularizacion.idConstancia == None and regularizacion.folioInscripcion == "" and regularizacion.folioInscripcion == None and regularizacion.folioInscripcion == "None"):
                    return {"error": "No se cumplen los requisitos para generar el txt"}
                else:
                    return file_base64
        else:
            return {"error": "No se encontró ninguna regularización en el rango de fechas de "+ (fecha_inicio.strftime("%d/%m/%Y")) + " a " + str(fecha_fin.strftime("%d/%m/%Y"))}


@app.get("/regularizacionesEstatales/{estado_id}")
async def get_regularizaciones_Estatales(estado_id:int,current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    regularizaciones = db.query(Regularizacion).join(Modulo, Regularizacion.fuenteInformacion_id==Modulo.id).filter(Modulo.estado_id == estado_id).filter(Regularizacion.fechaDesaduanamiento != None).all()
    output = {}
    i=0
    text =""
    
    if(regularizaciones):
        for regularizacion in regularizaciones:
            i=i+1
            if regularizacion:
                data = {
                    'id': "",
                    'clave_propia': ""
                }
                modulo_by_id = db.query(Modulo).filter(Modulo.id == regularizacion.fuenteInformacion_id).first()
                if modulo_by_id:
                    data['clave_propia'] = modulo_by_id.clave_propia
                municipio = db.query(Municipio).filter(Municipio.id == regularizacion.municipio_id).first()
                if municipio:
                    data['id'] = municipio.idMunicipio
                output[i] = "{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}".format(
                    regularizacion.movimiento,
                    regularizacion.claveInstitucion,
                    data['clave_propia'],
                    regularizacion.id,
                    regularizacion.patente,
                    regularizacion.fechaDesaduanamiento.strftime("%Y%m%d"),
                    regularizacion.marca,
                    regularizacion.modelo,
                    regularizacion.anio,    
                    regularizacion.color,
                    regularizacion.motor,
                    regularizacion.vin.upper(),
                    "",
                    regularizacion.folioInscripcion,
                    regularizacion.idConstancia,
                    regularizacion.curp,
                    regularizacion.rfc,
                    regularizacion.nombre,
                    regularizacion.primerApellido,
                    regularizacion.segundoApellido if regularizacion.segundoApellido == '' or regularizacion.segundoApellido == None else "" + regularizacion.segundoApellido + "",
                    regularizacion.claveEntidad_id,
                    data['id'],
                    regularizacion.calle,
                    regularizacion.numeroExterior,
                    regularizacion.numeroInterior,
                    regularizacion.colonia,
                    regularizacion.codigoPostal,
                    regularizacion.clavePedimento,
                )
                text+=output[i] + "\n"

        
        with open("base64.txt", "r+", encoding="utf-8") as file:
            file.write(text)
            file.seek(0)
            file_bytes = file.read().encode("utf-8")
            file_base64 = base64.b64encode(file_bytes)
            file.truncate(0)
            if(regularizacion.idConstancia == "" and regularizacion.idConstancia == "None" and regularizacion.idConstancia == None and regularizacion.folioInscripcion == "" and regularizacion.folioInscripcion == None and regularizacion.folioInscripcion == "None"):
                return {"error": "No se cumplen los requisitos para generar el txt"}
            else:
                return file_base64
    else:
        text="No hay regularizaciones"
        with open("base64.txt", "r+", encoding="utf-8") as file:
            file.write(text)
            file.seek(0)
            file_bytes = file.read().encode("utf-8")
            file_base64 = base64.b64encode(file_bytes)
            file.truncate(0)
        return file_base64

@app.get("/regularizacionesEstatalesFecha/{fecha_inicio}/{fecha_fin}/{estado_id}")
async def get_regularizacionesEstatales_fecha(fecha_inicio:date,fecha_fin:date,estado_id:int ,current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    regularizaciones = db.query(Regularizacion).join(Modulo, Regularizacion.fuenteInformacion_id==Modulo.id).filter(Regularizacion.fechaDesaduanamiento >= fecha_inicio).filter(Regularizacion.fechaDesaduanamiento <= fecha_fin).filter(Regularizacion.idConstancia != None).filter(Regularizacion.folioInscripcion != None).filter(Modulo.estado_id == estado_id).filter(Regularizacion.fechaDesaduanamiento != None).all()
    output = {}
    i=0
    text =""
    if(regularizaciones):
        for regularizacion in regularizaciones:
            i=i+1
            if regularizacion:
                data = {
                    'id': "",
                    'clave_propia': ""
                }
                
                modulo_by_id = db.query(Modulo).filter(Modulo.id == regularizacion.fuenteInformacion_id).first()
                if modulo_by_id:
                    data['clave_propia'] = modulo_by_id.clave_propia
                municipio = db.query(Municipio).filter(Municipio.id == regularizacion.municipio_id).first()
                if municipio:
                    data['id'] = municipio.idMunicipio

                output[i] = "{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}".format(
                    regularizacion.movimiento,
                    regularizacion.claveInstitucion,
                    data['clave_propia'],
                    regularizacion.id,
                    regularizacion.patente,
                    regularizacion.fechaDesaduanamiento.strftime("%Y%m%d"),
                    regularizacion.marca,
                    regularizacion.modelo,
                    regularizacion.anio,    
                    regularizacion.color,
                    regularizacion.motor,
                    regularizacion.vin.upper(),
                    "",
                    regularizacion.folioInscripcion,
                    regularizacion.idConstancia,
                    regularizacion.curp,
                    regularizacion.rfc,
                    regularizacion.nombre,
                    regularizacion.primerApellido,
                    regularizacion.segundoApellido if regularizacion.segundoApellido == '' or regularizacion.segundoApellido == None else "" + regularizacion.segundoApellido + "",
                    regularizacion.claveEntidad_id,
                    data['id'],
                    regularizacion.calle,
                    regularizacion.numeroExterior,
                    regularizacion.numeroInterior,
                    regularizacion.colonia,
                    regularizacion.codigoPostal,
                    regularizacion.clavePedimento,
                )
                text+=output[i] + "\n"

        with open("base64.txt", "r+", encoding="utf-8") as file:
            file.write(text)
            file.seek(0)
            file_bytes = file.read().encode("utf-8")
            file_base64 = base64.b64encode(file_bytes)
            file.truncate(0)
            if(regularizacion.idConstancia == "" and regularizacion.idConstancia == "None" and regularizacion.idConstancia == None and regularizacion.folioInscripcion == "" and regularizacion.folioInscripcion == None and regularizacion.folioInscripcion == "None"):
                return {"error": "No se cumplen los requisitos para generar el txt"}
            else:
                return file_base64

    else:
        return {"error": "No se encontró ninguna regularización"}


@app.post("/regularizarAuto")
async def generate_pdf(json: FinalData, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    # regularizacion = db.query(Regularizacion).get(regularizacion_id)
    
    today = date.today()
    d1 = today.strftime("%Y%m%d")
    # regularizacion.fechaDesaduanamiento  = d1
    
    regularizacion = Regularizacion(
        movimiento = "0",
        claveInstitucion = "423",
        fuenteInformacion_id = json.fuenteInformacion,
        numeroImportacion = 0,
        patente = "9999",
        fechaDesaduanamiento = d1,
        marca = json.marca,
        modelo = json.modelo,
        anio = json.anio,
        color = json.color,
        motor = json.motor,
        vin = json.vin,
        nrpv = json.nrpv,
        folioInscripcion = json.folioInscripcion,
        anexoIdentificacion=json.anexoIdentificacion,
        anexo2 = json.anexo2,
        anexo3 = json.anexo3,
        anexo4 = json.anexo4,
        anexo5 = json.anexo5,
        anexoZip = json.anexoZip,
        idConstancia = json.idConstancia,
        curp = json.curp,
        rfc = json.curp[:10],
        nombre = json.nombre,
        primerApellido = json.primerApellido,
        segundoApellido = json.segundoApellido,
        claveEntidad_id = json.claveEntidad_id,
        municipio_id = json.municipio_id,
        calle = json.calle,
        numeroExterior = json.numeroExterior,
        numeroInterior = json.numeroInterior,
        colonia = json.colonia,
        codigoPostal = json.codigoPostal,
        clavePedimento = "PR"
    )
    
    

    db.add(regularizacion)
    db.flush()
    db.refresh(regularizacion)
    
    regularizacion.numeroImportacion = str(regularizacion.id).zfill(7)
    
    db.commit()

    data = json.dict()
    pdf = asyncio.create_task(generate_pdf_report(data, regularizacion.numeroImportacion, db))
    # print(pdf)
    pdf_base64 = await pdf

    return pdf_base64


@app.post("/altaPersonas")
async def register_user(json: UserData, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    user_data = Regularizacion(
        fuenteInformacion_id=json.fuenteInformacion,
        marca=json.marca,
        modelo=json.modelo,
        anio=json.anio,
        vin=json.vin,
        curp=json.nombre,
        nombre=json.nombre,
        primerApellido=json.primerApellido,
        segundoApellido=json.segundoApellido,
        movimiento="0",
        claveInstitucion="423",
        patente="9999",
        clavePedimento="PR"
    )
    
    db.add(user_data)
    db.flush()
    db.refresh(user_data)

    user_data.folioInscripcion = str(user_data.id).zfill(7)

    db.commit()

    return {"mensaje": "Usuario registrado correctamente"}




add_pagination(app)
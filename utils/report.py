from jinja2 import Environment, FileSystemLoader
from pathlib import Path
import platform, json, pdfkit, datetime, locale, base64, io, pyqrcode
from models import *
from datetime import date
import os
from pprint import pprint

meses = {
    1: 'Enero',
    2: 'Febrero',
    3: 'Marzo',
    4: 'Abril',
    5: 'Mayo',
    6: 'Junio',
    7: 'Julio',
    8: 'Agosto',
    9: 'Septiembre',
    10: 'Octubre',
    11: 'Noviembre',
    12: 'Diciembre'
}


async def generate_pdf(info, numeroImportacion: str, db):
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('./index.html')

    
    root_dir = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..'))

    # print(f'{root_dir=}')

    # Variables for the template
    nombre = info.nombre
    primerApellido = info.primerApellido
    segundoApellido = info.segundoApellido if info.segundoApellido else ""
    curp = info.curp
    # claveEntidad_id = info.claveEntidad_id
    marca = info.marca
    modelo = info.modelo
    anio_carro = info.anio
    vin = info.vin
    fechaDesaduanamiento = info.fechaDesaduanamiento
    created_at = info.created_at
    id = info.id
    
    # claveEntidad_id = db.query(EntidadFederativa).get(int(claveEntidad_id))

    # locale.setlocale(locale.LC_ALL, 'es_MX')
    
    anio_creacion = created_at.year
    dia_creacion = created_at.day
    mes_creacion = created_at.month
    mes_creacion = meses.get(mes_creacion)
    
    dia = fechaDesaduanamiento.day
    
    mes = fechaDesaduanamiento.month
    mes = meses.get(mes)
    
    anio = fechaDesaduanamiento.year
    
    # Generate the qrcode
    DOMINIO = os.getenv("DOMINIO")
    url = f'{DOMINIO}/dashboard/getpdf/{id}'
    qr = pyqrcode.create(url).png_as_base64_str(scale = 5)
    
    # pdf information
    context = {
        "nombre": nombre,
        "id": id,
        "primerApellido": primerApellido,
        "segundoApellido": segundoApellido,
        "curp": curp,
        # "claveEntidad_id": claveEntidad_id.nombre,
        "marca": marca,
        "modelo": modelo,
        "anio_desaduanamiento": anio,
        "mes_desaduanamiento": mes,
        "dia_desaduanamiento":dia,
        "anio_creacion": anio_creacion,
        "mes_creacion": mes_creacion,
        "dia_creacion":dia_creacion,
        "vin": vin,
        "pago": "",
        "root_dir":root_dir,
        "numeroImportacion": numeroImportacion,
        "anio_carro":anio_carro,
        'qr':qr
    }

    # PDF config
    options = {
        "page-size": 'Letter',
        'title': "Constancia de Registro",
        # 'margin-top': '200px',
        # 'margin-right': '0px',
        # 'margin-left': '0px',
        # 'margin-bottom': '10px',
        'encoding': "ISO-8859-3",
        'orientation':'landscape',
        # 'footer-html': f'{root_dir}/templates/footer.html',
        # '--header-html': 'templates/header.html',
        # '--header-spacing': '-223',
        # '--footer-spacing': '-14',
        # '--enable-local-file-access': "",
    }

    # Server
    # config = pdfkit.configuration(wkhtmltopdf='/usr/local/bin/wkhtmltopdf') \
    # Fajardo
    config = pdfkit.configuration(wkhtmltopdf='/usr/bin/wkhtmltopdf') \
        if platform.system() != 'Windows' \
        else pdfkit.configuration(
        wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
    )

    css = [f'{root_dir}/templates/assets/css/styles.min.css']

    html = template.render(context)

    buffer = io.BytesIO()
    pdf_file = pdfkit.from_string(html, options=options, configuration=config,css=css)
    buffer.write(pdf_file)
    buffer.seek(0)

    # save pdf as base64
    pdf_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return pdf_base64

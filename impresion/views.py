from django.shortcuts import render
from django.http import HttpResponse
from PIL import Image, ImageDraw, ImageFont
if not hasattr(Image, "ANTIALIAS"):
    # Pillow >=10.0: alias para compatibilidad con brother_ql
    Image.ANTIALIAS = Image.Resampling.LANCZOS
import time
from brother_ql.raster import BrotherQLRaster
from brother_ql.conversion import convert
from brother_ql.backends.helpers import send
from brother_ql.backends import backend_factory
from brother_ql.backends.helpers import discover
import csv
import os
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings



def format_ingredients(text, max_length=35):
    words = text.split()  # Separar por espacios sin depender de comas
    lines = []
    current_line = ""
    
    for word in words:
        if current_line and len(current_line) + len(word) + 1 > max_length:
            lines.append(current_line.center(max_length))  # Centrar la línea
            current_line = word  # Iniciar nueva línea con la palabra actual
        else:
            if current_line:
                current_line += " " + word
            else:
                current_line = word
    
    if current_line:
        lines.append(current_line.center(max_length))  # Centrar la última línea
    
    return "\n".join(lines)


def imprimirEtiquetaIngredientes(referencia, ingredientes):
    
    im = None
    label_size = '62'
    
    #file_path = os.path.join(current_directory, f'{ruta_carpeta}/_{referencia}.png')
    current_directory = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_directory, f'adg_out.png')

    im = crearImagenIngredientesADG(referencia, ingredientes)
      
    printer_model = 'QL-810W'
    backend = 'network'
    backend_type = 'network'
    printer_identifier='88.148.10.38:9899'
    ql_raster = BrotherQLRaster(printer_model)
    ql_raster.dpi_600 = True  # This activates high-resolution mode (300x600 DPI)

    rotate = 0
    instructions = convert(ql_raster, [im], label=label_size, rotate=rotate, dither=False, margin=0, threshold=55, dpi_600=True, cut=True)
    retry = 3
    success = False
    while retry > 0 and success == False:
        try:
            time.sleep(0.2)
            send(instructions, printer_identifier=printer_identifier,backend_identifier=backend,blocking=True)
            success = True
        except Exception as e:
            retry = retry -1 

def crearImagenIngredientesADG(referencia, ingredientes):
    # === CONFIGURACIÓN ===
    current_directory = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_directory, f'adg.png')
    file_path = os.path.join(settings.BASE_DIR, "impresion", "adg.png")
    font_path = os.path.join(settings.BASE_DIR, "impresion", 'Roboto-Light.ttf')
    
    font_size = 28
    font = ImageFont.truetype(font_path, font_size)

    # === FORMATEAR INGREDIENTES EN VARIAS LÍNEAS ===
    texto_ingredientes = format_ingredients(ingredientes, max_length=40)

    # === CARGAR IMAGEN BASE ===
    
    image = Image.open("adg.png").convert("RGB")
    draw = ImageDraw.Draw(image)

    # === TEXTO COMPLETO ===
    texto_final = f"{referencia} - INCI\n\n{texto_ingredientes}"

    # === CALCULAR TAMAÑO DEL BLOQUE DE TEXTO ===
    bbox = draw.multiline_textbbox((0, 0), texto_final, font=font, spacing=4)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    image_width, image_height = image.size

    # === POSICIONES CENTRADAS ===
    x_position = (image_width - text_width) // 2
    y_position = (image_height - text_height) // 2

    # === DIBUJAR TEXTO CENTRADO ===
    draw.multiline_text(
        (x_position, y_position),
        texto_final,
        fill="black",
        font=font,
        align="center",  # 👈 centra cada línea dentro del bloque
        spacing=4,       # espacio vertical entre líneas
    )

@csrf_exempt
def index(request):
    resultado = None

    if request.method == "POST":
        ref_form = request.POST.get("referencia", "").strip().upper()

        # Ruta al CSV dentro de la app
        csv_path = os.path.join(settings.BASE_DIR, "impresion", "ingredientes.tsv")

        if not os.path.exists(csv_path):
            resultado = "⚠️ No se encontró el archivo ingredientes.csv"
        else:
            registros = []

            # Leer el CSV (por posición de columnas)
            with open(csv_path, newline='', encoding='utf-8') as f:
                reader = csv.reader(f, delimiter='\t')
                next(reader, None)  # saltar la cabecera

                for fila in reader:
                    # Evitar filas vacías o incompletas
                    if len(fila) < 4:
                        continue

                    registro = {
                        "REFERENCIA": fila[0].strip().upper(),
                        "NOMBRE": fila[1].strip(),
                        "CONCENTRACION": fila[2].strip(),
                        "INGREDIENTES": fila[3].strip(),
                    }
                    registros.append(registro)

            # Buscar por referencia
            encontrado = next((r for r in registros if r["REFERENCIA"] == ref_form), None)

            if encontrado:
                imprimirEtiquetaIngredientes(ref_form, encontrado['INGREDIENTES'])
                resultado = (
                    f"IMPRESION ENVIADA {ref_form}:"
                    f"{encontrado['INGREDIENTES']}"
                )
            else:
                resultado = f"❌ No se encontró la referencia '{ref_form}' en el archivo."

    return render(request, "index.html", {"resultado": resultado})





import os
import json
from flask import Flask, render_template, request, jsonify
import gspread
from google.oauth2.service_account import Credentials

app = Flask(__name__)

# Configurar credenciales y conexión a Google Sheets
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

def get_sheets_client():
    creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    if creds_json:
        creds_dict = json.loads(creds_json)
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    else:
        # Para pruebas locales si usas archivo json físico
        creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
    
    client = gspread.authorize(creds)
    sheet_id = os.environ.get("GOOGLE_SHEET_ID")
    sheet = client.open_by_key(sheet_id).sheet1
    return sheet

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/verify", methods=["POST"])
def verify():
    data = request.json
    qr_code = data.get("qr_code")  # Ejemplo: FIESTA-ID-2
    
    if not qr_code:
        return jsonify({"status": "error", "message": "Código QR no válido."}), 400

    try:
        sheet = get_sheets_client()
        
        # Buscar la celda que contiene el ID único (Columna D)
        cell = sheet.find(qr_code)
        
        if not cell:
            return jsonify({"status": "not_found", "message": "❌ Entrada no encontrada en el sistema."}), 404
        
        row = cell.row
        # Asumiendo columnas: A=Timestamp, B=Nombre, C=Correo, D=ID, E=Estado
        nombre = sheet.cell(row, 2).value
        estado_actual = sheet.cell(row, 5).value
        
        if estado_actual == "Ingresado":
            return jsonify({
                "status": "already_used",
                "message": f"⚠️ ¡Entrada ya utilizada!\n{nombre} ya ingresó antes.",
                "name": nombre
            }), 200
        
        # Actualizar estado a "Ingresado" en la Columna E
        sheet.update_cell(row, 5, "Ingresado")
        
        return jsonify({
            "status": "success",
            "message": f"✅ ¡Acceso Concedido!\nBienvenido/a, {nombre}.",
            "name": nombre
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
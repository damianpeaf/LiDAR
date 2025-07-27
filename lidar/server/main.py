from flask import Flask, request, jsonify
import math
import json
import os
import redis
from datetime import datetime
from flask_cors import CORS


app = Flask(__name__)
CORS(app)

# Configuración de Redis
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
try:
    r = redis.from_url(REDIS_URL, decode_responses=True)
    r.ping()  # Test connection
    print("Conectado a Redis")
except:
    print("No se pudo conectar a Redis, usando archivo JSON como fallback")
    r = None

JSON_FILE = "lidar_data.json"
REDIS_KEY = "lidar_data"

def save_to_redis(data):
    """Guarda datos en Redis"""
    try:
        # Obtener datos existentes
        existing_data = r.get(REDIS_KEY)
        if existing_data:
            existing_list = json.loads(existing_data)
        else:
            existing_list = []
        
        # Agregar timestamp a cada punto de datos
        for point in data:
            point['timestamp'] = datetime.now().isoformat()
        
        # Extender lista existente
        existing_list.extend(data)
        
        # Guardar de vuelta en Redis
        r.set(REDIS_KEY, json.dumps(existing_list))
        
        # También mantener un contador
        r.incr("lidar_data_count", len(data))
        
        return True
    except Exception as e:
        print(f"Error guardando en Redis: {e}")
        return False

def save_to_file(data):
    """Guarda datos en archivo JSON (fallback)"""
    try:
        existing_data = []
        if os.path.exists(JSON_FILE):
            with open(JSON_FILE, "r") as f:
                try:
                    existing_data = json.load(f)
                    if not isinstance(existing_data, list):
                        existing_data = []
                except json.JSONDecodeError:
                    existing_data = []

        # Agregar timestamp
        for point in data:
            point['timestamp'] = datetime.now().isoformat()
            
        existing_data.extend(data)

        with open(JSON_FILE, "w") as f:
            json.dump(existing_data, f, separators=(",", ":"))
        
        return True
    except Exception as e:
        print(f"Error guardando en archivo: {e}")
        return False

@app.route("/_health", methods=["GET"])
def getHealth():
    data = {"response": "OK"}
    return jsonify(data)

@app.route("/", methods=["GET"])
def index():
    data = {"response": "It works"}
    return jsonify(data)

@app.route("/api/lidar-data", methods=["POST"])
def receive_lidar_data():
    try:
        raw_data = request.get_data(as_text=True)
        if not raw_data:
            return "", 204  

        values = [float(float(x)) for x in raw_data.split(",")]

        if len(values) % 4 != 0:
            return "", 400

        data_points = [values[i:i+4] for i in range(0, len(values), 4)]

        spherical_coords = [
            {
                "r": dist,
                "t": pan,
                "f": tilt,
                "s": strength
            }
            for dist, pan, tilt, strength in data_points
        ]

        # Intentar guardar en Redis primero, si falla usar archivo
        if r and save_to_redis(spherical_coords):
            print(f"Guardados {len(spherical_coords)} puntos en Redis")
        elif save_to_file(spherical_coords):
            print(f"Guardados {len(spherical_coords)} puntos en archivo")
        else:
            return "", 500

        return "", 204  

    except ValueError:
        return "", 400
    except Exception as e:
        print(f"Error procesando datos LIDAR: {e}")
        return "", 500

@app.route("/api/lidar-data", methods=["GET"])
def get_lidar_data():
    """Endpoint para obtener los datos almacenados"""
    try:
        if r:
            # Obtener de Redis
            data = r.get(REDIS_KEY)
            if data:
                return jsonify(json.loads(data))
            else:
                return jsonify([])
        else:
            # Obtener de archivo
            if os.path.exists(JSON_FILE):
                with open(JSON_FILE, "r") as f:
                    data = json.load(f)
                    return jsonify(data)
            else:
                return jsonify([])
    except Exception as e:
        print(f"Error obteniendo datos: {e}")
        return jsonify({"error": "Error obteniendo datos"}), 500

@app.route("/api/lidar-data/stats", methods=["GET"])
def get_stats():
    """Endpoint para obtener estadísticas"""
    try:
        if r:
            data = r.get(REDIS_KEY)
            count = r.get("lidar_data_count") or 0
            if data:
                points = json.loads(data)
                return jsonify({
                    "total_points": len(points),
                    "stored_in": "Redis",
                    "counter": int(count)
                })
        else:
            if os.path.exists(JSON_FILE):
                with open(JSON_FILE, "r") as f:
                    data = json.load(f)
                    return jsonify({
                        "total_points": len(data),
                        "stored_in": "File",
                        "counter": len(data)
                    })
        
        return jsonify({
            "total_points": 0,
            "stored_in": "None",
            "counter": 0
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/lidar-data/clear", methods=["DELETE"])
def clear_data():
    """Endpoint para limpiar todos los datos"""
    try:
        if r:
            r.delete(REDIS_KEY)
            r.delete("lidar_data_count")
        
        if os.path.exists(JSON_FILE):
            os.remove(JSON_FILE)
        
        return jsonify({"message": "Datos eliminados"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=False)
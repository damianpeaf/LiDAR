from nicegui import ui, app
import requests
import math
import os
import asyncio
from datetime import datetime
import plotly.graph_objects as go

# Configuración
FLASK_URL = os.getenv('FLASK_URL', 'http://server:3000')

class LidarDashboard:
    def __init__(self):
        self.data = []
        self.stats = {}
        self.auto_refresh = False
        self.scene = None  # Para almacenar la escena Three.js
        self.point_objects = []  # Para almacenar los objetos de la escena (esferas)

    async def fetch_data(self):
        """Obtiene datos del servidor Flask"""
        try:
            response = requests.get(f"{FLASK_URL}/api/lidar-data", timeout=5)
            if response.status_code == 200:
                self.data = response.json()
                return True
        except Exception as e:
            ui.notify(f"Error obteniendo datos: {e}", type='negative')
            return False
        return False

    async def fetch_stats(self):
        """Obtiene estadísticas del servidor Flask"""
        try:
            response = requests.get(f"{FLASK_URL}/api/lidar-data/stats", timeout=5)
            if response.status_code == 200:
                self.stats = response.json()
                return True
        except Exception as e:
            ui.notify(f"Error obteniendo estadísticas: {e}", type='negative')
            return False
        return False

    async def clear_data(self):
        """Limpia todos los datos"""
        try:
            response = requests.delete(f"{FLASK_URL}/api/lidar-data/clear", timeout=5)
            if response.status_code == 200:
                self.data = []
                self.stats = {}
                ui.notify("Datos eliminados correctamente", type='positive')
                await self.update_display()
                return True
        except Exception as e:
            ui.notify(f"Error eliminando datos: {e}", type='negative')
            return False
        return False

    def create_3d_scene(self):
        """Crea una escena 3D con Three.js para los datos LIDAR usando esferas"""
        if not self.data or not self.scene:
            return

        # Limpiar objetos anteriores
        for obj in self.point_objects:
            self.scene.remove(obj)
        self.point_objects.clear()

        # Crear esferas para los últimos 500 puntos (para mejor rendimiento)
        max_strength = max([point['s'] for point in self.data[-500:]] or [1])  # Evitar división por cero
        min_strength = min([point['s'] for point in self.data[-500:]] or [0])

        for point in self.data[-500:]:  # Mostrar últimos 500 puntos
            r = point['r']
            theta = math.radians(point['t'])  # pan
            phi = math.radians(point['f'])    # tilt

            # Conversión esférica a cartesiana
            x = r * math.sin(phi) * math.cos(theta)
            y = r * math.sin(phi) * math.sin(theta)
            z = r * math.cos(phi)

            # Normalizar la intensidad para el color (de 0 a 1)
            normalized_strength = (point['s'] - min_strength) / (max_strength - min_strength + 1e-6)
            # Color en formato hexadecimal (de rojo a azul)
            color = f'#{int(normalized_strength * 255):02x}00{int((1 - normalized_strength) * 255):02x}'

            # Crear una esfera pequeña para cada punto
            sphere = self.scene.sphere(radius=0.05).material(color=color).move(x, y, z)
            self.point_objects.append(sphere)

    def create_polar_plot(self):
        """Crea un gráfico polar 2D"""
        if not self.data:
            return go.Figure()
        
        recent_data = self.data[-500:]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=[point['r'] for point in recent_data],
            theta=[point['t'] for point in recent_data],
            mode='markers',
            marker=dict(
                size=4,
                color=[point['s'] for point in recent_data],
                colorscale='Plasma',
                colorbar=dict(title="Strength")
            ),
            text=[f"R:{point['r']}, T:{point['t']}, F:{point['f']}, S:{point['s']}" 
                  for point in recent_data],
            hovertemplate="Distancia: %{r}<br>Ángulo: %{theta}°<br>%{text}<extra></extra>"
        ))
        
        fig.update_layout(
            title="Vista Polar LIDAR",
            polar=dict(
                radialaxis=dict(visible=True),
                angularaxis=dict(direction="clockwise", period=360)
            ),
            height=500
        )
        
        return fig

    async def update_display(self):
        """Actualiza todos los elementos de la interfaz"""
        await self.fetch_data()
        await self.fetch_stats()

        # Actualizar estadísticas
        if hasattr(self, 'stats_card'):
            self.stats_card.clear()
            with self.stats_card:
                ui.label(f"Total de puntos: {self.stats.get('total_points', 0)}").classes('text-h6')
                ui.label(f"Almacenado en: {self.stats.get('stored_in', 'N/A')}")
                ui.label(f"Contador: {self.stats.get('counter', 0)}")
                if self.data:
                    last_point = self.data[-1]
                    if 'timestamp' in last_point:
                        ui.label(f"Último dato: {last_point['timestamp']}")

        # Actualizar tabla
        if hasattr(self, 'data_table'):
            recent_data = self.data[-10:] if self.data else []
            rows = []
            for i, point in enumerate(reversed(recent_data)):
                rows.append({
                    'id': len(self.data) - i,
                    'r': point['r'],
                    't': point['t'], 
                    'f': point['f'],
                    's': point['s'],
                    'timestamp': point.get('timestamp', 'N/A')
                })
            self.data_table.rows = rows

        # Actualizar escena 3D
        if hasattr(self, 'scene'):
            self.create_3d_scene()

        # Actualizar gráfico polar
        if hasattr(self, 'plot_polar'):
            self.plot_polar.figure = self.create_polar_plot()

# Crear instancia del dashboard
dashboard = LidarDashboard()

@ui.page('/')
async def main_page():
    ui.page_title('LIDAR Data Dashboard')

    with ui.header().classes('bg-primary text-white'):
        ui.label('Dashboard LIDAR').classes('text-h4')
        ui.space()
        refresh_btn = ui.button('Actualizar', on_click=dashboard.update_display).props('flat')
        clear_btn = ui.button('Limpiar Datos', on_click=dashboard.clear_data).props('flat color=negative')

    with ui.row().classes('w-full gap-4'):
        # Panel de estadísticas
        with ui.card().classes('w-1/4'):
            ui.label('Estadísticas').classes('text-h5 mb-4')
            dashboard.stats_card = ui.column()

        # Panel de control
        with ui.card().classes('w-1/4'):
            ui.label('Control').classes('text-h5 mb-4')
            
            with ui.row():
                auto_refresh_toggle = ui.switch('Auto-actualizar')
                
            async def toggle_auto_refresh():
                dashboard.auto_refresh = auto_refresh_toggle.value
                if dashboard.auto_refresh:
                    ui.notify('Auto-actualización activada', type='positive')
                    app.add_static_file('/refresh_timer', lambda: asyncio.create_task(auto_refresh_loop()))
                else:
                    ui.notify('Auto-actualización desactivada', type='info')
            
            auto_refresh_toggle.on('update:model-value', toggle_auto_refresh)
            
            ui.separator()
            
            ui.label('Información del servidor:')
            ui.label(f'Flask URL: {FLASK_URL}').classes('text-caption')

    # Gráficos
    with ui.row().classes('w-full gap-4'):
        with ui.card().classes('w-1/2'):
            ui.label('Vista 3D').classes('text-h6 mb-2')
            # Crear escena Three.js
            dashboard.scene = ui.scene().classes('w-full h-96')
            with dashboard.scene:
                dashboard.scene.axes_helper()  # Agregar ejes para referencia
                dashboard.create_3d_scene()  # Inicializar puntos

        with ui.card().classes('w-1/2'):
            ui.label('Vista Polar').classes('text-h6 mb-2')
            dashboard.plot_polar = ui.plotly(dashboard.create_polar_plot())

    # Tabla de datos recientes
    with ui.card().classes('w-full mt-4'):
        ui.label('Datos Recientes (últimos 10)').classes('text-h6 mb-2')
        
        columns = [
            {'name': 'id', 'label': 'ID', 'field': 'id'},
            {'name': 'r', 'label': 'Distancia (r)', 'field': 'r'},
            {'name': 't', 'label': 'Pan (t)', 'field': 't'},
            {'name': 'f', 'label': 'Tilt (f)', 'field': 'f'},
            {'name': 's', 'label': 'Strength (s)', 'field': 's'},
            {'name': 'timestamp', 'label': 'Timestamp', 'field': 'timestamp'},
        ]
        
        dashboard.data_table = ui.table(columns=columns, rows=[])

    # Cargar datos iniciales
    await dashboard.update_display()

async def auto_refresh_loop():
    """Loop de auto-actualización"""
    while dashboard.auto_refresh:
        await dashboard.update_display()
        await asyncio.sleep(2)

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(host="0.0.0.0", port=8080, title="LIDAR Dashboard")
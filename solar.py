import pygame
import random
import time
import json
import os
import math

# --- CONFIGURACIÓN GLOBAL ---
ANCHO, ALTO = 800, 600
RADIO_SOL = 18
RADIO_BRILLO = 90
INTERVALO_MS = 8000  # Tiempo en que el sol cambia de posición (8 segundos)
MARGEN = 80
GUARDAR_ARCHIVO = True

pygame.init()
pantalla = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("Simulación del Sol Aleatorio")
reloj = pygame.time.Clock()
fuente = pygame.font.SysFont(None, 22)

# Datos de cada tipo de panel solar
TIPOS_PANELES = {
    "monocristalino": {
        "color": (0, 0, 0),
        "imagen": "monocristalino.png",
        "eficiencia": 0.22,
        "descripcion": "Alta eficiencia, panel negro sólido.",
        "detalle": "Convierte más energía, ideal para espacio limitado."
    },
    "policristalino": {
        "color": (30, 144, 255),
        "imagen": "policristalino.jpg",
        "eficiencia": 0.17,
        "descripcion": "Eficiencia media, azul metalizado.",
        "detalle": "Más económico, menor rendimiento térmico."
    },
    "pelicula": {
        "color": (100, 100, 100),
        "imagen": "panelfino.png",
        "eficiencia": 0.12,
        "descripcion": "Baja eficiencia, gris oscuro.",
        "detalle": "Flexible, buen rendimiento con luz difusa."
    }
}


# --- FUNCIONES DE DIBUJO ---

def dibujar_fondo(superficie, ancho, alto):
    """Dibuja el cielo y la pradera como fondo."""
    # Cielo (Celeste suave) - 3/4 de la pantalla
    color_cielo = (135, 206, 235)  # Light Sky Blue
    alto_cielo = int(alto * 0.75)
    superficie.fill(color_cielo, (0, 0, ancho, alto_cielo))

    # Pradera (Verde) - 1/4 de la pantalla
    color_pradera = (34, 139, 34)  # Forest Green
    superficie.fill(color_pradera, (0, alto_cielo, ancho, alto - alto_cielo))


def dibujar_nubes(superficie, nubes_data):
    """Dibuja las nubes basadas en sus posiciones y tamaños."""
    color_nube = (255, 255, 255, 200)  # Blanco con transparencia (alpha 200)

    for cloud in nubes_data:
        cx, cy, w, h = cloud['x'], cloud['y'], cloud['w'], cloud['h']

        # Crea una superficie temporal con canal alfa (SRCALPHA permite transparencia)
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        # Dibuja una elipse en la superficie temporal
        pygame.draw.ellipse(s, color_nube, s.get_rect())
        # Blitea la superficie de la nube en la pantalla principal
        superficie.blit(s, (cx - w // 2, cy - h // 2))


def dibujar_panel_tipo(superficie, base_x, base_y, angulo, tipo_panel):
    """Dibuja un panel solar con color y tamaño según tipo."""
    if tipo_panel not in TIPOS_PANELES:
        tipo_panel = "policristalino"  # por defecto

    info = TIPOS_PANELES[tipo_panel]
    color_panel = info["color"]
    largo_palo = 100
    color_palo = (100, 100, 100)

    # Dibuja palo
    pygame.draw.line(superficie, color_palo, (base_x, base_y), (base_x, base_y - largo_palo), 8)

    # Panel solar
    ancho_panel = 120
    alto_panel = 40

    # Cargar imagen si existe o usar color sólido (respeta el código original del usuario)
    try:
        textura = pygame.image.load(info["imagen"]).convert_alpha()
        textura = pygame.transform.scale(textura, (ancho_panel, alto_panel))
    except pygame.error:
        # Si no hay imagen, usa color sólido
        textura = pygame.Surface((ancho_panel, alto_panel), pygame.SRCALPHA)
        textura.fill(color_panel)
    except:
        # Manejo de otros errores de carga
        textura = pygame.Surface((ancho_panel, alto_panel), pygame.SRCALPHA)
        textura.fill(color_panel)

    panel_rotado = pygame.transform.rotate(textura, angulo)

    pos_panel = (base_x - panel_rotado.get_width() // 2, base_y - largo_palo - panel_rotado.get_height() // 2)
    superficie.blit(panel_rotado, pos_panel)

    return info


def dibujar_brillo(superficie, centro, radio_interno, radio_externo, color=(255, 255, 0)):  # Sol amarillo brillante
    """Dibuja el sol con un efecto de brillo/resplandor."""
    cx, cy = centro
    brillo = pygame.Surface((radio_externo * 2, radio_externo * 2), pygame.SRCALPHA)
    pasos = 10
    # Dibuja círculos concéntricos para el resplandor con transparencia decreciente
    for i in range(pasos, 0, -1):
        r = int(radio_externo * (i / pasos))
        alpha = int(200 * (i / pasos) * 0.6)
        col = (color[0], color[1], color[2], alpha)
        pygame.draw.circle(brillo, col, (radio_externo, radio_externo), r)

    # Dibuja el círculo central del sol (opaco)
    pygame.draw.circle(brillo, (color[0], color[1], color[2], 255), (radio_externo, radio_externo), radio_interno)
    superficie.blit(brillo, (cx - radio_externo, cy - radio_externo))


# --- FUNCIONES DE DATOS Y LÓGICA ---

def guardar_posicion(x, y):
    """Guarda la posición del sol en un archivo JSON."""
    if not GUARDAR_ARCHIVO:
        return
    datos = {
        "x": int(x),
        "y": int(y),
        "tiempo_ms": int(time.time() * 1000)
    }
    try:
        with open("posicion_sol.json", "w") as f:
            json.dump(datos, f)
    except Exception as e:
        print("Error al guardar:", e)


def posicion_aleatoria():
    """Genera una posición aleatoria para el sol dentro de los márgenes."""
    x = random.randint(MARGEN, ANCHO - MARGEN)
    y = random.randint(MARGEN, ALTO - MARGEN)
    return x, y


def menu():
    """Muestra un menú simple para elegir el tipo de panel."""
    pantalla.fill((18, 22, 30))
    titulo = fuente.render("Selecciona el tipo de panel solar:", True, (255, 255, 255))
    pantalla.blit(titulo, (ANCHO // 2 - titulo.get_width() // 2, 160))

    opciones = ["[1] Monocristalino", "[2] Policristalino", "[3] Película delgada"]
    for i, texto in enumerate(opciones):
        op = fuente.render(texto, True, (200, 220, 255))
        pantalla.blit(op, (ANCHO // 2 - op.get_width() // 2, 220 + i * 40))
    pygame.display.flip()

    tipo = None
    esperando = True
    while esperando:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_1:
                    tipo = "monocristalino"
                    esperando = False
                elif evento.key == pygame.K_2:
                    tipo = "policristalino"
                    esperando = False
                elif evento.key == pygame.K_3:
                    tipo = "pelicula"
                    esperando = False
    return tipo


# --- BUCLE PRINCIPAL ---

def principal():
    tipo_panel = menu()
    sol_x, sol_y = posicion_aleatoria()
    tiempo_sol = pygame.time.get_ticks()
    guardar_posicion(sol_x, sol_y)
    angulo_panel = 0
    # Posición de la base del panel, ajustada a la pradera
    base_panel = (ANCHO // 2, ALTO - 50)
    area_panel = 1.5  # m²

    # Inicialización de las nubes con posición, tamaño y velocidad (pixeles/segundo)
    nubes = [
        {'x': 100, 'y': 100, 'w': 100, 'h': 50, 'speed': 20},
        {'x': 350, 'y': 80, 'w': 150, 'h': 60, 'speed': 15},
        {'x': 650, 'y': 120, 'w': 80, 'h': 40, 'speed': 25},
        {'x': ANCHO + 50, 'y': 110, 'w': 120, 'h': 55, 'speed': 18},  # Una nube que comienza fuera de pantalla
    ]

    ejecutando = True
    while ejecutando:
        dt = reloj.tick(60)  # Delta time en milisegundos (para movimiento suave)
        dt_seg = dt / 1000.0  # Delta time en segundos
        ahora = pygame.time.get_ticks()

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                ejecutando = False

        # --- LÓGICA DE MOVIMIENTO DE NUBES ---
        for cloud in nubes:
            cloud['x'] -= cloud['speed'] * dt_seg  # Mueve las nubes a la izquierda

            # Si la nube sale por completo por la izquierda, la reiniciamos por la derecha
            if cloud['x'] + cloud['w'] < 0:
                cloud['x'] = ANCHO + random.randint(50, 200)  # Posición de reinicio fuera de pantalla
                cloud['y'] = random.randint(80, 150)  # Altura aleatoria en el cielo
                cloud['w'] = random.randint(80, 150)  # Ancho aleatorio
                cloud['h'] = random.randint(40, 60)  # Alto aleatorio
                cloud['speed'] = random.randint(15, 30)  # Velocidad aleatoria

        # Cambio de posición del sol
        if ahora - tiempo_sol >= INTERVALO_MS:
            sol_x, sol_y = posicion_aleatoria()
            tiempo_sol = ahora
            guardar_posicion(sol_x, sol_y)
            print(f"[{time.strftime('%H:%M:%S')}] Nuevo sol en: ({sol_x}, {sol_y})")

        # --- DIBUJO ---
        dibujar_fondo(pantalla, ANCHO, ALTO)
        dibujar_nubes(pantalla, nubes)  # Ahora pasamos la lista de nubes en movimiento
        dibujar_brillo(pantalla, (sol_x, sol_y), RADIO_SOL, RADIO_BRILLO)

        # Control manual del panel (Q/E)
        teclas = pygame.key.get_pressed()
        if teclas[pygame.K_q]:
            angulo_panel += 1
        if teclas[pygame.K_e]:
            angulo_panel -= 1

        # Asegura que el ángulo del panel se mantenga en el rango [-180, 180] para visualización
        angulo_panel = angulo_panel % 360
        if angulo_panel > 180:
            angulo_panel -= 360

        # Dibuja el panel y obtiene su info
        info = dibujar_panel_tipo(pantalla, base_panel[0], base_panel[1], angulo_panel, tipo_panel)

        # --- SIMULACIÓN DE ENERGÍA MEJORADA (Cálculo de Angulo de Incidencia) ---

        radiacion_maxima = 800  # W/m² (Valor constante de radiación global horizontal)

        # 1. Calcular el vector del sol al punto central del panel (parte superior del palo)
        centro_panel_y = base_panel[1] - 100
        dx = sol_x - base_panel[0]
        dy = sol_y - centro_panel_y

        # 2. Calcular el ángulo del sol (acimut/elevación simplificado, relativo a la vertical 90 grados)
        # atan2(y, x) da el ángulo respecto al eje X positivo. Aquí queremos el ángulo respecto a la vertical
        angulo_sol_rad = math.atan2(dx,
                                    -dy)  # atan2(dx, -dy) da el ángulo respecto al eje Y negativo (vertical hacia arriba)
        angulo_sol_deg = math.degrees(angulo_sol_rad)

        # 3. Calcular la diferencia angular entre el panel y el sol (ángulo de incidencia)
        diferencia_angulo = abs(angulo_sol_deg - angulo_panel)
        # Normalizar la diferencia al rango [0, 180] grados
        diferencia_angulo = diferencia_angulo % 360
        if diferencia_angulo > 180:
            diferencia_angulo = 360 - diferencia_angulo

        # 4. Factor de eficiencia angular: cos(ángulo de incidencia). Máximo (1.0) cuando la diferencia es 0.
        factor_incidencia = math.cos(math.radians(diferencia_angulo))

        # Radiación efectiva que impacta la superficie
        radiacion_efectiva = radiacion_maxima * max(0, factor_incidencia)

        # Potencia generada
        potencia = radiacion_efectiva * area_panel * info["eficiencia"]

        # --- INFORMACIÓN EN PANTALLA ---
        info_texto = [
            f"Tipo: {tipo_panel.capitalize()}",
            f"Eficiencia Base: {info['eficiencia'] * 100:.1f}%",
            f"Potencia Estimada: {potencia:.1f} W",
            "--- Ángulos y Rendimiento ---",
            f"Radiación efectiva: {radiacion_efectiva:.1f} W/m² (Max: {radiacion_maxima} W/m²)",
            f"Ángulo del panel: {angulo_panel:.1f}°",
            f"Ángulo Óptimo (Sol): {angulo_sol_deg:.1f}°",
            f"Ángulo de Incidencia: {diferencia_angulo:.1f}°",
        ]

        # Indicador visual de rendimiento (verde=bueno, amarillo=medio, rojo=malo)
        rendimiento_color = (0, 255, 0) if factor_incidencia > 0.9 else (
            (255, 255, 0) if factor_incidencia > 0.6 else (255, 100, 100))
        rendimiento_texto = fuente.render(f"Factor de Rendimiento Angular: {max(0, factor_incidencia) * 100:.1f}%",
                                          True, rendimiento_color)
        pantalla.blit(rendimiento_texto, (10, 10))

        for i, texto in enumerate(info_texto):
            linea = fuente.render(texto, True, (240, 240, 240))
            # Ajusta la posición de la información para que inicie después del texto de rendimiento
            pantalla.blit(linea, (10, 10 + (i + 1) * 22))

            # Controles
        controles = fuente.render("Controles: [Q] Girar izquierda, [E] Girar derecha", True, (200, 220, 255))
        pantalla.blit(controles, (10, ALTO - 30))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    if GUARDAR_ARCHIVO and os.path.exists("posicion_sol.json"):
        try:
            os.remove("posicion_sol.json")
        except:
            pass
    print("Iniciando simulación. Cierra la ventana para terminar.")
    principal()
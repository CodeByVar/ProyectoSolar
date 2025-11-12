import pygame
import random
import time
import json
import os
import math

# --- CONFIGURACIÓN GLOBAL ---
ANCHO, ALTO = 800, 600
RADIO_SOL = 18
RADIO_BRILLO = 110 # Se mantiene el brillo mayor de origin/main
INTERVALO_MS = 8000  # Tiempo en que el sol cambia de posición (8 segundos)
MARGEN_PX = 80 # Se mantiene el nombre de variable de origin/main
GUARDAR_ARCHIVO = True

COLOR_BG = (18, 22, 30)
COLOR_PANEL = (30, 144, 255)
COLOR_PALO = (110, 110, 110)
COLOR_TEXTO = (235, 235, 235)
COLOR_HUD_BG = (0, 0, 0, 150)
COLOR_MARGEN = (70, 80, 90)
COLOR_LINEA_SOL = (250, 230, 120)
COLOR_NORMAL = (120, 220, 255)
COLOR_ERROR = (255, 120, 120)

ANG_MIN, ANG_MAX = -85, 85
Kp = 0.35
VEL_MAX = 3.5

# ---parámetros de movimiento realista ---
MODO_REALISTA = True                 # ON por defecto
VEL_MAX_DEG_PER_SEC = 140.0          # límite de velocidad (°/s)
ACC_MAX_DEG_PER_SEC2 = 300.0         # límite de aceleración (°/s²)
FRICCION_ZETA = 2.5
BANDA_MUERTA_DEG = 1.5               # zona sin corrección
HISTERESIS_DEG = 0.5                 # salida de la zona
RAFAGA_VIENTO_ON = False             # (G) alterna ráfagas

os.environ["SDL_VIDEO_CENTERED"] = "1"
pygame.init()

WIN_START_W, WIN_START_H = 1100, 700
flags_windowed = pygame.RESIZABLE
pantalla = pygame.display.set_mode((WIN_START_W, WIN_START_H), flags_windowed)
pygame.display.set_caption("Seguidor Solar - líneas, normal y seguimiento")
reloj = pygame.time.Clock()
try:
    fuente = pygame.font.SysFont("consolas", 18)
except:
    fuente = pygame.font.SysFont(None, 18)

is_fullscreen = False
windowed_size = (WIN_START_W, WIN_START_H)  # record para volver de fullscreen

def viewport_size():
    """Tamaño actual de la superficie de dibujo."""
    return pantalla.get_size()

# Datos de cada tipo de panel solar (Mantenido de HEAD)
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


# --- FUNCIONES DE LÓGICA Y AYUDA (Mantenidas de origin/main) ---

def guardar_posicion(x, y):
    """Guarda la posición del sol en un archivo JSON."""
    if not GUARDAR_ARCHIVO:
        return
    # Nota: Tu rama HEAD no especificaba el nombre de archivo, usamos el nombre de tu rama anterior.
    datos = {"x": int(x), "y": int(y), "tiempo_ms": int(time.time() * 1000)}
    try:
        with open("posicion_sol.json", "w") as f:
            json.dump(datos, f)
    except Exception as e:
        print("Error al guardar:", e)

def posicion_aleatoria(tipo_panel):
    """
    Genera una posición aleatoria para el sol, asegurándose
    de que quede por encima del panel solar (en toda la zona superior).
    """
    w, h = viewport_size()
    margen = max(40, MARGEN_PX)
    # Se unifica la lógica de posicionamiento aleatorio del sol (tomada de origin/main)
    base_y = h - 100
    largo_palo = 100
    # Aquí se requiere saber el tipo para calcular el límite.
    # Como la rama HEAD introdujo tipos, simplificamos el alto por ahora o asumimos un valor fijo.
    alto_panel = 40 if tipo_panel in ["horizontal", "monocristalino", "policristalino"] else 100
    panel_top = base_y - largo_palo - (alto_panel / 2)
    limite_superior_y = int(panel_top - RADIO_SOL - 8)
    if limite_superior_y <= margen:
        limite_superior_y = margen + 10

    x = random.randint(margen, max(margen, w - margen))
    y = random.randint(margen, limite_superior_y)
    return x, y

def normalize_angle_deg(a):
    return (a + 180) % 360 - 180

def clamp(v, vmin, vmax):
    return max(vmin, min(vmax, v))

def angulo_hacia_punto(x0, y0, x1, y1):
    dx, dy = (x1 - x0), (y1 - y0)
    return -math.degrees(math.atan2(dy, dx))

def vector_desde_angulo(angulo_deg, largo):
    rad = math.radians(-angulo_deg)
    dx = math.cos(rad) * largo
    dy = math.sin(rad) * largo
    return dx, dy

def toggle_fullscreen():
    global is_fullscreen, windowed_size, pantalla
    if not is_fullscreen:
        windowed_size = viewport_size()
        info = pygame.display.Info()
        pantalla = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
        is_fullscreen = True
    else:
        pantalla = pygame.display.set_mode(windowed_size, flags_windowed)
        is_fullscreen = False

# --- FUNCIONES DE DIBUJO ---

def dibujar_fondo(superficie, ancho, alto):
    """Dibuja el cielo y la pradera como fondo. (Mantenido de HEAD)"""
    # Cielo (Celeste suave) - 3/4 de la pantalla
    color_cielo = (135, 206, 235)  # Light Sky Blue
    alto_cielo = int(alto * 0.75)
    superficie.fill(color_cielo, (0, 0, ancho, alto_cielo))

    # Pradera (Verde) - 1/4 de la pantalla
    color_pradera = (34, 139, 34)  # Forest Green
    superficie.fill(color_pradera, (0, alto_cielo, ancho, alto - alto_cielo))


def dibujar_nubes(superficie, nubes_data):
    """Dibuja las nubes basadas en sus posiciones y tamaños. (Mantenido de HEAD)"""
    color_nube = (255, 255, 255, 200)  # Blanco con transparencia (alpha 200)

    for cloud in nubes_data:
        cx, cy, w, h = cloud['x'], cloud['y'], cloud['w'], cloud['h']
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.ellipse(s, color_nube, s.get_rect())
        superficie.blit(s, (cx - w // 2, cy - h // 2))

def dibujar_brillo(superficie, centro, radio_interno, radio_externo, color=(255, 210, 40)): # Unificado el color amarillo de sol
    """Dibuja el sol con un efecto de brillo/resplandor."""
    cx, cy = centro
    brillo = pygame.Surface((radio_externo*2, radio_externo*2), pygame.SRCALPHA)
    pasos = 18 # Usamos más pasos para un brillo más suave (de origin/main)
    for i in range(pasos, 0, -1):
        r = int(radio_externo * (i / pasos))
        alpha = int(200 * (i / pasos) * 0.6)
        col = (color[0], color[1], color[2], alpha)
        pygame.draw.circle(brillo, col, (radio_externo, radio_externo), r)
    pygame.draw.circle(brillo, (color[0], color[1], color[2], 255), (radio_externo, radio_externo), radio_interno)
    superficie.blit(brillo, (cx - radio_externo, cy - radio_externo))

def dibujar_margen(superficie):
    """Dibuja un margen (de origin/main)."""
    w, h = viewport_size()
    margen = max(40, MARGEN_PX)
    pygame.draw.rect(superficie, COLOR_MARGEN, (margen, margen, w - 2*margen, h - 2*margen), 1)

def dibujar_panel(superficie, base_x, base_y, angulo, tipo_panel):
    """
    Dibuja el panel usando el palo (origin/main) y la textura/color
    basado en el tipo (HEAD).
    """
    largo_palo = 100
    pygame.draw.line(superficie, COLOR_PALO, (base_x, base_y), (base_x, base_y - largo_palo), 8)

    ancho_panel = 120
    # Ajuste de alto basado en el tipo de panel
    if tipo_panel in TIPOS_PANELES:
        # Los paneles de HEAD son de alto fijo (40)
        alto_panel = 40
        info = TIPOS_PANELES[tipo_panel]
        color_panel = info["color"]
        try:
            # Intenta cargar la imagen
            textura = pygame.image.load(info["imagen"]).convert_alpha()
            textura = pygame.transform.scale(textura, (ancho_panel, alto_panel))
        except:
            # Si falla, usa color sólido
            textura = pygame.Surface((ancho_panel, alto_panel), pygame.SRCALPHA)
            textura.fill(color_panel)
    else:
        # Paneles 'horizontal'/'vertical' (de origin/main), fallback a color sólido
        alto_panel = 40 if tipo_panel == "horizontal" else 100
        textura = pygame.Surface((ancho_panel, alto_panel), pygame.SRCALPHA)
        textura.fill(COLOR_PANEL)
        info = {"eficiencia": 0.18} # info dummy para evitar error de eficiencia

    panel_rotado = pygame.transform.rotate(textura, angulo)

    pos_panel = (base_x - panel_rotado.get_width() // 2,
                 base_y - largo_palo - panel_rotado.get_height() // 2)
    superficie.blit(panel_rotado, pos_panel)

    return base_x, base_y - largo_palo, info # Se devuelve la info para cálculos de energía

def dibujar_lineas_imaginarias(superficie, punta_x, punta_y, sol_x, sol_y, angulo_panel):
    """Dibuja líneas de seguimiento y normal (de origin/main)."""
    # Línea Sol (amarilla)
    pygame.draw.line(superficie, COLOR_LINEA_SOL, (punta_x, punta_y), (sol_x, sol_y), 2)

    # Línea Normal al Panel (azul claro)
    n_dx, n_dy = vector_desde_angulo(angulo_panel, 140)
    pygame.draw.line(superficie, COLOR_NORMAL, (punta_x, punta_y), (punta_x + n_dx, punta_y + n_dy), 2)

    # Línea de Error (roja, distancia entre normal y sol)
    objetivo = angulo_hacia_punto(punta_x, punta_y, sol_x, sol_y)
    nx, ny = (punta_x + n_dx, punta_y + n_dy)
    t_dx, t_dy = vector_desde_angulo(objetivo, 120)
    tx, ty = (punta_x + t_dx, punta_y + t_dy)
    pygame.draw.line(superficie, COLOR_ERROR, (nx, ny), (tx, ty), 2)

def hud(superficie, texto_linea):
    """Dibuja una barra de información superior (de origin/main)."""
    w, _ = viewport_size()
    barra = pygame.Surface((w, 28), pygame.SRCALPHA)
    barra.fill(COLOR_HUD_BG)
    superficie.blit(barra, (0, 0))
    surf_txt = fuente.render(texto_linea, True, COLOR_TEXTO)
    superficie.blit(surf_txt, (8, 5))

# --- FUNCIÓN DE MENÚ ---

def menu():
    """Muestra un menú con las opciones de panel (combinando HEAD y origin/main)."""
    seleccion = None
    while True:
        pantalla.fill(COLOR_BG)
        w, h = viewport_size()
        titulo = fuente.render("Selecciona el tipo de panel solar:", True, (255, 255, 255))
        t1 = fuente.render("[1] Monocristalino (Alta Ef.)", True, (200, 220, 255))
        t2 = fuente.render("[2] Policristalino (Media Ef.)", True, (200, 220, 255))
        t3 = fuente.render("[3] Película Delgada (Baja Ef.)", True, (200, 220, 255))
        t4 = fuente.render("[4] Panel Vertical (Default)", True, (200, 220, 255)) # Opción de la otra rama

        pantalla.blit(titulo, (w//2 - titulo.get_width()//2, h//2 - 90))
        pantalla.blit(t1,     (w//2 - t1.get_width()//2,     h//2 - 40))
        pantalla.blit(t2,     (w//2 - t2.get_width()//2,     h//2))
        pantalla.blit(t3,     (w//2 - t3.get_width()//2,     h//2 + 40))
        pantalla.blit(t4,     (w//2 - t4.get_width()//2,     h//2 + 80))
        pygame.display.flip()

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit(); exit()
            elif evento.type == pygame.VIDEORESIZE:
                pass
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_1:
                    seleccion = "monocristalino"
                elif evento.key == pygame.K_2:
                    seleccion = "policristalino"
                elif evento.key == pygame.K_3:
                    seleccion = "pelicula"
                elif evento.key == pygame.K_4:
                    seleccion = "vertical" # Opción de origin/main
                elif evento.key == pygame.K_f:
                    toggle_fullscreen()
        if seleccion:
            return seleccion


# --- BUCLE PRINCIPAL ---

def principal():
    tipo_panel = menu()

    # Inicialización de nubes (De HEAD)
    w_start, h_start = viewport_size()
    nubes = [
        {'x': 100, 'y': 100, 'w': 100, 'h': 50, 'speed': 20},
        {'x': 350, 'y': 80, 'w': 150, 'h': 60, 'speed': 15},
        {'x': 650, 'y': 120, 'w': 80, 'h': 40, 'speed': 25},
        {'x': w_start + 50, 'y': 110, 'w': 120, 'h': 55, 'speed': 18},
    ]

    sol_x, sol_y = posicion_aleatoria(tipo_panel)
    tiempo_sol = pygame.time.get_ticks()
    guardar_posicion(sol_x, sol_y)

    angulo_panel = 0
    seguimiento_continuo = True # De origin/main

    # ---estado del movimiento realista ---
    vel_ang = 0.0
    en_banda_muerta = False

    ejecutando = True
    while ejecutando:
        dt = reloj.tick(60)  # Delta time en milisegundos (para movimiento suave)
        dt_seg = dt / 1000.0  # Delta time en segundos
        ahora = pygame.time.get_ticks()
        w, h = viewport_size() # Se usa el tamaño actual, no la constante ANCHO/ALTO

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                ejecutando = False
            elif evento.type == pygame.VIDEORESIZE:
                pass
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    ejecutando = False
                elif evento.key == pygame.K_r:
                    sol_x, sol_y = posicion_aleatoria(tipo_panel)
                    tiempo_sol = ahora
                    guardar_posicion(sol_x, sol_y)
                elif evento.key == pygame.K_f:
                    toggle_fullscreen()
                elif evento.key == pygame.K_t:
                    seguimiento_continuo = not seguimiento_continuo
                # --- alternar viento ---
                elif evento.key == pygame.K_g:
                    global RAFAGA_VIENTO_ON
                    RAFAGA_VIENTO_ON = not RAFAGA_VIENTO_ON

        # --- LÓGICA DE NUBES (De HEAD) ---
        for cloud in nubes:
            cloud['x'] -= cloud['speed'] * dt_seg
            if cloud['x'] + cloud['w'] < 0:
                cloud['x'] = w + random.randint(50, 200)
                cloud['y'] = random.randint(80, 150)
                cloud['w'] = random.randint(80, 150)
                cloud['h'] = random.randint(40, 60)
                cloud['speed'] = random.randint(15, 30)

        # Cambio de posición del sol
        if ahora - tiempo_sol >= INTERVALO_MS:
            sol_x, sol_y = posicion_aleatoria(tipo_panel)
            tiempo_sol = ahora
            guardar_posicion(sol_x, sol_y)
            print(f"[{time.strftime('%H:%M:%S')}] Nuevo sol en: ({sol_x}, {sol_y})")

        # --- LÓGICA DEL PANEL (Combinación de ambas ramas) ---
        base_panel = (w // 2, h - 100) # Se usa el ancho/alto de la ventana actual
        punta_x, punta_y, panel_info = dibujar_panel(pantalla, base_panel[0], base_panel[1], angulo_panel, tipo_panel)
        area_panel = 1.5 # m² (tomado de HEAD)

        # Control manual del panel (Q/E)
        teclas = pygame.key.get_pressed()
        if teclas[pygame.K_q]:
            angulo_panel = clamp(angulo_panel + 1.5, ANG_MIN, ANG_MAX)
        if teclas[pygame.K_e]:
            angulo_panel = clamp(angulo_panel - 1.5, ANG_MIN, ANG_MAX)


        # Cálculo del ángulo objetivo y error (De origin/main)
        ang_objetivo = angulo_hacia_punto(punta_x, punta_y, sol_x, sol_y)
        error = normalize_angle_deg(ang_objetivo - angulo_panel)

        # Lógica de seguimiento continuo (De origin/main)
        if seguimiento_continuo:
            delta = clamp(Kp * error, -VEL_MAX, VEL_MAX)
            angulo_panel = clamp(angulo_panel + delta, ANG_MIN, ANG_MAX)

        # --- movimiento realista (inercia, aceleración, fricción y banda muerta) ---
        if seguimiento_continuo and MODO_REALISTA:
            if en_banda_muerta:
                if abs(error) > (BANDA_MUERTA_DEG + HISTERESIS_DEG):
                    en_banda_muerta = False
            else:
                if abs(error) <= BANDA_MUERTA_DEG:
                    en_banda_muerta = True

            if en_banda_muerta:
                vel_obj = 0.0
            else:
                vel_obj = clamp(Kp * error * (VEL_MAX_DEG_PER_SEC / max(VEL_MAX, 1e-6)),
                                -VEL_MAX_DEG_PER_SEC, VEL_MAX_DEG_PER_SEC)

            acc = clamp(vel_obj - vel_ang, -ACC_MAX_DEG_PER_SEC2 * dt_seg, ACC_MAX_DEG_PER_SEC2 * dt_seg)
            if RAFAGA_VIENTO_ON and random.random() < 0.1:
                acc += random.gauss(0.0, 15.0) * dt_seg

            vel_ang = (vel_ang * max(0.0, 1.0 - FRICCION_ZETA * dt_seg)) + acc
            vel_ang = clamp(vel_ang, -VEL_MAX_DEG_PER_SEC, VEL_MAX_DEG_PER_SEC)

            angulo_panel += vel_ang * dt_seg
            if angulo_panel < ANG_MIN:
                angulo_panel = ANG_MIN; vel_ang = 0.0
            elif angulo_panel > ANG_MAX:
                angulo_panel = ANG_MAX; vel_ang = 0.0

        # --- CÁLCULO DE ENERGÍA MEJORADO (De HEAD) ---
        radiacion_maxima = 800
        factor_incidencia = math.cos(math.radians(abs(error)))
        radiacion_efectiva = radiacion_maxima * max(0, factor_incidencia)
        potencia = radiacion_efectiva * area_panel * panel_info["eficiencia"]

        # --- DIBUJO ---
        dibujar_fondo(pantalla, w, h)
        dibujar_nubes(pantalla, nubes)
        dibujar_margen(pantalla) # Dibujar margen para limitar movimiento del sol

        dibujar_brillo(pantalla, (sol_x, sol_y), RADIO_SOL, RADIO_BRILLO)

        punta_x, punta_y, _ = dibujar_panel(pantalla, base_panel[0], base_panel[1], angulo_panel, tipo_panel)
        dibujar_lineas_imaginarias(pantalla, punta_x, punta_y, sol_x, sol_y, angulo_panel)

        # --- HUD (Combinación) ---
        tiempo_restante = max(0, INTERVALO_MS - (ahora - tiempo_sol)) / 1000.0

        rendimiento_color = (0, 255, 0) if factor_incidencia > 0.9 else (
            (255, 255, 0) if factor_incidencia > 0.6 else (255, 100, 100))

        # muestra de velocidad y estados
        hud_txt = (
            f"Tipo: {tipo_panel.capitalize()} | Seguimiento: {'ON' if seguimiento_continuo else 'OFF'} | "
            f"Potencia: {potencia:.1f} W | Rendimiento Angular: {max(0, factor_incidencia) * 100:.1f}% | "
            f"Error: {int(error):>3}° | Ángulo Panel: {int(angulo_panel):>3}° | "
            f"Vel: {vel_ang:4.1f}°/s | Realista:{'ON' if MODO_REALISTA else 'OFF'} | Viento:{'ON' if RAFAGA_VIENTO_ON else 'OFF'} | "
            f"[T] toggle | [R] sol | [Q/E] manual | [F] full | [G] viento"
        )
        surf_txt = fuente.render(hud_txt, True, rendimiento_color)
        barra = pygame.Surface((w, 28), pygame.SRCALPHA)
        barra.fill(COLOR_HUD_BG)
        pantalla.blit(barra, (0, 0))
        pantalla.blit(surf_txt, (8, 5))

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

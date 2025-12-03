import pygame
import random
import time
import json
import os
import math

pygame.init()

ANCHO, ALTO = 800, 600
RADIO_SOL = 18
RADIO_BRILLO = 110
INTERVALO_MS = 8000
MARGEN_PX = 80
GUARDAR_ARCHIVO = True

COLOR_BG = (18, 22, 30)
COLOR_PANEL_DEF = (30, 144, 255)
COLOR_PALO = (110, 110, 110)
COLOR_TEXTO = (235, 235, 235)
COLOR_HUD_BG = (0, 0, 0, 150)
COLOR_MARGEN = (70, 80, 90)
COLOR_LINEA_SOL = (250, 230, 120)
COLOR_NORMAL = (120, 220, 255)
COLOR_ERROR = (255, 120, 120)
#colores extra
COLOR_UI_BG = (20, 25, 35, 230)
COLOR_UI_BORDER = (60, 160, 220)
COLOR_ACCENT = (255, 180, 50)
COLOR_TEXT_H1 = (255, 255, 255)
COLOR_TEXT_H2 = (180, 200, 220)
COLOR_SUCCESS = (100, 255, 100)
COLOR_DANGER = (255, 80, 80)
COLOR_HUD_BG_DARK = (15, 20, 30, 245)
COLOR_WIDGET_FILL = (30, 35, 45)
COLOR_WIDGET_STROKE = (60, 70, 85)
COLOR_LABEL = (150, 160, 170)
COLOR_VALUE = (220, 230, 240)

#tipografias
try:
    fuente_grande = pygame.font.SysFont("consolas", 32, bold=True)
    fuente_ui = pygame.font.SysFont("consolas", 16)
    fuente_bold = pygame.font.SysFont("consolas", 16, bold=True)
except:
    fuente_grande = pygame.font.SysFont(None, 40)
    fuente_ui = pygame.font.SysFont(None, 20)
    fuente_bold = pygame.font.SysFont(None, 20)


def dibujar_caja_ui(superficie, x, y, w, h, color_bg=COLOR_UI_BG, borde=True):
    # Dibuja un rectángulo con fondo oscuro y borde neón
    rect = pygame.Rect(x, y, w, h)
    # Fondo (necesita superficie con alpha para transparencia real)
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    s.fill(color_bg)
    superficie.blit(s, (x, y))

    if borde:
        pygame.draw.rect(superficie, COLOR_UI_BORDER, rect, 2, border_radius=6)
        # Pequeño detalle técnico en las esquinas
        pygame.draw.circle(superficie, COLOR_UI_BORDER, (x, y), 2)
        pygame.draw.circle(superficie, COLOR_UI_BORDER, (x + w, y), 2)
        pygame.draw.circle(superficie, COLOR_UI_BORDER, (x, y + h), 2)
        pygame.draw.circle(superficie, COLOR_UI_BORDER, (x + w, y + h), 2)

ANG_MIN, ANG_MAX = -85, 85

Kp = 0.15
Ki = 0.0001
Kd = 0.02

VEL_MAX = 3.5
SMOOTH = 0.22

MODO_REALISTA = True
VEL_MAX_DEG_PER_SEC = 140.0
ACC_MAX_DEG_PER_SEC2 = 300.0
FRICCION_ZETA = 2.5
BANDA_MUERTA_DEG = 1.5
HISTERESIS_DEG = 0.5
RAFAGA_VIENTO_ON = False

SHOW_DEBUG_CONTROL = True

os.environ["SDL_VIDEO_CENTERED"] = "1"
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
windowed_size = (WIN_START_W, WIN_START_H)


def tam_viewport():
    return pantalla.get_size()



TIPOS_PANELES = {
    "monocristalino": {
        "color": (0, 0, 0),
        "imagen": "monocristalino.png",
        "eficiencia_base": 0.22,
        "area_m2": 1.6,
        "coef_difuso": 0.95,
        "coef_angulo": 1.2,
        "variacion": 0.98,
        "descripcion": "Alta eficiencia, panel negro sólido.",
        "detalle": "Convierte más energía, ideal para espacio limitado."
    },
    "policristalino": {
        "color": (30, 144, 255),
        "imagen": "policristalino.jpg",
        "eficiencia_base": 0.17,
        "area_m2": 1.8,
        "coef_difuso": 1.0,
        "coef_angulo": 1.35,
        "variacion": 1.02,
        "descripcion": "Eficiencia media, azul metalizado.",
        "detalle": "Más económico, menor rendimiento térmico."
    },
    "pelicula": {
        "color": (100, 100, 100),
        "imagen": "panelfino.png",
        "eficiencia_base": 0.12,
        "area_m2": 2.0,
        "coef_difuso": 1.25,
        "coef_angulo": 1.1,
        "variacion": 1.05,
        "descripcion": "Baja eficiencia, gris oscuro.",
        "detalle": "Flexible, buen rendimiento con luz difusa."
    },
    "vertical": {
        "color": (140, 140, 140),
        "imagen": "",
        "eficiencia_base": 0.18,
        "area_m2": 1.2,
        "coef_difuso": 0.9,
        "coef_angulo": 1.4,
        "variacion": 1.0,
        "descripcion": "Panel vertical o por defecto.",
        "detalle": "Configuración por defecto."
    }
}

PANEL_W = 220
PANEL_X = ANCHO - PANEL_W - 10
COLOR_PANEL_BG = (40, 45, 55, 220)
COLOR_BOTON_ACTIVO = (255, 165, 0)
COLOR_BOTON_INACTIVO = (70, 70, 70)

MODOS_CLIMATICOS = {
    "soleado": {
        "coef_ilum": 1.0,
        "prob_nube": 0.05,
        "vel_nube_min": 5,
        "vel_nube_max": 15,
        "descripcion": "Cielo claro, máxima irradiancia.",
        "idx": 0
    },
    "parcialmente_nublado": {
        "coef_ilum": 0.85,
        "prob_nube": 0.4,
        "vel_nube_min": 15,
        "vel_nube_max": 30,
        "descripcion": "Alternando sol y nubes.",
        "idx": 1
    },
    "nublado": {
        "coef_ilum": 0.35,
        "prob_nube": 0.8,
        "vel_nube_min": 10,
        "vel_nube_max": 25,
        "descripcion": "Cielo cubierto, luz difusa dominante.",
        "idx": 2
    },
    "tormenta": {
        "coef_ilum": 0.1,
        "prob_nube": 0.95,
        "vel_nube_min": 30,
        "vel_nube_max": 50,
        "descripcion": "Muy poca luz, nubes densas y rápidas.",
        "idx": 3
    }
}


PANEL_W = 220
PANEL_X = ANCHO - PANEL_W - 10 # Posición inicial del panel
COLOR_PANEL_BG = (40, 45, 55, 220)
COLOR_BOTON_ACTIVO = (255, 165, 0)
COLOR_BOTON_INACTIVO = (70, 70, 70)

MODOS_CLIMATICOS = {
    "soleado": {
        "coef_ilum": 1.0,
        "prob_nube": 0.05,
        "vel_nube_min": 5,
        "vel_nube_max": 15,
        "descripcion": "Cielo claro, máxima irradiancia.",
        "idx": 0 # Nuevo índice para el botón
    },
    "parcialmente_nublado": {
        "coef_ilum": 0.85,
        "prob_nube": 0.4,
        "vel_nube_min": 15,
        "vel_nube_max": 30,
        "descripcion": "Alternando sol y nubes.",
        "idx": 1
    },
    "nublado": {
        "coef_ilum": 0.35,
        "prob_nube": 0.8,
        "vel_nube_min": 10,
        "vel_nube_max": 25,
        "descripcion": "Cielo cubierto, luz difusa dominante.",
        "idx": 2
    },
    "tormenta": {
        "coef_ilum": 0.1,
        "prob_nube": 0.95,
        "vel_nube_min": 30,
        "vel_nube_max": 50,
        "descripcion": "Muy poca luz, nubes densas y rápidas.",
        "idx": 3
    }
}

def guardar_posicion(x, y, iluminacion=None):
    if not GUARDAR_ARCHIVO:
        return
    datos = {"x": int(x), "y": int(y), "tiempo_ms": int(time.time() * 1000)}
    if iluminacion is not None:
        datos["iluminacion"] = float(iluminacion)
    try:
        with open("posicion_sol.json", "w") as f:
            json.dump(datos, f)
    except Exception as e:
        print("Error al guardar:", e)


def posicion_aleatoria(tipo_panel):
    w, h = tam_viewport()
    margen = max(40, MARGEN_PX)
    base_y = h - 100
    largo_palo = 100
    alto_panel = 40 if tipo_panel in ["vertical", "monocristalino", "policristalino"] else 100
    panel_top = base_y - largo_palo - (alto_panel / 2)
    limite_superior_y = int(panel_top - RADIO_SOL - 8)
    if limite_superior_y <= margen:
        limite_superior_y = margen + 10
    x = random.randint(margen, max(margen, w - margen))
    y = random.randint(margen, limite_superior_y)
    return x, y


def normalizar_angulo_deg(a):
    return (a + 180) % 360 - 180


def limitar(v, vmin, vmax):
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
        windowed_size = tam_viewport()
        info = pygame.display.Info()
        pantalla = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
        is_fullscreen = True
    else:
        pantalla = pygame.display.set_mode(windowed_size, flags_windowed)
        is_fullscreen = False


def dibujar_panel_clima(superficie, x, y,  modo_clima_actual):

    panel_w = 240
    panel_h = 210

    rect_panel = pygame.Rect(x, y, panel_w, panel_h)

    dibujar_caja_ui(superficie, x, y, panel_w, panel_h)


    titulo = fuente_bold.render("CONTROL CLIMÁTICO", True, COLOR_ACCENT)
    superficie.blit(titulo, (x + 15, y + 10))

    y_start = y + 40
    botones = []

    for key, info in MODOS_CLIMATICOS.items():
        es_activo = (key == modo_clima_actual)

        color_rect = (40, 100, 140) if es_activo else (40, 45, 55)
        color_borde = COLOR_ACCENT if es_activo else (80, 80, 80)
        color_texto = (255, 255, 255) if es_activo else (180, 180, 180)

        btn_h = 32
        btn_w_pad = PANEL_W - 30
        btn_rect = pygame.Rect(x + 15, y_start, btn_w_pad, btn_h)

        pygame.draw.rect(superficie, color_rect, btn_rect, border_radius=5)
        pygame.draw.rect(superficie, color_borde, btn_rect, 1 if not es_activo else 2, border_radius=4)
        texto_btn = fuente_ui.render(f"{key.replace('_', ' ').title()}", True, color_texto)
        superficie.blit(texto_btn, (btn_rect.x + 10, btn_rect.y + 8))

        if es_activo:
            pygame.draw.circle(superficie, COLOR_SUCCESS, (btn_rect.right - 15, btn_rect.centery), 4)
        botones.append({"key": key, "rect": btn_rect})
        y_start += btn_h + 8

    return rect_panel, botones


def dibujar_fondo(superficie, ancho, alto, clima_info, cobertura_nubes):
    color_cielo_soleado = (135, 206, 235)
    color_pradera_base = (34, 139, 34)
    coef_ilum = clima_info.get("coef_ilum", 1.0)

    def mezclar_color(color_base, factor):
        r = int(color_base[0] * factor + COLOR_BG[0] * (1 - factor))
        g = int(color_base[1] * factor + COLOR_BG[1] * (1 - factor))
        b = int(color_base[2] * factor + COLOR_BG[2] * (1 - factor))
        return (r, g, b)

    factor_mezcla = max(0.3, 0.5 + coef_ilum * 0.5)

    color_cielo = mezclar_color(color_cielo_soleado, factor_mezcla)
    color_pradera = mezclar_color(color_pradera_base, factor_mezcla)

    alto_cielo = int(alto * 0.75)
    superficie.fill(color_cielo, (0, 0, ancho, alto_cielo))
    superficie.fill(color_pradera, (0, alto_cielo, ancho, alto - alto_cielo))

    if cobertura_nubes > 0.0 or coef_ilum < 0.9:
        neblina = pygame.Surface((ancho, alto), pygame.SRCALPHA)
        neblina_base = (200, 220, 240)
        neblina_color = mezclar_color(neblina_base, factor_mezcla)

        alpha_cobertura = cobertura_nubes * 120
        alpha_oscuridad = (1 - coef_ilum) * 100
        alpha = int(min(255, alpha_cobertura + alpha_oscuridad))

        neblina.fill((neblina_color[0], neblina_color[1], neblina_color[2], alpha))
        superficie.blit(neblina, (0, 0))


def dibujar_nubes(superficie, nubes_data, sol_x, sol_y, clima_info):
    coef_ilum = clima_info.get("coef_ilum", 1.0)
    base_color_val = int(255 * (0.6 + 0.4 * coef_ilum))
    color_nube_base = (base_color_val, base_color_val, base_color_val)

    for c in nubes_data:
        dx = sol_x - c['x']
        dy = sol_y - c['y']
        rx = max(1.0, c['w'] / 2.0)
        ry = max(1.0, c['h'] / 2.0)
        nd = math.hypot(dx / rx, dy / ry)

        base_alpha = int(150 + (1.0 - coef_ilum) * 90)
        dist_alpha_factor = 1.0
        if nd <= 1.0:
            dist_alpha_factor = 0.5
        elif nd <= 2.0:
            dist_alpha_factor = 0.5 + 0.5 * (nd - 1.0)

        final_alpha = int(base_alpha * dist_alpha_factor)
        final_alpha = limitar(final_alpha, 50, 255)

        col = (color_nube_base[0], color_nube_base[1], color_nube_base[2], final_alpha)
        s = pygame.Surface((c['w'], c['h']), pygame.SRCALPHA)
        pygame.draw.ellipse(s, col, s.get_rect())
        superficie.blit(s, (c['x'] - c['w'] // 2, c['y'] - c['h'] // 2))


def dibujar_brillo(superficie, centro, radio_interno, radio_externo, coef_ilum=1.0):
    cx, cy = centro
    color_base = (255, 210, 40)

    r_adj = int(color_base[0] * (0.5 + coef_ilum * 0.5))
    g_adj = int(color_base[1] * (0.6 + coef_ilum * 0.4))
    b_adj = int(color_base[2] * (0.7 + coef_ilum * 0.3))
    color_sol_ajustado = (r_adj, g_adj, b_adj)

    brillo = pygame.Surface((radio_externo * 2, radio_externo * 2), pygame.SRCALPHA)
    pasos = 18

    for i in range(pasos, 0, -1):
        r = int(radio_externo * (i / pasos))
        alpha_base = int(200 * (i / pasos) * 0.6)
        alpha = int(alpha_base * coef_ilum)
        col = (color_sol_ajustado[0], color_sol_ajustado[1], color_sol_ajustado[2], alpha)
        pygame.draw.circle(brillo, col, (radio_externo, radio_externo), r)

    alpha_centro = int(255 * min(1.0, 0.7 + coef_ilum * 0.3))
    pygame.draw.circle(
        brillo,
        (color_sol_ajustado[0], color_sol_ajustado[1], color_sol_ajustado[2], alpha_centro),
        (radio_externo, radio_externo),
        radio_interno
    )

    superficie.blit(brillo, (cx - radio_externo, cy - radio_externo))


def dibujar_margen(superficie):
    w, h = tam_viewport()
    margen = max(40, MARGEN_PX)
    pygame.draw.rect(superficie, COLOR_MARGEN, (margen, margen, w - 2 * margen, h - 2 * margen), 1)


def dibujar_panel(superficie, base_x, base_y, angulo, tipo_panel):
    largo_palo = 100
    pygame.draw.line(superficie, COLOR_PALO, (base_x, base_y), (base_x, base_y - largo_palo), 8)
    ancho_panel = 120
    if tipo_panel in TIPOS_PANELES:
        alto_panel = 40
        info = TIPOS_PANELES[tipo_panel]
        color_panel = info["color"]
        try:
            textura = pygame.image.load(info["imagen"]).convert_alpha()
            textura = pygame.transform.scale(textura, (ancho_panel, alto_panel))
        except:
            textura = pygame.Surface((ancho_panel, alto_panel), pygame.SRCALPHA)
            textura.fill(color_panel)
    else:
        alto_panel = 40 if tipo_panel == "horizontal" else 100
        textura = pygame.Surface((ancho_panel, alto_panel), pygame.SRCALPHA)
        textura.fill(COLOR_PANEL_DEF)
        info = {"eficiencia_base": 0.18, "area_m2": 1.5, "coef_difuso": 1.0, "coef_angulo": 1.3, "variacion": 1.0}
    panel_rotado = pygame.transform.rotate(textura, angulo)
    pos_panel = (base_x - panel_rotado.get_width() // 2,
                 base_y - largo_palo - panel_rotado.get_height() // 2)
    superficie.blit(panel_rotado, pos_panel)
    return base_x, base_y - largo_palo, info


def dibujar_lineas_imaginarias(superficie, punta_x, punta_y, sol_x, sol_y, angulo_panel, error_deg, en_banda_muerta):
    pygame.draw.line(superficie, COLOR_LINEA_SOL, (punta_x, punta_y), (sol_x, sol_y), 2)

    n_dx, n_dy = vector_desde_angulo(angulo_panel, 140)
    pygame.draw.line(superficie, COLOR_NORMAL, (punta_x, punta_y), (punta_x + n_dx, punta_y + n_dy), 2)

    objetivo = angulo_hacia_punto(punta_x, punta_y, sol_x, sol_y)
    nx, ny = (punta_x + n_dx, punta_y + n_dy)
    t_dx, t_dy = vector_desde_angulo(objetivo, 120)
    tx, ty = (punta_x + t_dx, punta_y + t_dy)

    e = abs(error_deg)
    if en_banda_muerta:
        color = (150, 150, 150)
    elif e < 5:
        color = (0, 255, 0)
    elif e < 15:
        color = (255, 255, 0)
    else:
        color = (255, 80, 80)

    grosor = 1 if e < 5 else (2 if e < 15 else 3)
    pygame.draw.line(superficie, color, (nx, ny), (tx, ty), grosor)


def dibujar_barra_iluminacion(superficie, iluminacion_normalizada):
    w, _ = tam_viewport()
    bw = 180
    bh = 14
    x = w - bw - 12
    y = 34
    pygame.draw.rect(superficie, (40, 40, 40), (x, y, bw, bh), border_radius=6)
    llenado = int(bw * iluminacion_normalizada)
    if llenado > 0:
        pygame.draw.rect(superficie, COLOR_LINEA_SOL, (x + 2, y + 2, max(0, llenado - 4), bh - 4), border_radius=6)
    porcentaje = f"{int(iluminacion_normalizada * 100):>3}%"
    surf = fuente.render(porcentaje, True, COLOR_TEXTO)
    superficie.blit(surf, (x - 60, y - 2))


def dibujar_widget(superficie, x, y, titulo, valor, color_val=COLOR_VALUE, ancho=140):
    alto = 60  # AUMENTO: Antes era 50, ahora 60 para más espacio vertical
    rect_bg = pygame.Rect(x, y, ancho, alto)

    # 1. Fondo del widget
    pygame.draw.rect(superficie, COLOR_WIDGET_FILL, rect_bg, border_radius=8)

    # 2. Borde sutil
    pygame.draw.rect(superficie, COLOR_WIDGET_STROKE, rect_bg, 1, border_radius=8)

    # 3. Renderizar textos
    lbl = fuente_ui.render(titulo, True, COLOR_LABEL)
    val = fuente_grande.render(str(valor), True, color_val)

    # 4. CENTRADO PERFECTO
    # Calculamos el centro horizontal (centerx) basado en la caja.
    # Para la altura (Y), dividimos la caja visualmente:

    # El título se centra exactamente en el píxel 15 desde arriba
    lbl_rect = lbl.get_rect(centerx=rect_bg.centerx, centery=rect_bg.y + 15)

    # El valor (número) se centra un poco más abajo, en el píxel 42 desde arriba
    val_rect = val.get_rect(centerx=rect_bg.centerx, centery=rect_bg.y + 42)

    superficie.blit(lbl, lbl_rect)
    superficie.blit(val, val_rect)


def hud(superficie, texto_linea_ignorado, iluminacion_normalizada, seguimiento_continuo,
        potencia, energia, error, angulo, vel_ang, realista, viento):
    w, h = tam_viewport()
    alto_hud = 120  # Expandido para mayor comodidad visual

    # --- FONDO DEL PANEL SUPERIOR ---
    s = pygame.Surface((w, alto_hud), pygame.SRCALPHA)
    s.fill(COLOR_HUD_BG_DARK)
    superficie.blit(s, (0, 0))

    # Línea de acento neón en la parte inferior del HUD
    pygame.draw.line(superficie, COLOR_UI_BORDER, (0, alto_hud), (w, alto_hud), 2)

    # --- CÁLCULO DE POSICIONES (GRID DE 3 COLUMNAS) ---
    # Dividimos el ancho en 3 secciones para distribuir los elementos
    ancho_seccion = w // 3
    center_1 = ancho_seccion * 0.5  # Centro de la sección izquierda
    center_2 = ancho_seccion * 1.5  # Centro de la sección central
    center_3 = ancho_seccion * 2.5  # Centro de la sección derecha

    # Ancho estándar de las cajas
    w_box = 130
    gap = 10  # Espacio entre cajas

    # ================= SECCIÓN 1: ESTADO Y CONTROL (Izquierda) =================
    # Título de sección (Opcional, visual)
    lbl_sec1 = fuente_bold.render("SISTEMA DE CONTROL", True, COLOR_UI_BORDER)
    superficie.blit(lbl_sec1, (20, 10))

    lbl_modo = "AUTO" if seguimiento_continuo else "MANUAL"
    col_modo = COLOR_SUCCESS if seguimiento_continuo else COLOR_ACCENT

    # Caja 1: Modo
    dibujar_widget(superficie, 20, 35, "MODO", lbl_modo, col_modo, w_box)

    # Caja 2: Simulación (Debajo o al lado, aquí lo pongo al lado)
    estado_sim = "REAL" if realista else "SIMPLE"
    dibujar_widget(superficie, 20 + w_box + gap, 35, "FÍSICA", estado_sim, COLOR_TEXT_H2, w_box)

    # Indicador de Viento (Pequeño led o texto)
    if viento:
        txt_viento = fuente_ui.render("⚠ VIENTO ACTIVO", True, COLOR_DANGER)
        superficie.blit(txt_viento, (20, 90))

    # ================= SECCIÓN 2: ENERGÍA (Centro) =================
    # Centramos este bloque en la pantalla
    start_x_sec2 = (w // 2.2) - (w_box * 2 + gap) // 2

    # Barra de Irradiancia (Arriba de los números)
    bar_w = 280
    bar_h = 6
    bar_x = (w // 2) - (bar_w // 2)
    bar_y = 20

    # Fondo barra
    pygame.draw.rect(superficie, (50, 60, 70), (bar_x, bar_y, bar_w, bar_h), border_radius=3)
    # Llenado barra
    fill_w = int(bar_w * iluminacion_normalizada)
    if fill_w > 0:
        # Color gradiente simple (Amarillo a Rojo según intensidad)
        col_bar = (255, 220, 50) if iluminacion_normalizada > 0.5 else (200, 150, 50)
        pygame.draw.rect(superficie, col_bar, (bar_x, bar_y, fill_w, bar_h), border_radius=3)

    lbl_irr = fuente_ui.render(f"IRRADIANCIA SOLAR: {iluminacion_normalizada * 100:.1f}%", True, COLOR_TEXT_H2)
    lbl_rect = lbl_irr.get_rect(centerx=w // 2, bottom=bar_y - 4)
    superficie.blit(lbl_irr, lbl_rect)

    # Widgets de energía
    dibujar_widget(superficie, start_x_sec2, 35, "POTENCIA (W)", f"{potencia:.1f}", COLOR_ACCENT, w_box)
    dibujar_widget(superficie, start_x_sec2 + w_box + gap, 35, "ENERGÍA (Wh)", f"{energia:.1f}", COLOR_SUCCESS, w_box)

    # ================= SECCIÓN 3: TELEMETRÍA (Derecha) =================
    # Alineado a la derecha
    start_x_sec3 = w - (w_box * 3 + gap * 2) - 20

    # Colores dinámicos para el error
    col_err = COLOR_SUCCESS if abs(error) < 2 else (COLOR_ACCENT if abs(error) < 10 else COLOR_DANGER)

    dibujar_widget(superficie, start_x_sec3, 35, "ERROR (°)", f"{error:.2f}", col_err, w_box)
    dibujar_widget(superficie, start_x_sec3 + w_box + gap, 35, "ÁNGULO PANEL", f"{angulo:.1f}", COLOR_TEXT_H1, w_box)
    dibujar_widget(superficie, start_x_sec3 + (w_box + gap) * 2, 35, "VEL. MOTOR", f"{vel_ang:.1f}", COLOR_TEXT_H2,
                   w_box)

    # Teclas de ayuda rápida (pie del HUD)
    ayuda = "[T] Auto/Man  [R] Reset Sol  [G] Viento  [M] Realismo  [C] Debug"
    txt_ayuda = fuente_ui.render(ayuda, True, (100, 110, 120))
    # Centrar ayuda en la parte inferior del HUD
    rect_ayuda = txt_ayuda.get_rect(centerx=w // 2, bottom=alto_hud - 6)
    superficie.blit(txt_ayuda, rect_ayuda)


def dibujar_barra_error(superficie, error_deg, base_panel):
    e = min(abs(error_deg), 30)
    calidad = 1.0 - (e / 30.0)

    bar_w, bar_h = 120, 10
    bar_x = base_panel[0] - bar_w // 2
    bar_y = base_panel[1] + 25

    pygame.draw.rect(superficie, (40, 40, 40), (bar_x, bar_y, bar_w, bar_h))
    r = int(255 * (1.0 - calidad))
    g = int(255 * calidad)
    color = (r, g, 0)
    pygame.draw.rect(superficie, color, (bar_x, bar_y, int(bar_w * calidad), bar_h))


def dibujar_debug_control(superficie, p_term, i_term, d_term, vel_obj, vel_ang, error, en_banda_muerta):
    w, h = tam_viewport()
    box_w, box_h = 260, 110
    box_x, box_y = 20, h - box_h - 20

    panel = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
    panel.fill((0, 0, 0, 180))
    superficie.blit(panel, (box_x, box_y))

    titulo = fuente.render("DEBUG CONTROL (PID)", True, COLOR_TEXTO)
    superficie.blit(titulo, (box_x + 8, box_y + 5))

    e_txt = fuente.render(f"Error: {error:5.1f}°  BandaMuerta: {'SI' if en_banda_muerta else 'NO'}", True, COLOR_TEXTO)
    superficie.blit(e_txt, (box_x + 8, box_y + 25))

    p_txt = fuente.render(f"P={p_term:6.2f}  I={i_term:6.2f}  D={d_term:6.2f}", True, COLOR_TEXTO)
    superficie.blit(p_txt, (box_x + 8, box_y + 45))

    bar_w, bar_h = box_w - 40, 8
    bar_x = box_x + 20
    cmd_y = box_y + 70
    act_y = box_y + 90

    pygame.draw.rect(superficie, (60, 60, 60), (bar_x, cmd_y, bar_w, bar_h))
    pygame.draw.rect(superficie, (60, 60, 60), (bar_x, act_y, bar_w, bar_h))

    def draw_signed_bar(center_x, y, width, height, value, max_abs, color):
        if max_abs <= 0:
            return
        v = limitar(value / max_abs, -1.0, 1.0)
        half = width // 2
        if abs(v) < 1e-3:
            return
        length = int(half * abs(v))
        if v > 0:
            rect = (center_x, y, length, height)
        else:
            rect = (center_x - length, y, length, height)
        pygame.draw.rect(superficie, color, rect)

    center_x = bar_x + bar_w // 2
    draw_signed_bar(center_x, cmd_y, bar_w, bar_h, vel_obj, VEL_MAX_DEG_PER_SEC, (200, 200, 0))
    draw_signed_bar(center_x, act_y, bar_w, bar_h, vel_ang, VEL_MAX_DEG_PER_SEC, (0, 200, 255))

    lab_cmd = fuente.render("Cmd", True, COLOR_TEXTO)
    lab_act = fuente.render("Act", True, COLOR_TEXTO)
    superficie.blit(lab_cmd, (bar_x - 30, cmd_y - 2))
    superficie.blit(lab_act, (bar_x - 30, act_y - 2))


def menu():
    seleccion = None
    reloj_menu = pygame.time.Clock()

    opciones = [
        ("1", "monocristalino", "Monocristalino", "Alta eficiencia, alto costo."),
        ("2", "policristalino", "Policristalino", "Balance costo/beneficio."),
        ("3", "pelicula", "Película Delgada", "Flexible, baja eficiencia."),
        ("4", "vertical", "Panel Vertical", "Configuración estándar.")
    ]

    while True:
        pantalla.fill((10, 15, 20))  # Fondo muy oscuro
        w, h = tam_viewport()

        # Título
        titulo = fuente_grande.render("SISTEMA DE SEGUIMIENTO SOLAR", True, COLOR_UI_BORDER)
        subtitulo = fuente_ui.render("Seleccione el tipo de tecnología fotovoltaica para iniciar", True, COLOR_TEXT_H2)

        pantalla.blit(titulo, (w // 2 - titulo.get_width() // 2, 80))
        pantalla.blit(subtitulo, (w // 2 - subtitulo.get_width() // 2, 120))

        # Dibujar Tarjetas de opciones
        card_w, card_h = 500, 80
        start_y = 180
        mouse_pos = pygame.mouse.get_pos()

        for idx, key, nombre, desc in opciones:
            rect_card = pygame.Rect(w // 2 - card_w // 2, start_y, card_w, card_h)
            hover = rect_card.collidepoint(mouse_pos)

            # Color dinámico si el mouse está encima
            bg_color = (30, 40, 50, 200) if not hover else (40, 60, 80, 200)
            border_col = COLOR_UI_BORDER if not hover else COLOR_ACCENT

            # Dibujar fondo tarjeta
            dibujar_caja_ui(pantalla, rect_card.x, rect_card.y, rect_card.w, rect_card.h, bg_color, False)
            pygame.draw.rect(pantalla, border_col, rect_card, 2 if not hover else 3, border_radius=8)

            # Texto Key [1]
            txt_key = fuente_grande.render(f"[{idx}]", True, border_col)
            pantalla.blit(txt_key, (rect_card.x + 20, rect_card.y + 25))

            # Nombre y Detalle
            txt_nom = fuente_grande.render(nombre, True, COLOR_TEXT_H1)
            txt_desc = fuente_ui.render(desc, True, COLOR_TEXT_H2)

            pantalla.blit(txt_nom, (rect_card.x + 90, rect_card.y + 15))
            pantalla.blit(txt_desc, (rect_card.x + 90, rect_card.y + 45))

            start_y += card_h + 15

        # Footer
        footer = fuente_ui.render("Presione la tecla [F] para Pantalla Completa | [ESC] Salir", True, (100, 100, 100))
        pantalla.blit(footer, (w // 2 - footer.get_width() // 2, h - 40))

        pygame.display.flip()

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit();
                exit()
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_1:
                    return "monocristalino"
                elif evento.key == pygame.K_2:
                    return "policristalino"
                elif evento.key == pygame.K_3:
                    return "pelicula"
                elif evento.key == pygame.K_4:
                    return "vertical"
                elif evento.key == pygame.K_ESCAPE:
                    pygame.quit(); exit()
                elif evento.key == pygame.K_f:
                    toggle_fullscreen()

        reloj_menu.tick(30)


def calcular_cobertura_nubes(sol_x, sol_y, nubes):
    cobertura = 0.0
    for c in nubes:
        dx = sol_x - c['x']
        dy = sol_y - c['y']
        rx = max(1.0, c['w'] / 2.0)
        ry = max(1.0, c['h'] / 2.0)
        nd = math.hypot(dx / rx, dy / ry)
        if nd <= 1.0:
            contrib = 1.0
        elif nd <= 2.0:
            contrib = max(0.0, 1.0 - (nd - 1.0))
        else:
            contrib = 0.0
        cobertura += contrib * 0.8
    return limitar(cobertura, 0.0, 1.0)


def regenerar_nubes(w, h, clima_info):
    nubes = []
    prob_factor = clima_info.get('prob_nube', 0.0)
    cloud_factor = 1.0 + (prob_factor * 3)
    num_nubes = int(4 * cloud_factor)

    for _ in range(num_nubes):
        nubes.append({
            'x': random.randint(0, w),
            'y': random.randint(80, 200),
            'w': random.randint(80, 200),
            'h': random.randint(40, 100),
            'speed': random.randint(clima_info['vel_nube_min'], clima_info['vel_nube_max']),
        })
    return nubes


def principal():
    global RAFAGA_VIENTO_ON, MODO_REALISTA, SHOW_DEBUG_CONTROL

    tipo_panel = menu()
    if not tipo_panel:
        return

    modo_clima = "soleado"
    clima_info = MODOS_CLIMATICOS[modo_clima]

    w_start, h_start = tam_viewport()
    nubes = regenerar_nubes(w_start, h_start, clima_info)

    sol_x, sol_y = posicion_aleatoria(tipo_panel)
    tiempo_sol = pygame.time.get_ticks()
    guardar_posicion(sol_x, sol_y)

    angulo_panel = 0.0
    seguimiento_continuo = True
    vel_ang = 0.0
    en_banda_muerta = False
    ejecutando = True
    iluminacion_actual = 0.0
    pid_integral = 0.0
    pid_prev_error = 0.0
    pid_integral_limit = 50.0
    energia_acumulada_Wh = 0.0

    p_term = 0.0
    i_term = 0.0
    d_term = 0.0
    vel_obj = 0.0

    botones_clima = []

    clima_x = w_start - 260
    clima_y = 140

    rect_clima = pygame.Rect(clima_x, clima_y, 240, 210)  # Rect inicial temporal
    arrastrando_clima = False
    offset_drag_x = 0
    offset_drag_y = 0
    ultimo_modo_clima = modo_clima

    while ejecutando:
        dt = reloj.tick(60)
        dt_seg = dt / 1000.0
        ahora = pygame.time.get_ticks()
        w, h = tam_viewport()

        clima_info = MODOS_CLIMATICOS[modo_clima]
        cobertura = calcular_cobertura_nubes(sol_x, sol_y, nubes)

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                ejecutando = False
            elif evento.type == pygame.VIDEORESIZE:
                pass
            elif evento.type == pygame.MOUSEBUTTONDOWN:
                if evento.button == 1:
                    mouse_pos = evento.pos
                    click_en_boton = False

                    for boton in botones_clima:
                        if boton["rect"].collidepoint(mouse_pos):
                            modo_clima = boton["key"]
                            pid_integral = 0.0
                            pid_prev_error = 0.0
                            print(f"Modo climático cambiado a: {modo_clima}")
                            click_en_boton = True
                            break
                    if not click_en_boton:
                        if rect_clima.collidepoint(mouse_pos):
                            arrastrando_clima = True
                            # Calcular la diferencia entre el mouse y la esquina del panel
                            offset_drag_x = clima_x - mouse_pos[0]
                            offset_drag_y = clima_y - mouse_pos[1]
            elif evento.type == pygame.MOUSEBUTTONUP:
                if evento.button == 1:
                    arrastrando_clima = False

            elif evento.type == pygame.MOUSEMOTION:
                if arrastrando_clima:
                    # Actualizar posición del panel
                    clima_x = evento.pos[0] + offset_drag_x
                    clima_y = evento.pos[1] + offset_drag_y

            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    ejecutando = False
                if evento.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4]:
                    idx = evento.key - pygame.K_1
                    for key, info in MODOS_CLIMATICOS.items():
                        if info['idx'] == idx:
                            modo_clima = key
                            pid_integral = 0.0
                            pid_prev_error = 0.0
                            print(f"Modo climático cambiado a: {modo_clima}")
                            break
                elif evento.key == pygame.K_r:
                    sol_x, sol_y = posicion_aleatoria(tipo_panel)
                    tiempo_sol = ahora
                    guardar_posicion(sol_x, sol_y)
                elif evento.key == pygame.K_f:
                    toggle_fullscreen()
                elif evento.key == pygame.K_t:
                    seguimiento_continuo = not seguimiento_continuo
                elif evento.key == pygame.K_g:
                    RAFAGA_VIENTO_ON = not RAFAGA_VIENTO_ON
                elif evento.key == pygame.K_m:
                    MODO_REALISTA = not MODO_REALISTA
                elif evento.key == pygame.K_c:
                    SHOW_DEBUG_CONTROL = not SHOW_DEBUG_CONTRO

        if modo_clima != ultimo_modo_clima:
            clima_info = MODOS_CLIMATICOS[modo_clima]
            nubes = regenerar_nubes(w, h, clima_info)
            ultimo_modo_clima = modo_clima

        for cloud in nubes:
            cloud['x'] -= cloud['speed'] * dt_seg

            if cloud['x'] + cloud['w'] < 0:
                cloud['x'] = w + random.randint(50, 200)
                cloud['y'] = random.randint(80, 150)
                cloud['w'] = random.randint(80, 150)
                cloud['h'] = random.randint(40, 60)
                cloud['speed'] = random.randint(clima_info['vel_nube_min'], clima_info['vel_nube_max'])

        if ahora - tiempo_sol >= INTERVALO_MS:
            sol_x, sol_y = posicion_aleatoria(tipo_panel)
            tiempo_sol = ahora
            guardar_posicion(sol_x, sol_y)
            print(f"[{time.strftime('%H:%M:%S')}] Nuevo sol en: ({sol_x}, {sol_y})")

        base_panel = (w // 2, h - 100)

        teclas = pygame.key.get_pressed()
        if teclas[pygame.K_q]:
            angulo_panel = limitar(angulo_panel + 1.5, ANG_MIN, ANG_MAX)
        if teclas[pygame.K_e]:
            angulo_panel = limitar(angulo_panel - 1.5, ANG_MIN, ANG_MAX)

        punta_x_temp = base_panel[0]
        punta_y_temp = base_panel[1] - 100
        ang_objetivo = angulo_hacia_punto(punta_x_temp, punta_y_temp, sol_x, sol_y)
        error = normalizar_angulo_deg(ang_objetivo - angulo_panel)

        # Reinicio visual de términos si no hay seguimiento
        if not seguimiento_continuo:
            vel_obj = 0.0
            p_term = i_term = d_term = 0.0

        if seguimiento_continuo:
            if dt_seg <= 0:
                dt_seg = 1e-6

            if MODO_REALISTA:
                if en_banda_muerta:
                    if abs(error) > (BANDA_MUERTA_DEG + HISTERESIS_DEG):
                        en_banda_muerta = False
                else:
                    if abs(error) <= BANDA_MUERTA_DEG:
                        en_banda_muerta = True

                if en_banda_muerta:
                    vel_obj = 0.0
                    p_term = 0.0
                    i_term = 0.0
                    d_term = 0.0
                else:
                    pid_integral += error * dt_seg
                    pid_integral = limitar(pid_integral, -pid_integral_limit, pid_integral_limit)
                    derivada = (error - pid_prev_error) / dt_seg
                    pid_prev_error = error

                    p_term = Kp * error
                    i_term = Ki * pid_integral
                    d_term = Kd * derivada
                    salida_pid = p_term + i_term + d_term


                    vel_obj = limitar(
                        salida_pid * (VEL_MAX_DEG_PER_SEC / max(VEL_MAX, 1e-6)),
                        -VEL_MAX_DEG_PER_SEC,
                        VEL_MAX_DEG_PER_SEC
                    )

                acc = limitar(
                    vel_obj - vel_ang,
                    -ACC_MAX_DEG_PER_SEC2 * dt_seg,
                    ACC_MAX_DEG_PER_SEC2 * dt_seg
                )

                if RAFAGA_VIENTO_ON and random.random() < 0.1:
                    acc += random.gauss(0.0, 15.0) * dt_seg

                vel_ang = (vel_ang * max(0.0, 1.0 - FRICCION_ZETA * dt_seg)) + acc
                vel_ang = limitar(vel_ang, -VEL_MAX_DEG_PER_SEC, VEL_MAX_DEG_PER_SEC)

                angulo_panel += vel_ang * dt_seg
                if angulo_panel < ANG_MIN:
                    angulo_panel = ANG_MIN
                    vel_ang = 0.0
                elif angulo_panel > ANG_MAX:
                    angulo_panel = ANG_MAX
                    vel_ang = 0.0
            else:
                pid_integral += error * dt_seg
                pid_integral = limitar(pid_integral, -pid_integral_limit, pid_integral_limit)
                derivada = (error - pid_prev_error) / dt_seg
                pid_prev_error = error

                p_term = Kp * error
                i_term = Ki * pid_integral
                d_term = Kd * derivada
                salida_pid = p_term + i_term + d_term

                salida_pid_clamped = limitar(salida_pid, -VEL_MAX, VEL_MAX)
                angulo_panel = limitar(angulo_panel + salida_pid_clamped * SMOOTH, ANG_MIN, ANG_MAX)

        punta_x, punta_y, panel_info = dibujar_panel(pantalla, base_panel[0], base_panel[1], angulo_panel, tipo_panel)
        area_panel_sim = panel_info.get("area_m2", 1.5)

        dxs = sol_x - punta_x
        dys = sol_y - punta_y
        dist = math.hypot(dxs, dys)
        if dist == 0:
            dist = 0.0001
        dir_sol_x = dxs / dist
        dir_sol_y = dys / dist

        nvx, nvy = vector_desde_angulo(angulo_panel, 1)
        nlen = math.hypot(nvx, nvy)
        if nlen == 0:
            nlen = 0.0001
        nvx /= nlen
        nvy /= nlen

        cosi = nvx * dir_sol_x + nvy * dir_sol_y
        if cosi < 0:
            cosi = 0.0

        atenuacion = 1.0 / (1.0 + (dist / 400.0) ** 2)
        cobertura = calcular_cobertura_nubes(sol_x, sol_y, nubes)

        factor_clima_base = clima_info.get("coef_ilum", 1.0)
        iluminacion_normalizada = limitar(cosi * atenuacion * (1.0 - cobertura) * factor_clima_base, 0.0, 1.0)

        radiacion_maxima = 1000.0
        radiacion_efectiva = radiacion_maxima * iluminacion_normalizada
        eficiencia_base = panel_info.get("eficiencia_base", 0.18)
        coef_difuso = panel_info.get("coef_difuso", 1.0)
        coef_angulo = panel_info.get("coef_angulo", 1.3)
        variacion = panel_info.get("variacion", 1.0) * (0.95 + 0.1 * random.random())
        factor_angulo = (cosi ** coef_angulo) if cosi > 0 else 0.0
        factor_difuso = (1.0 - cobertura) + cobertura * coef_difuso

        potencia = radiacion_efectiva * area_panel_sim * eficiencia_base * variacion * factor_angulo * factor_difuso
        potencia = max(0.0, potencia)
        energia_acumulada_Wh += potencia * dt_seg / 3600.0
        iluminacion_actual = iluminacion_normalizada

        dibujar_fondo(pantalla, w, h, clima_info, cobertura)
        dibujar_nubes(pantalla, nubes, sol_x, sol_y, clima_info)
        dibujar_margen(pantalla)
        dibujar_brillo(pantalla, (sol_x, sol_y), RADIO_SOL, RADIO_BRILLO, clima_info.get("coef_ilum", 1.0))
        punta_x, punta_y, _ = dibujar_panel(pantalla, base_panel[0], base_panel[1], angulo_panel, tipo_panel)
        dibujar_lineas_imaginarias(pantalla, punta_x, punta_y, sol_x, sol_y, angulo_panel, error, en_banda_muerta)
        dibujar_barra_error(pantalla, error, base_panel)

        eficacia = 0.0
        if radiacion_maxima * area_panel_sim > 0:
            eficacia = potencia / (radiacion_maxima * area_panel_sim)

        hud(
            pantalla,
            "",  # Texto ignorado
            iluminacion_normalizada,
            seguimiento_continuo,
            potencia,
            energia_acumulada_Wh,
            error,
            angulo_panel,
            vel_ang,
            MODO_REALISTA,
            RAFAGA_VIENTO_ON
        )

        rect_clima, botones_clima = dibujar_panel_clima(pantalla, clima_x, clima_y, modo_clima)

        if SHOW_DEBUG_CONTROL:
            dibujar_debug_control(pantalla, p_term, i_term, d_term, vel_obj, vel_ang, error, en_banda_muerta)

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

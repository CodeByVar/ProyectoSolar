import pygame
import random
import time
import json
import os
import math

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


def dibujar_panel_clima(superficie, modo_clima_actual):
    w, h = tam_viewport()
    panel_x = w - PANEL_W - 10
    panel_y = 40
    panel_h = 240

    panel_surf = pygame.Surface((PANEL_W, panel_h), pygame.SRCALPHA)
    panel_surf.fill(COLOR_PANEL_BG)
    superficie.blit(panel_surf, (panel_x, panel_y))

    titulo = fuente.render("MODO CLIMÁTICO", True, COLOR_TEXTO)
    superficie.blit(titulo, (panel_x + PANEL_W // 2 - titulo.get_width() // 2, panel_y + 10))

    y_start = panel_y + 40
    botones = []

    for key, info in MODOS_CLIMATICOS.items():
        es_activo = (key == modo_clima_actual)
        color_btn = COLOR_BOTON_ACTIVO if es_activo else COLOR_BOTON_INACTIVO

        btn_h = 30
        btn_w_pad = PANEL_W - 20
        btn_rect = pygame.Rect(panel_x + 10, y_start, btn_w_pad, btn_h)

        pygame.draw.rect(superficie, color_btn, btn_rect, border_radius=5)
        texto_btn = fuente.render(f"[{info['idx'] + 1}] {key.replace('_', ' ').title()}", True, COLOR_TEXTO)
        superficie.blit(texto_btn, (btn_rect.x + 8, btn_rect.y + 7))

        botones.append({"key": key, "rect": btn_rect})
        y_start += btn_h + 8

    return botones


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


def hud(superficie, texto_linea, iluminacion_normalizada, seguimiento_continuo):
    w, _ = tam_viewport()
    barra = pygame.Surface((w, 28), pygame.SRCALPHA)
    barra.fill(COLOR_HUD_BG)
    superficie.blit(barra, (0, 0))
    surf_txt = fuente.render(texto_linea, True, COLOR_TEXTO)
    superficie.blit(surf_txt, (8, 5))

    modo_texto = "AUTO" if seguimiento_continuo else "MANUAL"
    modo_color = (0, 200, 0) if seguimiento_continuo else (200, 60, 60)
    modo_surf = fuente.render(modo_texto, True, (0, 0, 0))
    box_w, box_h = 80, 22
    box_x, box_y = 10, 30
    pygame.draw.rect(superficie, modo_color, (box_x, box_y, box_w, box_h), border_radius=5)
    superficie.blit(modo_surf, (box_x + 10, box_y + 3))

    dibujar_barra_iluminacion(superficie, iluminacion_normalizada)


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
    while True:
        pantalla.fill(COLOR_BG)
        w, h = tam_viewport()
        titulo = fuente.render("Selecciona el tipo de panel solar:", True, (255, 255, 255))
        t1 = fuente.render("[1] Monocristalino (Alta Ef.)", True, (200, 220, 255))
        t2 = fuente.render("[2] Policristalino (Media Ef.)", True, (200, 220, 255))
        t3 = fuente.render("[3] Película Delgada (Baja Ef.)", True, (200, 220, 255))
        t4 = fuente.render("[4] Panel Vertical (Default)", True, (200, 220, 255))
        pantalla.blit(titulo, (w // 2 - titulo.get_width() // 2, h // 2 - 90))
        pantalla.blit(t1, (w // 2 - t1.get_width() // 2, h // 2 - 40))
        pantalla.blit(t2, (w // 2 - t2.get_width() // 2, h // 2))
        pantalla.blit(t3, (w // 2 - t3.get_width() // 2, h // 2 + 40))
        pantalla.blit(t4, (w // 2 - t4.get_width() // 2, h // 2 + 80))
        pygame.display.flip()
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif evento.type == pygame.K_ESCAPE:
                pygame.quit()
                exit()
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
                    seleccion = "vertical"
                elif evento.key == pygame.K_f:
                    toggle_fullscreen()
        if seleccion:
            return seleccion


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

    # --- NUEVO: términos del control para debug ---
    p_term = 0.0
    i_term = 0.0
    d_term = 0.0
    vel_obj = 0.0

    botones_clima = []
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
                    for boton in botones_clima:
                        if boton["rect"].collidepoint(mouse_pos):
                            modo_clima = boton["key"]
                            pid_integral = 0.0
                            pid_prev_error = 0.0
                            print(f"Modo climático cambiado a: {modo_clima}")
                            break
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
                # --- NUEVO: toggle modo realista y panel debug ---
                elif evento.key == pygame.K_m:
                    MODO_REALISTA = not MODO_REALISTA
                elif evento.key == pygame.K_c:
                    SHOW_DEBUG_CONTROL = not SHOW_DEBUG_CONTROL
                # --- FIN NUEVO ---

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

                    # --- NUEVO: desglosar PID para mostrarlo ---
                    p_term = Kp * error
                    i_term = Ki * pid_integral
                    d_term = Kd * derivada
                    salida_pid = p_term + i_term + d_term
                    # --- FIN NUEVO ---

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

        hud_txt = (
            f"Tipo: {tipo_panel.capitalize()} | Clima: {modo_clima.replace('_', ' ').title()} | Seguimiento: {'ON' if seguimiento_continuo else 'OFF'} | "
            f"Potencia: {potencia:.1f} W | Eficacia: {eficacia * 100:4.1f}% | Energia acum: {energia_acumulada_Wh:6.3f} Wh | "
            f"Ilumin: {iluminacion_normalizada * 100:5.1f}% | Error: {int(error):>3}° | Ángulo Panel: {int(angulo_panel):>3}° | "
            f"Vel: {vel_ang:4.1f}°/s | Realista:{'ON' if MODO_REALISTA else 'OFF'} | Viento:{'ON' if RAFAGA_VIENTO_ON else 'OFF'} | "
            f"[T] toggle | [R] sol | [Q/E] manual | [F] full | [G] viento | [M] modo PID | [C] debug"
        )
        hud(pantalla, hud_txt, iluminacion_normalizada, seguimiento_continuo)

        botones_clima = dibujar_panel_clima(pantalla, modo_clima)
        guardar_posicion(sol_x, sol_y, iluminacion_actual)

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

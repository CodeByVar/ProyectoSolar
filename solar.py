import pygame
import random
import time
import json
import os
import math

RADIO_SOL = 18
RADIO_BRILLO = 110
INTERVALO_MS = 8000
MARGEN_PX = 80
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

def guardar_posicion(x, y):
    if not GUARDAR_ARCHIVO:
        return
    datos = {"x": int(x), "y": int(y), "tiempo_ms": int(time.time() * 1000)}
    try:
        with open("posicion_sol.json", "w") as f:
            json.dump(datos, f)
    except Exception as e:
        print("Error al guardar:", e)

def posicion_aleatoria(tipo_panel):
    """
    Genera una posición aleatoria para el sol, **pero asegurándose**
    de que quede por encima del panel solar (en toda la zona superior).
    """
    w, h = viewport_size()
    margen = max(40, MARGEN_PX)
    base_y = h - 100
    largo_palo = 100
    alto_panel = 40 if tipo_panel == "horizontal" else 100
    panel_top = base_y - largo_palo - (alto_panel / 2)
    limite_superior_y = int(panel_top - RADIO_SOL - 8)
    if limite_superior_y <= margen:
        limite_superior_y = margen + 10

    x = random.randint(margen, max(margen, w - margen))
    y = random.randint(margen, limite_superior_y)
    return x, y

def dibujar_brillo(superficie, centro, radio_interno, radio_externo, color=(255, 210, 40)):
    cx, cy = centro
    brillo = pygame.Surface((radio_externo*2, radio_externo*2), pygame.SRCALPHA)
    pasos = 18
    for i in range(pasos, 0, -1):
        r = int(radio_externo * (i / pasos))
        alpha = int(200 * (i / pasos) * 0.6)
        col = (color[0], color[1], color[2], alpha)
        pygame.draw.circle(brillo, col, (radio_externo, radio_externo), r)
    pygame.draw.circle(brillo, (color[0], color[1], color[2], 255), (radio_externo, radio_externo), radio_interno)
    superficie.blit(brillo, (cx - radio_externo, cy - radio_externo))

def dibujar_margen(superficie):
    w, h = viewport_size()
    margen = max(40, MARGEN_PX)
    pygame.draw.rect(superficie, COLOR_MARGEN, (margen, margen, w - 2*margen, h - 2*margen), 1)

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

def dibujar_panel(superficie, base_x, base_y, angulo, tipo):
    largo_palo = 100
    pygame.draw.line(superficie, COLOR_PALO, (base_x, base_y), (base_x, base_y - largo_palo), 8)

    ancho_panel = 120
    alto_panel = 40 if tipo == "horizontal" else 100
    panel_rect = pygame.Surface((ancho_panel, alto_panel), pygame.SRCALPHA)
    panel_rect.fill(COLOR_PANEL)
    panel_rotado = pygame.transform.rotate(panel_rect, angulo)

    pos_panel = (base_x - panel_rotado.get_width() // 2,
                 base_y - largo_palo - panel_rotado.get_height() // 2)
    superficie.blit(panel_rotado, pos_panel)

    return base_x, base_y - largo_palo

def dibujar_lineas_imaginarias(superficie, punta_x, punta_y, sol_x, sol_y, angulo_panel):
    pygame.draw.line(superficie, COLOR_LINEA_SOL, (punta_x, punta_y), (sol_x, sol_y), 2)

    n_dx, n_dy = vector_desde_angulo(angulo_panel, 140)
    pygame.draw.line(superficie, COLOR_NORMAL, (punta_x, punta_y), (punta_x + n_dx, punta_y + n_dy), 2)

    objetivo = angulo_hacia_punto(punta_x, punta_y, sol_x, sol_y)
    nx, ny = (punta_x + n_dx, punta_y + n_dy)
    t_dx, t_dy = vector_desde_angulo(objetivo, 120)
    tx, ty = (punta_x + t_dx, punta_y + t_dy)
    pygame.draw.line(superficie, COLOR_ERROR, (nx, ny), (tx, ty), 2)

def hud(superficie, texto_linea):
    w, _ = viewport_size()
    barra = pygame.Surface((w, 28), pygame.SRCALPHA)
    barra.fill(COLOR_HUD_BG)
    superficie.blit(barra, (0, 0))
    surf_txt = fuente.render(texto_linea, True, COLOR_TEXTO)
    superficie.blit(surf_txt, (8, 5))

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

def menu():
    seleccion = None
    while True:
        pantalla.fill(COLOR_BG)
        w, h = viewport_size()
        titulo = fuente.render("Selecciona el tipo de panel solar:", True, (255, 255, 255))
        t1 = fuente.render("[1] Panel Horizontal", True, (200, 220, 255))
        t2 = fuente.render("[2] Panel Vertical", True, (200, 220, 255))

        pantalla.blit(titulo, (w//2 - titulo.get_width()//2, h//2 - 60))
        pantalla.blit(t1,     (w//2 - t1.get_width()//2,     h//2))
        pantalla.blit(t2,     (w//2 - t2.get_width()//2,     h//2 + 40))
        pygame.display.flip()

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit(); exit()
            elif evento.type == pygame.VIDEORESIZE:
                pass
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_1:
                    seleccion = "horizontal"
                elif evento.key == pygame.K_2:
                    seleccion = "vertical"
                elif evento.key == pygame.K_f:
                    toggle_fullscreen()
        if seleccion:
            return seleccion

def principal():
    tipo_panel = menu()

    sol_x, sol_y = posicion_aleatoria(tipo_panel)
    tiempo_sol = pygame.time.get_ticks()
    guardar_posicion(sol_x, sol_y)

    angulo_panel = 0
    seguimiento_continuo = True

    ejecutando = True
    while ejecutando:
        dt = reloj.tick(60)
        ahora = pygame.time.get_ticks()

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

        if ahora - tiempo_sol >= INTERVALO_MS:
            sol_x, sol_y = posicion_aleatoria(tipo_panel)
            tiempo_sol = ahora
            guardar_posicion(sol_x, sol_y)
            print(f"[{time.strftime('%H:%M:%S')}] Nuevo sol en: ({sol_x}, {sol_y})")

        teclas = pygame.key.get_pressed()
        if teclas[pygame.K_q]:
            angulo_panel = clamp(angulo_panel + 1.5, ANG_MIN, ANG_MAX)
        if teclas[pygame.K_e]:
            angulo_panel = clamp(angulo_panel - 1.5, ANG_MIN, ANG_MAX)

        w, h = viewport_size()
        base_panel = (w // 2, h - 100)
        punta_x, punta_y = base_panel[0], base_panel[1] - 100
        ang_objetivo = angulo_hacia_punto(punta_x, punta_y, sol_x, sol_y)
        error = normalize_angle_deg(ang_objetivo - angulo_panel)
        if seguimiento_continuo:
            delta = clamp(Kp * error, -VEL_MAX, VEL_MAX)
            angulo_panel = clamp(angulo_panel + delta, ANG_MIN, ANG_MAX)

        pantalla.fill(COLOR_BG)
        dibujar_margen(pantalla)
        dibujar_brillo(pantalla, (sol_x, sol_y), RADIO_SOL, RADIO_BRILLO)

        punta_x, punta_y = dibujar_panel(pantalla, base_panel[0], base_panel[1], angulo_panel, tipo_panel)
        dibujar_lineas_imaginarias(pantalla, punta_x, punta_y, sol_x, sol_y, angulo_panel)

        tiempo_restante = max(0, INTERVALO_MS - (ahora - tiempo_sol)) / 1000.0
        hud_txt = (
            f"Tipo:{tipo_panel}  Seguimiento:{'ON' if seguimiento_continuo else 'OFF'}  "
            f"Ángulo:{int(angulo_panel):>3}°  Error:{int(error):>3}°  "
            f"[Q/E] manual  [T] toggle  [R] nuevo sol  [F] fullscreen  "
            f"Tiempo:{tiempo_restante:4.1f}s  Sol:({sol_x},{sol_y})"
        )
        hud(pantalla, hud_txt)

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    if GUARDAR_ARCHIVO and os.path.exists("posicion_sol.json"):
        try:
            os.remove("posicion_sol.json")
        except:
            pass
    principal()
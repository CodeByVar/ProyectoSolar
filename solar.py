import pygame
import random
import time
import json
import os
import math

ANCHO, ALTO = 800, 600
RADIO_SOL = 18
RADIO_BRILLO = 90
INTERVALO_MS = 8000
MARGEN = 80
GUARDAR_ARCHIVO = True

pygame.init()
pantalla = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("Simulación del Sol Aleatorio")
reloj = pygame.time.Clock()
fuente = pygame.font.SysFont(None, 22)

def guardar_posicion(x, y):
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
    x = random.randint(MARGEN, ANCHO - MARGEN)
    y = random.randint(MARGEN, ALTO - MARGEN)
    return x, y

def dibujar_brillo(superficie, centro, radio_interno, radio_externo, color=(255, 210, 40)):
    cx, cy = centro
    brillo = pygame.Surface((radio_externo*2, radio_externo*2), pygame.SRCALPHA)
    pasos = 10
    for i in range(pasos, 0, -1):
        r = int(radio_externo * (i / pasos))
        alpha = int(200 * (i / pasos) * 0.6)
        col = (color[0], color[1], color[2], alpha)
        pygame.draw.circle(brillo, col, (radio_externo, radio_externo), r)
    pygame.draw.circle(brillo, (color[0], color[1], color[2], 255), (radio_externo, radio_externo), radio_interno)
    superficie.blit(brillo, (cx - radio_externo, cy - radio_externo))

def dibujar_panel(superficie, base_x, base_y, angulo, tipo):
    """
    Dibuja un panel solar sostenido por un palo.
    tipo: "horizontal" o "vertical"
    """
    # Altura del palo
    largo_palo = 100
    color_palo = (100, 100, 100)

    # Dibuja palo
    pygame.draw.line(superficie, color_palo, (base_x, base_y), (base_x, base_y - largo_palo), 8)

    # Panel solar
    ancho_panel = 120
    alto_panel = 40 if tipo == "horizontal" else 100

    # Rotar el panel según el ángulo
    panel_rect = pygame.Surface((ancho_panel, alto_panel), pygame.SRCALPHA)
    panel_rect.fill((30, 144, 255))
    panel_rotado = pygame.transform.rotate(panel_rect, angulo)

    # Posición de montaje (extremo del palo)
    pos_panel = (base_x - panel_rotado.get_width() // 2, base_y - largo_palo - panel_rotado.get_height() // 2)
    superficie.blit(panel_rotado, pos_panel)

def menu():
        """Muestra un menú simple para elegir el tipo de panel"""
        pantalla.fill((18, 22, 30))
        titulo = fuente.render("Selecciona el tipo de panel solar:", True, (255, 255, 255))
        pantalla.blit(titulo, (ANCHO // 2 - titulo.get_width() // 2, 200))

        opcion1 = fuente.render("[1] Panel Horizontal", True, (200, 220, 255))
        opcion2 = fuente.render("[2] Panel Vertical", True, (200, 220, 255))
        pantalla.blit(opcion1, (ANCHO // 2 - opcion1.get_width() // 2, 260))
        pantalla.blit(opcion2, (ANCHO // 2 - opcion2.get_width() // 2, 300))
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
                        tipo = "horizontal"
                        esperando = False
                    elif evento.key == pygame.K_2:
                        tipo = "vertical"
                        esperando = False
        return tipo

def principal():
    tipo_panel = menu()
    sol_x, sol_y = posicion_aleatoria()
    tiempo_sol = pygame.time.get_ticks()
    guardar_posicion(sol_x, sol_y)
    angulo_panel = 0  # Grado inicial del panel
    base_panel = (ANCHO // 2, ALTO - 100)

    ejecutando = True
    while ejecutando:
        dt = reloj.tick(60)
        ahora = pygame.time.get_ticks()

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                ejecutando = False

        if ahora - tiempo_sol >= INTERVALO_MS:
            sol_x, sol_y = posicion_aleatoria()
            tiempo_sol = ahora
            guardar_posicion(sol_x, sol_y)
            print(f"[{time.strftime('%H:%M:%S')}] Nuevo sol en: ({sol_x}, {sol_y})")

        pantalla.fill((18, 22, 30))
        dibujar_brillo(pantalla, (sol_x, sol_y), RADIO_SOL, RADIO_BRILLO)

        tiempo_restante = max(0, INTERVALO_MS - (ahora - tiempo_sol))
        tiempo_s = tiempo_restante / 1000.0
        texto = f"Tiempo restante: {tiempo_s:.1f}s   Posición sol: ({sol_x},{sol_y})"
        texto_superficie = fuente.render(texto, True, (230, 230, 230))
        pantalla.blit(texto_superficie, (10, ALTO - 30))

        dibujar_panel(pantalla, base_panel[0], base_panel[1], angulo_panel, tipo_panel)

        # === CONTROL MANUAL DEL PANEL CON Q Y E ===
        teclas = pygame.key.get_pressed()
        if teclas[pygame.K_q]:
            angulo_panel += 1
        if teclas[pygame.K_e]:
            angulo_panel -= 1

        # === TEXTO DE INFORMACIÓN ===
        texto = f"Tipo: {tipo_panel} | Ángulo: {angulo_panel}° | Q/E: rotar panel | Tiempo: {tiempo_s:.1f}s | Sol: ({sol_x},{sol_y})"
        texto_superficie = fuente.render(texto, True, (230, 230, 230))
        pantalla.blit(texto_superficie, (10, ALTO - 30))

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

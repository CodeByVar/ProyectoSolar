import pygame
import random
import time
import json
import os

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
fuente = pygame.font.SysFont(None, 20)

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

def principal():
    sol_x, sol_y = posicion_aleatoria()
    tiempo_sol = pygame.time.get_ticks()
    guardar_posicion(sol_x, sol_y)
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

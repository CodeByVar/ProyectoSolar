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
# Datos de cada tipo de panel solar
TIPOS_PANELES = {
    "monocristalino": {
        "color": (0, 0, 0),
        "eficiencia": 0.22,
        "descripcion": "Alta eficiencia, panel negro sólido.",
        "detalle": "Convierte más energía, ideal para espacio limitado."
    },
    "policristalino": {
        "color": (30, 144, 255),
        "eficiencia": 0.17,
        "descripcion": "Eficiencia media, azul metalizado.",
        "detalle": "Más económico, menor rendimiento térmico."
    },
    "pelicula": {
        "color": (100, 100, 100),
        "eficiencia": 0.12,
        "descripcion": "Baja eficiencia, gris oscuro.",
        "detalle": "Flexible, buen rendimiento con luz difusa."
    }
}


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
    panel_rect = pygame.Surface((ancho_panel, alto_panel), pygame.SRCALPHA)
    panel_rect.fill(color_panel)
    panel_rotado = pygame.transform.rotate(panel_rect, angulo)

    pos_panel = (base_x - panel_rotado.get_width() // 2, base_y - largo_palo - panel_rotado.get_height() // 2)
    superficie.blit(panel_rotado, pos_panel)

    return info


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


def menu():
    """Muestra un menú simple para elegir el tipo de panel"""
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
def principal():
    tipo_panel = menu()
    sol_x, sol_y = posicion_aleatoria()
    tiempo_sol = pygame.time.get_ticks()
    guardar_posicion(sol_x, sol_y)
    angulo_panel = 0
    base_panel = (ANCHO // 2, ALTO - 100)
    area_panel = 1.5  # m²

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

        # Control manual del panel
        teclas = pygame.key.get_pressed()
        if teclas[pygame.K_q]:
            angulo_panel += 1
        if teclas[pygame.K_e]:
            angulo_panel -= 1

        # Dibuja el panel y obtiene su info
        info = dibujar_panel_tipo(pantalla, base_panel[0], base_panel[1], angulo_panel, tipo_panel)

        # Simulación simple de energía generada
        radiacion = 800  # W/m² (valor constante para la demo)
        potencia = radiacion * area_panel * info["eficiencia"]

        # Mostrar información del panel
        info_texto = [
            f"Tipo: {tipo_panel.capitalize()}",
            f"Eficiencia: {info['eficiencia']*100:.1f}%",
            f"Potencia estimada: {potencia:.1f} W",
            f"Ángulo actual: {angulo_panel}°",
            f"Descripción: {info['descripcion']}"
        ]
        for i, texto in enumerate(info_texto):
            linea = fuente.render(texto, True, (240, 240, 240))
            pantalla.blit(linea, (10, 10 + i * 22))

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
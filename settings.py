import pygame
from os.path import join
from map import load_map_tmx

WINDOW_WIDTH, WINDOW_HEIGHT = 1280, 720
FRAMERATE = 60
TILE_SIZE = 96
ANGLES = 360
MENU_BG_COLOR = "white"
HEALTH_BAR_COLOR = "#ed252a"
LIGHT_BLACK = "#1c1c1c"

# Precompute missile rotations
def precompute_missile_rotations():
    original_image = pygame.Surface((25, 25), pygame.SRCALPHA)
    pygame.draw.polygon(original_image, '#edb3bf', [(0, 0), (22, 12.5), (0, 25)])
    rotations = {}
    for angle in range(ANGLES):
        rotated_image = pygame.transform.rotate(original_image, angle)
        rotations[angle] = rotated_image
    return rotations
precomputed_missile_rotations = precompute_missile_rotations()

# Map
tile_grid = load_map_tmx('data/map.tmx')

# Stats
gun_w, gun_h = 30, 15
shop_w , shop_h = 760, 430
enemy_spawn_distance = 1000
enemy_value = 10

player_stats = {
    'player_w': 50,
    'player_h': 50,
    'player_radius': 25,
    'walk_spd': 250,  # default is 250
}

enemy_type = {
    'Fast':   {'spd': 250, 'radius': 15, 'mask_time': 150, 'max_hp': 1, 'color': '#b1c983'},
    'Normal': {'spd': 170, 'radius': 35, 'mask_time': 200, 'max_hp': 4, 'color': '#f3c567'},
    'Tank':   {'spd': 70, 'radius': 60, 'mask_time': 250, 'max_hp': 16, 'color': '#dd984b'},
}

boss_stats = {
    'spd' : 50,
    'radius' : 100,
    'mask time' : 500,
    'max HP' : 500,
    'color' : '#6a5b86',
}
    

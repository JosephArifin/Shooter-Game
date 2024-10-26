import pygame.freetype
from settings import *
from math import cos, sin, radians

def cast_rays(player_pos, camera_offset, map):
    rays = []

    # Cast rays in 360 degrees
    for angle in range(0, 360, 10):
        
        radian = radians(angle)
        ray_x = cos(radian)
        ray_y = sin(radian)

        # Initialize ray position at player's position
        dx, dy = player_pos[0], player_pos[1]
        
        while True:
            dx += ray_x
            dy += ray_y

            # calculate tile position the ray is currently in
            map_x = int(dy // TILE_SIZE)
            map_y = int(dx // TILE_SIZE)

            # check collision with a wall
            if map[map_x][map_y] == 1:
                # adjust the ray end position according to the camera offset
                adjusted_ray_end = pygame.Vector2(dx, dy) + camera_offset
                
                # add ray to list
                rays.append(adjusted_ray_end)
                break
    return rays

def draw_visibility_polygon(screen, rays):
    # Create a transparent surface to darken the rest of the screen
    darkness_surface = pygame.Surface((screen.get_size()), pygame.SRCALPHA)
    darkness_surface.fill((0, 0, 0, 150))

    # Draw the visibility polygon (everything visible to the player)
    pygame.draw.polygon(darkness_surface, (0, 0, 0, 0), rays)

    vision_mask = pygame.mask.from_surface(darkness_surface)

    # blit the surface onto the screen
    screen.blit(darkness_surface, (0,0))
    return vision_mask
    



import pygame.freetype
from settings import *

class EnemySpawnRect(pygame.sprite.Sprite):
    def __init__(self, groups, player):
        super().__init__(groups)
        self.player = player
        
        self.image = pygame.Surface((1536,1536), pygame.SRCALPHA)
        self.image.fill((0,0,0,0))
        self.rect = self.image.get_frect(center = self.player.rect.center)

    def update(self, dt):
        self.rect.center = self.player.rect.center
    
class BossRoom(pygame.sprite.Sprite):
    def __init__(self, groups, pos):
        super().__init__(groups)
        self.image = pygame.Surface((2 * TILE_SIZE, 2 * TILE_SIZE), pygame.SRCALPHA)
        self.image.fill((0,0,0,0))
        self.rect = self.image.get_frect(topleft = pos)

class SafeZone(pygame.sprite.Sprite):
    def __init__(self, groups, pos):
        super().__init__(groups)
        self.image = pygame.Surface((10 * TILE_SIZE, 10 * TILE_SIZE), pygame.SRCALPHA)
        self.image.fill((0,0,0,0))
        self.rect = self.image.get_frect(topleft = pos)

class PlayerVisionRect(pygame.sprite.Sprite):
    def __init__(self, groups, player):
        super().__init__(groups)
        self.player = player
        self.image = pygame.Surface((1300, 770), pygame.SRCALPHA)
        self.rect = self.image.get_frect(center = player.rect.center)

    def update(self, dt):
        self.rect.center = self.player.rect.center


    


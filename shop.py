from settings import *

class Shop(pygame.sprite.Sprite):
    def __init__(self, groups, pos, surf):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_frect(topleft = pos)

class ShopUI(pygame.sprite.Sprite):
    def __init__(self, groups, pos):
        super().__init__(groups)
        
        self.image = pygame.Surface((400,200))
        pygame.draw.rect(self.image, '#E8B18A', pygame.FRect(0, 0, 400, 200))
        self.rect = self.image.get_frect(center = pos)
        
class ShopText(pygame.sprite.Sprite):
    def __init__(self, groups, pos, font, text):
        super().__init__(groups)
        self.image = font.render(text, False, LIGHT_BLACK)
        self.rect = self.image.get_frect(center = pos)

class Button(pygame.sprite.Sprite):
    def __init__(self, groups, pos): 
        super().__init__(groups)
        self.image = pygame.Surface((40,20))
        pygame.draw.rect(self.image, '#cd6157', pygame.FRect(0,0,40,20),0,4)
        self.rect = self.image.get_frect(center = pos)
        self.image.set_colorkey('black')

class StatBar(pygame.sprite.Sprite):
    def __init__(self, groups, pos, value=0):
        super().__init__(groups)
        self.image = pygame.Surface((20, 100))
        pygame.draw.rect(self.image, "#727272", pygame.FRect(0, 0, 20, 100))
        self.rect = self.image.get_frect(center=pos)

        self.value = value
        self.max_stat = 5

    def update_stat_bar(self, value):
        # Update stat value
        self.value = value
        if self.value > self.max_stat:
            self.value = self.max_stat  # Prevent exceeding max_stat
        
        # Clear the stat bar first
        pygame.draw.rect(self.image, "#727272", pygame.FRect(0, 0, 20, 100))

        # Calculate height of the green progress bar based on value
        ratio = self.image.height / self.max_stat
        progress_height = self.value * ratio
        
        # Draw the progress from the bottom up
        progress_stat_rect = pygame.FRect(0, self.image.height - progress_height, 20, progress_height)
        pygame.draw.rect(self.image, '#86c280', progress_stat_rect)


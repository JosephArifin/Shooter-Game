from settings import *
from math import degrees, atan2

class Player(pygame.sprite.Sprite): 
    def __init__(self, groups, pos, collision_sprites):
        super().__init__(groups)
        # player setup
        self.radius = player_stats['player_radius']
        player_w = player_stats['player_w']
        player_h = player_stats['player_h']
        self.is_player_in_safezone = True

        self.collision_sprites = collision_sprites
        self.coins = 1000

        self.image = pygame.Surface((player_w, player_h), pygame.SRCALPHA)
        pygame.draw.circle(self.image, '#3e4a56', (player_w / 2, player_h / 2), self.radius)  # body

        # rect
        self.rect = self.image.get_frect(center = pos)

        # movement
        self.direction = pygame.Vector2()
        self.spd = player_stats['walk_spd']

    def collisions(self, direction):
        for sprite in self.collision_sprites:
            if sprite.rect.colliderect(self.rect):
                if direction == 'horizontal':
                    if self.direction.x < 0: self.rect.left = sprite.rect.right
                    if self.direction.x > 0: self.rect.right = sprite.rect.left
                else:
                    if self.direction.y < 0: self.rect.top = sprite.rect.bottom
                    if self.direction.y > 0: self.rect.bottom = sprite.rect.top

    def input(self):
        keys = pygame.key.get_pressed()
        self.direction.x = int(keys[pygame.K_d or pygame.K_RIGHT]) - int(keys[pygame.K_a or pygame.K_LEFT])
        self.direction.y = int(keys[pygame.K_s or pygame.K_DOWN]) - int(keys[pygame.K_w or pygame.K_UP])
        self.direction = self.direction.normalize() if self.direction else self.direction

    def move(self, dt):
        self.rect.centerx += self.direction.x * self.spd * dt
        self.collisions('horizontal')
        self.rect.centery += self.direction.y * self.spd * dt
        self.collisions('vertical')

    def update(self, dt):
        self.input()
        self.move(dt)

class Gun(pygame.sprite.Sprite):
    def __init__(self, groups, player):
        # player
        self.player = player
        self.distance = 40
        self.player_direction = pygame.Vector2()

        super().__init__(groups)
        # image, rect
        self.image = pygame.Surface((gun_w, gun_h), pygame.SRCALPHA)
        self.ogimage = self.image
        pygame.draw.rect(self.image, 'gray', pygame.FRect(0, 0, gun_w, gun_h))
        self.rect = self.image.get_frect(topleft = self.player.rect.center + self.player_direction * self.distance)

    def follow_mouse(self):
        # getting angle
        mouse_pos = pygame.Vector2(pygame.mouse.get_pos())
        player_pos = pygame.Vector2(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2)
        if mouse_pos - player_pos != (0,0):
            self.player_direction = (mouse_pos - player_pos).normalize()
        self.angle = degrees(atan2(-self.player_direction.y, self.player_direction.x))

        # reassigning new pos
        self.image = pygame.transform.rotozoom(self.ogimage, self.angle, 1)
        self.rect = self.image.get_frect(center = self.player.rect.center + self.player_direction * self.distance)

    def update(self, _):
        self.follow_mouse()
        
class Bullet(pygame.sprite.Sprite):
    def __init__(self, groups, pos, angle, direction, bullet_spd, bullet_penetration):
        super().__init__(groups)
        self.angle = angle
        self.pos = pos
        self.direction = direction

        # bullet stats
        self.spd = bullet_spd
        self.penetration = bullet_penetration

        self.image = pygame.Surface((15, 8), pygame.SRCALPHA)
        self.ogimage = self.image
        pygame.draw.rect(self.image, 'yellow', pygame.FRect(0, 0, 30, 10))
        self.image = pygame.transform.rotozoom(self.ogimage, self.angle, 1)
        self.rect = self.image.get_frect(center = self.pos)
        self.mask = pygame.mask.from_surface(self.image)

    def rotate(self):
        self.image = pygame.transform.rotozoom(self.ogimage, self.angle, 1)

    def move(self, dt):
        self.rect.center += self.direction * self.spd * dt

    def update(self, dt):
        self.rotate()
        self.move(dt)

class ReloadBar(pygame.sprite.Sprite):
    def __init__(self, groups, player, bullets_per_reload, gun_reload_time):
        super().__init__(groups)
        self.player = player
        self.bullets_per_reload = bullets_per_reload
        self.gun_reload_time = gun_reload_time

        self.image = pygame.Surface((90, 10))
        self.image.fill('#86c280')
        self.rect = self.image.get_frect(center = self.player.rect.center - pygame.Vector2(0,50))

        # gun bar
        self.max_bullets = self.bullets_per_reload
        self.bullets = self.max_bullets
        self.isReloading = False
        self.reload_value = 0

    def update_bar(self, dt):
        reload_rect = pygame.FRect(0, 0, self.image.width, 10)
        pygame.draw.rect(self.image, '#3c7136', reload_rect)
        
        if self.isReloading:
            self.reload_value += 1100 * dt
            ratio = self.image.width / self.gun_reload_time
        else:
            self.max_bullets = self.bullets_per_reload
            self.reload_value = self.bullets
            ratio = reload_rect.width / self.max_bullets
        progress_rect = pygame.FRect(reload_rect.topleft, (self.reload_value * ratio, reload_rect.height))
        pygame.draw.rect(self.image, '#86c280', progress_rect)

        if self.reload_value * ratio >= 90:
            self.bullets = self.bullets_per_reload

    def reloading(self, dt):
        if self.bullets < self.bullets_per_reload:
            self.update_bar(dt)
        elif self.bullets >= self.bullets_per_reload:
            self.isReloading = False

    def update(self, dt):
        self.rect.center = self.player.rect.center - pygame.Vector2(0,50)
        if self.isReloading:
            self.reloading(dt)
        else:
            self.update_bar(dt)
        

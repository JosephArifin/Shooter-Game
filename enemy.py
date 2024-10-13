from settings import *
from random import choice
from math import degrees, atan2, sqrt

class Enemy(pygame.sprite.Sprite):
    def __init__(self, groups, pos, player, collision_sprites, enemies):
        super().__init__(groups)
        # get enemy stats
        self.enemy_type = choice(list(enemy_type.items()))    # get enemy type
        self.stats = dict(self.enemy_type[1])

        # enemy setup
        self.player = player    # player connection
        self.enemies = enemies    # enemy sprites
        self.death_time = self.stats['mask_time']
        self.color = self.stats['color']
        self.radius = self.stats['radius']
        self.start_death = 0
        self.spawn_time = pygame.time.get_ticks()
        self.collision_sprites = collision_sprites


        # draw enemy
        self.image = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, self.color, (self.radius, self.radius), self.radius)
        self.rect = self.image.get_frect(center = pos)
        self.mask = pygame.mask.from_surface(self.image)
        
        # enemy movement
        self.spd = self.stats['spd']
        self.direction = pygame.Vector2()

        # enemy health
        self.max_health = self.stats['max_hp']
        self.hitpoints = self.max_health
        
    def collisions(self, direction):
        for sprite in self.collision_sprites:
            if sprite.rect.colliderect(self.rect):
                if direction == 'horizontal':
                    if self.direction.x < 0 and self.rect.left > sprite.rect.left: 
                        self.rect.left = sprite.rect.right
                    if self.direction.x > 0 and self.rect.right < sprite.rect.right: 
                        self.rect.right = sprite.rect.left
                else:
                    if self.direction.y < 0 and self.rect.top > sprite.rect.top: 
                        self.rect.top = sprite.rect.bottom
                    if self.direction.y > 0 and self.rect.bottom < sprite.rect.bottom: 
                        self.rect.bottom = sprite.rect.top

    def avoid_other_enemies(self):
        for other_enemy in self.enemies:
            if other_enemy == self:
                continue
            
            self_pos = pygame.Vector2(self.rect.center)
            other_pos = pygame.Vector2(other_enemy.rect.center)
            distance = self_pos.distance_to(other_pos)
            if distance < self.radius * 2:
                push_direction = pygame.Vector2(self.rect.center) - pygame.Vector2(other_enemy.rect.center)
                if push_direction.length() > 0:
                    push_direction = push_direction.normalize()
                    self.rect.center += push_direction * 1.5
                    for sprite in self.collision_sprites:
                        if sprite.rect.colliderect(self.rect):
                            self.rect.center -= push_direction * 1.5

    def decrease_health(self, bullet_dmg):
        self.hitpoints -= bullet_dmg
        if self.hitpoints == 0 or self.hitpoints < 0:
            self.player.coins += enemy_value
            # start death timer
            self.start_death = pygame.time.get_ticks()
            # change the image
            image = pygame.mask.from_surface(self.image).to_surface()
            image.set_colorkey('black')
            self.image = image
        
    def death_timer(self):   
        if pygame.time.get_ticks() - self.start_death >= self.death_time:
            self.destroy()

    def too_far(self):
        if pygame.Vector2(self.rect.center).distance_to(pygame.Vector2(self.player.rect.center)) > enemy_spawn_distance:
            self.destroy()

    def inside_corner_collision(self):
        if self.old_posx != self.new_posx and self.old_posy != self.new_posy:
            self.destroy()

    def destroy(self):
        self.hitpoints = 0 # kills the health bar
        self.kill()

    def move(self, dt):
        # calculate enemy direction
        player_pos = pygame.Vector2(self.player.rect.center)
        enemy_pos = pygame.Vector2(self.rect.center)
        self.direction = (player_pos - enemy_pos).normalize()

        # move enemy and get old and new pos for inside corner collision
        self.rect.centerx += self.direction.x * self.spd * dt
        self.old_posx = self.rect.centerx # for inside corner collision
        self.collisions('horizontal')
        self.new_posx = self.rect.centerx # for inside corner collision

        self.rect.centery += self.direction.y * self.spd * dt
        self.old_posy = self.rect.centery # for inside corner collision
        self.collisions('vertical')
        self.new_posy = self.rect.centery # for inside corner collision

    def update(self, dt):
        self.too_far() # checks if enemy is too far from player
        if self.start_death == 0:
            self.move(dt) # moves enemy
            self.inside_corner_collision() # checks if enemy is in an inside corner
            self.avoid_other_enemies()
        else:
            self.death_timer()

class EnemyHealthBar(pygame.sprite.Sprite):
    def __init__(self, groups, pos, enemy):
        super().__init__(groups)
        self.enemy = enemy
        self.pos = pos

        self.image = pygame.Surface((50, 10))
        self.rect = self.image.get_frect(center = self.pos)

    def update_health_bar(self):
        # update health bar
        health_rect = pygame.FRect(0, 0, self.image.width, 10)
        pygame.draw.rect(self.image, 'black', health_rect)
        self.draw_bar(health_rect, self.enemy.hitpoints, self.enemy.max_health)
        
        # if enemy is dead
        if self.enemy.hitpoints <= 0:
            self.kill()
        
    def draw_bar(self, rect, value, max_value):
        ratio = rect.width / max_value
        progress_rect = pygame.FRect(rect.topleft, (value * ratio, rect.height))
        pygame.draw.rect(self.image, 'red', progress_rect)    

    def move(self):
        self.rect.centerx = self.enemy.rect.centerx
        self.rect.centery = self.enemy.rect.top - 20

    def update(self, _):
        self.move()
        self.update_health_bar()

class Boss(pygame.sprite.Sprite):
    def __init__(self, groups, pos, player, collision_sprites):
        super().__init__(groups)
        # general setup
        self.radius = boss_stats['radius']
        self.color = boss_stats['color']
        self.spd = boss_stats['spd']
        self.death_time = boss_stats['mask time']
        self.direction = pygame.Vector2()
        self.player = player
        self.collision_sprites = collision_sprites
        self.start_death = 0
        self.doRecoil = False
        self.recoil_iteration = 0

        # health
        self.max_health = boss_stats['max HP']
        self.hitpoints = self.max_health

        # image & rect
        self.image = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, self.color, (self.radius, self.radius), self.radius)
        self.rect = self.image.get_frect(center = pos)
        self.mask = pygame.mask.from_surface(self.image)

    def cannon_recoil(self):
        if self.doRecoil:
            # set spd to negative for some iterations.
            if self.recoil_iteration <= 25:
                self.spd = -(boss_stats['spd'] * 1.4)
            else:
                self.spd = boss_stats['spd']
                self.recoil_iteration = 0
                self.doRecoil = False

    def death_timer(self):   
        if pygame.time.get_ticks() - self.start_death >= self.death_time:
            self.hitpoints = 0 # kills the health bar
            self.kill()
        
    def decrease_health(self, bullet_dmg):
        self.hitpoints -= bullet_dmg
        if self.hitpoints == 0 or self.hitpoints < 0:
            self.player.coins += enemy_value
            # start death timer
            self.start_death = pygame.time.get_ticks()
            # change the image
            image = pygame.mask.from_surface(self.image).to_surface()
            image.set_colorkey('black')
            self.image = image

    def collisions(self, direction):
        for sprite in self.collision_sprites:
            if sprite.rect.colliderect(self.rect):
                if direction == 'horizontal':
                    if self.direction.x < 0 and self.rect.left > sprite.rect.left: 
                        self.rect.left = sprite.rect.right
                    if self.direction.x > 0 and self.rect.right < sprite.rect.right: 
                        self.rect.right = sprite.rect.left
                else:
                    if self.direction.y < 0 and self.rect.top > sprite.rect.top: 
                        self.rect.top = sprite.rect.bottom
                    if self.direction.y > 0 and self.rect.bottom < sprite.rect.bottom: 
                        self.rect.bottom = sprite.rect.top

    def move(self, dt):
        player_pos = pygame.Vector2(self.player.rect.center)
        enemy_pos = pygame.Vector2(self.rect.center)
        if player_pos - enemy_pos != (0,0):
            self.direction = (player_pos - enemy_pos).normalize()

        self.rect.centerx += self.direction.x * self.spd * dt 
        self.collisions('horizontal')
        self.rect.centery += self.direction.y * self.spd * dt 
        self.collisions('vertical')
        if self.doRecoil:
            self.recoil_iteration += 1

    def update(self, dt):
        if self.start_death == 0:
            
            self.move(dt)
            self.cannon_recoil()
        else:
            self.death_timer()

class BossCannon(pygame.sprite.Sprite):
    def __init__(self, groups, boss, player):
        super().__init__(groups)
        self.boss = boss
        self.player = player
        self.cannon_offset = 100
        self.direction = pygame.Vector2()

        self.image = pygame.Surface((190, 180), pygame.SRCALPHA)
        self.og_image = self.image
        pygame.draw.rect(self.image, 'gray', pygame.FRect(0,0, self.image.width, self.image.height))
        self.rect = self.image.get_frect(center = self.boss.rect.center + self.direction * self.cannon_offset)

    def follow_player(self):
        # get angle
        player_center = pygame.Vector2(self.player.rect.center)
        boss_center = pygame.Vector2(self.boss.rect.center)
        

        if player_center != (0,0):
            self.direction = -(boss_center - player_center).normalize()
        angle = degrees(atan2(-self.direction.y, self.direction.x))

        # reassign pos
        self.image = pygame.transform.rotate(self.og_image, angle)
        self.rect = self.image.get_frect(center = self.boss.rect.center + self.direction * self.cannon_offset)

    def update(self, _):
        self.follow_player()
        if self.boss.hitpoints <= 0:
            self.kill()

class BossProjectile(pygame.sprite.Sprite):
    def __init__(self, groups, boss_cannon, collision_sprites):
        super().__init__(groups)
        self.boss_cannon = boss_cannon
        self.direction = boss_cannon.direction
        self.collision_sprites = collision_sprites
        self.spd = 300

        self.image = pygame.Surface((180,180), pygame.SRCALPHA)
        pygame.draw.circle(self.image, 'purple', (180 / 2, 180 / 2), 180 / 2)
        self.rect = self.image.get_frect(center = self.boss_cannon.rect.center)
        self.mask = pygame.mask.from_surface(self.image)

    def decrease_health(self, _):    # this projectile doesn't have health; only here for convience sake in bullet_collisions
        pass

    def move(self, dt):
        self.rect.center += self.direction * self.spd * dt

    def update(self, dt):
        self.move(dt)
        if pygame.sprite.spritecollide(self, self.collision_sprites, False):
            self.kill()

class BossMissiles(pygame.sprite.Sprite):
    def __init__(self, groups, pos, player):
        super().__init__(groups)
        self.player = player
        self.spd = 150
        self.direction = pygame.Vector2()
        self.angle = 0
        self.doKill = False

        self.og_image = pygame.Surface((25,25), pygame.SRCALPHA)
        self.image = pygame.Surface((25,25), pygame.SRCALPHA)
        pygame.draw.polygon(self.image, 'pink', [(0,0),(25,12.5),(0,25)])
        self.rect = self.image.get_frect(center = pos)
        self.mask = pygame.mask.from_surface(self.image)

    def decrease_health(self, _):
        self.kill()

    def move(self, dt):
        player_pos = pygame.Vector2(self.player.rect.center)
        enemy_pos = pygame.Vector2(self.rect.center)
        if player_pos - enemy_pos != (0,0):
            self.direction = (player_pos - enemy_pos).normalize()

        self.rect.centerx += self.direction.x * self.spd * dt
        self.rect.centery += self.direction.y * self.spd * dt

    def rotate(self):
        # calculate the angle to rotate
        self.angle = degrees(atan2(-self.direction.y, self.direction.x)) % 360
        
        # use precomputed rotation
        rotated_image_index = int(self.angle) % ANGLES
        self.image = precomputed_missile_rotations[rotated_image_index]
        self.rect = self.image.get_rect(center=self.rect.center)

    def update(self, dt):
        self.move(dt)
        self.rotate()
        if self.doKill:
            # print('test')
            self.kill()

class BossHealthBar(pygame.sprite.Sprite):
    def __init__(self, groups, player, boss):
        super().__init__(groups)
        self.player = player
        self.boss = boss
        self.pos = self.player.rect.center + pygame.Vector2(0, -(WINDOW_HEIGHT / 2) + 50)

        self.image = pygame.Surface((960, 25), pygame.SRCALPHA)
        pygame.draw.rect(self.image, 'red', pygame.FRect(0,0, self.image.width, self.image.height))
        self.rect = self.image.get_frect(center = self.pos)

    def update_health_bar(self):
        # update health bar
        health_rect = pygame.FRect(0, 0, self.image.width, self.image.height)
        pygame.draw.rect(self.image, 'black', health_rect)
        self.draw_bar(health_rect, self.boss.hitpoints, self.boss.max_health)

        # if enemy is dead
        if self.boss.hitpoints <= 0:
            self.kill()

    def draw_bar(self, rect, value, max_value):
        ratio = rect.width / max_value
        progress_rect = pygame.FRect(rect.topleft, (value * ratio, rect.height))
        pygame.draw.rect(self.image, 'red', progress_rect)

    def update(self, _):
        self.rect.center = self.player.rect.center + pygame.Vector2(0, -(WINDOW_HEIGHT / 2) + 50)
        self.update_health_bar()

class BossText(pygame.sprite.Sprite):
    def __init__(self, groups, font, health_bar):
        super().__init__(groups)
        self.health_bar = health_bar
        self.image = font.render('Boss Health', False, 'black')
        self.rect = self.image.get_frect(center = (health_bar.rect.centerx, health_bar.rect.centery - 25))

    def update(self, _):
        self.rect.center = (self.health_bar.rect.centerx, self.health_bar.rect.centery - 25)
        if self.health_bar.alive() == False:
            self.kill()




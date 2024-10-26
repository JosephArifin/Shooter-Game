from settings import *
from player import *
from enemy import *
from groups import *
from shop import *
from rects import *
from map import load_map_tmx
from fieldOfView import cast_rays, draw_visibility_polygon
from random import randint
from math import cos, sin, radians
from pytmx.util_pygame import load_pygame
import sys

class Game:
    def __init__(self):
        pygame.init()
        self.display_surf = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.boss_font = pygame.font.Font(None, 35)
        self.clock = pygame.time.Clock()
        self.game_running = False

        # end game
        self.fight_boss_clicked = False
        self.play_from_start_clicked = False

        # groups
        self.all_sprites = AllSprites()
        self.collision_sprites = pygame.sprite.Group()
        self.bullet_sprites = pygame.sprite.Group()
        self.enemy_sprites = pygame.sprite.Group()
        self.shop_sprites = pygame.sprite.Group()
        self.boss_health_sprites = pygame.sprite.Group()
        self.missile_sprites = pygame.sprite.Group()

        # gun timer
        self.shoot = True
        self.shoot_time = pygame.time.get_ticks()
        self.bullets_shot = 0
        self.time_since_reloaded = -2000
        self.reloading = False

        # enemy timer
        self.enemy_spawn_timer = pygame.event.custom_type() + 0
        pygame.time.set_timer(self.enemy_spawn_timer, 2000)
        
        # boss missile timer
        self.boss_missile_spawn_event = pygame.event.custom_type() + 1
        self.boss_missile_spawn_timer = pygame.time.set_timer(self.boss_missile_spawn_event, 5000)

        # boss shoot timer
        self.boss_shoot_event = pygame.event.custom_type() + 2
        self.boss_shoot_timer = pygame.time.set_timer(self.boss_shoot_event, 3000)

        # bossfight enemies timer
        self.bossfight_enemies_event = pygame.event.custom_type() + 3
        self.bossfight_enemies_timer = pygame.time.set_timer(self.bossfight_enemies_event, 4000)

        # base bullet stats
        self.bullet_spd = 700
        self.bullet_penetration = 1
        self.bullet_reload_time = 300 # in milisecs
        self.bullet_dmg = 1  # default is 1
        self.gun_reload_time = 2000 # in milisecs default is 2000
        self.bullets_per_reload = 8

        # shop
        self.shop_state = False
        self.shopfont = pygame.font.Font(None, 20)
        self.shop_price = 100

        self.bullet_dmg_statsbar_value = 0
        self.bullet_penetration_statsbar_value = 0
        self.bullet_spd_statsbar_value = 0
        self.bullet_reload_statsbar_value = 0

        # boss
        self.has_boss_spawned = False
        self.is_player_fighting_boss = False
        self.has_boss_hit_half_health = False  # Tracks if the boss hit half health

        # setup
        self.setup()

    # game funcs 
    def game_event_loop(self):
        for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == self.enemy_spawn_timer and self.is_player_fighting_boss == False:
                    self.spawn_enemy()
                if event.type == self.boss_missile_spawn_event and self.is_player_fighting_boss:
                    for i in range(randint(2,3)):
                        self.spawn_boss_missile()
                if event.type == self.boss_shoot_event and self.is_player_fighting_boss:
                    self.boss_do_shoot()
                if event.type == self.bossfight_enemies_event and self.is_player_fighting_boss:
                    for i in range(randint(1,2)):
                        self.spawn_bossfight_enemies()

    def setup(self):
        self.map = load_pygame(join('data', 'map.tmx'))
        shop_surf = pygame.image.load(join('data', 'shop.png')).convert_alpha()
        self.tile_grid = load_map_tmx('data/map.tmx')

        for x, y, image in self.map.get_layer_by_name('Ground').tiles():
            Sprite((x * TILE_SIZE, y * TILE_SIZE), image, self.all_sprites)

        for x, y, image in self.map.get_layer_by_name('Walls').tiles():
            self.wall = Sprite((x * TILE_SIZE, y * TILE_SIZE), image, (self.all_sprites, self.collision_sprites))

        for obj in self.map.get_layer_by_name('Entities'):
            if obj.name == 'Player':
                self.player = Player(self.all_sprites, (obj.x, obj.y), self.collision_sprites)
                self.gun = Gun(self.all_sprites, self.player)
                self.reload_bar = ReloadBar(self.all_sprites, self.player, self.bullets_per_reload, self.gun_reload_time)
                self.enemy_spawn_rect = EnemySpawnRect(self.all_sprites, self.player)
                self.player_vision_rect = PlayerVisionRect(self.all_sprites, self.player)
            if obj.name == 'Shop':
                self.shop = Shop((self.all_sprites), (obj.x, obj.y), shop_surf)
            if obj.name == 'Safe_zone':
                self.safezone = SafeZone((self.all_sprites), (obj.x, obj.y))
            if obj.name == 'Boss_rect':
                self.boss_room = BossRoom(self.all_sprites, (obj.x, obj.y))

    def bullet_collisions(self):
        if self.bullet_sprites:
            for bullet in self.bullet_sprites:
                collision_sprites = pygame.sprite.spritecollide(bullet, self.enemy_sprites, False, pygame.sprite.collide_mask)
                if collision_sprites:
                    if bullet.penetration > 0:
                        for sprite in collision_sprites:
                            sprite.decrease_health(self.bullet_dmg)
                        normal_enemy_type = sprite.enemy_type[0] == 'Fast' or sprite.enemy_type[0] == 'Normal' or sprite.enemy_type[0] == 'Tank'
                        if normal_enemy_type:
                            bullet.penetration -= 1
                            bullet.rect.center += bullet.direction * 80
                        else:
                            bullet.kill()
                    elif bullet.penetration < 1:
                        for sprite in collision_sprites:
                            sprite.decrease_health(self.bullet_dmg)
                        bullet.kill()
                        
                # bullet collision with wall
                if pygame.sprite.spritecollide(bullet, self.collision_sprites, False): bullet.kill()

    def player_collisions(self):
        collision_sprites = pygame.sprite.spritecollide(self.player, self.enemy_sprites, False, pygame.sprite.collide_mask)
        if collision_sprites:
            self.all_sprites.remove(self.enemy_sprites)
            self.enemy_sprites.empty()
            self.player.rect.center = pygame.Vector2(self.map.get_object_by_name('Player').x, self.map.get_object_by_name('Player').y)
            self.all_sprites.remove(self.bullet_sprites)

    def player_coins(self):
        self.font = pygame.font.SysFont("arialblack", 40)
        self.image = self.font.render("Coins: " + str(self.player.coins), False, "gold")
        self.display_surf.blit(self.image, (WINDOW_WIDTH - 270, WINDOW_HEIGHT - 60))

    def input(self):
        mouse = pygame.mouse.get_pressed()
        # shooting
        if self.shop_state == False:
            if self.bullets_shot < self.bullets_per_reload:
                # if time since reloaded to current time is 2 sec:
                if pygame.time.get_ticks() - self.time_since_reloaded >= self.gun_reload_time:
                    self.reloading = False
                    if self.bullets_shot == 0:
                        self.reload_bar.bullets = self.bullets_per_reload
                    if mouse[0] and self.shoot:
                        pos = (self.gun.rect.centerx, self.gun.rect.centery)
                        Bullet((self.all_sprites, self.bullet_sprites), pos, self.gun.angle, self.gun.player_direction, self.bullet_spd, self.bullet_penetration)
                        self.all_sprites.move_to_front(self.gun)
                        self.bullets_shot += 1
                        self.reload_bar.bullets -= 1
                        self.shoot_time = pygame.time.get_ticks()
                        self.shoot = False
                    elif mouse[2]:
                        self.time_since_reloaded = pygame.time.get_ticks()
                        self.reloading = True
                        self.bullets_shot = 0
                        self.reload_bar.bullets = 0
                        self.reload_bar.isReloading = True
                        self.reload_bar.reload_value = 0
            else:
                if mouse[2] and self.reloading == False:
                    self.time_since_reloaded = pygame.time.get_ticks()
                    self.reloading = True
                    self.bullets_shot = 0
                    self.reload_bar.bullets = 0
                    self.reload_bar.isReloading = True
                    self.reload_bar.reload_value = 0
     
        # pausing game
        if pygame.key.get_just_pressed()[pygame.K_SPACE]:
            self.game_running = False
            self.main_menu_running = True
            self.main_menu()

    def gun_timer(self):
        if self.shop_state == False:
            current_time = pygame.time.get_ticks()
            if current_time - self.shoot_time >= self.bullet_reload_time:
                self.shoot = True

    def spawn_enemy(self):
        if self.enemy_sprites.__len__() < 10:
            if not self.player.rect.colliderect(self.safezone.rect):
                for obj in self.map.get_layer_by_name('Entities'):
                    if obj.name == 'Enemy':
                        if not self.player_vision_rect.rect.collidepoint(obj.x, obj.y):
                            if self.enemy_spawn_rect.rect.collidepoint(obj.x, obj.y):
                                self.enemy = Enemy((self.all_sprites, self.enemy_sprites), (obj.x, obj.y), self.player, self.player_vision_polygon, self.collision_sprites, self.enemy_sprites, self.all_sprites.offset)
                                self.enemy_health_bar = EnemyHealthBar((self.all_sprites), (self.enemy.rect.centerx, self.enemy.rect.top - 20), self.enemy)
        
    # shop funcs
    def shop_collision(self):
        if self.player.rect.colliderect(self.shop.rect) and self.shop_state == False:
            self.open_shop()
        elif not self.player.rect.colliderect(self.shop.rect) and self.shop_state:
            self.close_shop()

    def shop_ui(self):
        if self.shop_state:
            mouse_pos = self.all_sprites.mouse_pos
            check_click_state = pygame.mouse.get_just_released()[0]
            check_player_coins = self.player.coins >= self.shop_price
            if self.bullet_dmg_button.rect.collidepoint(mouse_pos):
                if check_click_state and check_player_coins:
                    if self.bullet_dmg <= 3:
                        self.bullet_dmg += 0.5
                        self.bullet_dmg_statsbar_value += 1
                        self.player.coins -= 100
                    self.bullet_dmg_statsbar.update_stat_bar(self.bullet_dmg_statsbar_value)

            if self.bullet_penetration_button.rect.collidepoint(mouse_pos):
                if check_click_state and check_player_coins:
                    if self.bullet_penetration <= 5:
                        self.bullet_penetration += 1
                        self.bullet_penetration_statsbar_value += 1
                        self.player.coins -= 100
                    self.bullet_penetration_statsbar.update_stat_bar(self.bullet_penetration_statsbar_value)

            if self.bullet_spd_button.rect.collidepoint(mouse_pos):
                if check_click_state and check_player_coins:
                    if self.bullet_spd <= 1100:
                        self.bullet_spd += 100
                        self.bullet_spd_statsbar_value += 1
                        self.player.coins -= 100
                    self.bullet_spd_statsbar.update_stat_bar(self.bullet_spd_statsbar_value)

            if self.bullet_reload_time_button.rect.collidepoint(mouse_pos):
                if check_click_state and check_player_coins:
                    if self.bullet_reload_time >= 150:
                        self.bullet_reload_time -= 35
                        self.bullet_reload_statsbar_value += 1
                        self.player.coins -= 100
                    if self.gun_reload_time > 800:
                        self.gun_reload_time -= 240
                        self.reload_bar.gun_reload_time = self.gun_reload_time
                    if self.bullets_per_reload < 18:
                        self.bullets_per_reload += 2
                        self.reload_bar.bullets_per_reload += 2
                        
                    self.bullet_reload_time_statsbar.update_stat_bar(self.bullet_reload_statsbar_value)
            
    def open_shop(self):
        self.shop_state = True
        self.shopui = ShopUI((self.all_sprites), (self.player.rect.center))

        # buttons
        self.bullet_dmg_button = Button((self.all_sprites), (self.shopui.rect.topleft + pygame.Vector2(50,60)))
        self.bullet_penetration_button = Button((self.all_sprites), (self.shopui.rect.topleft + pygame.Vector2(150,60)))
        self.bullet_spd_button = Button((self.all_sprites), (self.shopui.rect.topleft + pygame.Vector2(250,60)))
        self.bullet_reload_time_button = Button((self.all_sprites), (self.shopui.rect.topleft + pygame.Vector2(350,60)))

        # stats bars
        self.bullet_dmg_statsbar = StatBar((self.all_sprites, self.shop_sprites), (self.bullet_dmg_button.rect.center + pygame.Vector2(0,70)))
        self.bullet_penetration_statsbar = StatBar((self.all_sprites, self.shop_sprites), (self.bullet_penetration_button.rect.center + pygame.Vector2(0,70))) 
        self.bullet_spd_statsbar = StatBar((self.all_sprites, self.shop_sprites), (self.bullet_spd_button.rect.center + pygame.Vector2(0,70)))
        self.bullet_reload_time_statsbar = StatBar((self.all_sprites, self.shop_sprites), (self.bullet_reload_time_button.rect.center + pygame.Vector2(0,70)))
        
        # text
        self.bullet_dmg_text = ShopText((self.all_sprites), self.bullet_dmg_button.rect.center + pygame.Vector2(0,-30), self.shopfont, "Damage")
        self.bullet_penetration_text = ShopText((self.all_sprites), self.bullet_penetration_button.rect.center + pygame.Vector2(0,-30), self.shopfont, "Penetration")
        self.bullet_spd_text = ShopText((self.all_sprites), self.bullet_spd_button.rect.center + pygame.Vector2(0,-30), self.shopfont, "Speed")
        self.bullet_reload_time_text = ShopText((self.all_sprites), self.bullet_reload_time_button.rect.center + pygame.Vector2(0,-30), self.shopfont, "Reload")

        # price text
        self.bullet_dmg_price = ShopText((self.all_sprites), self.bullet_dmg_button.rect.center, self.shopfont, "100")
        self.bullet_penetration_price = ShopText((self.all_sprites), self.bullet_penetration_button.rect.center, self.shopfont, "100")
        self.bullet_spd_price = ShopText((self.all_sprites), self.bullet_spd_button.rect.center, self.shopfont, "100")
        self.bullet_reload_time_price = ShopText((self.all_sprites), self.bullet_reload_time_button.rect.center, self.shopfont, "100")
        
        # update stat bars
        self.bullet_dmg_statsbar.update_stat_bar(self.bullet_dmg_statsbar_value)
        self.bullet_penetration_statsbar.update_stat_bar(self.bullet_penetration_statsbar_value)
        self.bullet_spd_statsbar.update_stat_bar(self.bullet_spd_statsbar_value)
        self.bullet_reload_time_statsbar.update_stat_bar(self.bullet_reload_statsbar_value)

        self.shop_ui()

    def close_shop(self):
        self.shop_state = False

        # Kill every shop sprite
        self.shopui.kill()
        self.bullet_dmg_button.kill()
        self.bullet_penetration_button.kill()
        self.bullet_spd_button.kill()
        self.bullet_reload_time_button.kill()
        self.bullet_dmg_statsbar.kill()
        self.bullet_penetration_statsbar.kill()
        self.bullet_spd_statsbar.kill()
        self.bullet_reload_time_statsbar.kill()
        self.bullet_dmg_text.kill()
        self.bullet_penetration_text.kill()
        self.bullet_spd_text.kill()
        self.bullet_reload_time_text.kill()
        self.bullet_dmg_price.kill()
        self.bullet_penetration_price.kill()
        self.bullet_spd_price.kill()
        self.bullet_reload_time_price.kill()


    # boss fight funcs
    def boss_room_detection(self):
        if self.player.rect.colliderect(self.boss_room.rect):
            self.is_player_fighting_boss = True

            # spawn boss
            if self.has_boss_spawned == False:
                self.spawn_boss()
                self.has_boss_spawned = True

                # prespawn some missiles
                for i in range(randint(5,7)):
                       posx = randint(2 * TILE_SIZE, 14 * TILE_SIZE)
                       posy = randint(44 * TILE_SIZE, 50 * TILE_SIZE)
                       self.boss_missile = BossMissiles((self.all_sprites, self.enemy_sprites, self.missile_sprites), (posx, posy), self.player)

    def spawn_boss(self):
        x, y = self.map.get_object_by_name('Boss').x, self.map.get_object_by_name('Boss').y    # get boss position
        self.boss = Boss((self.all_sprites, self.enemy_sprites), (x, y), self.player, self.collision_sprites)    # spawn boss
        self.boss_cannon = BossCannon(self.all_sprites, self.boss, self.player)
        self.boss_health_bar = BossHealthBar(self.boss_health_sprites, self.player, self.boss)    # boss health bar
        self.boss_text = BossText(self.boss_health_sprites, self.boss_font, self.boss_health_bar)    # text

    def boss_do_shoot(self):
        # spawn proj, reorder, and doRecoil
        self.boss_projectile = BossProjectile((self.all_sprites, self.enemy_sprites), self.boss_cannon, self.collision_sprites)
        self.all_sprites.move_to_front(self.boss_cannon)
        self.boss.doRecoil = True

    def spawn_boss_missile(self):
        # get random angle
        angle = radians(randint(0, 360))

        # get random distance away from player
        distance = randint(650, 750)

        # get the pos based on angle and distance using unit circle
        x_offset, y_offset = cos(angle) * distance, sin(angle) * distance    # calculates offset for x, y
        pos = (self.player.rect.centerx + x_offset, self.player.rect.centery - y_offset)    # gets the coord for missile
        
        # spawn missile
        self.boss_missile = BossMissiles((self.all_sprites, self.enemy_sprites,self.missile_sprites), pos, self.player)

    def check_reset_boss_fight(self):
        if self.is_player_fighting_boss and self.player.rect.bottom < 3072:
            self.boss.kill()
            self.boss_cannon.kill()
            self.boss_text.kill()
            self.boss_health_bar.kill()
            self.is_player_fighting_boss = False
            self.has_boss_spawned = False

    def spawn_bossfight_enemies(self):
        # get random pos inside bossfight
        x, y = randint(2* TILE_SIZE, 14 * TILE_SIZE), randint(34 * TILE_SIZE, 46 * TILE_SIZE)

        # check if pos is not inside player vision
        if not self.player_vision_rect.rect.collidepoint(x,y):
            self.enemy = Enemy((self.all_sprites, self.enemy_sprites), (x, y), self.player, self.player_vision_polygon, self.collision_sprites, self.enemy_sprites, self.all_sprites.offset)
            self.enemy.spd = (self.enemy.spd * .6) + 18
            self.enemy_health_bar = EnemyHealthBar(self.all_sprites, (self.enemy.rect.centerx, self.enemy.rect.top - 20), self.enemy)
        else:  # If pos is inside player vision, reget random pos
            self.spawn_bossfight_enemies()

    def check_boss_health(self):
        # check if boss is at half health
        if self.is_player_fighting_boss and not self.has_boss_hit_half_health:
            if self.boss.hitpoints <= boss_stats['max HP'] / 2:
                # Update timers with faster intervals
                pygame.time.set_timer(self.boss_missile_spawn_event, 4000)
                pygame.time.set_timer(self.boss_shoot_event, 2000)
                pygame.time.set_timer(self.bossfight_enemies_event, 3000)
            
                # ensure timers dont reset repeatedly
                self.has_boss_hit_half_health = True
        
        # checks if boss is dead
        if self.is_player_fighting_boss:
            if self.boss.hitpoints <= 0:
                self.game_running = False
                self.bossfight_end()
                
    def check_is_player_in_safezone(self):
        self.player.is_player_in_safezone = True if self.player.rect.colliderect(self.safezone.rect) else False

    def reorder_boss_sprites(self):
        if self.is_player_fighting_boss:
            self.all_sprites.move_to_front(self.boss)
            for sprite in self.missile_sprites:
                self.all_sprites.move_to_front(sprite)

            # Boss health bar
            self.boss_health_sprites.update()
            self.display_surf.blit(self.boss_health_bar.image, (WINDOW_WIDTH / 2 - self.boss_health_bar.image.width / 2, 40))
            self.display_surf.blit(self.boss_text.image, (WINDOW_WIDTH / 2 - self.boss_text.image.width / 2, 15))

    # menus / screens
    def bossfight_end(self):
        screen = pygame.display.get_surface()
        pygame.display.set_caption('End')
        
        # fade surf for transition
        fade_surf = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        fade_surf.fill(MENU_BG_COLOR)

        # transition to menu
        for alpha in range(0,256):
            fade_surf.set_alpha(alpha)
            screen.fill('black')
            self.all_sprites.draw(self.player.rect.center)
            screen.blit(fade_surf, (0,0))
            pygame.display.update()

        # menu loop
        didDelay = False
        self.bossfight_end_running = True
        while self.bossfight_end_running:

            screen.fill(MENU_BG_COLOR)

            menu_state = 'end'

            # create button instances
            fight_boss_button = NavButton(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 - 200, pygame.image.load('data/buttons/fight_boss.png'), 1.5)
            play_from_start_button = NavButton(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2, pygame.image.load('data/buttons/play_start.png'), 1.5)
            quit_button = NavButton(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 + 200, pygame.image.load('data/buttons/quit_button.png'), 1.5)

            # delay before spawning buttons
            if didDelay == False:
                pygame.time.delay(1000)
                didDelay = True

            if menu_state == 'end':
                if fight_boss_button.draw(screen):
                    self.fight_boss_clicked = True
                    self.game_run()
                    

                if play_from_start_button.draw(screen):
                    self.play_from_start_clicked = True
                    self.game_run()
                    

                if quit_button.draw(screen):
                    pygame.quit()
                    sys.exit()

            #event handler
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
            
            pygame.display.update()

    def main_menu(self):
        screen = pygame.display.get_surface()
        pygame.display.set_caption('Menu')

        #game variable
        menu_state = "main"

        #define fonts
        font = pygame.font.SysFont("arialblack", 35)
    
        # create button instances
        play_button = NavButton(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 - 200, pygame.image.load('data/buttons/play_button.png'), 1.5)
        keys_button = NavButton(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2, pygame.image.load('data/buttons/keys_button.png'), 1.5)
        quit_button = NavButton(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 + 200, pygame.image.load('data/buttons/quit_button.png'), 1.5)
        back_button = NavButton(WINDOW_WIDTH / 2, 600, pygame.image.load('data/buttons/back_button.png'), 1.5)

        # drawing text func
        def draw_text(text, font, text_col, x, y):
            img = font.render(text, False, text_col)
            screen.blit(img, (x, y))

        # transition to game
        def fade_in():
            fade_surf = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
            fade_surf.fill(MENU_BG_COLOR)
            transition_image = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
            transition_image.fill('black')

            for alpha in range(255,-1, -1):
                fade_surf.set_alpha(alpha)
                screen.blit(transition_image, (0,0))
                screen.blit(fade_surf, (0,0))

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()

                pygame.display.update()

        #game loop
        self.main_menu_running = True
        while self.main_menu_running:
        
            screen.fill('white')

            # check if game is paused
            # check menu state
            if menu_state == "main":
            # draw pause screen buttons
                if play_button.draw(screen):
                    fade_in()
                    self.game_run()
                if keys_button.draw(screen):
                    menu_state = "options"
                if quit_button.draw(screen):
                    pygame.quit()
                    sys.exit()

            # check if the options menu is open
            if menu_state == "options":
                # draw the back button
                draw_text('SPACE to pause\nWASD to move\nLEFT CLICK to shoot\nUNLESS in safe zone\nRIGHT CLICK to reload', font, "black", 380, 200)
                if back_button.draw(screen):
                    menu_state = "main"

            #event handler
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            pygame.display.update()

    def game_run(self):
        pygame.display.set_caption('Shooter')

        # if player wants to fight boss again
        if self.fight_boss_clicked:
            self.player.rect.centerx = self.map.get_object_by_name('Player_boss').x
            self.player.rect.centery = self.map.get_object_by_name('Player_boss').y
            self.fight_boss_clicked = False

        # if player wants to play from start again
        if self.play_from_start_clicked:
            self.player.rect.centerx = self.map.get_object_by_name('Player').x
            self.player.rect.centery = self.map.get_object_by_name('Player').y
            self.play_from_start_clicked = False

        self.game_running = True
        while self.game_running:
            dt = self.clock.tick(FRAMERATE) / 1000
            self.game_event_loop()
            
            # open shop
            self.all_sprites.offset_mouse_pos()
            self.shop_collision()
            self.shop_ui()
               
            # update
            self.all_sprites.update(dt)
            self.gun_timer()
            self.input()
            self.bullet_collisions()
            
            self.check_is_player_in_safezone()
            self.player_collisions()
            
            # update boss fight
            self.boss_room_detection()
            self.check_reset_boss_fight()
            self.check_boss_health()
            
            # draw
            self.display_surf.fill('black')
            self.all_sprites.draw(self.player.rect.center)
            
            # Call the raycasting function, passing the player's position and camera offset
            self.player_vision_polygon = draw_visibility_polygon(self.display_surf, cast_rays(self.player.rect.center, self.all_sprites.offset, self.tile_grid))
            self.player_coins()
            self.reorder_boss_sprites()

            # update display
            pygame.display.update()

if __name__ == '__main__':
    game = Game()
    game.main_menu() 
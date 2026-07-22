import pygame
import sys
import random
import math
from enum import Enum

pygame.init()

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
ORANGE = (255, 165, 0)

class GameState(Enum):
    MENU = 0
    PLAYING = 1
    PAUSED = 2
    GAME_OVER = 3

class Entity:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.speed = 0
        self.velocity = [0, 0]
        self.health = 100
        self.max_health = 100
        self.alive = True

    def update(self, delta_time):
        self.x += self.velocity[0] * delta_time
        self.y += self.velocity[1] * delta_time

    def draw(self, surface):
        pass

    def get_rect(self):
        return pygame.Rect(self.x - self.width // 2, self.y - self.height // 2, self.width, self.height)

    def take_damage(self, damage):
        self.health -= damage
        if self.health <= 0:
            self.health = 0
            self.alive = False

class Particle:
    def __init__(self, x, y, color, speed, angle, lifetime, size=4):
        self.x = x
        self.y = y
        self.color = color
        self.speed = speed
        self.angle = angle
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.size = size
        self.velocity = [math.cos(angle) * speed, math.sin(angle) * speed]
        self.alpha = 255

    def update(self, delta_time):
        self.lifetime -= delta_time
        self.x += self.velocity[0]
        self.y += self.velocity[1]
        self.alpha = int(255 * (self.lifetime / self.max_lifetime))
        self.size *= 0.99

    def draw(self, surface):
        if self.lifetime <= 0:
            return
        color = (*self.color, self.alpha)
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), max(1, int(self.size)))

class ParticleSystem:
    def __init__(self):
        self.particles = []

    def add_explosion(self, x, y, color=ORANGE, count=20):
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(2, 5)
            lifetime = random.uniform(0.3, 0.6)
            size = random.uniform(3, 6)
            self.particles.append(Particle(x, y, color, speed, angle, lifetime, size))

    def add_laser_trail(self, x, y, color=CYAN):
        for _ in range(2):
            angle = random.uniform(-0.1, 0.1)
            speed = random.uniform(1, 3)
            lifetime = random.uniform(0.1, 0.2)
            size = random.uniform(1, 3)
            self.particles.append(Particle(x, y, color, speed, angle, lifetime, size))

    def update(self, delta_time):
        self.particles = [p for p in self.particles if p.lifetime > 0]
        for particle in self.particles:
            particle.update(delta_time)

    def draw(self, surface):
        for particle in self.particles:
            particle.draw(surface)

class StarBackground:
    def __init__(self):
        self.stars = []
        for _ in range(80):
            self.stars.append({
                'x': random.randint(0, SCREEN_WIDTH),
                'y': random.randint(0, SCREEN_HEIGHT),
                'speed': random.uniform(1, 3),
                'size': random.uniform(1, 2),
                'brightness': random.uniform(0.5, 1)
            })

    def update(self, delta_time):
        for star in self.stars:
            star['y'] += star['speed'] * delta_time * 60
            if star['y'] > SCREEN_HEIGHT:
                star['y'] = 0
                star['x'] = random.randint(0, SCREEN_WIDTH)

    def draw(self, surface):
        for star in self.stars:
            color = (int(255 * star['brightness']), int(255 * star['brightness']), int(255 * star['brightness']))
            pygame.draw.circle(surface, color, (int(star['x']), int(star['y'])), int(star['size']))

class Player(Entity):
    def __init__(self):
        super().__init__(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80, 30, 40)
        self.speed = 400
        self.shield = 100
        self.max_shield = 100
        self.weapon_level = 1
        self.fire_rate = 0.25
        self.last_fire_time = 0
        self.invincible = False
        self.invincible_time = 0
        self.score = 0
        self.lives = 3

    def update(self, delta_time, keys):
        super().update(delta_time)
        
        self.velocity = [0, 0]
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.velocity[0] -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.velocity[0] += self.speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.velocity[1] -= self.speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.velocity[1] += self.speed

        if self.invincible:
            self.invincible_time -= delta_time
            if self.invincible_time <= 0:
                self.invincible = False

        self.x = max(self.width // 2, min(SCREEN_WIDTH - self.width // 2, self.x))
        self.y = max(self.height // 2, min(SCREEN_HEIGHT - self.height // 2, self.y))

    def draw(self, surface):
        if self.invincible and int(pygame.time.get_ticks() / 100) % 2 == 0:
            return
        
        points = [
            (self.x, self.y - self.height // 2),
            (self.x - self.width // 2, self.y + self.height // 2),
            (self.x - self.width // 4, self.y + self.height // 3),
            (self.x, self.y + self.height // 2.5),
            (self.x + self.width // 4, self.y + self.height // 3),
            (self.x + self.width // 2, self.y + self.height // 2)
        ]
        pygame.draw.polygon(surface, WHITE, points)
        pygame.draw.polygon(surface, CYAN, points, 2)

    def fire(self, current_time):
        if current_time - self.last_fire_time >= self.fire_rate:
            self.last_fire_time = current_time
            bullets = []
            
            if self.weapon_level == 1:
                bullets.append(Bullet(self.x, self.y - self.height // 2, 0, -1))
            elif self.weapon_level == 2:
                bullets.append(Bullet(self.x - 8, self.y - self.height // 2, 0, -1))
                bullets.append(Bullet(self.x + 8, self.y - self.height // 2, 0, -1))
            elif self.weapon_level >= 3:
                bullets.append(Bullet(self.x, self.y - self.height // 2, 0, -1))
                bullets.append(Bullet(self.x - 12, self.y - self.height // 4, -0.2, -1))
                bullets.append(Bullet(self.x + 12, self.y - self.height // 4, 0.2, -1))
            
            return bullets
        return []

    def take_damage(self, damage):
        if self.invincible:
            return
        
        if self.shield > 0:
            self.shield -= damage
            if self.shield < 0:
                self.health += self.shield
                self.shield = 0
        else:
            self.health -= damage
        
        if self.health <= 0:
            self.health = 0
            self.lives -= 1
            if self.lives > 0:
                self.health = 100
                self.shield = 50
                self.invincible = True
                self.invincible_time = 2
            else:
                self.alive = False

class Bullet(Entity):
    def __init__(self, x, y, vx, vy, is_enemy=False):
        super().__init__(x, y, 5, 12)
        self.speed = 600 if not is_enemy else 300
        self.velocity = [vx * self.speed, vy * self.speed]
        self.is_enemy = is_enemy
        self.damage = 20 if not is_enemy else 10

    def update(self, delta_time):
        super().update(delta_time)
        
        if self.y < -self.height or self.y > SCREEN_HEIGHT + self.height or \
           self.x < -self.width or self.x > SCREEN_WIDTH + self.width:
            self.alive = False

    def draw(self, surface):
        if self.is_enemy:
            pygame.draw.rect(surface, RED, self.get_rect())
        else:
            pygame.draw.rect(surface, CYAN, self.get_rect())

class Enemy(Entity):
    def __init__(self, enemy_type):
        self.enemy_type = enemy_type
        if enemy_type == 'basic':
            super().__init__(random.randint(20, SCREEN_WIDTH - 20), -25, 25, 25)
            self.speed = 120
            self.health = 40
            self.max_health = 40
            self.score_value = 100
            self.color = ORANGE
            self.move_pattern = 'straight'
        elif enemy_type == 'fast':
            super().__init__(random.randint(20, SCREEN_WIDTH - 20), -20, 20, 20)
            self.speed = 250
            self.health = 20
            self.max_health = 20
            self.score_value = 150
            self.color = YELLOW
            self.move_pattern = 'zigzag'
            self.zigzag_offset = 0
        elif enemy_type == 'tank':
            super().__init__(random.randint(30, SCREEN_WIDTH - 30), -40, 50, 40)
            self.speed = 60
            self.health = 120
            self.max_health = 120
            self.score_value = 300
            self.color = RED
            self.move_pattern = 'straight'
        elif enemy_type == 'shooter':
            super().__init__(random.randint(30, SCREEN_WIDTH - 30), -30, 35, 35)
            self.speed = 80
            self.health = 50
            self.max_health = 50
            self.score_value = 200
            self.color = MAGENTA
            self.move_pattern = 'hover'
            self.hover_time = 0
            self.fire_rate = 1.5
            self.last_fire_time = 0
        
        self.velocity = [0, self.speed]

    def update(self, delta_time, player_x=None):
        super().update(delta_time)
        
        if self.move_pattern == 'zigzag':
            self.zigzag_offset += delta_time * 3
            self.velocity[0] = math.sin(self.zigzag_offset) * 80
        elif self.move_pattern == 'hover':
            self.hover_time += delta_time
            if self.y > 80 and self.y < 150:
                self.velocity[1] = 0
                self.velocity[0] = math.sin(self.hover_time * 2) * 40
        
        if self.y > SCREEN_HEIGHT + self.height:
            self.alive = False

    def draw(self, surface):
        if self.enemy_type == 'basic':
            points = [
                (self.x, self.y + self.height // 2),
                (self.x - self.width // 2, self.y - self.height // 2),
                (self.x + self.width // 2, self.y - self.height // 2)
            ]
            pygame.draw.polygon(surface, self.color, points)
        elif self.enemy_type == 'fast':
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.width // 2)
            pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), self.width // 4)
        elif self.enemy_type == 'tank':
            pygame.draw.rect(surface, self.color, self.get_rect())
            pygame.draw.rect(surface, (100, 0, 0), (self.x - self.width // 2 + 4, self.y - self.height // 2 + 4, self.width - 8, self.height - 8))
        elif self.enemy_type == 'shooter':
            points = [
                (self.x, self.y - self.height // 2),
                (self.x - self.width // 2, self.y + self.height // 2),
                (self.x, self.y + self.height // 4),
                (self.x + self.width // 2, self.y + self.height // 2)
            ]
            pygame.draw.polygon(surface, self.color, points)

    def fire(self, current_time, player_x, player_y):
        if self.enemy_type != 'shooter':
            return []
        
        if current_time - self.last_fire_time >= self.fire_rate:
            self.last_fire_time = current_time
            dx = player_x - self.x
            dy = player_y - self.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist > 0:
                vx = dx / dist
                vy = dy / dist
                return [Bullet(self.x, self.y, vx, vy, is_enemy=True)]
        return []

class PowerUp(Entity):
    def __init__(self, x, y, power_type):
        super().__init__(x, y, 20, 20)
        self.power_type = power_type
        self.speed = 80
        self.velocity = [0, self.speed]
        self.animation_time = 0
        
        if power_type == 'health':
            self.color = GREEN
            self.symbol = '+'
        elif power_type == 'shield':
            self.color = CYAN
            self.symbol = 'S'
        elif power_type == 'weapon':
            self.color = YELLOW
            self.symbol = 'W'
        elif power_type == 'score':
            self.color = MAGENTA
            self.symbol = '$'

    def update(self, delta_time):
        super().update(delta_time)
        self.animation_time += delta_time
        
        if self.y > SCREEN_HEIGHT + self.height:
            self.alive = False

    def draw(self, surface):
        pulse = 1 + math.sin(self.animation_time * 4) * 0.2
        size = int(self.width // 2 * pulse)
        
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), size)
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), size, 2)
        
        font = pygame.font.Font(None, 16)
        text = font.render(self.symbol, True, BLACK)
        text_rect = text.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(text, text_rect)

class WaveManager:
    def __init__(self):
        self.wave = 1
        self.enemies_spawned = 0
        self.enemies_per_wave = 5
        self.spawn_timer = 0
        self.spawn_interval = 1.5
        self.wave_complete = False

    def update(self, delta_time, enemies):
        if self.wave_complete:
            return None
        
        self.spawn_timer += delta_time
        
        if self.spawn_timer >= self.spawn_interval and self.enemies_spawned < self.enemies_per_wave:
            self.spawn_timer = 0
            self.enemies_spawned += 1
            
            if self.wave == 1:
                return Enemy('basic')
            elif self.wave == 2:
                return Enemy('basic' if random.random() > 0.3 else 'fast')
            elif self.wave == 3:
                return Enemy(random.choice(['basic', 'fast', 'shooter']))
            else:
                rand = random.random()
                if rand < 0.5:
                    return Enemy('basic')
                elif rand < 0.7:
                    return Enemy('fast')
                elif rand < 0.85:
                    return Enemy('shooter')
                else:
                    return Enemy('tank')
        
        if self.enemies_spawned >= self.enemies_per_wave and len(enemies) == 0:
            self.wave_complete = True
        
        return None

    def next_wave(self):
        self.wave += 1
        self.enemies_spawned = 0
        self.enemies_per_wave = 5 + (self.wave - 1) * 2
        self.spawn_interval = max(0.5, 1.5 - (self.wave - 1) * 0.1)
        self.wave_complete = False

class CameraShake:
    def __init__(self):
        self.intensity = 0
        self.duration = 0

    def shake(self, intensity, duration):
        self.intensity = intensity
        self.duration = duration

    def update(self, delta_time):
        if self.duration > 0:
            self.duration -= delta_time
            self.intensity *= 0.95
            if self.duration <= 0:
                self.intensity = 0

    def get_offset(self):
        if self.intensity <= 0:
            return (0, 0)
        return (random.uniform(-self.intensity, self.intensity),
                random.uniform(-self.intensity, self.intensity))

class HUD:
    def __init__(self):
        self.font = pygame.font.Font(None, 28)
        self.small_font = pygame.font.Font(None, 20)

    def draw(self, surface, player):
        score_text = self.font.render(f"Score: {player.score}", True, WHITE)
        surface.blit(score_text, (10, 10))

        lives_text = self.font.render(f"Lives: {'X' * player.lives}", True, RED)
        surface.blit(lives_text, (10, 40))

        health_percent = player.health / player.max_health
        health_color = GREEN if health_percent > 0.5 else YELLOW if health_percent > 0.25 else RED
        pygame.draw.rect(surface, BLACK, (SCREEN_WIDTH - 170, 10, 150, 20))
        pygame.draw.rect(surface, health_color, (SCREEN_WIDTH - 170, 10, 150 * health_percent, 20))
        health_text = self.small_font.render(f"HP: {player.health}/{player.max_health}", True, WHITE)
        surface.blit(health_text, (SCREEN_WIDTH - 165, 12))

        shield_percent = player.shield / player.max_shield
        pygame.draw.rect(surface, BLACK, (SCREEN_WIDTH - 170, 35, 150, 20))
        pygame.draw.rect(surface, CYAN, (SCREEN_WIDTH - 170, 35, 150 * shield_percent, 20))
        shield_text = self.small_font.render(f"Shield: {player.shield}/{player.max_shield}", True, WHITE)
        surface.blit(shield_text, (SCREEN_WIDTH - 165, 37))

        weapon_text = self.font.render(f"Weapon: Lv.{player.weapon_level}", True, YELLOW)
        surface.blit(weapon_text, (SCREEN_WIDTH - 170, 60))

class Menu:
    def __init__(self):
        self.font = pygame.font.Font(None, 56)
        self.small_font = pygame.font.Font(None, 36)
        self.options = ["Start Game", "Quit"]
        self.selected_index = 0

    def update(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP or event.key == pygame.K_w:
                self.selected_index = (self.selected_index - 1) % len(self.options)
            if event.key == pygame.K_DOWN or event.key == pygame.K_s:
                self.selected_index = (self.selected_index + 1) % len(self.options)

    def draw(self, surface):
        title_text = self.font.render("SPACE SHOOTER", True, CYAN)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4))
        surface.blit(title_text, title_rect)

        subtitle_text = self.small_font.render("Press ENTER to select", True, WHITE)
        subtitle_rect = subtitle_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        surface.blit(subtitle_text, subtitle_rect)

        for i, option in enumerate(self.options):
            y_pos = SCREEN_HEIGHT // 2 + 50 + i * 40
            if i == self.selected_index:
                text = self.small_font.render(option, True, CYAN)
                rect = text.get_rect(center=(SCREEN_WIDTH // 2, y_pos))
                pygame.draw.rect(surface, CYAN, (rect.x - 10, rect.y - 5, rect.width + 20, rect.height + 10), 2)
            else:
                text = self.small_font.render(option, True, WHITE)
                rect = text.get_rect(center=(SCREEN_WIDTH // 2, y_pos))
            surface.blit(text, rect)

class GameOverScreen:
    def __init__(self):
        self.font = pygame.font.Font(None, 56)
        self.small_font = pygame.font.Font(None, 36)

    def draw(self, surface, score):
        game_over_text = self.font.render("GAME OVER", True, RED)
        game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3))
        surface.blit(game_over_text, game_over_rect)

        score_text = self.small_font.render(f"Final Score: {score}", True, YELLOW)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        surface.blit(score_text, score_rect)

        restart_text = self.small_font.render("Press ENTER to restart", True, WHITE)
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
        surface.blit(restart_text, restart_rect)

        quit_text = self.small_font.render("Press ESC to quit", True, WHITE)
        quit_rect = quit_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 90))
        surface.blit(quit_text, quit_rect)

class PauseScreen:
    def __init__(self):
        self.font = pygame.font.Font(None, 56)
        self.small_font = pygame.font.Font(None, 36)

    def draw(self, surface):
        pause_text = self.font.render("PAUSED", True, YELLOW)
        pause_rect = pause_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3))
        surface.blit(pause_text, pause_rect)

        resume_text = self.small_font.render("Press ESC to resume", True, WHITE)
        resume_rect = resume_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        surface.blit(resume_text, resume_rect)

        quit_text = self.small_font.render("Press Q to quit", True, WHITE)
        quit_rect = quit_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
        surface.blit(quit_text, quit_rect)

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Space Shooter")
        
        self.clock = pygame.time.Clock()
        self.delta_time = 0
        self.last_time = pygame.time.get_ticks()
        
        self.game_state = GameState.MENU
        
        self.player = Player()
        self.bullets = []
        self.enemies = []
        self.powerups = []
        self.particle_system = ParticleSystem()
        self.star_background = StarBackground()
        self.wave_manager = WaveManager()
        self.camera_shake = CameraShake()
        self.hud = HUD()
        self.menu = Menu()
        self.game_over_screen = GameOverScreen()
        self.pause_screen = PauseScreen()

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        
        if event.type == pygame.KEYDOWN:
            if self.game_state == GameState.MENU:
                self.menu.update(event)
                if event.key == pygame.K_RETURN:
                    if self.menu.selected_index == 0:
                        self.start_game()
                    elif self.menu.selected_index == 1:
                        pygame.quit()
                        sys.exit()
            
            elif self.game_state == GameState.PLAYING:
                if event.key == pygame.K_ESCAPE:
                    self.game_state = GameState.PAUSED
            
            elif self.game_state == GameState.PAUSED:
                if event.key == pygame.K_ESCAPE:
                    self.game_state = GameState.PLAYING
                if event.key == pygame.K_q:
                    self.game_state = GameState.MENU
            
            elif self.game_state == GameState.GAME_OVER:
                if event.key == pygame.K_RETURN:
                    self.start_game()
                if event.key == pygame.K_ESCAPE:
                    self.game_state = GameState.MENU

    def update(self):
        if self.game_state != GameState.PLAYING:
            return
        
        keys = pygame.key.get_pressed()
        self.player.update(self.delta_time, keys)
        
        current_time = pygame.time.get_ticks() / 1000
        new_bullets = self.player.fire(current_time)
        if new_bullets:
            self.bullets.extend(new_bullets)
            for bullet in new_bullets:
                self.particle_system.add_laser_trail(bullet.x, bullet.y)
        
        self.star_background.update(self.delta_time)
        self.particle_system.update(self.delta_time)
        self.camera_shake.update(self.delta_time)
        
        new_enemy = self.wave_manager.update(self.delta_time, self.enemies)
        if new_enemy:
            self.enemies.append(new_enemy)
        
        if self.wave_manager.wave_complete:
            self.wave_manager.next_wave()
        
        for enemy in self.enemies[:]:
            enemy.update(self.delta_time, self.player.x)
            if not enemy.alive:
                self.enemies.remove(enemy)
                continue
            
            current_time = pygame.time.get_ticks() / 1000
            new_bullets = enemy.fire(current_time, self.player.x, self.player.y)
            if new_bullets:
                self.bullets.extend(new_bullets)
        
        for bullet in self.bullets[:]:
            bullet.update(self.delta_time)
            if not bullet.alive:
                self.bullets.remove(bullet)
        
        for powerup in self.powerups[:]:
            powerup.update(self.delta_time)
            if not powerup.alive:
                self.powerups.remove(powerup)
        
        self.check_collisions()
        
        if not self.player.alive:
            self.game_state = GameState.GAME_OVER

    def check_collisions(self):
        player_rect = self.player.get_rect()
        
        for bullet in self.bullets[:]:
            bullet_rect = bullet.get_rect()
            
            if bullet.is_enemy:
                if player_rect.colliderect(bullet_rect):
                    self.player.take_damage(bullet.damage)
                    self.bullets.remove(bullet)
                    self.camera_shake.shake(10, 0.2)
            else:
                for enemy in self.enemies[:]:
                    enemy_rect = enemy.get_rect()
                    if enemy_rect.colliderect(bullet_rect):
                        enemy.take_damage(bullet.damage)
                        self.bullets.remove(bullet)
                        self.particle_system.add_laser_trail(bullet.x, bullet.y)
                        
                        if not enemy.alive:
                            self.player.score += enemy.score_value
                            self.particle_system.add_explosion(enemy.x, enemy.y)
                            self.camera_shake.shake(5, 0.1)
                            
                            if random.random() < 0.15:
                                power_types = ['health', 'shield', 'weapon', 'score']
                                power_type = random.choice(power_types)
                                self.powerups.append(PowerUp(enemy.x, enemy.y, power_type))
                        break
        
        for enemy in self.enemies[:]:
            enemy_rect = enemy.get_rect()
            if player_rect.colliderect(enemy_rect):
                self.player.take_damage(50)
                enemy.take_damage(enemy.health)
                self.particle_system.add_explosion(enemy.x, enemy.y)
                self.camera_shake.shake(15, 0.3)
        
        for powerup in self.powerups[:]:
            powerup_rect = powerup.get_rect()
            if player_rect.colliderect(powerup_rect):
                self.apply_powerup(powerup)
                self.powerups.remove(powerup)

    def apply_powerup(self, powerup):
        if powerup.power_type == 'health':
            self.player.health = min(self.player.max_health, self.player.health + 30)
        elif powerup.power_type == 'shield':
            self.player.shield = min(self.player.max_shield, self.player.shield + 50)
        elif powerup.power_type == 'weapon':
            self.player.weapon_level = min(3, self.player.weapon_level + 1)
        elif powerup.power_type == 'score':
            self.player.score += 500

    def draw(self):
        self.screen.fill(BLACK)
        
        self.star_background.draw(self.screen)
        
        offset_x, offset_y = self.camera_shake.get_offset()
        shake_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        
        for powerup in self.powerups:
            powerup.draw(shake_surface)
        
        for bullet in self.bullets:
            bullet.draw(shake_surface)
        
        for enemy in self.enemies:
            enemy.draw(shake_surface)
        
        self.player.draw(shake_surface)
        
        self.particle_system.draw(shake_surface)
        
        self.screen.blit(shake_surface, (offset_x, offset_y))
        
        if self.game_state == GameState.PLAYING:
            self.hud.draw(self.screen, self.player)
        elif self.game_state == GameState.MENU:
            self.menu.draw(self.screen)
        elif self.game_state == GameState.PAUSED:
            self.pause_screen.draw(self.screen)
        elif self.game_state == GameState.GAME_OVER:
            self.game_over_screen.draw(self.screen, self.player.score)
        
        pygame.display.flip()

    def start_game(self):
        self.player = Player()
        self.bullets = []
        self.enemies = []
        self.powerups = []
        self.particle_system = ParticleSystem()
        self.wave_manager = WaveManager()
        self.camera_shake = CameraShake()
        self.game_state = GameState.PLAYING

    def run(self):
        running = True
        while running:
            current_time = pygame.time.get_ticks()
            self.delta_time = (current_time - self.last_time) / 1000
            self.last_time = current_time
            
            for event in pygame.event.get():
                self.handle_event(event)
            
            self.update()
            self.draw()
            
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    try:
        game = Game()
        game.run()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")
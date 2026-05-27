import os
import sys
import math
import time
import random
import traceback
import tkinter as tk
from PIL import Image, ImageTk

# Initialize Pygame and font safely
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame

try:
    pygame.font.init()
except Exception as e:
    print(f"Pygame font init warning: {e}", file=sys.stderr)

# Clean terminal sound bridge
def trigger_sound(name):
    try:
        from chaohub import play_sound_effect
        play_sound_effect(name)
    except Exception:
        pass

# ==============================================================================
# BASE PYGAME FRAME BRIDGING TKINTER CANVAS
# ==============================================================================
class PygameGameFrame(tk.Frame):
    def __init__(self, parent, width=600, height=400):
        super().__init__(parent, bg="#000000")
        self.width = width
        self.height = height
        
        # UI Container
        self.canvas = tk.Canvas(self, width=self.width, height=self.height, bg="#000000", highlightthickness=1, highlightbackground="#ff00ff")
        self.canvas.pack(expand=True, pady=10)
        
        # Offscreen Pygame surface
        self.pygame_surface = pygame.Surface((self.width, self.height))
        self.clock = pygame.time.Clock()
        
        # Non-blocking key states
        self.keys = {}
        
        # Pre-allocated image item for GC throttling
        self.photo = None
        self.image_item_id = self.canvas.create_image(0, 0, anchor="nw")
        
        # Binds
        self.canvas.bind("<FocusIn>", self.on_focus_in)
        self.canvas.bind("<FocusOut>", self.on_focus_out)
        self.canvas.bind("<Button-1>", lambda event: self.canvas.focus_set())
        self.canvas.bind("<KeyPress>", self.on_key_press)
        self.canvas.bind("<KeyRelease>", self.on_key_release)
        
        self.running = True
        self.error_state = False
        self.error_message = ""
        
        # Start game logic
        self.reset_game()
        self.run_loop()
        
        # Grab focus instantly on creation
        self.after(100, self.canvas.focus_set)

    def on_focus_in(self, event):
        self.canvas.config(highlightbackground="#00ffff")

    def on_focus_out(self, event):
        self.canvas.config(highlightbackground="#ff00ff")

    def on_key_press(self, event):
        key = event.keysym
        self.keys[key] = True
        self.handle_single_key(key)

    def on_key_release(self, event):
        key = event.keysym
        self.keys[key] = False

    def handle_single_key(self, key):
        """Override for discrete keystroke events (e.g. menus or single snaps)."""
        pass

    def reset_game(self):
        pass

    def update(self, dt):
        pass

    def draw(self, surface):
        pass

    def render_to_canvas(self):
        try:
            # Convert surface to raw RGBA bytes
            try:
                data = pygame.image.tostring(self.pygame_surface, "RGBA")
            except AttributeError:
                data = pygame.image.tobytes(self.pygame_surface, "RGBA")
                
            img = Image.frombytes("RGBA", (self.width, self.height), data)
            
            # Persistent PhotoImage update
            self.photo = ImageTk.PhotoImage(img)
            self.canvas.itemconfig(self.image_item_id, image=self.photo)
        except Exception as e:
            print(f"[ArcadeCore] Rendering failed: {e}", file=sys.stderr)

    def run_loop(self):
        if not self.running:
            return
            
        try:
            # Precison 60 FPS lock using Pygame clock
            dt_ms = self.clock.tick(60)
            dt = dt_ms / 1000.0
            dt = min(dt, 0.1)  # Cap step size to avoid warp speed anomalies
            
            if not self.error_state:
                self.update(dt)
                self.draw(self.pygame_surface)
            else:
                self.draw_error_screen(self.pygame_surface)
                
            self.render_to_canvas()
            
        except Exception as e:
            print(f"[ArcadeCore] Exception caught in frame loop: {e}", file=sys.stderr)
            traceback.print_exc()
            self.error_state = True
            self.error_message = f"RUNTIME FAULT: {str(e)[:40]}..."
            
        if self.running:
            self.after(1, self.run_loop)

    def draw_error_screen(self, surface):
        surface.fill((0, 0, 0))
        
        # Scanlines
        for y in range(0, self.height, 4):
            pygame.draw.line(surface, (15, 0, 15), (0, y), (self.width, y))
            
        font = pygame.font.SysFont("Courier", 18, bold=True)
        
        # Alert frame
        pygame.draw.rect(surface, (255, 0, 0), (50, 80, self.width - 100, 240), 2)
        
        title = font.render("☠ CORE INTRUSION EXCEPTION ☠", True, (255, 0, 0))
        surface.blit(title, (self.width // 2 - title.get_width() // 2, 110))
        
        msg = font.render(self.error_message.upper(), True, (255, 255, 255))
        surface.blit(msg, (self.width // 2 - msg.get_width() // 2, 160))
        
        prompt = font.render("PRESS 'R' TO REBOOT SEGMENT", True, (255, 255, 0))
        surface.blit(prompt, (self.width // 2 - prompt.get_width() // 2, 220))
        
        exit_prompt = font.render("PRESS 'ESC' TO TERMINATE PROGRAM", True, (0, 255, 255))
        surface.blit(exit_prompt, (self.width // 2 - exit_prompt.get_width() // 2, 260))

        if self.keys.get("r") or self.keys.get("R"):
            self.error_state = False
            self.reset_game()
        elif self.keys.get("Escape"):
            self.return_to_main_menu()

    def return_to_main_menu(self):
        self.running = False
        try:
            import __main__
            if hasattr(__main__, 'app') and __main__.app:
                __main__.app.switch_module("ARCHIVE CONTRABAND")
        except Exception as e:
            print(f"[ArcadeCore] Navigation escape failed: {e}", file=sys.stderr)

    def destroy(self):
        self.running = False
        super().destroy()


# ==============================================================================
# ENTITIES FOR CYBER BLOCK BREAKER
# ==============================================================================
class CyberBall:
    def __init__(self, x, y, dx, dy, radius=6):
        self.x = float(x)
        self.y = float(y)
        self.dx = float(dx)
        self.dy = float(dy)
        self.radius = radius
        self.is_caught = False
        self.offset_x = 0.0

class CyberBlock:
    def __init__(self, x, y, w, h, color, health, score_val):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = color
        self.health = health
        self.max_health = health
        self.score_val = score_val

class CyberPowerUp:
    def __init__(self, x, y, p_type, speed=130):
        self.x = float(x)
        self.y = float(y)
        self.type = p_type  # "EXPAND", "MULTI", "LASER", "STICKY"
        self.speed = speed
        self.width = 24
        self.height = 14

class CyberLaser:
    def __init__(self, x, y, speed=380):
        self.x = float(x)
        self.y = float(y)
        self.speed = speed
        self.width = 4
        self.height = 10


# ==============================================================================
# GAME 1: CYBER BLOCK BREAKER (CyberBreak)
# ==============================================================================
class CyberBreak(PygameGameFrame):
    def reset_game(self):
        self.score = 0
        self.high_score = 0
        self.lives = 3
        self.game_state = "MENU"  # "MENU", "PLAYING", "GAMEOVER", "VICTORY"
        
        self.base_paddle_width = 90
        self.paddle_width = self.base_paddle_width
        self.paddle_height = 10
        self.paddle_x = self.width // 2
        self.paddle_y = 360
        self.paddle_speed = 450.0
        
        self.balls = []
        self.blocks = []
        self.powerups = []
        self.lasers = []
        
        # State timers
        self.expand_timer = 0.0
        self.laser_timer = 0.0
        self.sticky_timer = 0.0
        self.is_sticky = False
        self.laser_cooldown = 0.0
        
        # Particles
        self.particles = []
        
        self.build_grid()
        self.spawn_initial_ball()

    def build_grid(self):
        self.blocks.clear()
        rows = 5
        cols = 8
        margin_x = 22
        margin_y = 60
        block_w = 68
        block_h = 16
        gap_x = 4
        gap_y = 6
        
        # Neon palette mapping [color, health, score]
        row_configs = [
            ((255, 255, 0), 3, 50),   # Yellow
            ((255, 0, 255), 2, 40),   # Magenta
            ((0, 255, 255), 2, 30),   # Cyan
            ((0, 255, 0), 1, 20),     # Matrix Green
            ((0, 255, 255), 1, 10)    # Cyan
        ]
        
        for r in range(rows):
            color, hp, score = row_configs[r]
            for c in range(cols):
                bx = margin_x + c * (block_w + gap_x)
                by = margin_y + r * (block_h + gap_y)
                self.blocks.append(CyberBlock(bx, by, block_w, block_h, color, hp, score))

    def spawn_initial_ball(self):
        self.balls.clear()
        ball = CyberBall(self.paddle_x, self.paddle_y - 15, 200, -220)
        ball.is_caught = True
        ball.offset_x = 0.0
        self.balls.append(ball)

    def handle_single_key(self, key):
        if self.game_state == "MENU":
            if key in ["s", "S"]:
                self.game_state = "PLAYING"
                trigger_sound("click")
        elif self.game_state in ["GAMEOVER", "VICTORY"]:
            if key in ["r", "R"]:
                self.reset_game()
                self.game_state = "PLAYING"
                trigger_sound("click")
            elif key == "Escape":
                self.return_to_main_menu()
        elif self.game_state == "PLAYING":
            if key == "Escape":
                self.return_to_main_menu()

    def spawn_debris(self, x, y, color, count=10):
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(50, 150)
            self.particles.append({
                "x": float(x),
                "y": float(y),
                "dx": speed * math.cos(angle),
                "dy": speed * math.sin(angle),
                "life": 0.4,
                "color": color
            })

    def update(self, dt):
        if self.game_state != "PLAYING":
            return
            
        # Update particles
        retained_particles = []
        for p in self.particles:
            p["x"] += p["dx"] * dt
            p["y"] += p["dy"] * dt
            p["life"] -= dt
            if p["life"] > 0:
                retained_particles.append(p)
        self.particles = retained_particles
            
        # Paddle movement
        if self.keys.get("Left"):
            self.paddle_x -= self.paddle_speed * dt
        if self.keys.get("Right"):
            self.paddle_x += self.paddle_speed * dt
            
        # Constrain paddle
        half_w = self.paddle_width / 2
        if self.paddle_x - half_w < 10:
            self.paddle_x = 10 + half_w
        if self.paddle_x + half_w > self.width - 10:
            self.paddle_x = self.width - 10 - half_w
            
        # Power-up state timers
        if self.expand_timer > 0:
            self.expand_timer -= dt
            self.paddle_width = int(self.base_paddle_width * 1.5)
        else:
            self.paddle_width = self.base_paddle_width
            
        if self.laser_timer > 0:
            self.laser_timer -= dt
            # Fire blasters on Spacebar
            if self.keys.get("space") and self.laser_cooldown <= 0:
                left_gun = self.paddle_x - half_w + 5
                right_gun = self.paddle_x + half_w - 5
                self.lasers.append(CyberLaser(left_gun, self.paddle_y))
                self.lasers.append(CyberLaser(right_gun, self.paddle_y))
                self.laser_cooldown = 0.28
                trigger_sound("beep")
        
        if self.laser_cooldown > 0:
            self.laser_cooldown -= dt
            
        if self.sticky_timer > 0:
            self.sticky_timer -= dt
            self.is_sticky = True
        else:
            self.is_sticky = False
            
        # Relaunch caught balls
        if self.keys.get("space") or self.keys.get("Up"):
            for ball in self.balls:
                if ball.is_caught:
                    ball.is_caught = False
                    ball.dy = -abs(ball.dy)
                    trigger_sound("click")
                    
        # Update balls
        dead_balls = []
        for ball in self.balls:
            if ball.is_caught:
                ball.x = self.paddle_x + ball.offset_x
                ball.y = self.paddle_y - self.paddle_height//2 - ball.radius
                continue
                
            # Physics updates
            ball.x += ball.dx * dt
            ball.y += ball.dy * dt
            
            # Wall reflection
            if ball.x - ball.radius < 10:
                ball.x = 10 + ball.radius
                ball.dx = abs(ball.dx)
                trigger_sound("click")
            elif ball.x + ball.radius > self.width - 10:
                ball.x = self.width - 10 - ball.radius
                ball.dx = -abs(ball.dx)
                trigger_sound("click")
                
            if ball.y - ball.radius < 40:
                ball.y = 40 + ball.radius
                ball.dy = abs(ball.dy)
                trigger_sound("click")
            elif ball.y + ball.radius > self.height:
                # Ball lost
                dead_balls.append(ball)
                continue
                
            # Paddle collision
            paddle_rect = pygame.Rect(self.paddle_x - half_w, self.paddle_y - self.paddle_height//2, self.paddle_width, self.paddle_height)
            ball_rect = pygame.Rect(ball.x - ball.radius, ball.y - ball.radius, ball.radius*2, ball.radius*2)
            
            if ball_rect.colliderect(paddle_rect) and ball.dy > 0:
                if self.is_sticky:
                    ball.is_caught = True
                    ball.offset_x = ball.x - self.paddle_x
                    trigger_sound("click")
                else:
                    # Angle calculation based on hit point
                    relative_hit = (ball.x - (self.paddle_x - half_w)) / self.paddle_width
                    relative_hit = max(0.0, min(1.0, relative_hit))
                    influence = (relative_hit - 0.5) * 2.0  # -1.0 to 1.0
                    
                    speed = math.hypot(ball.dx, ball.dy)
                    ball.dx = speed * influence * 0.8
                    ball.dy = -math.sqrt(max(0.15, speed**2 - ball.dx**2))
                    trigger_sound("click")
                    
            # Block collisions
            for block in self.blocks[:]:
                if ball_rect.colliderect(block.rect):
                    block.health -= 1
                    self.score += block.score_val
                    if self.score > self.high_score:
                        self.high_score = self.score
                        
                    # Handle block destruction
                    if block.health <= 0:
                        trigger_sound("explosion")
                        self.spawn_debris(block.rect.centerx, block.rect.centery, block.color, 12)
                        self.blocks.remove(block)
                        
                        # Power-up drop trigger (15% chance)
                        if random.random() < 0.15:
                            p_type = random.choice(["EXPAND", "MULTI", "LASER", "STICKY"])
                            self.powerups.append(CyberPowerUp(block.rect.centerx, block.rect.centery, p_type))
                    else:
                        trigger_sound("beep")
                        self.spawn_debris(ball.x, ball.y, block.color, 4)
                        
                    # Vector reflection math
                    overlap_x = min(ball_rect.right - block.rect.left, block.rect.right - ball_rect.left)
                    overlap_y = min(ball_rect.bottom - block.rect.top, block.rect.bottom - ball_rect.top)
                    
                    if overlap_x < overlap_y:
                        if ball.dx > 0 and ball.x < block.rect.centerx:
                            ball.dx = -abs(ball.dx)
                        elif ball.dx < 0 and ball.x > block.rect.centerx:
                            ball.dx = abs(ball.dx)
                    else:
                        if ball.dy > 0 and ball.y < block.rect.centery:
                            ball.dy = -abs(ball.dy)
                        elif ball.dy < 0 and ball.y > block.rect.centery:
                            ball.dy = abs(ball.dy)
                    break
                    
        # Remove dead balls
        for b in dead_balls:
            if b in self.balls:
                self.balls.remove(b)
                
        # Handle all balls lost
        if not self.balls:
            self.lives -= 1
            if self.lives > 0:
                self.spawn_initial_ball()
                # Clear active timers
                self.expand_timer = 0.0
                self.laser_timer = 0.0
                self.sticky_timer = 0.0
                trigger_sound("explosion")
            else:
                self.game_state = "GAMEOVER"
                trigger_sound("explosion")
                
        # Victory check
        if not self.blocks and self.game_state == "PLAYING":
            self.game_state = "VICTORY"
            trigger_sound("beep")
            
        # Update power-ups
        for pu in self.powerups[:]:
            pu.y += pu.speed * dt
            # Paddle capture logic
            pu_rect = pygame.Rect(pu.x - pu.width//2, pu.y - pu.height//2, pu.width, pu.height)
            pad_rect = pygame.Rect(self.paddle_x - half_w, self.paddle_y - self.paddle_height//2, self.paddle_width, self.paddle_height)
            
            if pu_rect.colliderect(pad_rect):
                trigger_sound("beep")
                self.apply_powerup(pu.type)
                self.powerups.remove(pu)
            elif pu.y > self.height:
                self.powerups.remove(pu)
                
        # Update lasers
        for l in self.lasers[:]:
            l.y -= l.speed * dt
            l_rect = pygame.Rect(l.x - l.width//2, l.y - l.height//2, l.width, l.height)
            
            # Offscreen check
            if l.y < 40:
                self.lasers.remove(l)
                continue
                
            # Block collisions
            hit = False
            for block in self.blocks[:]:
                if l_rect.colliderect(block.rect):
                    hit = True
                    block.health -= 1
                    self.score += block.score_val
                    if self.score > self.high_score:
                        self.high_score = self.score
                        
                    if block.health <= 0:
                        trigger_sound("explosion")
                        self.spawn_debris(block.rect.centerx, block.rect.centery, block.color, 12)
                        self.blocks.remove(block)
                        if random.random() < 0.15:
                            p_type = random.choice(["EXPAND", "MULTI", "LASER", "STICKY"])
                            self.powerups.append(CyberPowerUp(block.rect.centerx, block.rect.centery, p_type))
                    else:
                        trigger_sound("beep")
                        self.spawn_debris(l.x, l.y, block.color, 5)
                        
                    self.lasers.remove(l)
                    break
            if hit:
                continue

    def apply_powerup(self, p_type):
        if p_type == "EXPAND":
            self.expand_timer = 10.0
        elif p_type == "MULTI":
            new_balls = []
            for b in self.balls:
                speed = math.hypot(b.dx, b.dy)
                angle = math.atan2(b.dy, b.dx)
                for ang_offset in [-0.28, 0.28]:
                    n_ang = angle + ang_offset + random.uniform(-0.06, 0.06)
                    n_dx = speed * math.cos(n_ang)
                    n_dy = speed * math.sin(n_ang)
                    new_balls.append(CyberBall(b.x, b.y, n_dx, n_dy))
            self.balls.extend(new_balls)
        elif p_type == "LASER":
            self.laser_timer = 8.0
        elif p_type == "STICKY":
            self.is_sticky = True
            self.sticky_timer = 10.0

    def draw(self, surface):
        surface.fill((0, 0, 0))
        
        # Cyber-terminal grid background
        for y in range(40, self.height, 25):
            pygame.draw.line(surface, (8, 12, 8), (10, y), (self.width - 10, y))
        for x in range(10, self.width, 25):
            pygame.draw.line(surface, (8, 12, 8), (x, 40), (x, self.height))
            
        # Draw screen boundaries
        pygame.draw.rect(surface, (255, 0, 255), (10, 40, self.width - 20, self.height - 40), 1)
        
        # Draw HUD Panel
        pygame.draw.rect(surface, (11, 11, 11), (0, 0, self.width, 40))
        pygame.draw.line(surface, (0, 255, 255), (0, 40), (self.width, 40), 2)
        
        font = pygame.font.SysFont("Courier", 13, bold=True)
        hud_txt = font.render(f"SCORE: {self.score:05d}  HI-SCORE: {self.high_score:05d}", True, (0, 255, 255))
        surface.blit(hud_txt, (15, 12))
        
        # Draw lives
        lives_lbl = font.render("SYSTEM LIFE:", True, (0, 255, 0))
        surface.blit(lives_lbl, (self.width - 160, 12))
        for i in range(self.lives):
            lx = self.width - 60 + i * 16
            pygame.draw.rect(surface, (0, 255, 0), (lx, 15, 10, 8))
            
        # Draw blocks
        for block in self.blocks:
            # Draw inner block (shaded fill based on health)
            fill_color = (int(block.color[0]*0.15), int(block.color[1]*0.15), int(block.color[2]*0.15))
            pygame.draw.rect(surface, fill_color, block.rect)
            
            # Neon border outline
            pygame.draw.rect(surface, block.color, block.rect, 1)
            
            # Health tick bars
            tw = block.rect.width
            th = block.rect.height
            for h in range(block.health):
                tx = block.rect.left + 5 + h * 8
                ty = block.rect.top + 4
                pygame.draw.rect(surface, block.color, (tx, ty, 4, th - 8))
                
        # Draw power-ups
        for pu in self.powerups:
            # Draw capsule body
            color_map = {
                "EXPAND": (0, 255, 255),  # Cyan
                "MULTI": (0, 255, 0),    # Matrix Green
                "LASER": (255, 0, 255),  # Magenta
                "STICKY": (255, 255, 0)  # Yellow
            }
            color = color_map.get(pu.type, (255, 255, 255))
            px = int(pu.x - pu.width//2)
            py = int(pu.y - pu.height//2)
            pygame.draw.rect(surface, (0, 0, 0), (px, py, pu.width, pu.height))
            pygame.draw.rect(surface, color, (px, py, pu.width, pu.height), 1)
            
            # Symbol text inside
            sym_char = pu.type[0]
            sym = font.render(sym_char, True, color)
            surface.blit(sym, (px + pu.width//2 - sym.get_width()//2, py + pu.height//2 - sym.get_height()//2 + 1))
            
        # Draw lasers
        for l in self.lasers:
            lx = int(l.x - l.width//2)
            ly = int(l.y - l.height//2)
            pygame.draw.rect(surface, (255, 50, 50), (lx, ly, l.width, l.height))
            
        # Draw particles
        for p in self.particles:
            pygame.draw.circle(surface, p["color"], (int(p["x"]), int(p["y"])), 2)
            
        # Draw paddle
        half_w = self.paddle_width // 2
        px = int(self.paddle_x - half_w)
        py = int(self.paddle_y - self.paddle_height//2)
        
        # Paddle styling: cyan core, warning yellow edges
        pygame.draw.rect(surface, (0, 255, 255), (px, py, self.paddle_width, self.paddle_height))
        pygame.draw.rect(surface, (255, 255, 0), (px, py, 6, self.paddle_height))
        pygame.draw.rect(surface, (255, 255, 0), (px + self.paddle_width - 6, py, 6, self.paddle_height))
        
        # Powerup visual indicators
        if self.is_sticky:
            pygame.draw.rect(surface, (0, 255, 0), (px, py, self.paddle_width, self.paddle_height), 1)
        if self.laser_timer > 0:
            # Gun mounts
            pygame.draw.rect(surface, (255, 0, 255), (px - 2, py - 4, 4, 6))
            pygame.draw.rect(surface, (px + self.paddle_width - 2, py - 4, 4, 6))
            
        # Draw balls
        for ball in self.balls:
            bx = int(ball.x)
            by = int(ball.y)
            pygame.draw.circle(surface, (0, 255, 0), (bx, by), ball.radius)
            pygame.draw.circle(surface, (255, 255, 255), (bx, by), ball.radius - 2)
            
        # Scanlines
        for y in range(0, self.height, 4):
            pygame.draw.line(surface, (5, 5, 5), (0, y), (self.width, y))
            
        # Game states overlays
        large_font = pygame.font.SysFont("Courier", 24, bold=True)
        if self.game_state == "MENU":
            self.draw_overlay_screen(surface, "CYBER BLOCK BREAKER", "PRESS 'S' TO START PROGRAM", (0, 255, 255))
        elif self.game_state == "GAMEOVER":
            self.draw_overlay_screen(surface, "SYSTEM TERMINATED // GAME OVER", "PRESS 'R' TO REBOOT PROGRAM", (255, 0, 0))
        elif self.game_state == "VICTORY":
            self.draw_overlay_screen(surface, "TRANSACTION SECURED // VICTORY ACHIEVED", "PRESS 'R' TO REBOOT PROGRAM", (0, 255, 0))

    def draw_overlay_screen(self, surface, title_str, prompt_str, color):
        # Translucent terminal pane mockup
        pygame.draw.rect(surface, (0, 0, 0), (40, 100, self.width - 80, 200))
        pygame.draw.rect(surface, color, (40, 100, self.width - 80, 200), 2)
        
        font_lg = pygame.font.SysFont("Courier", 20, bold=True)
        font_sm = pygame.font.SysFont("Courier", 12, bold=True)
        
        t_surf = font_lg.render(title_str, True, color)
        p_surf = font_sm.render(prompt_str, True, (255, 255, 0))
        e_surf = font_sm.render("PRESS 'ESC' FOR MAIN ENCLAVE", True, (255, 255, 255))
        
        surface.blit(t_surf, (self.width//2 - t_surf.get_width()//2, 140))
        surface.blit(p_surf, (self.width//2 - p_surf.get_width()//2, 195))
        surface.blit(e_surf, (self.width//2 - e_surf.get_width()//2, 230))


# ==============================================================================
# ENTITIES FOR SHIFTING LANES RACER
# ==============================================================================
class CyberObstacle:
    def __init__(self, lane, y, obs_type):
        self.lane = lane
        self.y = float(y)
        self.type = obs_type  # "WALL", "BLOCKADE", "NODE"
        self.width = 65
        self.height = 22
        
        if obs_type == "WALL":
            self.width = 85
            self.height = 18
        elif obs_type == "BLOCKADE":
            self.width = 75
            self.height = 26
        elif obs_type == "NODE":
            self.width = 40
            self.height = 40


# ==============================================================================
# GAME 2: SHIFTING LANES RACER (NeonRunner)
# ==============================================================================
class NeonRunner(PygameGameFrame):
    def reset_game(self):
        self.score = 0
        self.high_score = 0
        self.game_state = "MENU"  # "MENU", "PLAYING", "GAMEOVER"
        
        # Lanes (Left: 180, Center: 300, Right: 420)
        self.lane_width = 120
        self.lanes = [180, 300, 420]
        
        self.current_lane = 1
        self.player_x = float(self.lanes[self.current_lane])
        self.player_y = 320.0
        self.player_width = 32
        self.player_height = 44
        
        # Speed dynamics
        self.base_speed = 220.0
        self.speed_multiplier = 1.0
        self.global_speed = self.base_speed
        
        # Endless scrolling variables
        self.scroll_y = 0.0
        
        self.obstacles = []
        self.spawn_timer = 0.0
        
        # Screen shake
        self.shake_time = 0.0
        self.shake_magnitude = 0.0
        self.shake_x = 0
        self.shake_y = 0
        
        # Decorative highway stars/particles
        self.ambient_stars = []
        for _ in range(35):
            self.ambient_stars.append({
                "x": random.randint(10, self.width - 10),
                "y": random.randint(0, self.height),
                "speed": random.uniform(1.2, 3.5),
                "size": random.randint(1, 2)
            })

    def handle_single_key(self, key):
        if self.game_state == "MENU":
            if key in ["s", "S"]:
                self.game_state = "PLAYING"
                trigger_sound("click")
        elif self.game_state == "GAMEOVER":
            if key in ["r", "R"]:
                self.reset_game()
                self.game_state = "PLAYING"
                trigger_sound("click")
            elif key == "Escape":
                self.return_to_main_menu()
        elif self.game_state == "PLAYING":
            if key in ["Left", "a", "A"] and self.current_lane > 0:
                self.current_lane -= 1
                trigger_sound("click")
            elif key in ["Right", "d", "D"] and self.current_lane < 2:
                self.current_lane += 1
                trigger_sound("click")
            elif key == "Escape":
                self.return_to_main_menu()

    def update(self, dt):
        # Update screen shake
        if self.shake_time > 0:
            self.shake_time -= dt
            self.shake_x = random.randint(-int(self.shake_magnitude), int(self.shake_magnitude))
            self.shake_y = random.randint(-int(self.shake_magnitude), int(self.shake_magnitude))
        else:
            self.shake_x = 0
            self.shake_y = 0
            
        if self.game_state != "PLAYING":
            return
            
        # Progressive velocity scaling: +0.05 every second
        self.speed_multiplier += 0.05 * dt
        self.global_speed = self.base_speed * self.speed_multiplier
        
        # Scroll highway background markers
        self.scroll_y = (self.scroll_y + self.global_speed * dt) % 60
        
        # Scroll ambient stars
        for star in self.ambient_stars:
            star["y"] += star["speed"] * self.global_speed * dt * 0.15
            if star["y"] > self.height:
                star["y"] = -10
                star["x"] = random.randint(10, self.width - 10)
                
        # Player lane tracking using exponential lerp
        target_x = float(self.lanes[self.current_lane])
        self.player_x += (target_x - self.player_x) * (1.0 - math.exp(-18 * dt))
        
        # Procedural spawn logic
        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            # Dynamic interval reduction scaled to multiplier
            spawn_interval = max(0.65, 1.7 / self.speed_multiplier)
            self.spawn_timer = spawn_interval + random.uniform(-0.15, 0.15)
            
            # 30% chance for a double-lane block at high speeds
            if self.speed_multiplier > 1.4 and random.random() < 0.35:
                # Double hazard (make sure one lane is open!)
                lanes = [0, 1, 2]
                blocked_lanes = random.sample(lanes, 2)
                for l in blocked_lanes:
                    o_type = random.choice(["WALL", "BLOCKADE", "NODE"])
                    self.obstacles.append(CyberObstacle(l, -40, o_type))
            else:
                # Single hazard
                l = random.choice([0, 1, 2])
                o_type = random.choice(["WALL", "BLOCKADE", "NODE"])
                self.obstacles.append(CyberObstacle(l, -40, o_type))
                
        # Update obstacles
        player_rect = pygame.Rect(self.player_x - self.player_width//2, self.player_y - self.player_height//2, self.player_width, self.player_height)
        
        for obs in self.obstacles[:]:
            obs.y += self.global_speed * dt
            
            # Screen exit check
            if obs.y > self.height + 40:
                self.obstacles.remove(obs)
                self.score += 10
                if self.score > self.high_score:
                    self.high_score = self.score
                continue
                
            # Collision detection (AABB check)
            obs_x = self.lanes[obs.lane]
            obs_rect = pygame.Rect(obs_x - obs.width//2, obs.y - obs.height//2, obs.width, obs.height)
            
            if player_rect.colliderect(obs_rect):
                # Trigger crash and screen shake
                self.game_state = "GAMEOVER"
                self.shake_time = 0.5
                self.shake_magnitude = 10.0
                trigger_sound("explosion")
                break

    def draw(self, surface):
        # Pre-shake clear
        surface.fill((0, 0, 0))
        
        # Secondary shake canvas offsets
        canvas_surface = pygame.Surface((self.width, self.height))
        canvas_surface.fill((0, 0, 0))
        
        # Ambient side space starfield
        for star in self.ambient_stars:
            pygame.draw.rect(canvas_surface, (100, 100, 100), (int(star["x"]), int(star["y"]), star["size"], star["size"]))
            
        # Draw highway lane separators
        # Lane bounds boundaries (Left road edge: 120, Right edge: 480)
        pygame.draw.line(canvas_surface, (0, 255, 255), (120, 0), (120, self.height), 2)
        pygame.draw.line(canvas_surface, (0, 255, 255), (480, 0), (480, self.height), 2)
        
        # Scrolling center division lane dashed markings
        dash_y = int(self.scroll_y) - 60
        while dash_y < self.height + 60:
            # Dividers between lane 0/1 and 1/2 (at x=240 and x=360)
            pygame.draw.line(canvas_surface, (0, 150, 150), (240, dash_y), (240, dash_y + 25), 1)
            pygame.draw.line(canvas_surface, (0, 150, 150), (360, dash_y), (360, dash_y + 25), 1)
            dash_y += 60
            
        # Draw cyber-obstacles
        font = pygame.font.SysFont("Courier", 11, bold=True)
        for obs in self.obstacles:
            ox = self.lanes[obs.lane]
            oy = int(obs.y)
            rx = ox - obs.width // 2
            ry = oy - obs.height // 2
            
            if obs.type == "WALL":
                # Wide magenta warning wall
                pygame.draw.rect(canvas_surface, (255, 0, 255), (rx, ry, obs.width, obs.height))
                pygame.draw.rect(canvas_surface, (0, 0, 0), (rx + 2, ry + 2, obs.width - 4, obs.height - 4))
                
                # Text inside
                t_lbl = font.render("LOCKED", True, (255, 0, 255))
                canvas_surface.blit(t_lbl, (ox - t_lbl.get_width()//2, oy - t_lbl.get_height()//2))
            elif obs.type == "BLOCKADE":
                # Saturated warning yellow blockade with caution lines
                pygame.draw.rect(canvas_surface, (255, 255, 0), (rx, ry, obs.width, obs.height), 2)
                # Draw hazard stripes
                for offset in range(0, obs.width, 10):
                    pygame.draw.line(canvas_surface, (255, 255, 0), (rx + offset, ry), (rx + min(obs.width, offset + 8), ry + obs.height - 2), 1)
            elif obs.type == "NODE":
                # Cyan neon diamond node
                pts = [
                    (ox, ry),
                    (rx + obs.width, oy),
                    (ox, ry + obs.height),
                    (rx, oy)
                ]
                pygame.draw.polygon(canvas_surface, (0, 255, 255), pts, 1)
                
                # Coordinate telemetry overlay
                dec_lbl = font.render("ERR_0x42", True, (0, 255, 255))
                canvas_surface.blit(dec_lbl, (ox - dec_lbl.get_width()//2, oy - dec_lbl.get_height()//2))
                
        # Draw player cyber-vehicle
        px = int(self.player_x)
        py = int(self.player_y)
        pw = self.player_width
        ph = self.player_height
        
        # Vehicle chassis: neon cyan arrowhead with magenta thruster core
        pts_chassis = [
            (px, py - ph//2),              # Nose tip
            (px + pw//2, py + ph//2),      # Right wing
            (px + pw//4, py + ph//3),      # Inner right notch
            (px - pw//4, py + ph//3),      # Inner left notch
            (px - pw//2, py + ph//2)       # Left wing
        ]
        pygame.draw.polygon(canvas_surface, (0, 255, 255), pts_chassis, 2)
        
        # Thruster flare: Matrix Green/Warning Yellow particles extending backwards
        boost_y = py + ph//2 + 5
        if self.game_state == "PLAYING" and int(time.time() * 20) % 2 == 0:
            pygame.draw.line(canvas_surface, (255, 255, 0), (px, boost_y), (px, boost_y + 12), 2)
            pygame.draw.line(canvas_surface, (0, 255, 0), (px - 4, boost_y), (px - 4, boost_y + 6), 1)
            pygame.draw.line(canvas_surface, (0, 255, 0), (px + 4, boost_y), (px + 4, boost_y + 6), 1)
            
        # Draw vehicle headlight vectors
        if self.game_state == "PLAYING":
            light_left = px - pw//4
            light_right = px + pw//4
            pygame.draw.polygon(canvas_surface, (0, 30, 30), [(light_left, py - ph//2), (light_left - 25, 0), (light_left + 15, 0)])
            pygame.draw.polygon(canvas_surface, (0, 30, 30), [(light_right, py - ph//2), (light_right - 15, 0), (light_right + 25, 0)])
            
        # Blit canvas surface to target window with shake offsets applied
        surface.blit(canvas_surface, (self.shake_x, self.shake_y))
        
        # Draw HUD Panel
        pygame.draw.rect(surface, (11, 11, 11), (0, 0, self.width, 40))
        pygame.draw.line(surface, (0, 255, 255), (0, 40), (self.width, 40), 2)
        
        hud_font = pygame.font.SysFont("Courier", 13, bold=True)
        hud_txt = hud_font.render(f"SCORE: {self.score:05d}  HI-SCORE: {self.high_score:05d}  MULTIPLIER: {self.speed_multiplier:.2f}X", True, (0, 255, 255))
        surface.blit(hud_txt, (15, 12))
        
        # Scanlines overlay
        for y in range(0, self.height, 4):
            pygame.draw.line(surface, (6, 6, 6), (0, y), (self.width, y))
            
        # Game Over / Start Menu Overlays
        if self.game_state == "MENU":
            self.draw_overlay_screen(surface, "SHIFTING LANES RACER", "PRESS 'S' TO START VEHICLE CORE", (0, 255, 255))
        elif self.game_state == "GAMEOVER":
            self.draw_overlay_screen(surface, "VEHICLE CORE SHATTERED // GAME OVER", "PRESS 'R' TO RE-CALIBRATE SPEED MULTIPLIER", (255, 0, 0))

    def draw_overlay_screen(self, surface, title_str, prompt_str, color):
        # Hologram prompt panel
        pygame.draw.rect(surface, (0, 0, 0), (40, 120, self.width - 80, 180))
        pygame.draw.rect(surface, color, (40, 120, self.width - 80, 180), 2)
        
        font_lg = pygame.font.SysFont("Courier", 18, bold=True)
        font_sm = pygame.font.SysFont("Courier", 11, bold=True)
        
        t_surf = font_lg.render(title_str, True, color)
        p_surf = font_sm.render(prompt_str, True, (255, 255, 0))
        e_surf = font_sm.render("PRESS 'ESC' TO DISCONNECT MATCH LINK", True, (255, 255, 255))
        
        surface.blit(t_surf, (self.width//2 - t_surf.get_width()//2, 155))
        surface.blit(p_surf, (self.width//2 - p_surf.get_width()//2, 205))
        surface.blit(e_surf, (self.width//2 - e_surf.get_width()//2, 240))

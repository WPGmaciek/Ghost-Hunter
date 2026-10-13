import pygame
import sys
import ctypes
import pygame.gfxdraw
import math
import random
import json

pygame.init()
pygame.mixer.init()
gun_sound = pygame.mixer.Sound("laser.wav")
fireball_sound = pygame.mixer.Sound("fireball.wav")
windowsize_x = 1920
windowsize_y = 1080
scale = ctypes.windll.shcore.GetScaleFactorForDevice(0) / 100
windowsize_x = int(windowsize_x / scale)
windowsize_y = int(windowsize_y / scale)
framerate = 60
screen = pygame.display.set_mode((windowsize_x, windowsize_y), pygame.RESIZABLE | pygame.DOUBLEBUF)
ctypes.windll.user32.ShowWindow(ctypes.windll.user32.GetForegroundWindow(), 3)
clock = pygame.time.Clock()
timer = 0

pygame.font.init()
font = pygame.font.Font(None, 36)

options = ["Play", "Settings", "High Scores"]
selected_option = 0
BUTTON_WIDTH = 200
BUTTON_HEIGHT = 50
BUTTON_SPACING = 20
MENU_OPTIONS = ["Play", "Settings", "High Scores"]
in_menu = True
menu_font = pygame.font.Font(None, 74)
def draw_button(screen, rect, text):
    pygame.draw.rect(screen, (50, 50, 50), rect)
    pygame.draw.rect(screen, (255, 255, 255), rect, 2)
    text_surface = font.render(text, True, (255, 255, 255))
    screen.blit(text_surface, (rect.x + (BUTTON_WIDTH - text_surface.get_width()) // 2, rect.y + (BUTTON_HEIGHT - text_surface.get_height()) // 2))

def show_menu():
    pygame.display.set_caption("Main Menu")
    menu_active = True
    button_rects = []
    for i, option in enumerate(MENU_OPTIONS):
        x = (windowsize_x - BUTTON_WIDTH) // 2
        y = (windowsize_y - (BUTTON_HEIGHT * len(MENU_OPTIONS) + BUTTON_SPACING * (len(MENU_OPTIONS) - 1))) // 2 + i * (BUTTON_HEIGHT + BUTTON_SPACING)
        button_rects.append(pygame.Rect(x, y, BUTTON_WIDTH, BUTTON_HEIGHT))

    while menu_active:
        screen.fill((0, 0, 0))

        for i, rect in enumerate(button_rects):
            draw_button(screen, rect, MENU_OPTIONS[i])

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = event.pos
                for i, rect in enumerate(button_rects):
                    if rect.collidepoint(mouse_pos):
                        if MENU_OPTIONS[i] == "Play":
                            menu_active = False 
                        elif MENU_OPTIONS[i] == "Settings":
                            print("Settings clicked")
                        elif MENU_OPTIONS[i] == "High Scores":
                            print("High Scores clicked")

        pygame.display.flip()
        clock.tick(60)

player_size = 40
player_surface = pygame.Surface((player_size, player_size))
player_rect = player_surface.get_rect(center=(windowsize_x / 2, windowsize_y / 2))
damage_timer = 10

vision_radius = 320
beam_width = math.pi / 2.5
angle = 0
target_angle = angle
last_direction=None
direction = {'N': 0, 'S': 0, 'E': 0, 'W': 0}

stamina, max_stamina, stamina_regen = 100, 100, 10
walk_speed, sprint_speed = 2, 3
sprinting = False
health, max_health = 100, 100
current_speed_x, current_speed_y = 0, 0
acceleration, deceleration = 0.2, 0.2
zero_threshold = 0.11
root2 = math.sqrt(2)

ghost_no = 8
class Ghost:
    def __init__(self):
        global ghost_no
        ghost_no += 1
        if ghost_no % 2 == 0:
            self.x = random.choice([random.randint(windowsize_x - 100, windowsize_x + 100), random.randint(-100, 100)])
            self.y = random.randint(0, windowsize_y)
        else:
            self.y = random.choice([random.randint(windowsize_x - 100, windowsize_x + 100), random.randint(-100, 100)])
            self.x = random.randint(0, windowsize_x)
        self.speed = 1.5
        self.size = 20
        self.color = (255, 255, 255, 16)
    def overlap(self, other):
        if isinstance(other, Ghost):
            distance = math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)
            return distance < (self.size + other.size)
        if isinstance(other, list):
            return self.point_in_polygon((self.x, self.y), other)
        elif isinstance(other, tuple):
            distance = math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)
            return distance < (self.size + vision_radius/4)
        elif isinstance(other, pygame.Rect):
            ghost_rect = pygame.Rect(self.x - self.size, self.y - self.size, self.size * 2, self.size * 2)
            return ghost_rect.colliderect(other)
        return False
   
    def point_in_polygon(self, point, polygon):
        x, y = point
        inside = False
        n = len(polygon)
        p1x, p1y = polygon[0]
        for i in range(n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                         inside = not inside
            p1x, p1y = p2x, p2y
        return inside
    def visible_t2(self):
        dist_x = player_rect.centerx - self.x
        dist_y = player_rect.centery - self.y
        distance = math.sqrt(dist_x**2 + dist_y**2)
        if distance < vision_radius / 4:
            return True
    def move(self):
        global torch1, damage
        dist_x = player_rect.centerx - self.x
        dist_y = player_rect.centery - self.y
        distance = math.sqrt(dist_x**2 + dist_y**2)
        if self.overlap(torch1) == False:
            if distance > 0:
                dist_x /= distance
                dist_y /= distance
                hyp = (dist_x ** 2 + dist_y ** 2) ** 0.5
                if hyp != 0:
                    self.x += (dist_x / hyp) * self.speed
                    self.y += (dist_y / hyp) * self.speed
            if self.x < 0:
                self.x = windowsize_x
            elif self.x > windowsize_x:
                self.x = 0
            if self.y < 0:
                self.y = windowsize_y
            elif self.y > windowsize_y:
                self.y = 0
            for ghost in ghosts:
                if ghost != self and self.overlap(ghost):
                    if self.x > ghost.x:
                        self.x += 1
                    else:
                        self.x -= 1
                    if self.y > ghost.y:
                        self.y += 1
                    else:
                        self.y -= 1
            opacity = 16
        if self.overlap(torch1) or self.visible_t2():
            opacity = max(0, min(255, int(255 * (1 - 0.6 * distance / vision_radius))))
        self.color = (255, 255,255 , opacity)
        pygame.gfxdraw.filled_circle(screen, int(self.x), int(self.y), self.size, self.color)
        pygame.gfxdraw.aacircle(screen, int(self.x), int(self.y), self.size, self.color)

def update_ghosts():
    global ghost_spawn_timer
    if ghost_spawn_timer > 0:
        ghost_spawn_timer -= 1
    if len(ghosts) < ghost_num and ghost_spawn_timer <= 0:
        new_ghost = Ghost()
        ghosts.append(new_ghost)
        ghost_spawn_timer = ghost_spawn_cooldown
ghost_spawn_timer = 0
ghost_spawn_cooldown = 40
ghost_num = 8
ghosts = []
ghosts_killed = 0
def draw_stamina_bar():
    bar_width = 20
    bar_height = 200
    bar_x = windowsize_x - 40
    bar_y = windowsize_y // 2 - bar_height // 2

    current_bar_height = int((stamina / max_stamina) * bar_height)
    pygame.draw.rect(screen, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height))
    pygame.draw.rect(screen, (255, 255, 0), (bar_x, bar_y + (bar_height - current_bar_height), bar_width, current_bar_height))
    stamina_text_surface = font.render(str(int(stamina))+" Stamina", True, (80, 80, 80))
    stamina_text_surface = pygame.transform.rotate(stamina_text_surface, 90)
    text_x = bar_x - 2
    text_y = bar_y + (bar_height - stamina_text_surface.get_height()) // 2
    screen.blit(stamina_text_surface, (text_x, text_y))
def player_move():
    global current_speed_x, current_speed_y, angle, stamina, sprinting, target_angle, player_velocity, move_x, move_y

    if sprinting and stamina > 0:
        player_speed = sprint_speed
        stamina -= (current_speed_x**2 + current_speed_y**2)**0.5 / 5
        if stamina < 0:
            stamina = 0
            sprinting = False
    else:
        player_speed = walk_speed
        stamina = min(max_stamina, stamina + stamina_regen / 60)

    move_x = (direction['E'] - direction['W']) * player_speed
    move_y = (direction['S'] - direction['N']) * player_speed

    if move_x and move_y:
        move_x *= 1 / root2
        move_y *= 1 / root2

    if move_x != 0:
        current_speed_x += (move_x - current_speed_x) * acceleration
        if abs(current_speed_x - move_x) < zero_threshold:
            current_speed_x = move_x
    else:
        if abs(current_speed_x) < zero_threshold:
            current_speed_x = 0
        elif current_speed_x > 0:
            current_speed_x -= deceleration
        elif current_speed_x < 0:
            current_speed_x += deceleration

    if move_y != 0:
        current_speed_y += (move_y - current_speed_y) * acceleration
        if abs(current_speed_y - move_y) < zero_threshold:
            current_speed_y = move_y
    else:
        if abs(current_speed_y) < zero_threshold:
            current_speed_y = 0
        elif current_speed_y > 0:
            current_speed_y -= deceleration
        elif current_speed_y < 0:
            current_speed_y += deceleration

    current_speed_x = round(current_speed_x, 3)
    current_speed_y = round(current_speed_y, 3)

    player_rect.x += current_speed_x
    player_rect.y += current_speed_y

    player_velocity = (current_speed_x**2 + current_speed_y**2)**0.5

    if -1.2 < current_speed_x < 1.2 and -1.2 < current_speed_y < 1.2:
        if direction['N'] and direction['E']:
            target_angle = -math.pi / 4
        elif direction['N'] and direction['W']:
            target_angle = -3 * math.pi / 4
        elif direction['S'] and direction['E']:
            target_angle = math.pi / 4
        elif direction['S'] and direction['W']:
            target_angle = 3 * math.pi / 4
        elif direction['E']:
            target_angle = 0
        elif direction['W']:
            target_angle = math.pi
        elif direction['N']:
            target_angle = -math.pi / 2
        elif direction['S']:
            target_angle = math.pi / 2
    else:
        target_angle = math.atan2(current_speed_y, current_speed_x)

    angle += ((target_angle - angle + math.pi) % (2 * math.pi) - math.pi) * 0.1

def draw_attack_bar():
    cooldown_bar_width = player_size
    cooldown_bar_height = 6
    cooldown_bar_x = player_rect.centerx - cooldown_bar_width // 2
    cooldown_bar_y = player_rect.top - 10
    cooldown = attack_frame / attack_cooldown
    filled_width = int(cooldown_bar_width * cooldown)
    pygame.draw.rect(screen, (100, 100, 100), (cooldown_bar_x, cooldown_bar_y, cooldown_bar_width, cooldown_bar_height))
    pygame.draw.rect(screen, (255, 255, 255), (cooldown_bar_x, cooldown_bar_y, filled_width, cooldown_bar_height))
attack_cooldown = 90
attack_frame = 0
xp = 0
level = 0
def attack():
    global attack_frame, ghosts_killed, xp
    if attack_frame < attack_cooldown:
        attack_frame += 1
    draw_attack_bar()
    if attack_frame == attack_cooldown:
        target = None
        min_distance = float('inf')
        for ghost in ghosts:
            if ghost.overlap(torch1) or ghost.visible_t2():
                distance = math.sqrt((ghost.x - player_rect.centerx) ** 2 + (ghost.y - player_rect.centery) ** 2)
                if distance < min_distance:
                    min_distance = distance
                    target = ghost
        if target:
            pygame.draw.line(screen, (255, 0, 0), player_rect.center, (target.x, target.y), 5)
            gun_sound.play()
            ghosts.remove(target)
            attack_frame = 0
            ghosts_killed += 1
            xp +=10
def level_up():
    global level, upgrades
    level += 1

    semi_transparent_overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    semi_transparent_overlay.fill((0, 0, 0, 128))  
    selected_upgrades = choose_three_upgrades()
    button_texts = [upgrade.name + " " + str(upgrade.tier) for upgrade in selected_upgrades]
    button_base_color = (50, 50, 50)
    button_hover_color = (80, 80, 80)
    button_border_color = (255, 255, 255)
    button_font = pygame.font.Font(None, 36)

    button_width, button_height = 300, 60
    button_margin = 120
    button_rects = []

    total_buttons_width = len(button_texts) * button_width + (len(button_texts) - 1) * button_margin
    start_x = (windowsize_x - total_buttons_width) // 2

    for i in range(len(button_texts)):
        x = start_x + i * (button_width + button_margin)
        y = (windowsize_y - button_height) // 2
        button_rects.append(pygame.Rect(x, y, button_width, button_height))

    selected_option = None
    while selected_option is None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()
                for i, rect in enumerate(button_rects):
                    if rect.collidepoint(mouse_pos):
                        selected_option = i
                        break

        for i, rect in enumerate(button_rects):
            color = button_hover_color if rect.collidepoint(pygame.mouse.get_pos()) else button_base_color
            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, button_border_color, rect, 2)

            text_surf = button_font.render(button_texts[i], True, (255, 255, 255))
            text_rect = text_surf.get_rect(center=rect.center)
            screen.blit(text_surf, text_rect)

        pygame.display.update(button_rects)

    direction.clear()
    direction.update({'N': 0, 'S': 0, 'E': 0, 'W': 0})  
    pygame.event.clear()
    print(f"Selected option: {button_texts[selected_option]}")

    upgrade = selected_upgrades[selected_option]
    print(upgrade)
    if upgrade.type == "ability":
        abilities[upgrade.name.replace(" ", "_").lower()] = True
        upgrades.remove(upgrade)
    elif upgrade.type == "stat":
        standard_name = upgrade.name.replace(" ", "_").lower()
        eval(standard_name)(upgrade.tier)
    else:
        print("This upgrade currently does nothing")

abilities = {}
upgrades = []
RARITIES = {    
    "Common": 60,
    "Rare": 25,
    "Epic": 10,
    "Legendary": 5 }
fireballframe, fireballcounter = 0, 0
firing = False
fireball_colour = pygame.image.load("fireball_colour.png").convert_alpha()
fireball_grayscale = pygame.image.load("fireball_grayscale.png").convert_alpha()
def fireball():
    global fireballframe, fireballcounter, xp, ghosts_killed, firing, screen, fireball_sound
    cooldown = 600
    size = 50
    fireball_x, fireball_y = pygame.mouse.get_pos()
    fireball_rect = pygame.Rect(fireball_x - size, fireball_y - size, size * 2, size * 2)
    if fireballcounter != cooldown:
        fireballcounter += 1
    if firing == True:
        fireballcounter = 0
        fireballframe = fireballframe + 1
        if fireballframe < 30:
            pygame.gfxdraw.filled_circle(screen, fireball_x, fireball_y, size, (255, 160, 0))
            pygame.gfxdraw.aacircle(screen, fireball_x, fireball_y, size, (255, 160, 0))
        else:
            pygame.gfxdraw.filled_circle(screen, fireball_x, fireball_y, size, (255, 0, 0))
            pygame.gfxdraw.aacircle(screen, fireball_x, fireball_y, size, (255, 160, 0))
            fireball_sound.play()
            for ghost in ghosts:
                if ghost.overlap(fireball_rect):
                    ghosts.remove(ghost)
                    ghosts_killed += 1
                    xp +=10
            firing = False
            fireballframe = 0

    fraction = 1 - ((cooldown - fireballcounter) / cooldown)
    colour_height = int(fireball_colour.get_height() * fraction)
    blended_image = pygame.Surface(fireball_colour.get_size(), pygame.SRCALPHA)
    blended_image.blit(fireball_grayscale, (0, 0))

    if colour_height > 0:
        coloured_rect = pygame.Rect(0, fireball_colour.get_height() - colour_height, 
                                fireball_colour.get_width(), colour_height)
        blended_image.blit(fireball_colour, (0, fireball_colour.get_height() - colour_height), coloured_rect)

    screen.blit(blended_image, (20, screen.get_height()-screen.get_height() / 8))

health_regeneration = 0 
def health_regen():
    global health, max_health, health_regeneration
    if health < max_health:
        health += health_regeneration
        health = round(health, 1)
    else:
        health = max_health
    
def health_regen_boost(tier):
    global health_regeneration
    health_regeneration += 0.05 * tier
def health_boost(tier):
    global max_health, health
    if tier == 4:
        max_health *= 1.5
        health *= 1.5
    else:
        health *= (max_health + 20 * tier) / max_health
        max_health += 20 * tier
    health = round(health)
    max_health = round(max_health)
def max_stamina_boost(tier):
    global max_stamina
    if tier == 4:
        max_stamina *= 1.5
    else:
        max_stamina += 20 * tier
def stamina_regen_boost(tier):
    global stamina_regen
    if tier ==4:
        stamina_regen *= 1.5
    else:
        stamina_regen += tier * 2
def speed_boost(tier):
    global walk_speed, sprint_speed
    if tier == 4:
        walk_speed *= 1.25
        sprint_speed *= 1.25
    else:
        walk_speed += 0.05 * tier
        sprint_speed += 0.075 * tier
def attack_speed_boost(tier):
    global attack_cooldown
    attack_cooldown *= 1 - tier / 20
    attack_cooldown = int(attack_cooldown)

class upgrade:
    global upgrades
    def __init__(self, name, description, rarity, type):
        self.name = name
        self.description = description
        self.rarity = rarity
        self.type = type

    def load_from_file():
        with open("upgrades.json", 'r') as file:
            data = json.load(file)
            return [upgrade(**entry) for entry in data]
upgrades = upgrade.load_from_file()
for upgrade in upgrades:
    if upgrade.type == "ability":
        abilities[upgrade.name.replace(" ", "_").lower()] = False
def choose_three_upgrades():
    global upgrades
    upgrades_by_rarity = {}
    for upgrade in upgrades:
        upgrades_by_rarity.setdefault(upgrade.rarity, []).append(upgrade)

    selected_upgrades = []
    while len(selected_upgrades) < 3:
        chosen_rarity = random.choices(list(RARITIES.keys()), weights=RARITIES.values())[0]

        if chosen_rarity in upgrades_by_rarity:
            available_upgrades = [upgrade for upgrade in upgrades_by_rarity[chosen_rarity] if upgrade not in selected_upgrades]
            if available_upgrades:
                selected_upgrade = random.choice(available_upgrades)
                if selected_upgrade.type == "stat":
                    rarity_list = list(RARITIES.keys())
                    tier_rarity = random.choices((rarity_list), weights=RARITIES.values())[0]
                    selected_upgrade.tier = rarity_list.index(tier_rarity) + 1
                else:
                    selected_upgrade.tier = ""
                selected_upgrades.append(selected_upgrade)

        if len(selected_upgrades) >= len(upgrades):
            break
    return selected_upgrades

def draw_xp_bar():
    global xp
    global level
    xp_needed = 100 + 10 * level
    xp_bar_width = 500
    xp_bar_height = 20
    xp_bar_x = windowsize_x // 2 - xp_bar_width // 2
    xp_bar_y = 40
    cooldown = xp / xp_needed
    filled_width = int(xp_bar_width * cooldown)
    pygame.draw.rect(screen, (100, 100, 100), (xp_bar_x, xp_bar_y, xp_bar_width, xp_bar_height))
    pygame.draw.rect(screen, (255, 255, 255), (xp_bar_x, xp_bar_y, filled_width, xp_bar_height))
    if cooldown >= 1:
        xp = 0
        level_up()
dcount = 0
def apply_damage():
    global damage, dcount, health
    if damage > 0:
        dcount = dcount + 1
        overlay = pygame.Surface((screen.get_width(), screen.get_height()), pygame.SRCALPHA)
        transparency = 100 + dcount
        if transparency > 255:
            transparency = 255
        overlay.fill((255, 255, 255, transparency))
        screen.blit(overlay, (0,0))
    else:
        dcount = 0
    if dcount > 10:
        health -= 1 * damage

def draw_text():
    fps_text = font.render(f"FPS: {int(fps)}", True, (255, 255, 255))
    screen.blit(fps_text, (10, 10))

    minutes = int(timer // 60)
    seconds = int(timer % 60)
    timer_text = font.render(f'Time: {minutes:02}:{seconds:02}', True, (255, 255, 255))
    screen.blit(timer_text, (screen.get_width() - timer_text.get_width() - 10, 10))

    ghosts_killed_text = font.render(f'Ghosts Killed: {ghosts_killed}', True, (255, 255, 255))
    screen.blit(ghosts_killed_text, (screen.get_width() - ghosts_killed_text.get_width() - 10, 50))

    velocity_text = font.render(f"Velocity: {player_velocity}", True, (255, 255, 255))
    screen.blit(velocity_text, (10, 50))

    health_text = font.render(f"Health: {health}/{max_health}", True, (255, 255, 255))
    screen.blit(health_text, (10, 90))

    cooldown_text = font.render(f"Attack Cooldown: {attack_cooldown}", True, (255, 255, 255))
    screen.blit(cooldown_text, (10, 130))
show_menu()
pygame.display.set_caption("Game")
while True:
    clock.tick(framerate)
    fps = clock.get_fps()
    timer += 1/fps
    screen.fill((0, 0, 0))
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()
        if event.type in (pygame.KEYDOWN, pygame.KEYUP):
            value = event.type == pygame.KEYDOWN
            if event.key == pygame.K_w: direction['N'] = value
            if event.key == pygame.K_d: direction['E'] = value
            if event.key == pygame.K_s: direction['S'] = value
            if event.key == pygame.K_a: direction['W'] = value
            if event.key == pygame.K_LSHIFT: sprinting = value
            if event.key == pygame.K_f:
                if fireballcounter == 600:
                    firing = True
                    fireballcounter = 0

    player_move()

    tip = (player_rect.centerx, player_rect.centery)
    left_point = (tip[0] + vision_radius * math.cos(angle - math.pi / 6),
                  tip[1] + vision_radius * math.sin(angle - math.pi / 6))
    right_point = (tip[0] + vision_radius * math.cos(angle + math.pi / 6),
                   tip[1] + vision_radius * math.sin(angle + math.pi / 6))
    
    
    
    
    torches = 40
    for torch_no in range(torches):
        colour_no = 150 / torches * torch_no + 10
        pygame.gfxdraw.filled_circle(screen, player_rect.centerx, player_rect.centery, int(vision_radius / 4 / torches * (torches -torch_no)), (0, colour_no, colour_no))
        
        
    num_arc_points = 8
    torches2 = 100
    for torch_no in range (torches2):
        arc_points = []
        for i in range(num_arc_points + 1):
            theta = angle - beam_width / 2 + (beam_width) * (i / num_arc_points)
            arc_x = tip[0] + (vision_radius / torches2 * (torches2 -torch_no)) * math.cos(theta)
            arc_y = tip[1] + (vision_radius / torches2 * (torches2 - torch_no)) * math.sin(theta)
            arc_points.append((arc_x, arc_y))
        colour_no = 200 / torches2 * torch_no + 10
        if torch_no == 0:
            torch1 = [tip] + arc_points
        pygame.gfxdraw.filled_polygon(screen, [tip] + arc_points, (0, colour_no, colour_no))
        pygame.gfxdraw.aapolygon(screen, [tip] + arc_points, (0, colour_no, colour_no))
        

    
    pygame.draw.rect(player_surface, (255, 0, 0), (0, 0, 80, 80))
    screen.blit(player_surface, player_rect.topleft)

    attack()
    health_regen()
    update_ghosts()
    damage = 0
    for ghost in ghosts:
        ghost.move()
        if ghost.overlap(player_rect):
            damage += 1
    apply_damage()
    draw_stamina_bar()
    draw_xp_bar()
    draw_text()
    for ability, active in abilities.items():
        if active:
            globals()[ability]()
    if health <= 0:
        pygame.quit()
        print("GAME OVER")
        break
    pygame.display.update()
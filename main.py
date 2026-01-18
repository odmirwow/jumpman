import pgzrun
import random
import math

# screen settings
WIDTH = 1024
HEIGHT = 768
TITLE = "Jumpman"

# game states
STATE_MENU = "menu"
STATE_PLAYING = "playing"
STATE_GAME_OVER = "game_over"
STATE_WIN = "win"
game_state = STATE_MENU
sound_enabled = True

# physics
GRAVITY = 0.6
JUMP_FORCE = -14
MOVE_SPEED = 4

# tiles
TILE_SIZE = 64
GROUND_Y = HEIGHT - TILE_SIZE

# Obscatles
HILL = 420
HILL_HEIGHT = 2 * TILE_SIZE


# CLASSES
class Platform:
    def __init__(self, image, pos, is_ground=False):
        self.actor = Actor(image, topleft=pos)
        self.is_ground = is_ground
    def draw(self):
        self.actor.draw()

def create_floating_platform(x, y, length):
    return [Platform("tiles/platform", (x + i * TILE_SIZE, y)) for i in range(length)]

class Hero:
    def __init__(self, pos):
        self.actor = Actor("hero/idle_0", topleft=pos)

        self.velocity_y = 0
        self.previous_bottom = self.actor.bottom
        self.on_ground = True #false

        self.idle_frames = ["hero/idle_0", "hero/idle_1"]
        self.run_frames = ["hero/run_0", "hero/run_1"]
        self.jump_frame = "hero/jump"

        self.frame_index = 0
        self.animation_timer = 0

    #hitbox
    def get_hitbox(self):
        width = 70
        height = 90
        x = self.actor.centerx - width // 2
        y = self.actor.bottom - height
        return (x, y, width, height)

    def update(self, platforms):
        self.previous_bottom = self.actor.bottom
        self.apply_gravity()
        self.move_horizontal()
        self.check_platform_collisions(platforms)
        self.update_animation()

    def apply_gravity(self):
        self.velocity_y += GRAVITY
        self.actor.y += self.velocity_y

    def move_horizontal(self):
        if keyboard.left:
            self.actor.x -= MOVE_SPEED
        if keyboard.right:
            self.actor.x += MOVE_SPEED

        #Screen Limits
        self.actor.x = max(0, min(WIDTH, self.actor.x))


    def jump(self):
        if self.on_ground:
            self.velocity_y = JUMP_FORCE
            self.on_ground = False
            if sound_enabled:
                sounds.jump.play()

    def check_platform_collisions(self, platforms):
        self.on_ground = False

        hx, hy, hw, hh = self.get_hitbox()

        for platform in platforms:
            px = platform.actor.left
            py = platform.actor.top
            pw = platform.actor.width
            ph = platform.actor.height

            horizontal_overlap = hx + hw > px and hx < px + pw

            if platform.is_ground and horizontal_overlap:
                if self.velocity_y >= 0 and self.actor.bottom >= py:
                    self.actor.bottom = py
                    self.velocity_y = 0
                    self.on_ground = True
                    return

            if not platform.is_ground:
                vertical_cross = (
                    self.velocity_y >= 0
                    and self.previous_bottom <= py
                    and hy + hh >= py
                )

                if horizontal_overlap and vertical_cross:
                    self.actor.bottom = py
                    self.velocity_y = 0
                    self.on_ground = True
                    return


    def update_animation(self):
        self.animation_timer += 1

        if not self.on_ground:
            self.actor.image = self.jump_frame
            return

        frames = (
            self.run_frames if (keyboard.left or keyboard.right) else self.idle_frames
        )

        if self.animation_timer % 10 == 0:
            self.frame_index = (self.frame_index + 1) % len(frames)
            self.actor.image = frames[self.frame_index]

    def check_enemy_collision(self, enemies):
        hx, hy, hw, hh = self.get_hitbox()

        for enemy in enemies:
            ex, ey, ew, eh = enemy.get_hitbox()

            if hx < ex + ew and hx + hw > ex and hy < ey + eh and hy + hh > ey:
                return True

        return False

    def draw(self):
        self.actor.draw()

class Enemy:
    def __init__(self, pos, left_limit, right_limit):
        self.actor = Actor("enemies/enemy_idle_0", topleft=pos)

        self.left_limit = left_limit
        self.right_limit = right_limit
        self.direction = 1
        self.speed = 2

        self.frames = ["enemies/enemy_move_0", "enemies/enemy_move_1"]

        self.frame_index = 0
        self.timer = 0

    #hitbox
    def get_hitbox(self):
        size = 50
        x = self.actor.centerx - size // 2
        y = self.actor.centery - size // 2
        return (x, y, size, size)

    def update(self):
        self.actor.x += self.speed * self.direction

        if self.actor.left <= self.left_limit:
            self.direction = 1
        elif self.actor.right >= self.right_limit:
            self.direction = -1

        self.timer += 1
        if self.timer % 15 == 0:
            self.frame_index = (self.frame_index + 1) % len(self.frames)
            self.actor.image = self.frames[self.frame_index]

    def draw(self):
        self.actor.draw()

class Flag:
    def __init__(self, pos):
        self.actor = Actor("tiles/flag_red_0", topleft=pos)
        self.activated = False
        self.frames = ["tiles/flag_red_0", "tiles/flag_red_1"]
        self.frame_index = 0
        self.animate_flag()

    def animate_flag(self):
        if self.activated:
            return  # para a animação se a bandeira já foi ativada
        self.frame_index = (self.frame_index + 1) % len(self.frames)
        self.actor.image = self.frames[self.frame_index]
        clock.schedule_unique(self.animate_flag, 0.3)

    def update(self):
        pass

    def draw(self):
        self.actor.draw()

    def check_victory(self, hero):
        if self.activated:
            return False

        if self.actor.colliderect(hero.actor):
            self.activated = True
            return True

        return False

class Button:
    def __init__(self, image, center):
        self.actor = Actor(image, center=center)

    def draw(self):
        self.actor.draw()

    def is_clicked(self, pos):
        return self.actor.collidepoint(pos)


# OBJECTS
# world setup
platforms = []
# ground
for x in range(0, WIDTH, TILE_SIZE):
    platforms.append(
        Platform("tiles/ground", (x, GROUND_Y), is_ground=True)
    )
# floating platforms
platforms.extend(create_floating_platform(200, 550, 3))
platforms.extend(create_floating_platform(610, 370, 3))
platforms.extend(create_floating_platform(450, 220, 2))
platforms.extend(create_floating_platform(250, 100, 2))

# hill
for i in range(3):
    platforms.append(
        Platform(
            "tiles/platform2",
            (HILL, GROUND_Y - (i + 1) * TILE_SIZE)
        )
    )

enemies = []

#buttons
start_y = HEIGHT // 2 - 60
start_button = Button("ui/button_start", (WIDTH // 2, start_y))
sound_button = Button("ui/button_sound", (WIDTH // 2, start_y + 80))
exit_button = Button("ui/button_exit", (WIDTH // 2, start_y + 160))
back_button = Button("ui/button_back", (WIDTH // 2, HEIGHT // 2 + 100))


def reset_game():
    global hero, enemies, flag, game_state

    hero = Hero((100, GROUND_Y - TILE_SIZE))

    enemies.clear()
    enemies.extend(
        [
            Enemy((200, GROUND_Y - TILE_SIZE), 200, 400),
            Enemy((600, GROUND_Y - TILE_SIZE), 600, 760),
            Enemy((610 + TILE_SIZE, 370 - TILE_SIZE), 610, 610 + 3 * TILE_SIZE),
        ]
    )

    flag = Flag((250 + TILE_SIZE // 2, 100 - TILE_SIZE))

    game_state = STATE_PLAYING

# INPUT
def on_key_down(key):
    global game_state

    if game_state == STATE_PLAYING and key == keys.SPACE:
        hero.jump()

def on_mouse_down(pos):
    global game_state

    if game_state == STATE_MENU:
        if start_button.is_clicked(pos):
            reset_game()
            if sound_enabled:
                music.play("music_bg")
        elif sound_button.is_clicked(pos):
            toggle_sound()
        elif exit_button.is_clicked(pos):
            exit_game()

    elif game_state in (STATE_GAME_OVER, STATE_WIN):
        if back_button.is_clicked(pos):
            game_state = STATE_MENU


# LOOP
def update():
    global game_state

    if game_state == STATE_PLAYING:
        hero.update(platforms)

        for enemy in enemies:
            enemy.update()

        # Lose
        if hero.check_enemy_collision(enemies):
            game_state = STATE_GAME_OVER
            music.stop()
            sounds.hit.play()
            return

        # Victory
        if flag.check_victory(hero):
            game_state = STATE_WIN
            music.stop()
            sounds.win.play()
            return

def draw():
    if game_state == STATE_MENU:
        draw_menu()
    elif game_state == STATE_PLAYING:
        draw_game()
    elif game_state == STATE_GAME_OVER:
        draw_game_over()
    elif game_state == STATE_WIN:
        draw_win()

def toggle_sound():
    global sound_enabled

    sound_enabled = not sound_enabled

    if sound_enabled:
        music.play("music_bg")
    else:
        music.stop()

def exit_game():
    quit()

def draw_win():
    screen.clear()
    screen.draw.text(
        "VICTORY!!!",
        center=(WIDTH // 2, HEIGHT // 2),
        fontsize=72,
        color="green",
    )
    back_button.draw()

def draw_game_over():
    screen.clear()
    screen.draw.text(
        "GAME OVER",
        center=(WIDTH // 2, HEIGHT // 2),
        fontsize=72,
        color="red",
    )
    back_button.draw()

#main menu
def draw_menu():
    screen.blit("background/menu_bg", (0, 0))
    screen.draw.text(
        "JUMPMAN",
        center=(WIDTH // 2, HEIGHT // 2 - 200),
        fontsize=72,
        color="black",
    )

    start_button.draw()
    sound_button.draw()
    exit_button.draw()

def draw_game():
    screen.clear()
    # background
    screen.blit("background/bg_large", (0, 0))
    # platform
    for platform in platforms:
        platform.actor.draw()
    # Enemy
    for enemy in enemies:
        enemy.actor.draw()
    # Hero
    hero.actor.draw()
    # Flag
    flag.actor.draw()


music.play("music_bg")
pgzrun.go()

import pygame
import random
import pytmx
import time
from pytmx import load_pygame


class Player:
    def __init__(self, x, y):
        self.width = 32
        self.height = 32
        self.direction = "stationary"
        self.move_speed = 2
        self.image_x = 0
        self.image_y = 0
        self.animation_delay = 0
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.player_sprite = pygame.image.load("player.png")
        self.collision = False
        self.dialog = False

    def update(self, map):

        # handle player movement
        pressed = pygame.key.get_pressed()

        if pressed[pygame.K_UP]:
            self.rect.y -= self.move_speed
            self.direction = "up"
        elif pressed[pygame.K_DOWN]:
            self.rect.y += self.move_speed
            self.direction = "down"
        elif pressed[pygame.K_LEFT]:
            self.rect.x -= self.move_speed
            self.direction = "left"
        elif pressed[pygame.K_RIGHT]:
            self.rect.x += self.move_speed
            self.direction = "right"
        else:
            self.direction = "stationary"

        self.collision = False

        for block in map.structure_list:
            if self.rect.colliderect(block.rect):
                self.collision = True
                if self.direction is "up":
                    self.rect.top = block.rect.bottom
                if self.direction is "down":
                    self.rect.bottom = block.rect.top
                if self.direction is "left":
                    self.rect.left = block.rect.right
                if self.direction is "right":
                    self.rect.right = block.rect.left

        absolute_x = self.rect.x - map.origin[0]
        absolute_y = self.rect.y - map.origin[1]

        if self.rect.left <= 0:
            self.rect.left = 0
        if self.rect.top <= 0:
            self.rect.top = 0
        if absolute_x + self.width >= map.map_width:
            self.collision = True
            self.rect.x -= self.move_speed
        if absolute_y + self.height >= map.map_height:
            self.collision = True
            self.rect.y -= self.move_speed

        # handle sprite alterations
        if self.direction is "down":
            self.image_y = 0
        elif self.direction is "up":
            self.image_y = 96
        elif self.direction is "left":
            self.image_y = 32
        elif self.direction is "right":
            self.image_y = 64

        if self.direction is not "stationary":
            # slow down the sprite animation
            if self.animation_delay == 10:
                self.image_x += 32
                self.animation_delay = 0
            else:
                self.animation_delay += 1
        else:
            self.image_x = 32

        if self.image_x > 64:
            self.image_x = 0

    def draw(self, game_display):
        game_display.blit(self.player_sprite, (self.rect.x, self.rect.y), (self.image_x, self.image_y, self.width, self.height))


class NPC:
    def __init__(self, x, y, status):
        self.width = 32
        self.height = 32
        self.still = 0
        self.still_delay = 2
        self.sprite = pygame.image.load("enemy.png")
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.animation = 0
        self.animation_delay = 15
        self.edge = 0
        self.stop = 0

        self.image_x = 0
        if random.randrange(1, 3) == 1:
            self.image_y = 32
            self.move_speed = -2
        else:
            self.image_y = 64
            self.move_speed = 2

    def update(self, player):
        if player.rect.colliderect(self.rect):
            self.image_x = 32
            return

        if self.still == self.still_delay:
            self.rect.x += self.move_speed
            self.still = 0

            if self.edge == 50:
                self.edge = 0
                self.move_speed = -self.move_speed
                if self.image_y == 32:
                    self.image_y = 64
                elif self.image_y == 64:
                    self.image_y = 32
            else:
                self.edge += 1
        else:
            self.still += 1

        if self.animation == self.animation_delay:
            self.image_x += 32
            self.animation = 0
        else:
            self.animation += 1

        if self.image_x > 64:
            self.image_x = 0


class Structure:
    def __init__(self, x, y, image):
        self.width = 32
        self.height = 32
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.image = image


class Gate:
    def __init__(self, x, y, width, height, map_name, map_id):
        self.width = width
        self.height = height
        self.rect = pygame.Rect(x, y, width, height)
        self.map_name = str(map_name)
        self.map_id = map_id


class Map:
    def __init__(self, map_id):
        # map properties
        self.map_id = int(map_id)
        self.map_tmx = load_pygame(self.get_map_file())
        self.map_music = pygame.mixer.Sound(self.get_map_music())
        self.map_width = self.map_tmx.width * self.map_tmx.tilewidth
        self.map_height = self.map_tmx.height * self.map_tmx.tileheight

        # map entities
        self.fg_list = []
        self.npc_list = []
        self.gate_list = []
        self.bg_list_top = []
        self.bg_list_bottom = []
        self.structure_list = []

        # map point of reference (camera)
        self.origin = pygame.Rect(0, 0, 640, 480)
        self.camera = pygame.Rect(0, 0, 640, 480)

    def load_map_entities(self, player):
        for layer in self.map_tmx.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer):
                for x, y, image in layer.tiles():
                    if layer.name == "foreground":
                        self.fg_list.append(Structure(x * self.map_tmx.tilewidth, y * self.map_tmx.tileheight, image))
                    elif layer.name == "background":
                        self.bg_list_top.append(Structure(x * self.map_tmx.tilewidth, y * self.map_tmx.tileheight, image))
                    elif layer.name == "canvas":
                        self.bg_list_bottom.append(Structure(x * self.map_tmx.tilewidth, y * self.map_tmx.tileheight, image))
                    elif layer.name == "structures":
                        self.structure_list.append(Structure(x * self.map_tmx.tilewidth, y * self.map_tmx.tileheight, image))
                    elif layer.name == "npc":
                        self.npc_list.append(NPC(x * self.map_tmx.tilewidth, y * self.map_tmx.tileheight, random.randrange(1, 3)))
                    elif layer.name == "player":
                        player.rect.x = x * self.map_tmx.tilewidth
                        player.rect.y = y * self.map_tmx.tileheight
                        player.image_y = 96
            elif isinstance(layer, pytmx.TiledObjectGroup):
                for obj in layer:
                    if layer.name == "gate":
                        self.gate_list.append(Gate(obj.x, obj.y, obj.width, obj.height, obj.name, obj.type))

        while player.rect.y > 240 and self.map_height > 480:
            if self.camera.bottom > self.map_height:
                break
            player.rect.y -= player.move_speed
            self.shift_map(0, -player.move_speed)

        while player.rect.x > 320 and self.map_width > 640:
            if self.camera.right > self.map_width:
                break
            player.rect.x -= player.move_speed
            self.shift_map(-player.move_speed, 0)

    def get_map_file(self):
        if self.map_id == 1:
            return "map.tmx"
        if self.map_id == 2:
            return "apartment.tmx"
        if self.map_id == 3:
            return "storage_room.tmx"
        if self.map_id == 4:
            return "field.tmx"

    def get_map_music(self):
        if self.map_id == 1:
            return "bg_music.wav"
        else:
            return "ambient.wav"

    def shift_map(self, shift_x, shift_y):
        for structure in self.structure_list:
            structure.rect.x += shift_x
            structure.rect.y += shift_y

        for bg in self.bg_list_top:
            bg.rect.x += shift_x
            bg.rect.y += shift_y

        for bg in self.bg_list_bottom:
            bg.rect.x += shift_x
            bg.rect.y += shift_y

        for fg in self.fg_list:
            fg.rect.x += shift_x
            fg.rect.y += shift_y

        for npc in self.npc_list:
            npc.rect.x += shift_x
            npc.rect.y += shift_y

        for gate in self.gate_list:
            gate.rect.x += shift_x
            gate.rect.y += shift_y

        self.origin.x += shift_x
        self.origin.y += shift_y

        self.camera.x -= shift_x
        self.camera.y -= shift_y


class Screen:
    def __init__(self, map_id):
        self.map = Map(map_id)

        self.clock = pygame.time.Clock()
        self.done = False
        self.fps = 60
        self.font = pygame.font.SysFont('arial', 30)
        self.dialog_list = []

    def run(self, game_display, player):
        self.map.load_map_entities(player)

        p = False

        while not self.done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit(-1)

                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    exit(-1)

                if event.type == pygame.KEYDOWN and event.key == pygame.K_KP_ENTER:
                    d = pygame.Rect(7*32, 13*32, 32, 32)
                    if player.rect.colliderect(d) and player.image_y == 96 and p is False:
                        self.dialog_list.append(Dialog())
                        p = True
                    else:
                        p = False
                        for r in self.dialog_list:
                            self.dialog_list.remove(r)

            absolute_x = player.rect.x - self.map.origin.x
            absolute_y = player.rect.y - self.map.origin.y

            string_one = str(absolute_x) + " : " + str(absolute_y)
            label_one = self.font.render(str(string_one), True, (255, 255, 255))
            string_two = str(self.map.map_width) + " x " + str(self.map.map_height)
            label_two = self.font.render(str(string_two), True, (255, 255, 255))
            string_three = str(self.map.map_id)
            label_three = self.font.render(str(string_three), True, (255, 255, 255))

            player.update(self.map)

            if player.collision is False:

                if (absolute_x > self.map.map_width - 320) and (self.map.map_width - 320 > 0):
                    diff = 0
                elif absolute_x > 320:
                    diff = player.move_speed
                    player.rect.x = 320
                else:
                    diff = 0

                if player.direction is "right":
                    self.map.shift_map(-diff, 0)
                elif player.direction is "left":
                    self.map.shift_map(diff, 0)

                if (absolute_y > self.map.map_height - 240) and (self.map.map_height - 240 > 0):
                    diff = 0
                elif absolute_y > 240:
                    diff = player.move_speed
                    player.rect.y = 240
                else:
                    diff = 0

                if player.direction is "down":
                    self.map.shift_map(0, -diff)
                elif player.direction is "up":
                    self.map.shift_map(0, diff)

            # gate handling
            for gate in self.map.gate_list:
                if player.rect.colliderect(gate.rect):
                    fade(game_display)
                    if self.map.map_id == 1 or self.map.map_id == 4:
                        screen = Screen(gate.map_id)
                        screen.run(game_display, player)
                        player.rect.x = gate.rect.x
                        player.rect.y = gate.rect.bottom + 32
                        player.image_y = 96
                    else:
                        self.done = True

            for npc in self.map.npc_list:
                npc.update(player)

            game_display.fill((0, 0, 0))

            for bg in self.map.bg_list_bottom:
                game_display.blit(bg.image, (bg.rect.x, bg.rect.y))

            for bg in self.map.bg_list_top:
                game_display.blit(bg.image, (bg.rect.x, bg.rect.y))

            for npc in self.map.npc_list:
                game_display.blit(npc.sprite, (npc.rect.x, npc.rect.y), (npc.image_x, npc.image_y, npc.width, npc.height))

            player.draw(game_display)

            for structure in self.map.structure_list:
                game_display.blit(structure.image, (structure.rect.x, structure.rect.y))

            for fg in self.map.fg_list:
                game_display.blit(fg.image, (fg.rect.x, fg.rect.y))

            for dialog in self.dialog_list:
                pygame.draw.rect(game_display, (255, 200, 200), dialog.rect)

            game_display.blit(label_one, (10, 10))
            game_display.blit(label_two, (500, 10))
            game_display.blit(label_three, (550, 420))

            pygame.display.update()
            self.clock.tick(self.fps)


class Dialog:
    def __init__(self):
        self.position = 0
        self.width = 640
        self.height = 80
        self.color = (255, 200, 200)
        self.rect = pygame.Rect(0, 0, self.width, self.height)
        self.done = False


def fade(game_display):
    s = pygame.Surface((640, 480))
    s.fill((0, 0, 0))
    alpha_value = 100

    for i in range(10):
        s.set_alpha(alpha_value)
        game_display.blit(s, (0, 0))
        pygame.display.update()
        alpha_value -= 5
        time.sleep(0.04)


def main():
    pygame.init()
    screen_width = 640
    screen_height = 480
    game_display = pygame.display.set_mode((screen_width, screen_height))
    player = Player(0, 0)

    screen_one = Screen(1)
    screen_one.run(game_display, player)

    pygame.quit()

main()

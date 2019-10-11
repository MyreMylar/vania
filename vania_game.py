import os
import pygame
from pygame.locals import *

from game.player import Player
from collision.collision_grid import CollisionGrid

from game.tiled_level import TiledLevel
from game.map_editor import MapEditor
from game.main_menu import MainMenu
from game.camera import Camera
from game.fps_counter import FPSCounter
from game.ui_player_health_bar import UIPlayerHealthBar
"""
CHALLENGE 1
-----------

Your first challenge is to add some water tiles to the game in a believable fashion.
You will need to use the map editor accessible from the game's main menu.

The water tiles are designed to be positioned as a 'pool' in between two wall tiles.
I've left a suitable spot for a pool of water on the top half of the map about half-way along, or you can make your own.

In the second challenge we will make colliding with the water slow the player's movement over in the player.py file.

ADDITIONAL INFO
---------------
- You may also want to take a look at the tile data files which define game data and which image to use for each type of 
  tile. They are accessible under 'data/tiles' in the Project view pane on the left hand side of the PyCharm editor. 
  
NEXT: Head to player.py, line 265.
"""


class VaniaGame:
    """
    An attempt to make a 'Metroidvania' style platform game.
    """
    def __init__(self):
        pygame.init()
        os.environ['SDL_VIDEO_CENTERED'] = '1'
        pygame.display.set_caption("Vania")
        world_size = [4096, 4096]
        self.camera = Camera((400, 300), (800, 600), world_size)
        pygame.display.set_icon(pygame.image.load('images/icon.png'))
        self.screen = pygame.display.set_mode(self.camera.dimensions, 0, 0)

        self.fonts = {"default_12": pygame.font.Font("data/fonts/Pavanam-Regular.ttf", 12),
                      "default_12_bold": pygame.font.Font("data/fonts/Pavanam-Regular.ttf", 12),
                      "default_14": pygame.font.Font("data/fonts/Pavanam-Regular.ttf", 14),
                      "default_14_bold": pygame.font.Font("data/fonts/Pavanam-Regular.ttf", 14),
                      "default_16": pygame.font.Font("data/fonts/Pavanam-Regular.ttf", 16),
                      "default_16_bold": pygame.font.Font("data/fonts/Pavanam-Regular.ttf", 16),
                      "default_32": pygame.font.Font("data/fonts/Pavanam-Regular.ttf", 32),
                      "default_64": pygame.font.Font("data/fonts/Pavanam-Regular.ttf", 64),
                      "julee_128": pygame.font.Font(os.path.abspath("data/fonts/Julee-Regular.ttf"), 128),
                      "roboto_14_bold": pygame.font.Font("data/fonts/Roboto-Bold.ttf", 14)}

        self.fonts["default_12_bold"].set_bold(True)
        self.fonts["default_14_bold"].set_bold(True)
        self.fonts["default_16_bold"].set_bold(True)

        self.background = pygame.Surface(self.camera.dimensions)
        self.background.fill(pygame.Color("#c4dbf3"))

        grid_square_size = 64

        world_filling_number_of_grid_squares = [int(world_size[0]/grid_square_size),
                                                int(world_size[1]/grid_square_size)]
        self.collision_grid = CollisionGrid(world_filling_number_of_grid_squares,
                                            grid_square_size)

        self.moving_sprites_group = pygame.sprite.Group()
        self.ui_sprites_group = pygame.sprite.Group()

        self.player = Player(self.moving_sprites_group, self.ui_sprites_group,
                             self.fonts, self.collision_grid, self.camera)
        self.player_health_ui = UIPlayerHealthBar((20, self.camera.dimensions[1]-30), self.fonts)

        self.tiled_level = TiledLevel(self.collision_grid, world_filling_number_of_grid_squares,
                                      self.moving_sprites_group, self.ui_sprites_group)
        self.editor = MapEditor(self.tiled_level, self.fonts, self.collision_grid, self.camera)

        self.main_menu = MainMenu(self.fonts, self.camera)

        self.is_main_menu = True
        self.is_editor = False
        self.start_game = False

        self.gravity = 800.0
        self.clock = pygame.time.Clock()
        self.fps_counter = FPSCounter(self.fonts)
        self.running = True

    def run(self):
        while self.running:
            frame_time = self.clock.tick(60)
            time_delta = min(0.1, frame_time / 1000.0)

            # TODO: make these three states into state classes and use a state machine dictionary to switch between them
            if self.is_main_menu:
                is_main_menu_and_index = self.main_menu.run(self.screen)
                if is_main_menu_and_index[0] == 0:
                    self.is_main_menu = True
                elif is_main_menu_and_index[0] == 1:
                    self.is_main_menu = False
                    self.start_game = True
                    self.camera.reset_camera_tracking()
                    self.camera.position[0] = 316.0
                    self.camera.position[1] = 596.0
                    self.player.respawn()
                    self.tiled_level.reset_entities()
                elif is_main_menu_and_index[0] == 2:
                    self.is_main_menu = False
                    self.is_editor = True
                elif is_main_menu_and_index[0] == 3:
                    self.running = False

            elif self.is_editor:
                self.is_editor = self.editor.run(self.screen, self.background, time_delta)
                if not self.is_editor:
                    self.is_main_menu = True
            else:
                for event in pygame.event.get():
                    if event.type == QUIT:
                        self.is_main_menu = True
                    if event.type == KEYDOWN:
                        if event.key == K_ESCAPE:
                            self.is_main_menu = True

                    self.player.process_events(event)

                if self.player.has_exited_level:
                    self.player.has_exited_level = False
                    self.is_main_menu = True

                self.camera.set_target_position(self.player.world_position)
                self.camera.update(time_delta)

                self.tiled_level.update(time_delta, self.camera)
                self.moving_sprites_group.update(time_delta, self.gravity, self.camera)
                self.collision_grid.update_shape_grid_positions()
                self.collision_grid.check_collisions()

                self.screen.blit(self.background, (0, 0))
                self.tiled_level.draw_back_layers(self.screen)
                self.moving_sprites_group.draw(self.screen)
                self.tiled_level.draw_front_layers(self.screen)

                # draw the collision shapes
                # self.tiled_level.draw_collision_shapes(self.screen, self.camera)
                # self.player.draw_collision_shapes(self.screen, self.camera)
                # for sprite in self.moving_sprites_group:
                #    if sprite.type == "enemy":
                #        sprite.draw_debug_info(self.screen, self.camera)

                self.player_health_ui.update(self.player)
                self.player_health_ui.draw(self.screen)

                self.ui_sprites_group.update()
                self.ui_sprites_group.draw(self.screen)

                self.fps_counter.update(time_delta)
                self.fps_counter.draw(self.screen, self.camera)

            pygame.display.flip()


vania_game = VaniaGame()
vania_game.run()

import math
from pygame.locals import *
from game.tile import *

from game.tiled_level import AISpawn
from game.map_editor_instructions_window import MapEditorInstructionsWindow


class MapEditor:

    def __init__(self, tiled_level, fonts, collision_grid, camera):
        self.palette_sprite_group = pygame.sprite.Group()
        self.collision_grid = collision_grid
        self.fonts = fonts
        self.editing_layer = 0
        self.tiled_level = tiled_level
        self.hud_rect = pygame.Rect((0, 500), (800, 100))
        
        self.left_mouse_held = False
        self.right_mouse_held = False
        self.right_mouse_clicked = False

        self.need_to_refresh_tiles = True

        self.default_tile = None
        # [pygame.Rect(0, 0, 0, 0), self.tiled_level.tile_map[0][0], "rock_centre", True, None]
        self.held_tile_data = self.default_tile
        self.rect_of_tile = None

        self.held_ai_spawn = None

        self.hovered_rec = None

        self.rotate_selected_tile_left = False
        self.rotate_selected_tile_right = False

        self.all_palette_tile_sprites = pygame.sprite.Group()
        self.all_ai_spawn_sprites = pygame.sprite.Group()

        self.palette_page = 0
        self.should_increase_palette_page = False
        self.should_decrease_palette_page = False
        
        self.palette_tiles = []
        self.palette_ai_spawns = []
        self.num_ai_spawns = 1
        self.tiles_per_page = 11
        all_tiles_and_ai = len(self.tiled_level.all_tile_data.keys()) + self.num_ai_spawns
        self.max_pages = int(math.ceil(all_tiles_and_ai / self.tiles_per_page))

        self.refresh_palette_tiles()

        self.left_scroll_held = False
        self.right_scroll_held = False
        self.up_scroll_held = False
        self.down_scroll_held = False

        self.map_scroll_speed = 256.0

        self.camera = camera  # self.tiled_level.find_player_start()

        instructions_message_rect = pygame.Rect((0, 0), (300, 180))
        instructions_message_rect.centerx = camera.screen_rect.centerx
        instructions_message_rect.centery = camera.screen_rect.centery
        self.map_editor_instructions = MapEditorInstructionsWindow(instructions_message_rect, self.fonts)

    def refresh_palette_tiles(self):
        self.all_palette_tile_sprites.empty()
        self.palette_tiles[:] = []
        self.palette_ai_spawns[:] = []
        x_pos = 40
        y_pos = 40

        sorted_tile_keys = sorted(self.tiled_level.all_tile_data.keys())
        display_tile = self.palette_page * self.tiles_per_page

        while display_tile < len(sorted_tile_keys) + self.num_ai_spawns and\
                display_tile < (self.palette_page * self.tiles_per_page) + self.tiles_per_page:
            if display_tile < len(sorted_tile_keys):
                tile_data = sorted_tile_keys[display_tile]
                self.palette_tiles.append(Tile(self.palette_sprite_group, self.collision_grid,
                                               self.tiled_level.all_tile_data[tile_data],
                                               [self.hud_rect[0] + x_pos, self.hud_rect[1] + y_pos],
                                               self.editing_layer, collision_enabled=False))
                display_tile += 1
            else:
                self.palette_ai_spawns.append(AISpawn([self.hud_rect[0] + x_pos, self.hud_rect[1] + y_pos],
                                                      "ai_spawn",
                                                      "archer",
                                                      self.tiled_level.ai_spawn_data))

                display_tile += self.num_ai_spawns
            x_pos += 72

            if x_pos > 760:
                x_pos = 40
                y_pos += 72

        for tile in self.palette_tiles:
            self.all_palette_tile_sprites.add(tile)

        for ai_spawn in self.palette_ai_spawns:
            self.all_palette_tile_sprites.add(ai_spawn.icon)

    def run(self, screen, background, time_delta):
        running = True
        for event in pygame.event.get():
            if self.map_editor_instructions is not None:
                self.map_editor_instructions.handle_input_event(event)
            else:
                if event.type == QUIT:
                    self.tiled_level.save_tiles()
                    running = False
                if event.type == MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.left_mouse_held = True
                    if event.button == 3:
                        self.right_mouse_held = True
                        self.right_mouse_clicked = True
                if event.type == MOUSEBUTTONUP:
                    if event.button == 1:
                        self.left_mouse_held = False
                    if event.button == 3:
                        self.right_mouse_held = False
                if event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        self.tiled_level.save_tiles()
                        running = False
                    if event.key == K_F5:
                        self.tiled_level.save_tiles()
                    if event.key == K_PERIOD:
                        self.rotate_selected_tile_right = True
                    if event.key == K_COMMA:
                        self.rotate_selected_tile_left = True
                    if event.key == K_UP:
                        self.up_scroll_held = True
                    if event.key == K_DOWN:
                        self.down_scroll_held = True
                    if event.key == K_LEFT:
                        self.left_scroll_held = True
                    if event.key == K_RIGHT:
                        self.right_scroll_held = True
                    if event.key == K_1:
                        self.editing_layer = 1
                    if event.key == K_0:
                        self.editing_layer = 0
                    if event.key == K_RIGHTBRACKET:
                        self.should_increase_palette_page = True
                    if event.key == K_LEFTBRACKET:
                        self.should_decrease_palette_page = True
                if event.type == KEYUP:
                    if event.key == K_UP:
                        self.up_scroll_held = False
                    if event.key == K_DOWN:
                        self.down_scroll_held = False
                    if event.key == K_LEFT:
                        self.left_scroll_held = False
                    if event.key == K_RIGHT:
                        self.right_scroll_held = False
            
        if self.map_editor_instructions is not None:
            self.map_editor_instructions.update()
            if self.map_editor_instructions.should_exit:
                self.map_editor_instructions = None

        if self.should_increase_palette_page:
            self.should_increase_palette_page = False
            if self.palette_page < self.max_pages - 1:
                self.palette_page += 1
            else:
                self.palette_page = 0  # loop back round
            self.refresh_palette_tiles()

        if self.should_decrease_palette_page:
            self.should_decrease_palette_page = False
            if self.palette_page > 0:
                self.palette_page -= 1
            else:
                self.palette_page = self.max_pages - 1  # loop back round
            self.refresh_palette_tiles()

        if self.up_scroll_held:
            self.camera.position[1] -= self.map_scroll_speed * time_delta
            if self.camera.position[1] < self.camera.half_height:
                self.camera.position[1] = self.camera.half_height
        if self.down_scroll_held:
            self.camera.position[1] += self.map_scroll_speed * time_delta
            map_y_bound = self.tiled_level.level_pixel_size[1] - self.camera.half_height + self.hud_rect[1]
            if self.camera.position[1] > map_y_bound:
                self.camera.position[1] = map_y_bound

        if self.left_scroll_held:
            self.camera.position[0] -= self.map_scroll_speed * time_delta
            if self.camera.position[0] < self.camera.half_width:
                self.camera.position[0] = self.camera.half_width
        if self.right_scroll_held:
            self.camera.position[0] += self.map_scroll_speed * time_delta
            if self.camera.position[0] > (self.tiled_level.level_pixel_size[0] - self.camera.half_width):
                self.camera.position[0] = (self.tiled_level.level_pixel_size[0] - self.camera.half_width)
                
        if self.rotate_selected_tile_right and self.held_tile_data[4] is not None:
            self.rotate_selected_tile_right = False
            self.held_tile_data[4].rotate_tile_right()
            self.need_to_refresh_tiles = True

        if self.rotate_selected_tile_left and self.held_tile_data[4] is not None:
            self.rotate_selected_tile_left = False
            self.held_tile_data[4].rotate_tile_left()
            self.need_to_refresh_tiles = True
        
        if self.left_mouse_held:
            click_pos = pygame.mouse.get_pos()
            if self.is_inside_hud(click_pos, self.hud_rect):
                self.held_tile_data = self.get_palette_tile_data_at_pos(click_pos)
                if self.held_tile_data is None:
                    self.held_ai_spawn = self.get_palette_ai_spawn_data_at_pos(click_pos)
                else:
                    self.held_ai_spawn = None
                    
            else:
                self.held_tile_data = self.tiled_level.get_tile_data_at_pos(self.camera, click_pos, self.editing_layer)

        if self.right_mouse_held:
            click_pos = pygame.mouse.get_pos()
            
            if self.is_inside_hud(click_pos, self.hud_rect):
                pass
            else:
                angle = 0
                if self.held_tile_data is not None:
                    if self.held_tile_data[4] is not None:
                        angle = self.held_tile_data[4].angle
                    if self.held_tile_data[2] != "":
                        self.rect_of_tile = self.tiled_level.set_tile_at_screen_pos(self.camera,
                                                                                    click_pos,
                                                                                    self.held_tile_data[2],
                                                                                    angle,
                                                                                    self.editing_layer)
                    else:
                        self.tiled_level.clear_tile_at_screen_pos(self.camera, click_pos, self.editing_layer)
                else:
                    self.tiled_level.clear_tile_at_screen_pos(self.camera, click_pos, self.editing_layer)

        if self.right_mouse_clicked:
            self.right_mouse_clicked = False
            if self.held_ai_spawn is not None:
                self.tiled_level.add_ai_spawn_at_screen_pos(pygame.mouse.get_pos(), self.held_ai_spawn, self.camera)

        self.tiled_level.update(time_delta, self.camera)

        hovered_tile_data = self.tiled_level.get_tile_data_at_pos(self.camera, pygame.mouse.get_pos(),
                                                                  self.editing_layer)
        if hovered_tile_data is not None:
            self.hovered_rec = hovered_tile_data[0]

        screen.blit(background, (0, 0))  # draw the background
        self.tiled_level.draw_back_layers(screen)
        for entity in self.tiled_level.entity_placements:
            entity.draw(screen, self.camera)
        self.tiled_level.draw_front_layers(screen)

        if self.held_tile_data is not None:
            if not self.held_tile_data[3]:
                view_top_left_position = (self.camera.position[0] - self.camera.half_width,
                                          self.camera.position[1] - self.camera.half_height)
                screen_position = [0.0, 0.0]
                screen_position[0] = self.held_tile_data[0].centerx - view_top_left_position[0]
                screen_position[1] = self.held_tile_data[0].centery - view_top_left_position[1]

                screen_rect = pygame.Rect((0, 0), self.tiled_level.tile_size)
                screen_rect.centerx = int(screen_position[0])
                screen_rect.centery = int(screen_position[1])

                pygame.draw.rect(screen, pygame.Color("#FF64FF"),
                                 screen_rect, 1)  # draw the selection rectangle
        if self.hovered_rec is not None:
            view_top_left_position = (self.camera.position[0] - self.camera.half_width,
                                      self.camera.position[1] - self.camera.half_height)
            screen_position = [0.0, 0.0]
            screen_position[0] = self.hovered_rec.centerx - view_top_left_position[0]
            screen_position[1] = self.hovered_rec.centery - view_top_left_position[1]

            screen_rect = pygame.Rect((0, 0), self.tiled_level.tile_size)
            screen_rect.centerx = int(screen_position[0])
            screen_rect.centery = int(screen_position[1])
            pygame.draw.rect(screen, pygame.Color("#FFE164"), screen_rect, 1)  # draw the selection rectangle

        layer_string = "Editing Layer: " + str(self.editing_layer)
        layer_string_render = self.fonts["default_16"].render(layer_string, True, pygame.Color("#FFFFFF"))
        screen.blit(layer_string_render, layer_string_render.get_rect(x=32, y=32))

        pygame.draw.rect(screen, pygame.Color("#3C3C3C"), self.hud_rect, 0)  # draw the hud
        self.all_palette_tile_sprites.draw(screen)

        if self.map_editor_instructions is not None:
            self.map_editor_instructions.draw(screen)

        pygame.display.flip()  # flip all our drawn stuff onto the screen

        return running

    @staticmethod
    def is_inside_hud(pos, hud_rect):
        if hud_rect[0] <= pos[0] and hud_rect[1] <= pos[1]:
            if hud_rect[0] + hud_rect[2] > pos[0] and hud_rect[1] + hud_rect[3] > pos[1]:
                return True
        return False

    def get_palette_tile_data_at_pos(self, click_pos):
        for tile in self.palette_tiles:
            if tile.rect[0] <= click_pos[0] and tile.rect[1] <= click_pos[1]:
                if tile.rect[0] + tile.rect[2] > click_pos[0] and\
                        tile.rect[1] + tile.rect[3] > click_pos[1]:
                    return [tile.rect, tile.image, tile.tile_data.tile_id, True, None]
        return None

    def get_palette_ai_spawn_data_at_pos(self, click_pos):
        for ai_spawn in self.palette_ai_spawns:
            if ai_spawn.icon.rect[0] <= click_pos[0] and ai_spawn.icon.rect[1] <= click_pos[1]:
                if ai_spawn.icon.rect[0] + ai_spawn.icon.rect[2] > click_pos[0] and\
                        ai_spawn.icon.rect[1] + ai_spawn.icon.rect[3] > click_pos[1]:
                    return ai_spawn
        return None

import os
import csv
import pygame
from game.tile import Tile, TileData
from game.collision_types import CollisionType

from game.enemy_archer import EnemyArcher


class EntityPlacement:
    def __init__(self, world_position, entity_type, entity_sub_type):
        self.world_position = world_position
        self.type = entity_type
        self.sub_type = entity_sub_type

    def spawn(self, entity_list):
        pass

    def draw(self, screen, camera):
        pass


class AISpawn(EntityPlacement):
    def __init__(self, world_position, entity_type, entity_sub_type, ai_spawn_data):
        super().__init__(world_position, entity_type, entity_sub_type)

        self.ai_spawn_data = ai_spawn_data
        self.moving_sprites_group = ai_spawn_data["moving_sprites_group"]
        self.ui_sprites_group = ai_spawn_data["ui_sprites_group"]
        self.collision_grid = ai_spawn_data["collision_grid"]
        self.archer_image = ai_spawn_data["archer_image"]

        if self.sub_type == "archer":
            self.icon = pygame.sprite.Sprite()
            self.image = self.archer_image.subsurface(pygame.Rect([0, 0], [64, 96]))
            self.icon.image = pygame.transform.smoothscale(self.image, [64, 64])
            self.icon.rect = self.icon.image.get_rect(centerx=world_position[0],
                                                      centery=world_position[1])

    def spawn(self, entity_list):
        if self.sub_type == "archer":
            entity_list.append(EnemyArcher(self.world_position, self.moving_sprites_group, self.ui_sprites_group,
                                           self.collision_grid, self.archer_image))

    def draw(self, screen, camera):
        view_top_left_position = (camera.position[0] - camera.half_width,
                                  camera.position[1] - camera.half_height)
        screen.blit(self.image, [self.world_position[0] - self.image.get_width()/2 - view_top_left_position[0],
                                 self.world_position[1] - self.image.get_height()/2 - view_top_left_position[1]])


class TiledLevel:
    def __init__(self, collision_grid, world_grid_dimensions, moving_sprites_group, ui_sprites_group):
        self.collision_grid = collision_grid

        # TODO: ideally we would pull all the level setup stats from the header area of the level data file
        self.file_name = "data/test_level_0.csv"

        self.tile_size = (64, 64)  # size of an individual tile in pixels
        self.level_tile_size = world_grid_dimensions  # number of tiles in a level by x * y
        self.level_pixel_size = [self.level_tile_size[0] * self.tile_size[0],
                                 self.level_tile_size[1] * self.tile_size[1]]  # size of entire level in pixels

        self.tile_image_atlas = self.load_tile_table("images/tiles.png",
                                                     self.tile_size[0],
                                                     self.tile_size[1],
                                                     True)

        self.ai_spawn_data = {"collision_grid": self.collision_grid,
                              "ui_sprites_group": ui_sprites_group,
                              "moving_sprites_group": moving_sprites_group,
                              "archer_image": pygame.image.load("images/archer.png").convert_alpha()}
        self.entity_placements = []
        self.active_entity_list = []

        self.all_tile_data = {}
        self.load_tile_data()

        self.tile_grid_layers = {}
        self.load_level_tiles()

    def load_tile_data(self):
        # load all the tile data files (could we just load the ones used in this level?)
        tile_data_files = [file for file in os.listdir("data/tiles/")
                           if os.path.isfile(os.path.join("data/tiles/", file))]
        for file_name in tile_data_files:
            new_tile_data = TileData(os.path.join("data/tiles/", file_name), self.tile_image_atlas)
            new_tile_data.load_tile_data()
            self.all_tile_data[new_tile_data.tile_id] = new_tile_data

    def create_empty_level(self):
        # create empty map with layers
        self.tile_grid_layers = {"layer_0": {"grid": [], "sprite_group": pygame.sprite.Group()},
                                 "layer_1": {"grid": [], "sprite_group": pygame.sprite.Group()}}

        for tile_layer in self.tile_grid_layers.values():
            for tile_x in range(0, self.level_tile_size[0]):
                column = []
                for tile_y in range(0, self.level_tile_size[1]):
                    column.append(None)
                tile_layer["grid"].append(column)

    def reset_entities(self):
        """ Should put the entities in the level (e.g. enemies)  back to the state they started the level in """
        for entity in self.active_entity_list:
            entity.shutdown()

        for entity_placements in self.entity_placements:
            entity_placements.spawn(self.active_entity_list)

    @staticmethod
    def load_tile_table(filename, width, height, use_transparency):
        if use_transparency:
            image = pygame.image.load(filename).convert_alpha()
        else:
            image = pygame.image.load(filename).convert()
        image_width, image_height = image.get_size()
        tile_table = []
        for tile_x in range(0, int(image_width / width)):
            line = []
            tile_table.append(line)
            for tile_y in range(0, int(image_height / height)):
                rect = (tile_x * width, tile_y * height, width, height)
                line.append(image.subsurface(rect))
        return tile_table

    def update(self, time_delta, camera):
        for layer in self.tile_grid_layers.values():
            layer["sprite_group"].update(camera)

    def draw_back_layers(self, screen):
        self.tile_grid_layers["layer_0"]["sprite_group"].draw(screen)

    def draw_front_layers(self, screen):
        self.tile_grid_layers["layer_1"]["sprite_group"].draw(screen)

    def draw_collision_shapes(self, screen, camera):
        for layer in self.tile_grid_layers.values():
            for tile in layer["sprite_group"].sprites():
                tile.draw_collision_shapes(screen, camera)

    def add_ai_spawn_at_screen_pos(self, screen_position, ai_spawn, camera):
        view_top_left_position = (camera.position[0] - camera.half_width,
                                  camera.position[1] - camera.half_height)
        self.entity_placements.append(AISpawn([float(screen_position[0] + view_top_left_position[0]),
                                               float(screen_position[1] + view_top_left_position[1])],
                                              ai_spawn.type, ai_spawn.sub_type, ai_spawn.ai_spawn_data))

    def get_tile_data_at_pos(self, camera, screen_position, layer):
        view_top_left_position = (camera.position[0] - camera.half_width,
                                  camera.position[1] - camera.half_height)
        world_click_position = [screen_position[0] + view_top_left_position[0],
                                screen_position[1] + view_top_left_position[1]]

        tile_x = int((world_click_position[0]) // self.tile_size[0])
        tile_y = int((world_click_position[1]) // self.tile_size[1])

        tile = self.tile_grid_layers["layer_" + str(layer)]["grid"][tile_x][tile_y]

        tile_world_min = [(tile_x * self.tile_size[0]),
                          (tile_y * self.tile_size[1])]

        if tile is not None:
            return [pygame.Rect([tile.world_position[0] - self.tile_size[0] / 2,
                                 tile.world_position[1] - self.tile_size[1] / 2],
                                self.tile_size), tile.tile_data.image,
                    tile.tile_data.tile_id, False, tile]
        else:
            return [pygame.Rect(tile_world_min, self.tile_size),
                    None, "", False, None]

    def clear_tile_at_screen_pos(self, camera, screen_position, layer):
        view_top_left_position = (camera.position[0] - camera.half_width,
                                  camera.position[1] - camera.half_height)
        world_click_position = [screen_position[0] + view_top_left_position[0],
                                screen_position[1] + view_top_left_position[1]]

        tile_x = int((world_click_position[0]) // self.tile_size[0])
        tile_y = int((world_click_position[1]) // self.tile_size[1])

        tile = self.tile_grid_layers["layer_" + str(layer)]["grid"][tile_x][tile_y]
        if tile is not None:
            self.tile_grid_layers["layer_" + str(layer)]["sprite_group"].remove(tile)
            self.tile_grid_layers["layer_" + str(layer)]["grid"][tile_x][tile_y] = None

            self.update_tile_collision_normals(tile_x, tile_y, layer)

    def set_tile_at_screen_pos(self, camera, screen_position, tile_data_id, angle, layer):
        view_top_left_position = (camera.position[0] - camera.half_width,
                                  camera.position[1] - camera.half_height)
        world_click_position = [screen_position[0] + view_top_left_position[0],
                                screen_position[1] + view_top_left_position[1]]
        half_tile_size = (self.tile_size[0]/2, self.tile_size[1]/2)
        tile_x = int((world_click_position[0]) // self.tile_size[0])
        tile_y = int((world_click_position[1]) // self.tile_size[1])

        tile_layer = self.tile_grid_layers["layer_" + str(layer)]
        tile_data = self.all_tile_data[tile_data_id]

        new_tile = Tile(tile_layer["sprite_group"], self.collision_grid, tile_data,
                        [(tile_x * self.tile_size[0]) + half_tile_size[0],
                         (tile_y * self.tile_size[1]) + half_tile_size[1]],
                        layer, angle)
        tile_layer["grid"][tile_x][tile_y] = new_tile

        self.update_tile_collision_normals(tile_x, tile_y, layer)

    """ This method is stupidly complicated and probably needs trimming down.
    
        The intent is to correctly adjust a tile location's collision normals, and 
        it's N,E,S,W neighbours' collision normals when a tile's collision state 
        may have changed. i.e. after you have added, removed or edited a tile"""
    def update_tile_collision_normals(self, tile_x, tile_y, layer):
        collision_types_to_adjust = [CollisionType.WORLD_SOLID,
                                     CollisionType.WORLD_JUMP_THROUGH,
                                     CollisionType.WORLD_PLATFORM_EDGE,
                                     CollisionType.WORLD_JUMP_THROUGH_EDGE]

        tile_to_update = self.tile_grid_layers["layer_" + str(layer)]["grid"][tile_x][tile_y]

        if tile_to_update is not None:
            # initialise to False
            tile_to_update.collision_shape.normals["left"].should_skip = False
            tile_to_update.collision_shape.normals["right"].should_skip = False
            tile_to_update.collision_shape.normals["top"].should_skip = False
            tile_to_update.collision_shape.normals["bottom"].should_skip = False

            if tile_to_update.tile_data.collision_type in collision_types_to_adjust:
                left_tile_x = tile_x - 1
                if left_tile_x > 0:
                    left_tile = self.tile_grid_layers["layer_" + str(layer)]["grid"][left_tile_x][tile_y]
                    if left_tile is not None:
                        if left_tile.tile_data.collision_type in collision_types_to_adjust:
                            tile_to_update.collision_shape.normals["left"].should_skip = True
                            left_tile.collision_shape.normals["right"].should_skip = True

                right_tile_x = tile_x + 1
                if right_tile_x < self.level_tile_size[0]:
                    right_tile = self.tile_grid_layers["layer_" + str(layer)]["grid"][right_tile_x][tile_y]
                    if right_tile is not None:
                        if right_tile.tile_data.collision_type in collision_types_to_adjust:
                            tile_to_update.collision_shape.normals["right"].should_skip = True
                            right_tile.collision_shape.normals["left"].should_skip = True

                top_tile_y = tile_y - 1
                if top_tile_y > 0:
                    top_tile = self.tile_grid_layers["layer_" + str(layer)]["grid"][tile_x][top_tile_y]
                    if top_tile is not None:
                        if top_tile.tile_data.collision_type in collision_types_to_adjust:
                            tile_to_update.collision_shape.normals["top"].should_skip = True
                            top_tile.collision_shape.normals["bottom"].should_skip = True

                bottom_tile_y = tile_y + 1
                if bottom_tile_y < self.level_tile_size[1]:
                    bottom_tile = self.tile_grid_layers["layer_" + str(layer)]["grid"][tile_x][bottom_tile_y]
                    if bottom_tile is not None:
                        if bottom_tile.tile_data.collision_type in collision_types_to_adjust:
                            tile_to_update.collision_shape.normals["bottom"].should_skip = True
                            bottom_tile.collision_shape.normals["top"].should_skip = True

        elif tile_to_update is None or tile_to_update.tile_data.collision_type not in collision_types_to_adjust:
            left_tile_x = tile_x - 1
            if left_tile_x > 0:
                left_tile = self.tile_grid_layers["layer_" + str(layer)]["grid"][left_tile_x][tile_y]
                if left_tile is not None:
                    if left_tile.tile_data.collision_type in collision_types_to_adjust:
                        left_tile.collision_shape.normals["right"].should_skip = False

            right_tile_x = tile_x + 1
            if right_tile_x < self.level_tile_size[0]:
                right_tile = self.tile_grid_layers["layer_" + str(layer)]["grid"][right_tile_x][tile_y]
                if right_tile is not None:
                    if right_tile.tile_data.collision_type in collision_types_to_adjust:
                        right_tile.collision_shape.normals["left"].should_skip = False

            top_tile_y = tile_y - 1
            if top_tile_y > 0:
                top_tile = self.tile_grid_layers["layer_" + str(layer)]["grid"][tile_x][top_tile_y]
                if top_tile is not None:
                    if top_tile.tile_data.collision_type in collision_types_to_adjust:
                        top_tile.collision_shape.normals["bottom"].should_skip = False

            bottom_tile_y = tile_y + 1
            if bottom_tile_y < self.level_tile_size[1]:
                bottom_tile = self.tile_grid_layers["layer_" + str(layer)]["grid"][tile_x][bottom_tile_y]
                if bottom_tile is not None:
                    if bottom_tile.tile_data.collision_type in collision_types_to_adjust:
                        bottom_tile.collision_shape.normals["top"].should_skip = False

    def save_tiles(self):
        with open(self.file_name, "w", newline='') as tileFile:
            writer = csv.writer(tileFile)
            for tile_layer in self.tile_grid_layers.values():
                for tile_x in range(0, self.level_tile_size[0]):
                    for tile_y in range(0, self.level_tile_size[1]):
                        tile = tile_layer["grid"][tile_x][tile_y]
                        if tile is not None:
                            writer.writerow(["tile", tile.tile_data.tile_id, str(tile.world_position[0]),
                                            str(tile.world_position[1]), str(tile.angle), str(tile.layer)])
            for entity_placement in self.entity_placements:
                writer.writerow(["entity_placement", entity_placement.type, entity_placement.sub_type,
                                 str(entity_placement.world_position[0]), str(entity_placement.world_position[1])])

    def load_level_tiles(self):
        if os.path.isfile(self.file_name):
            self.create_empty_level()

            with open(self.file_name, "r") as tileFile:
                reader = csv.reader(tileFile)
                for line in reader:
                    line_type = line[0]

                    if line_type == "tile":
                        tile_id = line[1]
                        tile_x_pos = float(line[2])
                        tile_y_pos = float(line[3])
                        tile_angle = int(line[4])
                        layer = 0
                        if len(line) == 6:
                            layer = int(line[5])

                        grid_layer = self.tile_grid_layers["layer_" + str(layer)]

                        tile_x = int((tile_x_pos - (self.tile_size[0] / 2)) / self.tile_size[0])
                        tile_y = int((tile_y_pos - (self.tile_size[1] / 2)) / self.tile_size[1])

                        loaded_tile = Tile(grid_layer["sprite_group"], self.collision_grid,
                                           self.all_tile_data[tile_id],
                                           [tile_x_pos, tile_y_pos],
                                           layer, tile_angle)

                        grid_layer["grid"][tile_x][tile_y] = loaded_tile
                        self.update_tile_collision_normals(tile_x, tile_y, layer)

                    elif line_type == "entity_placement":
                        type_id = line[1]
                        sub_type_id = line[2]
                        tile_x_pos = float(line[3])
                        tile_y_pos = float(line[4])
                        if type_id == "ai_spawn":
                            new_entity_placement = AISpawn([tile_x_pos, tile_y_pos],
                                                           type_id, sub_type_id, self.ai_spawn_data)
                            self.entity_placements.append(new_entity_placement)

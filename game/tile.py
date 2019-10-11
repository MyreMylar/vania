import os
import csv
import pygame
from collision.collision_shapes import CollisionRect
from collision.drawable_collision_shapes import DrawableCollisionRect
from game.collision_types import CollisionType


class TileData:
    def __init__(self, file_path, tile_map):
        self.file_path = file_path
        self.tile_map = tile_map
        self.tile_id = os.path.splitext(os.path.basename(file_path))[0]
        self.collidable = False
        self.collide_radius = 26
        self.collision_shapes = []
        self.collision_type = None
        self.image = None

    def load_tile_data(self):
        if os.path.isfile(self.file_path):
            with open(self.file_path, "r") as tileFile:
                reader = csv.reader(tileFile)
                for line in reader:
                    data_type = line[0]
                    if data_type == "isCollidable":
                        self.collidable = bool(int(line[1]))
                    elif data_type == "tileImageCoords":
                        self.image = self.tile_map[int(line[1])][int(line[2])]
                    elif data_type == "rect":
                        top_left_tile_offset = [int(line[1]), int(line[2])]
                        self.collision_shapes.append(["rect",
                                                      top_left_tile_offset,
                                                      pygame.Rect(int(line[1]),
                                                                  int(line[2]),
                                                                  int(line[3])-int(line[1]),
                                                                  int(line[4])-int(line[2]))])
                    elif data_type == "circle":
                        self.collision_shapes.append(["circle",
                                                      [int(line[1]), int(line[2])],
                                                      [int(line[1]), int(line[2])],
                                                      int(line[3])])

                        self.collide_radius = int(line[3])
                    elif data_type == "collision_type":
                        collision_type_string = line[1]
                        if collision_type_string == "world_solid":
                            self.collision_type = CollisionType.WORLD_SOLID
                        elif collision_type_string == "world_platform_edge":
                            self.collision_type = CollisionType.WORLD_PLATFORM_EDGE
                        elif collision_type_string == "ladder":
                            self.collision_type = CollisionType.LADDERS
                        elif collision_type_string == "world_jump_through":
                            self.collision_type = CollisionType.WORLD_JUMP_THROUGH
                        elif collision_type_string == "world_jump_through_edge":
                            self.collision_type = CollisionType.WORLD_JUMP_THROUGH_EDGE
                        elif collision_type_string == "door":
                            self.collision_type = CollisionType.DOOR
                        elif collision_type_string == "water":
                            self.collision_type = CollisionType.WATER
                        else:
                            self.collision_type = CollisionType.WORLD_SOLID


class Tile(pygame.sprite.Sprite):
    def __init__(self, non_moving_sprite_group, collision_grid, tile_data,
                 position, layer, angle=0, collision_enabled=True):
        super().__init__(non_moving_sprite_group)

        self.type = "tile"
        self.collision_enabled = collision_enabled
        self.tile_data = tile_data
        self.collision_grid = collision_grid
        self.image = self.tile_data.image
        self.rect = self.image.get_rect()

        self.world_position = [position[0], position[1]]

        self.layer = layer

        self.angle = angle

        self.collision_shape = None
        self.drawable_collision_rectangle = None
        self.create_collision_shape()

        self.screen_position = [position[0], position[1]]
        self.rect.centerx = int(self.screen_position[0])
        self.rect.centery = int(self.screen_position[1])

    def create_collision_shape(self, override_collision_type=None):
        if self.tile_data.collidable and self.collision_enabled:
            game_types_to_collide_with = [CollisionType.PLAYER]
            handlers_to_use = {CollisionType.PLAYER: self.collision_grid.no_handler}

            if override_collision_type is not None:
                collision_type = override_collision_type
            else:
                collision_type = self.tile_data.collision_type

            for collision_shape in self.tile_data.collision_shapes:
                if collision_shape[0] == "rect":
                    top_left_world_pos = [self.world_position[0]-(self.rect.width/2),
                                          self.world_position[1]-(self.rect.height/2)]

                    collision_rect = pygame.Rect(top_left_world_pos[0] + collision_shape[2].x,
                                                 top_left_world_pos[1] + collision_shape[2].y,
                                                 collision_shape[2].width,
                                                 collision_shape[2].height)
                    self.collision_shape = CollisionRect(collision_rect,
                                                         0,
                                                         handlers_to_use,
                                                         collision_type,
                                                         game_types_to_collide_with)

            self.collision_grid.add_static_grid_aligned_shape_to_grid(self.collision_shape)
            self.collision_shape.owner = self
            self.drawable_collision_rectangle = DrawableCollisionRect(self.collision_shape)

    def draw_collision_shapes(self, screen, camera):
        if self.drawable_collision_rectangle is not None:
            self.drawable_collision_rectangle.update_collided_colours()
            self.drawable_collision_rectangle.draw(screen, camera.position, (camera.half_width,
                                                                             camera.half_height))

    def update(self, camera):
        view_top_left_position = (camera.position[0]-camera.half_width,
                                  camera.position[1]-camera.half_height)
        self.screen_position[0] = self.world_position[0] - view_top_left_position[0]
        self.screen_position[1] = self.world_position[1] - view_top_left_position[1]

        self.rect.centerx = int(self.screen_position[0])
        self.rect.centery = int(self.screen_position[1])


import pygame
import random
import math
from game.collision_types import CollisionType
from collision.collision_shapes import CollisionRect
from collision.drawable_collision_shapes import DrawableCollisionRect


class Projectile(pygame.sprite.Sprite):
    def __init__(self, moving_sprites_group):
        super().__init__(moving_sprites_group)

        self.rect = None
        self.image = None


class ThrowingKnife(Projectile):
    def __init__(self, moving_sprites_group, collision_grid, knife_surface,
                 start_position, throwing_direction, projectile_drawable_rects,
                 camera, is_player_weapon=True, speed=1020.0):
        super().__init__(moving_sprites_group)

        self.collision_grid = collision_grid
        self.moving_sprites_group = moving_sprites_group
        self.original_image = knife_surface
        self.image = self.original_image.copy()
        self.rect = self.image.get_rect()
        self.knife_embed_length = (self.rect.width/9)*4
        self.facing_direction = throwing_direction[:]
        self.facing_angle = math.degrees(math.atan2(self.facing_direction[1], self.facing_direction[0]))

        self.world_position = [start_position[0], start_position[1]]
        self.screen_position = [0.0, 0.0]

        self.throw_speed = speed + random.normalvariate(0, 40)
        self.initial_throw_velocity = [self.facing_direction[0]*self.throw_speed,
                                       self.facing_direction[1]*self.throw_speed]

        self.velocity = [self.initial_throw_velocity[0], self.initial_throw_velocity[1]]

        game_types_to_collide_with = [CollisionType.WORLD_SOLID,
                                      CollisionType.WORLD_PLATFORM_EDGE,
                                      CollisionType.WORLD_JUMP_THROUGH,
                                      CollisionType.WORLD_JUMP_THROUGH_EDGE]

        handlers_to_use = {CollisionType.WORLD_SOLID: self.collision_grid.rub_handler,
                           CollisionType.WORLD_PLATFORM_EDGE: self.collision_grid.rub_handler,
                           CollisionType.WORLD_JUMP_THROUGH: self.collision_grid.rub_handler,
                           CollisionType.WORLD_JUMP_THROUGH_EDGE: self.collision_grid.rub_handler}

        if is_player_weapon:
            self.type = "player_projectile"
            collision_type = CollisionType.PLAYER_PROJECTILES
            game_types_to_collide_with.extend([CollisionType.AI,CollisionType.AI_PROJECTILES])
            handlers_to_use[CollisionType.AI] = self.collision_grid.no_handler
            handlers_to_use[CollisionType.AI_PROJECTILES] = self.collision_grid.no_handler
        else:
            self.type = "enemy_projectile"
            collision_type = CollisionType.AI_PROJECTILES
            game_types_to_collide_with.extend([CollisionType.PLAYER, CollisionType.PLAYER_PROJECTILES])
            handlers_to_use[CollisionType.PLAYER] = self.collision_grid.no_handler
            handlers_to_use[CollisionType.PLAYER_PROJECTILES] = self.collision_grid.no_handler

        self.collision_shape = CollisionRect(pygame.Rect(self.world_position[0],
                                                         self.world_position[1],
                                                         self.rect.width,
                                                         int(self.rect.height*0.6)),
                                             0,
                                             handlers_to_use,
                                             collision_type,
                                             game_types_to_collide_with)
        self.collision_shape.owner = self
        self.collision_grid.add_new_shape_to_grid(self.collision_shape)

        self.collision_shape.set_position(self.world_position)

        self.projectile_drawable_rects = projectile_drawable_rects
        self.drawable_rectangle = DrawableCollisionRect(self.collision_shape)
        self.projectile_drawable_rects.append(self.drawable_rectangle)

        self.frozen = False
        self.life_time = 15.0
        self.hit_something = False

        self.update_screen_position(camera)
        self.rect.centerx = int(self.screen_position[0])
        self.rect.centery = int(self.screen_position[1])

        self.should_kill = False

    def update(self, time_delta, gravity, camera):
        self.life_time -= time_delta
        if self.life_time <= 0.0:
            self.should_kill = True

        if self.collision_shape is not None:
            if len(self.collision_shape.collided_shapes_this_frame) > 0:
                for shape in self.collision_shape.collided_shapes_this_frame:
                    if shape.game_type == CollisionType.AI or shape.game_type == CollisionType.PLAYER or shape.game_type == CollisionType.PLAYER_PROJECTILES or shape.game_type == CollisionType.AI_PROJECTILES:
                        self.should_kill = True
                    else:
                        if not self.hit_something:
                            self.hit_something = True
                            # A bunch of code here to make sure daggers stick into things in a meaty fashion
                            self.world_position[0] = self.collision_shape.x
                            self.world_position[1] = self.collision_shape.y
                            self.velocity = [0.0, 0.0]
                            embed = random.normalvariate(self.knife_embed_length, self.knife_embed_length/8)
                            self.world_position[0] += self.facing_direction[0] * embed
                            self.world_position[1] += self.facing_direction[1] * embed

                            self.collision_shape.set_position(self.world_position)

                            self.frozen = True

        if not self.frozen:
            vel_length = math.sqrt(self.velocity[0] ** 2 + self.velocity[1] ** 2)
            if vel_length == 0.0:
                vel_length = 0.0001
            self.facing_direction = [self.velocity[0] / vel_length, self.velocity[1] / vel_length]
            self.facing_angle = math.degrees(math.atan2(self.facing_direction[1], self.facing_direction[0]))
            self.image = pygame.transform.rotate(self.original_image, -self.facing_angle)
            self.rect = self.image.get_rect()
            self.collision_shape.set_rotation(math.radians(-self.facing_angle))
            self.drawable_rectangle.on_rotation()

            self.velocity[1] += gravity * time_delta

            self.world_position[0] += self.velocity[0] * time_delta
            self.world_position[1] += self.velocity[1] * time_delta

            # set the position of the collision shape
            self.collision_shape.set_position(self.world_position)

        self.update_screen_position(camera)
        self.rect.centerx = int(self.screen_position[0])
        self.rect.centery = int(self.screen_position[1])

        if self.frozen and self.collision_shape is not None:
            self.collision_grid.remove_shape_from_grid(self.collision_shape)
            self.projectile_drawable_rects.remove(self.drawable_rectangle)
            self.collision_shape = None

        if self.should_kill:
            self.kill()
            if self.collision_shape is not None:
                self.collision_grid.remove_shape_from_grid(self.collision_shape)
                self.projectile_drawable_rects.remove(self.drawable_rectangle)
                self.collision_shape = None

    def update_screen_position(self, camera):
        view_top_left_position = (camera.position[0] - camera.half_width,
                                  camera.position[1] - camera.half_height)
        self.screen_position[0] = self.world_position[0] - view_top_left_position[0]
        self.screen_position[1] = self.world_position[1] - view_top_left_position[1]

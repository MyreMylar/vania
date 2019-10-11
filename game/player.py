import pygame
import random
import math

from pygame.locals import *
from game.animation import AnimSet
from game.projectile import ThrowingKnife
from game.collision_types import CollisionType
from collision.collision_shapes import CollisionRect
from collision.drawable_collision_shapes import DrawableCollisionRect
from game.view_cone import ViewCone
from game.exit_door_hint import ExitDoorHint
"""
Scroll down to line 269 for Challenge 2
"""


class Player(pygame.sprite.Sprite):
    def __init__(self, moving_sprites_group, ui_sprites_group, fonts, collision_grid, camera):
        super().__init__(moving_sprites_group)
        self.type = "player"
        self.moving_sprites_group = moving_sprites_group
        self.ui_sprites_group = ui_sprites_group
        self.fonts = fonts
        self.collision_grid = collision_grid
        self.camera = camera
        self.atlas_image = pygame.image.load("images/player.png")
        self.anim_sets = {"idle_right": AnimSet(self.atlas_image, [0, 96], [64, 96], 10, 10, [0, -1]),
                          "idle_left": AnimSet(self.atlas_image, [0, 96], [64, 96], 10, 10, [0, -1],
                                               looping=True, x_flip=True),
                          "run_right": AnimSet(self.atlas_image, [0, 0], [64, 96], 10, 30, [0, -1]),
                          "run_left": AnimSet(self.atlas_image, [0, 0], [64, 96], 10, 30, [0, -1],
                                              looping=True, x_flip=True),
                          "jump_right": AnimSet(self.atlas_image, [0, 192], [64, 96], 10, 8, [0, -1],
                                                looping=False, x_flip=False),
                          "jump_left": AnimSet(self.atlas_image, [0, 192], [64, 96], 10, 8, [0, -1],
                                               looping=False, x_flip=True),
                          "jump_attack_right": AnimSet(self.atlas_image, [0, 770], [96, 96], 10, 40, [0, -1],
                                                       looping=False, x_flip=False),
                          "jump_attack_left": AnimSet(self.atlas_image, [0, 770], [96, 96], 10, 40, [32, -1],
                                                      looping=False, x_flip=True),
                          "jump_throw_right": AnimSet(self.atlas_image, [0, 866], [96, 96], 10, 40, [0, -1],
                                                      looping=False, x_flip=False),
                          "jump_throw_left": AnimSet(self.atlas_image, [0, 866], [96, 96], 10, 40, [32, -1],
                                                     looping=False, x_flip=True),
                          "throw_right": AnimSet(self.atlas_image, [0, 288], [64, 96], 10, 40, [0, -1], False, False),
                          "throw_left": AnimSet(self.atlas_image, [0, 288], [64, 96], 10, 40, [0, -1], False, True),
                          "attack_right": AnimSet(self.atlas_image, [0, 384], [96, 96], 10, 60, [0, -1], False, False),
                          "attack_left": AnimSet(self.atlas_image, [0, 384], [96, 96], 10, 60, [32, -1], False, True),
                          "die_right": AnimSet(self.atlas_image, [0, 480], [96, 96], 10, 20, [0, -1], False, False),
                          "die_left": AnimSet(self.atlas_image, [0, 480], [96, 96], 10, 20, [32, -1], False, True),
                          "slide_right": AnimSet(self.atlas_image, [0, 576], [96, 96], 10, 15, [0, -1], False, False),
                          "slide_left": AnimSet(self.atlas_image, [0, 576], [96, 96], 10, 15, [32, -1], False, True),
                          "climb_up": AnimSet(self.atlas_image, [0, 672], [64, 96], 10, 30, [0, -1]),
                          "climb_down": AnimSet(self.atlas_image, [0, 672], [64, 96], 10, 30, [0, -1], True, True)
                          }

        # load the knife image
        knife_image_position = [0, 960]
        knife_image_dimensions = [30, 6]
        knife_image_rect = pygame.Rect(knife_image_position, knife_image_dimensions)
        self.knife_image = self.atlas_image.subsurface(knife_image_rect).convert_alpha()

        self.active_anim = self.anim_sets["idle_right"]
        self.image = self.active_anim.current_frame

        self.rect = self.image.get_rect()

        self.start_position = (316.0, 596.0)
        self.world_position = [coord for coord in self.start_position]
        self.screen_position = [self.world_position[0], self.world_position[1]]

        game_types_to_collide_with = [CollisionType.WORLD_SOLID,
                                      CollisionType.WORLD_PLATFORM_EDGE,
                                      CollisionType.WORLD_JUMP_THROUGH,
                                      CollisionType.WORLD_JUMP_THROUGH_EDGE,
                                      CollisionType.AI_ATTACKS,
                                      CollisionType.AI_PROJECTILES]
        handlers_to_use = {CollisionType.WORLD_SOLID: collision_grid.rub_handler,
                           CollisionType.WORLD_PLATFORM_EDGE: collision_grid.rub_handler,
                           CollisionType.WORLD_JUMP_THROUGH: collision_grid.no_handler,
                           CollisionType.WORLD_JUMP_THROUGH_EDGE: collision_grid.no_handler,
                           CollisionType.AI_ATTACKS: collision_grid.no_handler,
                           CollisionType.AI_PROJECTILES: collision_grid.no_handler}

        self.collision_shape_offset = [0, 0]
        self.collision_shape = CollisionRect(pygame.Rect(self.world_position[0],
                                                         self.world_position[1],
                                                         self.rect.width,
                                                         self.rect.height),
                                             0,
                                             handlers_to_use,
                                             CollisionType.PLAYER,
                                             game_types_to_collide_with)
        self.collision_grid.add_new_shape_to_grid(self.collision_shape)
        self.collision_shape.owner = self

        self.ladder_collider_offset = [0.0, 0.0]
        self.triggers_collision_shape = CollisionRect(pygame.Rect(self.world_position[0],
                                                                  self.world_position[1],
                                                                  self.rect.width / 3,
                                                                  self.rect.height),
                                                      0,
                                                      {CollisionType.LADDERS: collision_grid.no_handler,
                                                       CollisionType.DOOR: collision_grid.no_handler,
                                                       CollisionType.WATER: collision_grid.no_handler},
                                                      CollisionType.PLAYER_LADDER,
                                                      [CollisionType.LADDERS, CollisionType.DOOR, CollisionType.WATER])
        self.collision_grid.add_new_shape_to_grid(self.triggers_collision_shape)

        self.velocity = [0.0, 0.0]

        self.move_speed = 0.0

        # player speed values
        self.ground_top_speed = 500.0
        self.ground_acceleration = 1000.0
        self.slide_top_speed = 700.0
        self.slide_acceleration = 1500.0
        self.attack_top_speed = 300.0
        self.attack_acceleration = 3000.0
        self.air_top_speed = 250.0
        self.air_acceleration = 500.0
        self.attack_slide_top_speed = 1400.0
        self.attack_slide_acceleration = 3000.0

        self.climb_acceleration = 600.0
        self.climb_top_speed = 300.0
        self.climb_speed = 0.0

        self.jump_height = -600.0

        self.base_health = 100
        self.current_health = self.base_health

        self.action_to_start = ""
        self.motion_state = "idle"
        self.x_facing_direction = "right"
        self.y_facing_direction = "up"

        # directions
        self.move_left = False
        self.move_right = False
        self.climb_up = False
        self.climb_down = False

        # world position information
        self.in_climb_position = True
        self.touching_ground = False

        # weapons
        self.thrown_knife = False
        self.active_knives = []

        # collision shape drawing
        self.projectile_drawable_rects = []
        self.player_drawable_rectangle = DrawableCollisionRect(self.collision_shape)
        self.player_ladder_drawable_rectangle = DrawableCollisionRect(self.triggers_collision_shape)
        self.melee_attack_collision_drawable_rectangle = None
        self.frames_falling = 0

        self.found_ladder_position = [0.0, 0.0]

        self.rect.centerx = int(self.screen_position[0])
        self.rect.centery = int(self.screen_position[1])

        self.respawning = False
        self.respawn_time = 5.0
        self.respawn_timer = self.respawn_time
        self.should_respawn = False

        if self.x_facing_direction == "right":
            facing_vec = [1.0, 0.0]
        else:
            facing_vec = [-1.0, 0.0]
        self.view_cone = ViewCone(self.world_position, facing_vec, fov=145.0, length=450.0)
        self.collision_grid.add_new_shape_to_grid(self.view_cone.collision_circle)
        self.visible_enemies = None
        self.closest_visible_enemy = None

        # melee attack
        self.melee_collision_shape = None

        # handling level exit doors
        self.in_exit_door_position = False
        self.has_exited_level = False
        self.exit_door_hint = ExitDoorHint(self.fonts, self)

    def respawn(self):
        self.motion_state = "idle"
        self.current_health = self.base_health
        self.should_respawn = False
        self.world_position = [coord for coord in self.start_position]
        self.collision_shape.set_position([self.world_position[0] + self.collision_shape_offset[0],
                                           self.world_position[1] + self.collision_shape_offset[1]])

        self.collision_shape.set_position([self.world_position[0] + self.collision_shape_offset[0],
                                           self.world_position[1] + self.collision_shape_offset[1]])

        self.triggers_collision_shape.set_position([self.world_position[0] + self.ladder_collider_offset[0],
                                                    self.world_position[1] + self.ladder_collider_offset[1]])

    def process_events(self, event):
        if event.type == KEYDOWN:
            if event.key == K_LEFT:
                self.move_left = True
            if event.key == K_RIGHT:
                self.move_right = True
            if event.key == K_UP:
                if self.in_climb_position:
                    self.climb_up = True
                elif self.in_exit_door_position:
                    self.has_exited_level = True
                else:
                    self.camera.process_input(event)
            if event.key == K_DOWN:
                if self.in_climb_position:
                    self.climb_down = True
                else:
                    self.camera.process_input(event)
            if event.key == K_SPACE:
                if self.motion_state == "idle" or self.motion_state == "run" and self.touching_ground:
                    self.action_to_start = "jump"
            if event.key == K_LCTRL or event.key == K_RCTRL:
                if self.motion_state == "idle" or self.motion_state == "run" and self.touching_ground:
                    self.action_to_start = "throw"
                elif not self.touching_ground:
                    self.action_to_start = "jump_throw"
            if event.key == K_z or event.key == K_LSHIFT or event.key == K_RSHIFT:
                if self.motion_state == "idle" or self.motion_state == "run" and self.touching_ground:
                    self.action_to_start = "attack"
                elif not self.touching_ground:
                    self.action_to_start = "jump_attack"
            if event.key == K_x:
                if self.motion_state == "idle" or self.motion_state == "run" and self.touching_ground:
                    self.action_to_start = "slide"

            if event.key == K_ESCAPE:
                self.should_respawn = True
        if event.type == KEYUP:
            if event.key == K_LEFT:
                self.move_left = False
            if event.key == K_RIGHT:
                self.move_right = False
            if event.key == K_UP:
                if self.in_climb_position:
                    self.climb_up = False
                else:
                    self.camera.process_input(event)
            if event.key == K_DOWN:
                if self.in_climb_position:
                    self.climb_down = False
                else:
                    self.camera.process_input(event)

    def lose_health(self, health):
        self.current_health -= health
        if self.current_health < 0:
            self.current_health = 0

    def update(self, time_delta, gravity, camera):
        # react to collision stuff
        self.in_climb_position = False
        floor_collided_this_frame = False
        in_exit_door_position = False
        if len(self.triggers_collision_shape.collided_shapes_this_frame) > 0:
            for shape in self.triggers_collision_shape.collided_shapes_this_frame:
                """
                CHALLENGE 2
                -----------
                
                By now you should have added a new water tile to the game and placed some of it in the editor.
                In this step we will detect when the player is touching the water tiles and slow down their
                movement so we appear to 'wade' when in the water.
                
                You will also want to disable this effect when we are not touching water.
                
                HINTS
                ------
                
                - Look at the two if statements below. You will need to make something similar for
                  the CollisionType.WATER.
                - We will need to reduce the speed of our player by adjusting their acceleration and top speed values.
                  There are lots of different speed and acceleration values used here for different movements; it is 
                  likely a good idea to define a 'speed_multiplier' variable that defaults to 1.0. That way we can 
                  multiply our final speed by the multiplier and adjust all the different movements by the same factor
                - Somewhere in this function, further down on line 388-ish, there is some code where the player's 
                  horizontal velocity (self.velocity[0]) is set to the current move_speed. This is a good place to
                  multiply the move speed by our speed multiplier.
                - We need to set the speed multiplier to 1.0 when *not* colliding with water (set it at the top of this
                  function before we test for any collisions) and to something like 0.5 when we detect a collision just
                  below.
                  
                """
                if shape.game_type == CollisionType.LADDERS:
                    self.in_climb_position = True
                    self.found_ladder_position = [shape.x, shape.y]

                elif shape.game_type == CollisionType.DOOR:
                    in_exit_door_position = True
                    if not self.in_exit_door_position:
                        self.in_exit_door_position = True
                        self.add_exit_door_hint()

        if len(self.collision_shape.collided_shapes_this_frame) > 0:
            for shape in self.collision_shape.collided_shapes_this_frame:
                if shape.game_type == CollisionType.AI_PROJECTILES:
                    self.lose_health(10)
                if shape.game_type == CollisionType.WORLD_JUMP_THROUGH or\
                        shape.game_type == CollisionType.WORLD_JUMP_THROUGH_EDGE:
                    # moderately complicated handling for platforms that you can jump and climb through
                    # essentially they only act like platforms if you fall down on top of them
                    # I treat them like collision shapes with no handling and then only apply the mtv vector
                    # if a bunch of conditions are met (falling, not climbing or starting a jump & above the platform)
                    mtv_vector = self.collision_shape.get_frame_mtv_vector(shape)
                    if self.climb_down:
                        self.touching_ground = False
                    else:
                        if mtv_vector is not None and not (
                                self.action_to_start == "jump") and self.motion_state != "climb":
                            if abs(mtv_vector[1]) > abs(mtv_vector[0]) and mtv_vector[1] < 0 and self.velocity[1] > 0.0:
                                if abs(mtv_vector[1]) > 0.5:
                                    self.collision_shape.set_position([self.collision_shape.x + mtv_vector[0],
                                                                       self.collision_shape.y + mtv_vector[1]])
                                floor_collided_this_frame = True
                                self.velocity[1] = 0.0
                                self.frames_falling = 0
                                self.touching_ground = True
                                if self.motion_state == "jump" or self.motion_state == "jump_throw":
                                    self.thrown_knife = False

                        elif mtv_vector is None and self.motion_state != "climb":
                            if self.touching_ground:
                                floor_collided_this_frame = True

                if shape.game_type == CollisionType.WORLD_SOLID or \
                        shape.game_type == CollisionType.WORLD_PLATFORM_EDGE:
                    # see if we have an upwards facing mtv vector
                    mtv_vector = self.collision_shape.get_frame_mtv_vector(shape)
                    if mtv_vector is not None and not (self.action_to_start == "jump"):
                        if abs(mtv_vector[1]) > abs(mtv_vector[0]) and mtv_vector[1] < 0:
                            floor_collided_this_frame = True
                            self.velocity[1] = 0.0
                            self.frames_falling = 0
                            self.touching_ground = True
                            if self.motion_state == "jump" or self.motion_state == "jump_throw":
                                self.thrown_knife = False
                        # see if we have a sideways facing mtv vector
                        if abs(mtv_vector[0]) - abs(mtv_vector[1]) > 0.1:
                            self.move_speed = 0.0
                            self.motion_state = "idle"
                    elif mtv_vector is None:
                        if self.touching_ground:
                            floor_collided_this_frame = True

        if not in_exit_door_position:
            if self.in_exit_door_position:
                self.in_exit_door_position = False
                self.remove_exit_door_hint()

        if not floor_collided_this_frame:
            if self.touching_ground and self.frames_falling > 10:
                self.frames_falling = 0
                self.touching_ground = False
            self.frames_falling += 1

        if len(self.collision_shape.collided_shapes_this_frame) > 0:
            self.world_position[0] = self.collision_shape.x - self.collision_shape_offset[0]
            self.world_position[1] = self.collision_shape.y - self.collision_shape_offset[1]

        self.update_climbing(time_delta)

        if self.motion_state != "climb":
            if self.touching_ground or self.motion_state == "die":
                if self.motion_state == "throw":
                    self.update_throwing(camera)
                elif self.motion_state == "attack":
                    self.update_melee_attacking(time_delta)
                elif self.motion_state == "slide":
                    self.update_sliding(time_delta)
                elif self.motion_state == "die":
                    self.update_dying()
                else:
                    self.update_running(time_delta)
            else:
                self.update_jumping(time_delta, camera)

            self.velocity[0] = self.move_speed  # A good place to add a move speed multiplier

        # if attack is interrupted make sure we kill attack shape
        if not (self.motion_state == "attack" or self.motion_state == "jump_attack"):
            if self.melee_collision_shape is not None:
                self.collision_grid.remove_shape_from_grid(self.melee_collision_shape)
                self.melee_collision_shape = None

        # if slide interrupted make sure we restore normal collision shape dimensions
        if not self.motion_state == "slide":
            if self.collision_shape.width == 96 and self.collision_shape.height == 32:
                self.collision_shape.set_dimensions(64, 96)
                self.collision_shape_offset = [0, 0]
                self.player_drawable_rectangle.on_change_dimensions()

        if self.action_to_start != "":
            if self.action_to_start == "jump":
                self.touching_ground = False
                self.velocity[1] = self.jump_height
                self.world_position[1] -= 10.0
            if self.action_to_start == "slide":
                self.collision_shape.set_dimensions(96, 32)
                self.collision_shape_offset = [0, 32]
                self.player_drawable_rectangle.on_change_dimensions()
            self.motion_state = self.action_to_start
            self.action_to_start = ""

        if self.motion_state == "climb":
            pass
        else:
            if not floor_collided_this_frame:
                self.velocity[1] += gravity * time_delta

        self.world_position[0] += self.velocity[0] * time_delta
        self.world_position[1] += self.velocity[1] * time_delta

        self.update_animation(time_delta)

        # set the position of the collision shapes
        self.collision_shape.set_position([self.world_position[0] + self.collision_shape_offset[0],
                                           self.world_position[1] + self.collision_shape_offset[1]])

        self.triggers_collision_shape.set_position([self.world_position[0] + self.ladder_collider_offset[0],
                                                    self.world_position[1] + self.ladder_collider_offset[1]])

        self.update_visible_enemies()

        #  set the sprite's centre position based of the current
        #  position and the animation's 'centre point' offset
        self.update_screen_position(camera)
        self.rect.centerx = int(self.screen_position[0] - self.active_anim.centre_offset[0])
        self.rect.centery = int(self.screen_position[1] - self.active_anim.centre_offset[1])

        if self.should_respawn:
            self.respawn()

        if self.current_health <= 0 and not self.respawning:
            self.action_to_start = "die"
            self.respawning = True
            self.respawn_timer = self.respawn_time

        if self.respawning:
            if self.respawn_timer <= 0.0:
                self.should_respawn = True
                self.respawning = False
            else:
                self.respawn_timer -= time_delta

    def in_range_and_in_front(self, sprite):
        x_dist = sprite.world_position[0] - self.world_position[0]
        y_dist = sprite.world_position[1] - self.world_position[1]
        distance_squared = x_dist ** 2 + y_dist ** 2
        if distance_squared >= self.view_cone.length_squared:
            return False

        if self.x_facing_direction == "right":
            facing_vec = [1.0, 0.0]
        else:
            facing_vec = [-1.0, 0.0]
        dot = facing_vec[0] * x_dist + facing_vec[1] * y_dist
        if dot < 0:
            return False

        return True

    def update_visible_enemies(self):
        enemies = [sprite for sprite in self.moving_sprites_group.sprites()
                   if sprite.type == "enemy" and self.in_range_and_in_front(sprite)]

        if len(enemies) > 0 and self.collision_shape.moved_since_last_collision_test:
            self.view_cone.set_position(pygame.math.Vector2(self.world_position))
            if self.x_facing_direction == "right":
                facing_vec = [1.0, 0.0]
            else:
                facing_vec = [-1.0, 0.0]
            self.view_cone.set_facing_direction(pygame.math.Vector2(facing_vec))
            self.view_cone.update()
            self.visible_enemies = [sprite for sprite in enemies
                                    if self.view_cone.is_subject_visible(pygame.math.Vector2(sprite.world_position))]
            if len(self.visible_enemies) > 0:
                self.closest_visible_enemy = self.find_closest(self.visible_enemies)
            else:
                self.closest_visible_enemy = None
        else:
            self.view_cone.clear()
            self.closest_visible_enemy = None

    def find_closest(self, sprites):
        closest_distance = 9999999999999999.0
        closest_sprite = None
        for sprite in sprites:
            x_dist = self.world_position[0] - sprite.world_position[0]
            y_dist = self.world_position[1] - sprite.world_position[1]
            squared_dist = x_dist ** 2 + y_dist ** 2
            if squared_dist < closest_distance:
                closest_distance = squared_dist
                closest_sprite = sprite
        return closest_sprite

    def update_screen_position(self, camera):
        view_top_left_position = (camera.position[0] - camera.half_width,
                                  camera.position[1] - camera.half_height)
        self.screen_position[0] = self.world_position[0] - view_top_left_position[0]
        self.screen_position[1] = self.world_position[1] - view_top_left_position[1]

    def update_animation(self, time_delta):
        # set the animation name based on motion and direction
        anim_name = self.motion_state + "_"
        if self.motion_state == "climb":
            anim_name += self.y_facing_direction
        else:
            anim_name += self.x_facing_direction
        # if this is a new animation, run the start function
        if self.active_anim != self.anim_sets[anim_name]:
            self.active_anim = self.anim_sets[anim_name]
            self.active_anim.start()
        # update the animation & set the sprite image to the current animation frame
        self.active_anim.update(time_delta)
        self.image = self.active_anim.current_frame

    def update_jumping(self, time_delta, camera):
        if self.motion_state == "jump_attack":
            if self.active_anim.frame_index == 3 and self.melee_collision_shape is None:
                attack_position = [self.world_position[0], self.world_position[1]]
                if self.x_facing_direction == "left":
                    attack_position[0] -= 64
                attack_dimensions = [64, 16]
                game_types_to_collide_with = [CollisionType.AI]
                handlers_to_use = {CollisionType.AI: self.collision_grid.no_handler}
                self.melee_collision_shape = CollisionRect(pygame.Rect(attack_position[0],
                                                                       attack_position[1],
                                                                       attack_dimensions[0],
                                                                       attack_dimensions[1]),
                                                           0,
                                                           handlers_to_use,
                                                           CollisionType.PLAYER_ATTACKS,
                                                           game_types_to_collide_with)
                self.collision_grid.add_new_shape_to_grid(self.melee_collision_shape)
                self.melee_collision_shape.owner = self

                self.melee_attack_collision_drawable_rectangle = DrawableCollisionRect(self.melee_collision_shape)
            elif self.active_anim.frame_index > 3 and self.melee_collision_shape is not None:
                self.collision_grid.remove_shape_from_grid(self.melee_collision_shape)
                self.melee_collision_shape = None
            if not self.active_anim.running:
                self.motion_state = "jump"
        elif self.motion_state == "jump_throw":
            if self.active_anim.frame_index == 3 and not self.thrown_knife:
                self.thrown_knife = True
                if self.closest_visible_enemy is not None:
                    x_dir = self.closest_visible_enemy.world_position[0] - self.world_position[0]
                    y_dir = self.closest_visible_enemy.world_position[1] - self.world_position[1]
                    distance = math.sqrt(x_dir ** 2 + y_dir ** 2)
                    throwing_direction = [x_dir / distance, y_dir / distance]
                    # knives travel at roughly 1000.0 pixels a second, gravity is 800 pixels down per second
                    # so we need to correct the direction vector based on how far away the target is.
                    # after 1000 distance we will have descended roughly 800 from our target position

                    # calculated by assuming traveling in a straight line to the right to a point 1000.0 away
                    gravity_offset_vec = [0.0, -0.625 * distance / 1000.0]
                    throwing_direction = [throwing_direction[0] + gravity_offset_vec[0],
                                          throwing_direction[1] + gravity_offset_vec[1]]
                    # renormalise direction
                    throwing_dir_len = math.sqrt(throwing_direction[0] ** 2 + throwing_direction[1] ** 2)
                    throwing_direction = [throwing_direction[0] / throwing_dir_len,
                                          throwing_direction[1] / throwing_dir_len]

                else:
                    if self.x_facing_direction == 'left':
                        throwing_direction = [-0.98, -0.19 + random.normalvariate(0, 0.02)]
                    else:
                        throwing_direction = [0.98, -0.19 + random.normalvariate(0, 0.02)]
                knife = ThrowingKnife(self.moving_sprites_group, self.collision_grid, self.knife_image,
                                      self.world_position, throwing_direction, self.projectile_drawable_rects,
                                      camera)
                self.active_knives.append(knife)
            if not self.active_anim.running:
                self.thrown_knife = False
                self.motion_state = "jump"
        else:
            self.motion_state = "jump"
        if self.move_left:
            self.move_speed -= self.air_acceleration * time_delta
            if self.move_speed < -self.air_top_speed:
                self.move_speed = -self.air_top_speed

            self.velocity[0] = self.move_speed
            self.x_facing_direction = "left"
            speed_factor = abs(self.move_speed / self.air_top_speed)
            self.active_anim.set_speed_factor(speed_factor)
        elif self.move_right:
            self.move_speed += self.air_acceleration * time_delta
            if self.move_speed > self.air_top_speed:
                self.move_speed = self.air_top_speed
            self.velocity[0] = self.move_speed
            self.x_facing_direction = "right"
            speed_factor = abs(self.move_speed / self.air_top_speed)
            self.active_anim.set_speed_factor(speed_factor)

    def update_running(self, time_delta):
        if self.move_left:
            self.motion_state = "run"
            if self.x_facing_direction == "right":
                self.move_speed = 0.0
            self.move_speed -= self.ground_acceleration * time_delta
            if self.move_speed < -self.ground_top_speed:
                self.move_speed = -self.ground_top_speed
            self.velocity[0] = self.move_speed
            self.x_facing_direction = "left"
            speed_factor = abs(self.move_speed / self.ground_top_speed)
            self.active_anim.set_speed_factor(speed_factor)

        elif self.move_right:
            self.motion_state = "run"
            if self.x_facing_direction == "left":
                self.move_speed = 0.0
            self.move_speed += self.ground_acceleration * time_delta
            if self.move_speed > self.ground_top_speed:
                self.move_speed = self.ground_top_speed
            self.velocity[0] = self.move_speed
            self.x_facing_direction = "right"
            speed_factor = abs(self.move_speed / self.ground_top_speed)
            self.active_anim.set_speed_factor(speed_factor)
        else:
            self.move_speed = 0.0
            self.velocity[0] = self.move_speed
            self.motion_state = "idle"

    def update_dying(self):
        if not self.active_anim.running:
            pass
            # self.dying = False

    def update_melee_attacking(self, time_delta):
        if self.active_anim.running:
            if 3 < self.active_anim.frame_index < 10:
                if self.x_facing_direction == "left":
                    self.move_speed -= self.attack_slide_acceleration * time_delta
                    if self.move_speed < -self.attack_slide_top_speed:
                        self.move_speed = -self.attack_slide_top_speed
                    self.velocity[0] = self.move_speed
                elif self.x_facing_direction == "right":
                    self.move_speed += self.attack_slide_acceleration * time_delta
                    if self.move_speed > self.attack_slide_top_speed:
                        self.move_speed = self.attack_slide_top_speed
                    self.velocity[0] = self.move_speed
            if self.active_anim.frame_index == 3 and self.melee_collision_shape is None:
                attack_position = [self.world_position[0], self.world_position[1]]
                if self.x_facing_direction == "left":
                    attack_position[0] -= 64
                attack_dimensions = [64, 16]
                game_types_to_collide_with = [CollisionType.AI]
                handlers_to_use = {CollisionType.AI: self.collision_grid.no_handler}
                self.melee_collision_shape = CollisionRect(pygame.Rect(attack_position[0],
                                                                       attack_position[1],
                                                                       attack_dimensions[0],
                                                                       attack_dimensions[1]),
                                                           0,
                                                           handlers_to_use,
                                                           CollisionType.PLAYER_ATTACKS,
                                                           game_types_to_collide_with)
                self.collision_grid.add_new_shape_to_grid(self.melee_collision_shape)
                self.melee_collision_shape.owner = self

                self.melee_attack_collision_drawable_rectangle = DrawableCollisionRect(self.melee_collision_shape)
            elif self.active_anim.frame_index > 3 and self.melee_collision_shape is not None:
                self.collision_grid.remove_shape_from_grid(self.melee_collision_shape)
                self.melee_collision_shape = None

        else:
            self.motion_state = "idle"

    def update_throwing(self, camera):
        if self.active_anim.frame_index == 3 and not self.thrown_knife:
            self.thrown_knife = True
            if self.closest_visible_enemy is not None:
                x_dir = self.closest_visible_enemy.world_position[0] - self.world_position[0]
                y_dir = self.closest_visible_enemy.world_position[1] - self.world_position[1]
                distance = math.sqrt(x_dir ** 2 + y_dir ** 2)
                throwing_direction = [x_dir / distance, y_dir / distance]
                # knives travel at roughly 1000.0 pixels a second, gravity is 800 pixels down per second
                # so we need to correct the direction vector based on how far away the target is.
                # after 1000 distance we will have descended roughly 800 from our target position

                # calculated by assuming traveling in a straight line to the right to a point 1000.0 away
                gravity_offset_vec = [0.0, -0.625 * distance / 1000.0]
                throwing_direction = [throwing_direction[0] + gravity_offset_vec[0],
                                      throwing_direction[1] + gravity_offset_vec[1]]
                # renormalise direction
                throwing_dir_len = math.sqrt(throwing_direction[0] ** 2 + throwing_direction[1] ** 2)
                throwing_direction = [throwing_direction[0] / throwing_dir_len,
                                      throwing_direction[1] / throwing_dir_len]

            else:
                if self.x_facing_direction == 'left':
                    throwing_direction = [-0.98, -0.19 + random.normalvariate(0, 0.02)]
                else:
                    throwing_direction = [0.98, -0.19 + random.normalvariate(0, 0.02)]
            knife = ThrowingKnife(self.moving_sprites_group, self.collision_grid, self.knife_image,
                                  self.world_position, throwing_direction, self.projectile_drawable_rects,
                                  camera)
            self.active_knives.append(knife)
        if not self.active_anim.running:
            self.motion_state = "idle"
            self.thrown_knife = False

    def update_sliding(self, time_delta):
        if self.active_anim.running:
            if self.x_facing_direction == "left":
                self.move_speed -= self.slide_acceleration * time_delta
                if self.move_speed < -self.slide_top_speed:
                    self.move_speed = -self.slide_top_speed
                self.velocity[0] = self.move_speed
            elif self.x_facing_direction == "right":
                self.move_speed += self.slide_acceleration * time_delta
                if self.move_speed > self.slide_top_speed:
                    self.move_speed = self.slide_top_speed
                self.velocity[0] = self.move_speed
        else:
            self.collision_shape.set_dimensions(64, 96)
            self.collision_shape_offset = [0, 0]
            self.player_drawable_rectangle.on_change_dimensions()
            self.motion_state = "idle"

    def update_climbing(self, time_delta):
        if self.motion_state == "climb" and not self.in_climb_position:
            self.motion_state = "idle"
        if self.in_climb_position:
            if self.climb_up:
                self.world_position[0] = self.found_ladder_position[0]
                if self.touching_ground:
                    self.world_position[1] -= 10.0

                self.motion_state = "climb"
                self.y_facing_direction = "up"
                self.velocity[1] = 0.0
                self.move_speed = 0.0
                self.touching_ground = False
                self.climb_speed -= self.climb_acceleration * time_delta
                if self.climb_speed < -self.climb_top_speed:
                    self.climb_speed = -self.climb_top_speed
                self.world_position[1] += (self.climb_speed * time_delta)
                speed_factor = abs(self.climb_speed / self.climb_top_speed)
                self.active_anim.set_speed_factor(speed_factor)
            elif self.climb_down:
                self.world_position[0] = self.found_ladder_position[0]
                if self.touching_ground:
                    self.motion_state = "idle"
                    self.climb_speed = 0.0
                else:
                    self.motion_state = "climb"
                    self.y_facing_direction = "down"
                    self.velocity[1] = 0.0
                    self.move_speed = 0.0
                    self.touching_ground = False
                    self.climb_speed += self.climb_acceleration * time_delta
                    if self.climb_speed > self.climb_top_speed:
                        self.climb_speed = self.climb_top_speed
                    self.world_position[1] += (self.climb_speed * time_delta)
                    speed_factor = abs(self.climb_speed / self.climb_top_speed)
                    self.active_anim.set_speed_factor(speed_factor)
            elif self.motion_state == "climb":
                self.touching_ground = False
                self.velocity[1] = 0.0
                self.climb_speed = 0.0
                self.active_anim.set_speed_factor(0.0)
        else:
            self.climb_up = False
            self.climb_down = False
        if self.motion_state != "climb":
            self.climb_speed = 0.0

    def draw_collision_shapes(self, screen, camera):
        self.player_drawable_rectangle.update_collided_colours()
        self.player_drawable_rectangle.draw(screen, camera.position, (camera.half_width,
                                                                      camera.half_height))

        self.player_ladder_drawable_rectangle.update_collided_colours()
        self.player_ladder_drawable_rectangle.draw(screen, camera.position, (camera.half_width,
                                                                             camera.half_height))

        for rect in self.projectile_drawable_rects:
            rect.update_collided_colours()
            rect.draw(screen, camera.position, (camera.half_width,
                                                camera.half_height))

        self.view_cone.draw(screen, camera)

        if self.melee_collision_shape is not None:
            self.melee_attack_collision_drawable_rectangle.update_collided_colours()
            self.melee_attack_collision_drawable_rectangle.draw(screen, camera.position, (camera.half_width,
                                                                                          camera.half_height))

    def add_exit_door_hint(self):
        self.ui_sprites_group.add(self.exit_door_hint)

    def remove_exit_door_hint(self):
        self.ui_sprites_group.remove(self.exit_door_hint)

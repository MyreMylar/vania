import pygame
from game.animation import AnimSet
from game.collision_types import CollisionType
from collision.collision_shapes import CollisionRect
from collision.drawable_collision_shapes import DrawableCollisionRect
from game.ui_enemy_health_bar import UIEnemyHealthBar
from game.view_cone import ViewCone
from game.projectile import ThrowingKnife


class EnemyArcher(pygame.sprite.Sprite):
    """
    An enemy type for the Vania game. This guy is going to stroll about from left to right and back again on a platform,
    then, if he sees the player, shoot an arrow in that general direction.
    """
    def __init__(self, start_position, moving_sprites_group, ui_sprites_group, collision_grid, archer_image):
        super().__init__(moving_sprites_group)
        self.type = "enemy"
        self.moving_sprites_group = moving_sprites_group
        self.ui_sprites_group = ui_sprites_group
        self.collision_grid = collision_grid

        self.atlas_image = archer_image
        self.anim_sets = {"idle_right": AnimSet(atlas_surface=self.atlas_image, start_pos=[0, 0],
                                                frame_size=[64, 96], num_frames=8, base_speed=8,
                                                centre_offset=[0, -2]),
                          "idle_left": AnimSet(atlas_surface=self.atlas_image, start_pos=[0, 0],
                                               frame_size=[64, 96], num_frames=8, base_speed=8,
                                               centre_offset=[0, -2], x_flip=True),
                          "walk_right": AnimSet(atlas_surface=self.atlas_image, start_pos=[0, 96], frame_size=[64, 96],
                                                num_frames=6, base_speed=8, centre_offset=[0, -2]),
                          "walk_left": AnimSet(atlas_surface=self.atlas_image, start_pos=[0, 96], frame_size=[64, 96],
                                               num_frames=6, base_speed=8, centre_offset=[0, -2], x_flip=True),
                          "attack_right": AnimSet(atlas_surface=self.atlas_image, start_pos=[0, 192],
                                                  frame_size=[96, 96], num_frames=6, base_speed=8,
                                                  centre_offset=[0, -2]),
                          "attack_left": AnimSet(atlas_surface=self.atlas_image, start_pos=[0, 192],
                                                 frame_size=[96, 96], num_frames=6, base_speed=8,
                                                 centre_offset=[32, -2], x_flip=True)
                          }
        self.active_anim = self.anim_sets["idle_left"]
        self.image = self.active_anim.current_frame
        self.rect = self.image.get_rect()

        self.start_position = start_position[:]
        self.world_position = [coord for coord in self.start_position]
        self.screen_position = [self.world_position[0], self.world_position[1]]

        game_types_to_collide_with = [CollisionType.WORLD_SOLID,
                                      CollisionType.WORLD_JUMP_THROUGH,
                                      CollisionType.WORLD_PLATFORM_EDGE,
                                      CollisionType.WORLD_JUMP_THROUGH_EDGE,
                                      CollisionType.PLAYER_ATTACKS,
                                      CollisionType.PLAYER_PROJECTILES]
        handlers_to_use = {CollisionType.WORLD_SOLID: collision_grid.rub_handler,
                           CollisionType.WORLD_JUMP_THROUGH: collision_grid.rub_handler,
                           CollisionType.WORLD_PLATFORM_EDGE: collision_grid.rub_handler,
                           CollisionType.WORLD_JUMP_THROUGH_EDGE: collision_grid.rub_handler,
                           CollisionType.PLAYER_ATTACKS: collision_grid.no_handler,
                           CollisionType.PLAYER_PROJECTILES: collision_grid.no_handler}

        self.collision_shape_offset = [0, 0]
        self.collision_shape = CollisionRect(pygame.Rect(self.world_position[0],
                                                         self.world_position[1],
                                                         self.rect.width,
                                                         self.rect.height),
                                             0,
                                             handlers_to_use,
                                             CollisionType.AI,
                                             game_types_to_collide_with)
        self.collision_grid.add_new_shape_to_grid(self.collision_shape)
        self.collision_shape.owner = self

        self.base_health = 100
        self.current_health = self.base_health

        self.rect.centerx = int(self.screen_position[0])
        self.rect.centery = int(self.screen_position[1])

        self.velocity = [0.0, 0.0]
        self.motion_state = "idle"

        self.frames_falling = 0
        self.touching_ground = False
        self.move_speed = 0.0

        self.x_facing_direction = "left"
        self.changed_direction_recently = False

        self.health_ui = UIEnemyHealthBar(self, self.ui_sprites_group)

        # debug draw
        self.drawable_collision_rectangle = DrawableCollisionRect(self.collision_shape)

        # view cone params
        if self.x_facing_direction == "right":
            facing_vec = [1.0, 0.0]
        else:
            facing_vec = [-1.0, 0.0]
        self.view_cone = ViewCone(self.world_position, facing_vec, fov=30.0, length=400.0)
        self.collision_grid.add_new_shape_to_grid(self.view_cone.collision_circle)
        self.visible_enemies = None
        self.closest_visible_enemy = None

        arrow_image_position = [576, 0]
        arrow_image_dimensions = [46, 7]
        arrow_image_rect = pygame.Rect(arrow_image_position, arrow_image_dimensions)
        self.arrow_image = self.atlas_image.subsurface(arrow_image_rect).convert_alpha()
        self.time_since_last_saw_enemy = 0
        self.enemy_spotted_timeout = 3.0
        self.is_time_to_fire = False
        self.fire_time = 1.0
        self.fire_timer = 0.0
        self.active_arrows = []
        self.projectile_drawable_rects = []

        self.has_moved = False
        self.disable_movement = False

        self.sprite_flash_acc = 0.0
        self.sprite_flash_time = 0.25
        self.should_flash_sprite = False
        self.active_flash_sprite = False
        self.last_impact_direction_vec = None
        self.direction_change_time = 1.0
        self.direction_change_timer = 0.0
        self.impact_velocity = None
        self.impact_time = 0.1
        self.impact_timer = 0.0

        self.last_frame_x_pos = self.world_position[0]
        self.last_collision_shape_x = self.collision_shape.x

        self.collision_print_time = 1.0
        self.collision_print_timer = 0.0

        # debuggers
        self.start_frame_collision_shape_x = self.collision_shape.x
        self.pre_collision_gets_moved_x = self.collision_shape.x
        self.post_collision_gets_moved_x = self.collision_shape.x

        self.alive = True

    def shutdown(self):
        if self.alive:
            self.kill()
            self.health_ui.kill()
            self.collision_grid.remove_shape_from_grid(self.collision_shape)
            self.collision_grid.remove_shape_from_grid(self.view_cone.collision_circle)
            self.drawable_collision_rectangle = None
            self.alive = False

    def draw_debug_info(self, screen, camera):
        if self.drawable_collision_rectangle is not None:
            self.drawable_collision_rectangle.update_collided_colours()
            self.drawable_collision_rectangle.draw(screen, camera.position, (camera.half_width,
                                                                             camera.half_height))
            self.view_cone.draw(screen, camera)

    def update_screen_position(self, camera):
        view_top_left_position = (camera.position[0] - camera.half_width,
                                  camera.position[1] - camera.half_height)
        self.screen_position[0] = self.world_position[0] - view_top_left_position[0]
        self.screen_position[1] = self.world_position[1] - view_top_left_position[1]

    def update_animation(self, time_delta):
        # set the animation name based on motion and direction
        anim_name = self.motion_state + "_"
        anim_name += self.x_facing_direction
        # if this is a new animation, run the start function
        if self.active_anim != self.anim_sets[anim_name]:
            self.active_anim = self.anim_sets[anim_name]
            self.active_anim.start()
        # update the animation & set the sprite image to the current animation frame
        self.active_anim.update(time_delta)
        self.image = self.active_anim.current_frame

    def update_movement(self, time_delta, camera):
        self.has_moved = False
        if self.closest_visible_enemy is not None and self.touching_ground:
            self.velocity[0] = 0.0
            on_left = (self.closest_visible_enemy.world_position[0] - self.world_position[0]) < 0.0
            if on_left:
                self.motion_state = "attack"
                self.x_facing_direction = "left"
            else:
                self.motion_state = "attack"
                self.x_facing_direction = "right"

            if self.is_time_to_fire:
                self.is_time_to_fire = False
                self.fire_timer = 0.0
                if self.x_facing_direction == "left":
                    firing_direction = [-0.90, -0.1]
                else:
                    firing_direction = [0.90, -0.1]

                arrow = ThrowingKnife(self.moving_sprites_group, self.collision_grid, self.arrow_image,
                                      self.world_position, firing_direction, self.projectile_drawable_rects,
                                      camera, is_player_weapon=False, speed=1500.0)
                self.active_arrows.append(arrow)
            else:
                self.fire_timer += time_delta
                if self.fire_timer >= self.fire_time:
                    self.is_time_to_fire = True
        elif self.touching_ground:
            self.has_moved = True
            if self.x_facing_direction == "left":
                self.motion_state = "walk"
                self.velocity[0] = -100.0
            elif self.x_facing_direction == "right":
                self.motion_state = "walk"
                self.velocity[0] = 100.0
        else:
            self.motion_state = "idle"

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

        vector_to_point = [x_dist, y_dist]

        cross_1 = self.view_cone.cone_extent_facings[0][0] * vector_to_point[1] - self.view_cone.cone_extent_facings[0][1] * vector_to_point[0]
        cross_2 = self.view_cone.cone_extent_facings[1][0] * vector_to_point[1] - self.view_cone.cone_extent_facings[1][1] * vector_to_point[0]

        if cross_1 < 0 < cross_2 or cross_1 > 0 > cross_2:
            return True
        else:
            return False

    def update_visible_enemies(self, time_delta):
        if self.closest_visible_enemy is not None:
            self.time_since_last_saw_enemy += time_delta
        if self.time_since_last_saw_enemy > self.enemy_spotted_timeout:
            self.closest_visible_enemy = None

        enemies = [sprite for sprite in self.moving_sprites_group.sprites()
                   if sprite.type == "player" and self.in_range_and_in_front(sprite)]

        if len(enemies) > 0 and self.has_moved:
            self.view_cone.set_position(pygame.math.Vector2(self.world_position))
            if self.x_facing_direction == "right":
                facing_vec = [1.0, 0.0]
            else:
                facing_vec = [-1.0, 0.0]
            self.view_cone.set_facing_direction(pygame.math.Vector2(facing_vec))
            self.view_cone.update()
            self.visible_enemies = [sprite for sprite in enemies if
                                    self.view_cone.is_subject_visible(pygame.math.Vector2(sprite.world_position)) and
                                    sprite.current_health > 0]
            if len(self.visible_enemies) > 0:
                self.closest_visible_enemy = self.find_closest(self.visible_enemies)
                self.time_since_last_saw_enemy = 0
        else:
            self.view_cone.clear()

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

    def update(self, time_delta, gravity, camera):

        floor_collided_this_frame = False
        impact_velocity = None
        hit_wall = False
        mtv_vector = None

        if len(self.collision_shape.collided_shapes_this_frame) > 0:
            for shape in self.collision_shape.collided_shapes_this_frame:
                if shape.game_type == CollisionType.PLAYER_PROJECTILES:
                    if not self.should_flash_sprite:  # invincible for flash time secs (0.5) after taking damage
                        self.take_damage(15)
                        # turn to face damage source
                        self.last_impact_direction_vec = pygame.math.Vector2(shape.owner.velocity[0],
                                                                             shape.owner.velocity[1])
                        self.last_impact_direction_vec.normalize_ip()
                        impact_velocity = self.apply_knockback(shape)

                if shape.game_type == CollisionType.PLAYER_ATTACKS:
                    if not self.should_flash_sprite:  # invincible for flash time secs (0.5) after taking damage
                        self.take_damage(15)
                        # turn to face damage source
                        self.last_impact_direction_vec = pygame.math.Vector2(self.world_position[0] - shape.owner.world_position[0],
                                                                             self.world_position[1] - shape.owner.world_position[1])
                        if self.last_impact_direction_vec.length_squared() > 0:
                            self.last_impact_direction_vec.normalize_ip()
                        impact_velocity = self.apply_knockback(shape)

                if shape.game_type == CollisionType.WORLD_PLATFORM_EDGE or shape.game_type == CollisionType.WORLD_JUMP_THROUGH_EDGE:
                    # slightly tricksy bit of code here to detect when are at a left or right platform edge
                    # relies on the edges being tagged up using a special tile type and some poking at the normals
                    # to figure out if it is a left or right platform edge. This method won't work on single block
                    # platforms but that's probably OK, AI can just fall off those.
                    if not self.changed_direction_recently and self.motion_state == "walk":
                        if shape.y > self.collision_shape.aabb_rect.bottom:  # test we are walking on top of this edge
                            if self.x_facing_direction == "left":
                                if self.collision_shape.x < shape.x and not shape.normals['left'].should_skip:
                                    self.collision_shape.set_position([shape.x, self.collision_shape.y])
                                    self.changed_direction_recently = True
                                    self.x_facing_direction = "right"
                            elif self.x_facing_direction == "right":
                                if self.collision_shape.x > shape.x and not shape.normals['right'].should_skip:
                                    self.collision_shape.set_position([shape.x, self.collision_shape.y])
                                    self.changed_direction_recently = True
                                    self.x_facing_direction = "left"

                if shape.game_type == CollisionType.WORLD_SOLID or \
                        shape.game_type == CollisionType.WORLD_PLATFORM_EDGE or \
                        shape.game_type == CollisionType.WORLD_JUMP_THROUGH or \
                        shape.game_type == CollisionType.WORLD_JUMP_THROUGH_EDGE:
                    # see if we have an upwards facing mtv vector
                    mtv_vector = self.collision_shape.get_frame_mtv_vector(shape)
                    if mtv_vector is not None:
                        if abs(mtv_vector[1]) > abs(mtv_vector[0]) and mtv_vector[1] < 0:
                            floor_collided_this_frame = True
                            self.velocity[1] = 0.0
                            self.frames_falling = 0
                            self.touching_ground = True
                        # see if we have a sideways facing mtv vector
                        if abs(mtv_vector[0]) > abs(mtv_vector[1]):
                            hit_wall = True
                            self.velocity[0] = 0.0
                            # makes AI change direction if they hit a wall.
                            if not self.changed_direction_recently:
                                self.changed_direction_recently = True
                                if self.x_facing_direction == "left" and mtv_vector[0] > 0:
                                    self.x_facing_direction = "right"
                                elif self.x_facing_direction == "right" and mtv_vector[0] < 0:
                                    self.x_facing_direction = "left"

                    #if not self.touching_ground:
                    #    print("mid air collision")
                    #    self.velocity[0] = 0.0
                    #    self.velocity[1] = 0.0
                    #    self.collision_shape.x = self.world_position[0]
                    #    self.collision_shape.y = self.world_position[1]

        if not floor_collided_this_frame:
            if self.touching_ground and self.frames_falling > 10:
                self.frames_falling = 0
                self.touching_ground = False
            self.frames_falling += 1

        if len(self.collision_shape.collided_shapes_this_frame) > 0:
            self.world_position[0] = self.collision_shape.x - self.collision_shape_offset[0]
            self.world_position[1] = self.collision_shape.y - self.collision_shape_offset[1]

        if not floor_collided_this_frame:
            self.velocity[1] += gravity * time_delta

        self.update_impact_reactions(hit_wall, impact_velocity, time_delta)

        velocity_delta_vec = pygame.math.Vector2(self.velocity[0] * time_delta,
                                                 self.velocity[1] * time_delta)
        if velocity_delta_vec.length() < 32.0:
            self.world_position[0] += self.velocity[0] * time_delta
            self.world_position[1] += self.velocity[1] * time_delta
        else:
            print("clamping velocity")
            velocity_delta_vec = velocity_delta_vec.normalize_ip() * 32.0
            self.velocity[0] = velocity_delta_vec.x / time_delta
            self.velocity[1] = velocity_delta_vec.y / time_delta

        if not self.disable_movement:
            self.update_movement(time_delta, camera)
        self.update_animation(time_delta)
        self.update_sprite(time_delta)
        self.update_visible_enemies(time_delta)

        if self.changed_direction_recently:
            if self.direction_change_timer < self.direction_change_time:
                self.direction_change_timer += time_delta
            else:
                self.changed_direction_recently = False
                self.direction_change_timer = 0.0

        # set the position of the collision shape
        self.collision_shape.set_position([self.world_position[0] + self.collision_shape_offset[0],
                                           self.world_position[1] + self.collision_shape_offset[1]])

        self.update_screen_position(camera)
        self.rect.centerx = int(self.screen_position[0] - self.active_anim.centre_offset[0])
        self.rect.centery = int(self.screen_position[1] - self.active_anim.centre_offset[1])

        if self.current_health <= 0:
            self.shutdown()

    def update_impact_reactions(self, hit_wall, impact_velocity, time_delta):
        if impact_velocity is not None:
            self.touching_ground = False
            # self.disable_movement = True
            self.velocity[0] = 0.0
            self.velocity[1] = 0.0
            self.impact_velocity = impact_velocity
            self.impact_timer = 0.0
        if not hit_wall and not self.touching_ground and self.impact_velocity is not None:
            self.velocity[0] += self.impact_velocity.x * time_delta
            self.velocity[1] += self.impact_velocity.y * time_delta
            if self.impact_timer < self.impact_time:
                self.impact_timer += time_delta
            else:
                self.impact_velocity[0] *= 0.8
                self.impact_velocity[1] *= 0.8
        if self.touching_ground and self.last_impact_direction_vec is not None:
            if not self.changed_direction_recently:
                self.turn_to_face_direction(self.last_impact_direction_vec)
            self.last_impact_direction_vec = None
            # self.disable_movement = False
            self.impact_velocity = None

    def debug_knockback(self, post_collision_move_x, pre_collision_move_x):
        if abs(self.world_position[0] - self.last_frame_x_pos) > 4.0:
            print("LARGE x MOVE:", abs(self.world_position[0] - self.last_frame_x_pos))
            print("self.velocity:", self.velocity)
            print("collision shape x move:", abs(self.collision_shape.x - self.last_collision_shape_x))
            print("pre_collision_move_world_pos_x:", pre_collision_move_x)
            print("post_collision_move_world_pos_x", post_collision_move_x)
            # print("mtv_vector:", mtv_vector)
            for shape in self.collision_shape.collided_shapes_this_frame:
                print("shape:", shape.x, shape.y)
            print("\n")
            print("self.start_frame_collision_shape_x", self.start_frame_collision_shape_x)
            print("self.pre_collision_gets_moved_x", self.pre_collision_gets_moved_x)
            print("self.post_collision_gets_moved_x", self.post_collision_gets_moved_x)

    def apply_knockback(self, shape):
        impact_velocity = pygame.math.Vector2(self.last_impact_direction_vec.x * 500.0,
                                              (self.last_impact_direction_vec.y * 300.0) - 1200.0)
        return impact_velocity

    def turn_to_face_direction(self, direction):
        if self.x_facing_direction == "right":
            facing_vec = [1.0, 0.0]
        else:
            facing_vec = [-1.0, 0.0]
        dot = facing_vec[0] * direction.x + facing_vec[1] * direction.y
        if dot > 0 and self.x_facing_direction == "right":
            self.x_facing_direction = "left"
            self.has_moved = True
        elif dot > 0 and self.x_facing_direction == "left":
            self.x_facing_direction = "right"
            self.has_moved = True

    def update_sprite(self, time_delta):
        if self.should_flash_sprite and not self.current_health <= 0:
            self.sprite_flash_acc += time_delta
            if self.sprite_flash_acc > self.sprite_flash_time:
                self.sprite_flash_acc = 0.0
                self.should_flash_sprite = False

            else:
                lerp_value = self.sprite_flash_acc / self.sprite_flash_time
                flash_alpha = self.lerp(255, 0, lerp_value)
                flash_image = self.active_anim.current_frame.copy()
                flash_sprite = self.active_anim.current_frame.copy()
                flash_image.fill((255, 255, 255), None, pygame.BLEND_RGB_ADD)
                flash_image.fill((255, 255, 255, flash_alpha), None, pygame.BLEND_RGBA_MULT)
                flash_sprite.blit(flash_image, (0, 0))
                self.image = flash_sprite

                if not self.active_flash_sprite:
                    self.active_flash_sprite = True
        else:
            self.image = self.active_anim.current_frame

    def take_damage(self, damage):
        self.current_health -= damage
        if self.current_health < 0:
            self.current_health = 0
        self.should_flash_sprite = True
        self.sprite_flash_acc = 0.0

    @staticmethod
    def lerp(a, b, c):
        return (c * b) + ((1.0 - c) * a)

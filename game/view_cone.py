import pygame
import random
import math
import functools
from pygame.math import Vector2

from collision.collision_handling import CollisionNoHandler
from collision.collision_shapes import CollisionRect, CollisionCircle, BaseCollisionShape, Edge
from collision.drawable_collision_shapes import DrawableCollisionRect, DrawableCollisionCircle
from game.collision_types import CollisionType
from collision.collision_funcs import collide_circle_with_rotated_rectangle


class AnglePointSet:
    def __init__(self):
        self.points = []
        self.epsilon = 0.075

    def add_aux(self, index, aux_point):
        self.points[index].append(aux_point)

    def add(self, new_point):
        already_have_point = False
        for point_group in self.points:
            point = point_group[0]
            if abs(new_point.x - point.x) < self.epsilon and abs(new_point.y - point.y) < self.epsilon:
                already_have_point = True
        if not already_have_point:
            self.points.append([new_point])
        return len(self.points) - 1


class ViewCone:
    class PointInConeStatus:
        FRONT_SEMICIRCLE = 0,  # point within sector - containing semicircle but outside sector
        BEHIND = 1,  # point behind sector
        OUTSIDE = 2,  # point outside bounding circle
        WITHIN = 4

    class LineSegConfig:
        DISJOINT = 0,
        PARALLEL = 1,
        INTERSECT = 2

    def __init__(self, origin_centre_pos, facing_direction, fov=90.0, length=1000.0):

        self.facing_direction = Vector2(facing_direction[:])
        self.origin_centre_position = Vector2(origin_centre_pos[:])

        self.field_of_view = math.radians(fov)
        self.length = length
        self.length_squared = length ** 2

        self.epsilon = 0.075  # to handle floating point inaccuracy at small values (I think)
        self.arc_epsilon = 1.5  # to handle small gaps between arc points
        self.halfAuxRayTilt = 8.72664625995e-3 # half degree in radians
        self.half_aux_ray_tilt_cos = math.cos(self.halfAuxRayTilt)  # 0.999961923064
        self.half_aux_ray_tilt_sin = math.sin(self.halfAuxRayTilt)  # 8.72653549837e-3

        self.collision_circle = CollisionCircle(self.origin_centre_position.x,
                                                self.origin_centre_position.y,
                                                self.length,
                                                {CollisionType.WORLD_SOLID: CollisionNoHandler(),
                                                 CollisionType.WORLD_JUMP_THROUGH: CollisionNoHandler(),
                                                 CollisionType.WORLD_PLATFORM_EDGE: CollisionNoHandler(),
                                                 CollisionType.WORLD_JUMP_THROUGH_EDGE: CollisionNoHandler()},
                                                CollisionType.VIEW_CONE,
                                                [CollisionType.WORLD_SOLID,
                                                 CollisionType.WORLD_JUMP_THROUGH,
                                                 CollisionType.WORLD_PLATFORM_EDGE,
                                                 CollisionType.WORLD_JUMP_THROUGH_EDGE]
                                                )

        self.neg_cos_fov = math.cos(-self.field_of_view / 2)
        self.neg_sin_fov = math.sin(-self.field_of_view / 2)
        self.sin_fov = math.sin(self.field_of_view / 2)
        self.cos_fov = math.cos(self.field_of_view / 2)
        self.perp_facing_cos = math.cos(math.radians(90))
        self.perp_facing_sin = math.sin(math.radians(90))

        self.angle_points_array = []
        self.rays = []
        self.hit_points = []
        self.ctrl_points = []
        self.blocking_edges = []

        self.perp_facing_vec = None
        self.cone_extent_facings = None
        self.on_cone_changed_direction()

        self.end_positions = None
        self.on_cone_moved()

        self.fov_edges = [Edge("min", Vector2(self.origin_centre_position), Vector2(self.end_positions[0])),
                          Edge("max", Vector2(self.origin_centre_position), Vector2(self.end_positions[1]))]

        self.timing_clock = pygame.time.Clock()

    def on_cone_changed_direction(self):
        self.cone_extent_facings = [Vector2(self.facing_direction.x * self.cos_fov - self.facing_direction.y * self.sin_fov,
                                     self.facing_direction.x * self.sin_fov + self.facing_direction.y * self.cos_fov),
                                    Vector2(self.facing_direction.x * self.neg_cos_fov - self.facing_direction.y * self.neg_sin_fov,
                                        self.facing_direction.x * self.neg_sin_fov + self.facing_direction.y * self.neg_cos_fov)
                                    ]

        self.perp_facing_vec = Vector2(
            self.facing_direction.x * self.perp_facing_cos - self.facing_direction.y * self.perp_facing_sin,
            self.facing_direction.x * self.perp_facing_sin + self.facing_direction.y * self.perp_facing_cos)

    def on_cone_moved(self):
        self.end_positions = [[self.origin_centre_position.x + self.cone_extent_facings[0].x * self.length,
                               self.origin_centre_position.y + self.cone_extent_facings[0].y * self.length],
                              [self.origin_centre_position.x + self.cone_extent_facings[1].x * self.length,
                               self.origin_centre_position.y + self.cone_extent_facings[1].y * self.length]
                              ]

        self.fov_edges = [Edge("min", Vector2(self.origin_centre_position), Vector2(self.end_positions[0])),
                          Edge("max", Vector2(self.origin_centre_position), Vector2(self.end_positions[1]))]

    def set_facing_direction(self, direction):
        if direction[0] != self.facing_direction.x or direction.y != self.facing_direction.y:
            self.facing_direction.x = direction.x
            self.facing_direction.y = direction.y
            self.on_cone_changed_direction()
            self.on_cone_moved()

    def set_position(self, position):
        if position[0] != self.origin_centre_position.x or position.y != self.origin_centre_position.y:
            self.origin_centre_position.x = position.x
            self.origin_centre_position.y = position.y
            self.on_cone_moved()
            self.collision_circle.set_position((self.origin_centre_position.x, self.origin_centre_position.y))

    def is_point_in_sector(self, point_to_test):
        """
        Tests if a point is inside our cone and, if not roughly where it is in relation to our circle for future
        processing.

        :param point_to_test:
        :return: status class variable
        """
        vector_to_point = point_to_test - self.origin_centre_position

        dot = self.facing_direction.dot(vector_to_point)
        if dot < 0:
            return ViewCone.PointInConeStatus.BEHIND

        if (vector_to_point.length_squared() - self.length_squared) > self.epsilon:
            return ViewCone.PointInConeStatus.OUTSIDE

        self.cone_extent_facings[0].cross(vector_to_point)
        cross_1 = self.cone_extent_facings[0].cross(vector_to_point)  # self.cone_extent_facings[0][0] * min_vector_to_point[1] - self.cone_extent_facings[0][1] * min_vector_to_point[0]
        cross_2 = self.cone_extent_facings[1].cross(vector_to_point)  # self.cone_extent_facings[1][0] * max_vector_to_point[1] - self.cone_extent_facings[1][1] * max_vector_to_point[0]

        if cross_1 < 0 < cross_2 or cross_1 > 0 > cross_2:
            return ViewCone.PointInConeStatus.WITHIN

        return ViewCone.PointInConeStatus.FRONT_SEMICIRCLE

    def draw(self, surface, camera=None):
        if camera is not None:
            view_top_left_position = (camera.position[0] - (camera.dimensions[0] / 2),
                                      camera.position[1] - (camera.dimensions[1] / 2))
        else:
            view_top_left_position = [0.0, 0.0]

        arc_rect = pygame.Rect((0, 0), (self.length * 2,
                                        self.length * 2))
        arc_rect.center = [self.origin_centre_position[0] - view_top_left_position[0],
                           self.origin_centre_position[1] - view_top_left_position[1]]
        arc_angle = math.atan2(-self.facing_direction[1], self.facing_direction[0])
        #pygame.draw.arc(surface, pygame.Color("#FFFFFF"), arc_rect, arc_angle, arc_angle + (self.field_of_view / 2))
        #pygame.draw.arc(surface, pygame.Color("#FFFFFF"), arc_rect, arc_angle - (self.field_of_view / 2), arc_angle)

        view_top_left_vec = pygame.math.Vector2(view_top_left_position)
        #pygame.draw.line(surface, pygame.Color("#FFFFFF"), self.origin_centre_position - view_top_left_vec,
        #                 self.origin_centre_position + (self.facing_direction * self.length) - view_top_left_vec)

        #for ray in self.rays:
        #    pygame.draw.line(surface, pygame.Color("#999999"), self.origin_centre_position - view_top_left_vec, self.origin_centre_position + ray - view_top_left_vec)

        for j in range(0, len(self.hit_points)):
            hit_point = self.hit_points[j]
            pygame.draw.circle(surface, pygame.Color("#FF7700"), [int(hit_point.x - view_top_left_position[0]),
                                                                  int(hit_point.y - view_top_left_position[1])], 5)

        # draw los cone shape
        if len(self.hit_points) > 0:
            pygame.draw.line(surface, pygame.Color("#FFFF00"), self.origin_centre_position - view_top_left_vec, self.hit_points[0] - view_top_left_vec)

        for i in range(0, len(self.hit_points) - 1):
            if self.ctrl_points[i+1] is None:
                pygame.draw.line(surface, pygame.Color("#FFFF00"), self.hit_points[i] - view_top_left_vec, self.hit_points[i+1] - view_top_left_vec)
            else:
                start_angle_vec = self.hit_points[i] - self.origin_centre_position
                finish_angle_vec = self.hit_points[i+1] - self.origin_centre_position
                start_arc_angle = math.atan2(-start_angle_vec[1], start_angle_vec[0])
                finish_arc_angle = math.atan2(-finish_angle_vec[1], finish_angle_vec[0])

                x_diff = abs(start_angle_vec.x - finish_angle_vec.x)
                y_diff = abs(start_angle_vec.y - finish_angle_vec.y)
                if not (x_diff <= self.arc_epsilon and y_diff <= self.arc_epsilon):
                    pygame.draw.arc(surface, pygame.Color("#FFFF00"), arc_rect, start_arc_angle, finish_arc_angle)
                # else:
                # pygame.draw.arc(surface, pygame.Color("#FFFF00"), arc_rect, finish_arc_angle, start_arc_angle)

        if len(self.hit_points) > 0:
            pygame.draw.line(surface, pygame.Color("#FFFF00"), self.hit_points[len(self.hit_points)-1] - view_top_left_vec, self.origin_centre_position - view_top_left_vec)
        # end draw los cone shape

    def edge_within_radius(self, edge):
        return self.closest_point_on_edge(edge).distance_squared_to(self.origin_centre_position) <= self.length_squared

    def is_active_facing_edge(self, polygon, edge):
        edge_normal = polygon.normals[edge.name]
        if edge_normal.should_skip:
            return False
        return True

    def check_polygon(self, polygon, angle_points, blocking_edges):
        edges_list = [edge for edge in polygon.edges.values()
                      if self.edge_within_radius(edge) and self.is_active_facing_edge(polygon, edge)]
        n = len(edges_list)
        if n > 0:
            prev_edge = edges_list[n - 1]  # TODO: this might be wrong?
        else:
            prev_edge = None
        for i in range(0, len(edges_list)):
            edge = edges_list[i]

            point_a_status = self.is_point_in_sector(edge.a)
            point_b_status = self.is_point_in_sector(edge.b)
            if point_a_status == ViewCone.PointInConeStatus.BEHIND and point_b_status == ViewCone.PointInConeStatus.BEHIND:
                continue

            if point_a_status == ViewCone.PointInConeStatus.WITHIN and point_b_status == ViewCone.PointInConeStatus.WITHIN:

                self.add_angle_point_with_aux(edge.a, prev_edge, edge, angle_points)

                # for the last edge, send undefined as nextEdge to
                # addAnglePointWithAux; it should never get used since
                # both endpoints of the last edge would be handled by now
                # due to edges 0 and n − 2
                if i < len(edges_list) - 1:
                    self.add_angle_point_with_aux(edge.b, edge, edges_list[i + 1], angle_points)
                else:
                    self.add_angle_point_with_aux(edge.b, edge, None, angle_points)
                blocking_edges.append(edge)

            else:
                """
                ANGLE POINTS
                Either one or both the points are outside the sector; add
                the one which is inside. Perform edge – arc intersection
                test, if this edge has a possibility of intersecting the
                arc, add resultant intersection point(s) to angle_points.

                BLOCKING EDGE
                If one of the points is inside, then the edge is blocking,
                add it without any checks. If one or both are out, and the
                edge cuts the sector's arc then too the edge is blocking,
                add it to blocking_edges. If both are out and edge doesn't
                cut the arc, check if it cuts one of the sector's edges and
                add to blocking_edges if it does.
                """
                blocking = False
                if point_a_status == ViewCone.PointInConeStatus.WITHIN:
                    self.add_angle_point_with_aux(edge.a, prev_edge, edge, angle_points)
                    blocking = True
                if point_b_status == ViewCone.PointInConeStatus.WITHIN:
                    if i < len(edges_list) - 1:
                        self.add_angle_point_with_aux(edge.b, edge, edges_list[i+1], angle_points)
                    else:
                        self.add_angle_point_with_aux(edge.b, edge, None, angle_points)
                    blocking = True

                edge_may_intersect_arc = point_a_status == ViewCone.PointInConeStatus.OUTSIDE or point_b_status == ViewCone.PointInConeStatus.OUTSIDE

                test_seg_seg_xsect = True
                if edge_may_intersect_arc:
                    # perform line segment – sector arc intersection test to
                    # check if there're more angle points i.e. if the edge
                    # intersects the sector's arc then the intersection points
                    # would also become angle points.
                    arc_xsect_result = self.line_seg_arc_x_sect(edge)
                    if arc_xsect_result is not None:
                        if arc_xsect_result['config'] == ViewCone.PointInConeStatus.WITHIN:
                            # just add intersection point to Set without any
                            # auxiliarys as it's an intersection angle point
                            for point in arc_xsect_result['points']:
                                angle_points.add(point)
                            blocking = True

                        # edge – edge intersection test is not needed when the
                        # intersection point(s) are within or behind; the
                        # within case is ignored since it's already blocking
                        # and hence won't reach the lineSegLineSegXsect code
                        test_seg_seg_xsect = arc_xsect_result['config'] != ViewCone.PointInConeStatus.BEHIND

                # If there was an angle point added due to this edge, then it
                # is blocking; add and continue to avoid further processing.
                if blocking:
                    blocking_edges.append(edge)
                elif test_seg_seg_xsect and \
                        any([fov_edge for fov_edge in self.fov_edges
                             if self.edges_intersect(fov_edge, edge)]):
                    blocking_edges.append(edge)

                    """
                    If any angle point(s) would occur because of this edge, they
                    would have been found by now and the edge would have been
                    tagged as a blocking one. Even if no angle points were found
                    due to this edge it still may be a blocking, or not. Perform
                    a couple of segment – segment intersection tests with the
                    sector's edges to check if the edge is indeed blocking. This
                    is worth the expenditure incurred; say we have 10 angle
                    points, for every redundant, non-blocking edge added without
                    such a check means we waste time in performing 10 futile
                    line segment intersection tests. Prune them early on by
                    performing the tests beforehand.
    
                    Perform segment – segment testing if testSegSegXsect is
                    true; this will be so if the arc intersection was never
                    performed (say when both points are in FrontSemicircle and
                    their edge occluding vision) or if the intersection points
                    aren't behind the sector; there can be cases where not both
                    points are behind (if so they'd have gotten pruned by now),
                    but the intersection points are behind, prune them.
                    """

            prev_edge = edge

    def is_zero(self, vec):
        return (abs(vec.x) + abs(vec.y)) <= self.epsilon

    def are_parallel(self, vec_a, vec_b):
        return abs(vec_a.cross(vec_b)) <= self.epsilon

    def is_point_on_line(self, pt_vec, line):
        v = pt_vec - line.a
        return self.are_parallel(v, line.vec)

    @staticmethod
    def rotate_dir(direction, cos_a, sin_a):
        """ rotates dir based on cosA and sinA both counter-clockwise and clockwise
            doing it manually instead of using mat2d as these can be reused for
            rotation in both directions, avoiding their recalculation"""
        x_c = direction.x * cos_a
        y_c = direction.y * cos_a
        x_s = direction.x * sin_a
        y_s = direction.y * sin_a
        return [Vector2(x_c - y_s, x_s + y_c), Vector2(x_c + y_s, -x_s + y_c)]

    @staticmethod
    def point_on_line(line, t):
        return line.a + (line.b - line.a) * t

    @staticmethod
    def perp2d(v, clockwise=False):
        if clockwise:
            return Vector2(v.y, -v.x)
        return Vector2(-v.y, v.x)

    @staticmethod
    def inv_lerp(line, point):
        t = point - line.a
        return t.dot(line.vec) / line.length_squared

    def edges_intersect(self, edge_a, edge_b):
        """
        Simple wrapper function to turn complicated intersection of line segment test into a boolean True or False
        result.

        :param edge_a: first edge to test
        :param edge_b: second edge to test
        :return: True or False if the two segments intersect or not
        """
        return ViewCone.LineSegConfig.INTERSECT == self.line_seg_line_seg_x_sect(edge_a, edge_b)['config']

    def line_seg_line_seg_x_sect(self, line_1, line_2, should_compute_point=False, is_line_1_ray=False):
        """
        converted from here:
        https://github.com/legends2k/2d-fov/blob/gh-pages/index.html

        originally from §16.16.1, Real-Time Rendering, 3rd Edition with Antonio's optimisation.
        Code gets around eh?

        The intent of this function is to determine if two line segments intersect, it also provides additional
        information (on request) giving the point of intersection (if any) and if the non-intersecting lines are
        parallel or entirely disjoint.

        :param line_1: The first line segment to test
        :param line_2: The second line segment to test
        :param should_compute_point: Should we compute the point of intersection or not
        :param is_line_1_ray: Is line 1 a 'ray' which I believe in this context is asking if it is a view cone ray
        :return:
        """
        result = {'config': ViewCone.LineSegConfig.DISJOINT, 't': None, 'point': None}
        line_1_vec = line_1.b - line_1.a
        line_2_vec = line_2.b - line_2.a
        l1p = self.perp2d(line_1_vec)
        f = line_2_vec.dot(l1p)
        if abs(f) <= self.epsilon:
            result['config'] = ViewCone.LineSegConfig.PARALLEL
            # if line1 is a ray and an intersection point is needed, then filter
            # cases where line and ray are parallel, but the line isn't part of
            # ray e.g. ---> ____ should be filterd, but ---> ----- should not be.
            if is_line_1_ray and should_compute_point and self.is_point_on_line(line_2.a, line_1):
                # find the ray origin position with regards to the line segment
                alpha = self.inv_lerp(line_2, line_1.a)
                if 0 <= alpha <= 1:
                    result['t'] = 0
                    result['point'] = Vector2(line_1.a)
                elif alpha < 0:
                    result['point'] = Vector2(line_2.a)
                    result['t'] = self.inv_lerp(line_1, result['point'])
        else:
            c = line_1.a - line_2.a
            e = c.dot(l1p)
            #  t = e ÷ f, but computing t isn't necessary, just checking the values
            # of e and f we deduce if t ∈ [0, 1], if not the division and further
            # calculations are avoided: Antonio's optimisation.
            # f should never be zero here which means they're parallel
            if (f > 0 and 0 <= e <= f) or (f < 0 and 0 >= e >= f):
                l2p = self.perp2d(line_2_vec)
                d = c.dot(l2p)
                # if line 1 is a ray, checks relevant to restricting s to 1
                # isn't needed, just check if it wouldn't become < 0
                if (is_line_1_ray and ((f > 0 and d >= 0) or (f < 0 and d <= 0))) or (
                        (f > 0 and 0 <= d <= f) or (f < 0 and 0 >= d >= f)):
                    result['config'] = ViewCone.LineSegConfig.INTERSECT
                    if should_compute_point:
                        s = d / f
                        result['t'] = s
                        result['point'] = self.point_on_line(line_1, s)

        return result

    def line_seg_arc_x_sect(self, line):
        """
        Checks for intersection between a line and the 'arc' of a view cone/sector. Should be a fairly rarely used test
        as blocking edges have to be in a  very specific place to intersect the cone at this point.

        :param line: the line to test against the view cone's sector for intersection
        :return: None if no intersection at all, or {'config': ViewCone.PointInConeStatus.BEHIND} if both points of line
                 are behind the sector/cone. If there is an intersection returns a dictionary like so -
                 {'config': ViewCone.PointInConeStatus.WITHIN, 'points': points}
        """
        delta = line.a - self.origin_centre_position
        b = line.vec.dot(delta)
        d_2 = line.length_squared
        c = delta.length_squared() - self.length_squared
        det = (b * b) - (d_2 * c)
        if det > 0:
            det_sqrt = math.sqrt(det)
            if b >= 0:
                t = b + det_sqrt
                t1 = -t / d_2
                t2 = -c / t
            else:
                t = det_sqrt - b
                t1 = c / t
                t2 = t / d_2

            p1 = None
            p2 = None
            points = []
            p1_in_sector = None
            p2_in_sector = None
            if 0 <= t1 <= 1:
                p1 = self.point_on_line(line, t1)
                p1_in_sector = self.is_point_in_sector(p1)
                if p1_in_sector == ViewCone.PointInConeStatus.WITHIN:
                    points.append(p1)
            if 0 <= t2 <= 1:
                p2 = self.point_on_line(line, t2)
                p2_in_sector = self.is_point_in_sector(p2)
                if p2_in_sector == ViewCone.PointInConeStatus.WITHIN:
                    points.append(p2)

            # line segment is contained within circle; it may be cutting
            # the sector, but not the arc, so return false, as there're
            # no angle points
            if p1 is None and p2 is None:
                return None

            # both intersection points are behind, the edge has no way of cutting
            # the sector
            if p1_in_sector == ViewCone.PointInConeStatus.BEHIND and p2_in_sector == ViewCone.PointInConeStatus.BEHIND:
                return {'config': ViewCone.PointInConeStatus.BEHIND}

            if len(points) > 0:
                return {'config': ViewCone.PointInConeStatus.WITHIN, 'points': points}

        return None

    def add_angle_point_with_aux(self, point, prev_edge, next_edge, angle_points):
        """
        /*
          * Auxiliary rays (primary ray rotated both counter-clockwise and clockwise by
          * an iota angle). These are needed for cases where a primary ray would get hit
          * an edge's vertex and get past it to hit things behind it too.
          *
          *   ALLOW PENETRATION             DISALLOW PENETRATION
          *
          *  ----------X                        \  polygon  /
          *  polygon  / \  <- ray                X---------X
          *          /   \                                  \  <- ray
          *                                                  \
          * References:
          * 1: http://ncase.me/sight-and-light
          * 2: http://www.redblobgames.com/articles/visibility
          */
        :param angle_points:
        :param next_edge:
        :param prev_edge:
        :param point: the point to add
        :return:
        """
        current_size = len(angle_points.points)

        point_index = angle_points.add(point)
        # Add aux points only if the addition of the primary point was successful.
        # When a corner vertex of a polygon is added twice for edges A and B,
        # although the primary point would not be added since constructEdges would
        # have used the same vec2 object to make the end points of both edges,
        # this isn't case for the auxiliary points created in this function afresh
        # on each call. This check avoids redundant auxiliary point addition.
        if current_size != len(angle_points.points):
            ray = point - self.origin_centre_position
            auxiliaries = self.rotate_dir(ray, self.half_aux_ray_tilt_cos, self.half_aux_ray_tilt_sin)

            auxiliaries[0] += self.origin_centre_position
            auxiliaries[1] += self.origin_centre_position
            proj_axis = self.perp2d(ray)
            if (next_edge is None) or (next_edge == prev_edge):
                # line_vec should originate from the added endpoint going to the
                # other end; if added point is second in edge, flip edge's vector
                if point == prev_edge.a:
                    line_vec = prev_edge.b - prev_edge.a
                else:
                    prev_edge_vec = prev_edge.b - prev_edge.a
                    line_vec = Vector2(-prev_edge_vec.x, -prev_edge_vec.y)

                p = line_vec.dot(proj_axis)
                #  if line_vec is in −ve halfspace of proj_axis, add the auxiliary
                #  ray that would be in the +ve halfspace (i.e. the auxiliary ray
                #  due to rotating ray counter-clockwise by iota) and vice-versa
                if p <= 0:
                    angle_points.add_aux(point_index, auxiliaries[0])
                # use if instead of else if to deal with the case where ray and
                # edge are parallel, in which case both auxiliary rays are needed
                if p >= 0:
                    angle_points.add_aux(point_index, auxiliaries[1])
            else:
                # refer to vision_beyond.html workout to understand in which
                # situation vision can extend beyond corners and auxiliary rays
                #  are needed (we'll take that on trust since I'm not including that file)
                prev_edge_vec = prev_edge.b - prev_edge.a
                next_edge_vec = next_edge.b - next_edge.a
                p1 = prev_edge_vec.dot(proj_axis)
                p2 = next_edge_vec.dot(proj_axis)
                if (p1 >= 0) and (p2 <= 0):
                    angle_points.add_aux(point_index, auxiliaries[0])
                elif (p1 <= 0) and (p2 >= 0):
                    angle_points.add_aux(point_index, auxiliaries[1])

    def make_rays(self, angle_points):
        ray = angle_points[0] - self.origin_centre_position
        rays = [ray]
        # i for angle_points, j for rays to avoid doing len(angle_points) - 1
        j = 0
        for i in range(1, len(angle_points)):
            ray = angle_points[i] - self.origin_centre_position
            if not self.are_parallel(ray, rays[j]):
                rays.append(ray)
                j += 1
        return rays

    def angular_points_sorter(self, a, b):
        a_v = a[0] - self.origin_centre_position
        b_v = b[0] - self.origin_centre_position
        # sort expects a negative value when a should come before b; since
        # cross2d gives a negative value when the rotation from a to b is
        # counter-clockwise we use it as-is; see comment in isPointInSector
        return a_v.cross(b_v)

    def aux_angular_points_sorter(self, a, b):
        a_v = a - self.origin_centre_position
        b_v = b - self.origin_centre_position
        # sort expects a negative value when a should come before b; since
        # cross2d gives a negative value when the rotation from a to b is
        # counter-clockwise we use it as-is; see comment in isPointInSector
        return a_v.cross(b_v)

    def sort_angular_points(self, angle_points, blocking_edges):
        # need to determine if two co-planar edges share a point so we can strip it
        points_to_remove = []
        for edge in blocking_edges:
            for other_edge in blocking_edges:
                if edge != other_edge:
                    if 1.0 - abs(edge.vec.dot(other_edge.vec)) <= self.epsilon:
                        # edges are co_planar, do they share a point?
                        shared_point = None
                        if abs(edge.a.x - other_edge.a.x) <= self.epsilon and abs(edge.a.y - other_edge.a.y) <= self.epsilon:
                            shared_point = edge.a
                        elif abs(edge.a.x - other_edge.b.x) <= self.epsilon and abs(edge.a.y - other_edge.b.y) <= self.epsilon:
                            shared_point = edge.a
                        elif abs(edge.b.x - other_edge.a.x) <= self.epsilon and abs(edge.b.y - other_edge.a.y) <= self.epsilon:
                            shared_point = edge.b
                        elif abs(edge.b.x - other_edge.b.x) <= self.epsilon and abs(edge.b.y - other_edge.b.y) <= self.epsilon:
                            shared_point = edge.b
                        if shared_point is not None:
                            points_to_remove.append(shared_point)
        angle_points.points = [angle_points.points[i] for i in range(0, len(angle_points.points)) if
                               angle_points.points[i][0] not in points_to_remove]
        angle_points.points.sort(key=functools.cmp_to_key(self.angular_points_sorter))

        final_angle_points = []
        for point_group in angle_points.points:
            point_group.sort(key=functools.cmp_to_key(self.aux_angular_points_sorter))
            for point in point_group:
                final_angle_points.append(point)
        return final_angle_points

    @staticmethod
    def calc_quad_bez_curve_ctrl_point(v1, v2, centre, radius):
        ctrl_point = v1 + v2
        ctrl_point.normalize_ip()
        scale = radius * (2 - v1.dot(ctrl_point))
        ctrl_point = centre + (ctrl_point * scale)
        return ctrl_point

    def shoot_rays(self, rays, blocking_edges):
        line_1_is_ray = True
        should_compute_point = True
        n = len(rays)
        hit_points = [None for _ in range(0, n)]
        ctrl_points = [None for _ in range(0, n)]
        # rays is an array of vectors only, however the intersection functions
        # work on edges i.e. it also needs the end points and square length; hence
        # this_ray would act as the ray with additional edge data
        prev_point_on_arc = False
        prev_unit_ray = Vector2()
        for i in range(0, n):
            #  set edge data on this_ray specific to the ray currently shot
            this_ray = Edge("ray", self.origin_centre_position, self.origin_centre_position + rays[i])
            hit_point = Vector2()
            t = None
            blocker = None
            hit_dist_2 = None
            for j in range(0, len(blocking_edges)):
                res = self.line_seg_line_seg_x_sect(this_ray, blocking_edges[j], should_compute_point, line_1_is_ray)
                # both parallel and intersecting cases are valid for inspection;
                # both have the parameter and point defined
                if (res['t'] is not None) and ((t is None) or (res['t'] < t)):
                    # This is needed when the observer is exactly at a polygon's
                    # vertex, from where both worlds (outside and inside the
                    # polygon/building) are visible as the observer is standing at
                    # a pillar point where two walls meet. In such case, all rays
                    # emanating from the centre would hit one of these edges with
                    # t = 0 but this point should be discounted from calculations.
                    # However, the value of t can vary depending on the length of
                    # the ray, hence using the distance between the points as a
                    # better measure of proximity
                    hit_dist_2 = res['point'].distance_squared_to(self.origin_centre_position)
                    if hit_dist_2 > self.epsilon:
                        t = res['t']
                        hit_point = Vector2(res['point'])
                        blocker = blocking_edges[j]
            """
            the ray could've hit
            
              i. nothing (no blocking edge was in its way; t is None)
             ii. blocking edge(s) of which the closest intersecting point is
                 a. within the sector
                 b. on the sector's arc
                 c. beyond the sector's arc
            
            For (ii.c) t may be defined but the point would be beyond the
            sector's radius. For everything except (ii.a), the hit point would
            be on the arc and the unit vector along the ray would be needed to
            draw the Bézier curve, if the next point is also going to be on the
            arc. For cases (i) and (ii.c), a new hit point needs to be
            calculated too, which can use the unit vector.
            
            One can avoid sqrt and call atan2 to get the angle directly which
            would also help in drawing the actual arc (using ctx.arc) and not an
            approximation of the arc using ctx.quadraticCurveTo. However, sqrt
            is chosen over atan2 since it's usually faster:
            http://stackoverflow.com/a/9318108.
            """
            point_on_arc = (t is None) or ((hit_dist_2 + self.epsilon - self.length_squared) >= 0)
            if point_on_arc:
                unit_ray = rays[i].normalize()
                # for cases (i), (ii.b) and (ii.c) set the hit point; this would
                # be redundant for case (ii.b) but checking for it would be
                # cumbersome, so just reassign
                hit_point = self.origin_centre_position + (unit_ray * self.length)
                if prev_point_on_arc:
                    needs_arc = True
                    """
                    the case where part of the arc is cut by a blocking edge
                    needs to be handled differently:
                    
                                         /---  +----------+
                                     /---    \-|          |
                                 /---          X          |
                              /--              |\         |
                          /---                 | \        |
                         o                     |  |       |
                          ---\                 | /        |
                              --\              |/         |
                                 ---\          X          |
                                     ---\    /-|          |
                                         ----  +----------+
                    
                    although both hit points would be on the arc, they shouldn't
                    be connected by an arc since the blocking edge wouldn't
                    allow vision beyond; hence check if this ray hit a blocking
                    edge, if yes, then check if it's parallel to the edge formed
                    by the connection between this and the previous hit points,
                    if so don't make an arc.
                    
                    the check i > 0 isn't needed since if that was the case the
                    variable prevPointOnArc would be false and the control
                    would've not reached here, so doing i - 1 is safe here
                    """
                    if blocker:
                        connector = hit_points[i - 1] - hit_point
                        needs_arc = not self.are_parallel(blocker.b - blocker.a, connector)
                    if needs_arc:
                        ctrl_points[i] = self.calc_quad_bez_curve_ctrl_point(unit_ray, prev_unit_ray,
                                                                             self.origin_centre_position,
                                                                             self.length)

                prev_unit_ray = Vector2(unit_ray)

            prev_point_on_arc = point_on_arc
            hit_points[i] = hit_point

        return {'hit_points': hit_points, 'ctrl_points': ctrl_points}

    def los_blocked_test(self, ray, edge):
        res = self.line_seg_line_seg_x_sect(ray, edge, True)
        if ViewCone.LineSegConfig.INTERSECT == res['config']:
            return res['point'].distance_squared_to(self.origin_centre_position) > self.epsilon

    def is_subject_visible(self, target):
        if self.is_point_in_sector(target) == ViewCone.PointInConeStatus.WITHIN:
            ray = Edge("ray", self.origin_centre_position, target)
            return not any([True for edge in self.blocking_edges if self.los_blocked_test(ray, edge)])
        return False

    def update(self):
        """
        Based on method established here:
        https://legends2k.github.io/2d-fov/design.html

        :return:
        """
        #tick_1 = self.timing_clock.tick()
        # each loop we first grab the edges that are attached to world objects in our cone length/radius
        # then we cull down only to the edges whose closest point is in our radius
        if len(self.collision_circle.collided_shapes_this_frame) != 0:
            blocking_edges = []
            angle_points = AnglePointSet()

            for shape in self.collision_circle.collided_shapes_this_frame:
                if shape.type == BaseCollisionShape.RECT:
                    self.check_polygon(shape, angle_points, blocking_edges)

            sorted_angle_points = self.sort_angular_points(angle_points, blocking_edges)

            angle_points_array = [Vector2(self.end_positions[0])]
            angle_points_array.extend(sorted_angle_points)
            angle_points_array.append(Vector2(self.end_positions[1]))

            rays = self.make_rays(angle_points_array)
            result = self.shoot_rays(rays, blocking_edges)

            self.angle_points_array = angle_points_array
            self.rays = rays
            self.hit_points = result['hit_points']
            self.ctrl_points = result['ctrl_points']
            self.blocking_edges = blocking_edges

        #tick_2 = self.timing_clock.tick()

        #if tick_2 > 7:
        #   print("view_cone_timing:", tick_2, "ms")

    def clear(self):
        self.angle_points_array = []
        self.rays = []
        self.hit_points = []
        self.ctrl_points = []
        self.blocking_edges = []

    def closest_point_on_edge(self, edge):
        """
        Calculate closest point on a line segment to another point, in this case our cone's origin.

        Gathered from explanation here:
        http://doswa.com/2009/07/13/circle-segment-intersectioncollision.html
        :param edge: a line segment or an 'edge' in this case of a polygon or rectangle
        :return: the closest point on the segment to the origin point of our view cone
        """
        seg_v = edge.vec
        pt_v = self.origin_centre_position - edge.a
        seg_length_squared = edge.length_squared

        if seg_length_squared <= 0:
            raise ValueError("Segment length is less than or equal to zero")

        if seg_length_squared != 1:
            seg_len = math.sqrt(seg_length_squared)
            seg_v_unit = seg_v / seg_len
        else:
            seg_len = 1
            seg_v_unit = seg_v

        proj = pt_v.dot(seg_v_unit)
        if proj <= 0:
            return Vector2(edge.a)
        if proj >= seg_len:
            return Vector2(edge.b)

        return (seg_v_unit * proj) + edge.a


def test_cone():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))

    background = pygame.Surface((800, 600))
    background.fill(pygame.Color("#000000"))

    running = True
    view_cone = ViewCone([400, 300], [1.0, 0.0], fov=60, length=200)

    test_rect = CollisionRect(pygame.Rect((310, 400), (30, 30)), 0,
                              {CollisionType.VIEW_CONE: CollisionNoHandler()},
                              CollisionType.WORLD_SOLID,
                              [CollisionType.VIEW_CONE]
                              )
    drawable_test_rect = DrawableCollisionRect(test_rect)

    test_rect_2 = CollisionRect(pygame.Rect((340, 400), (30, 30)), 0,
                               {CollisionType.VIEW_CONE: CollisionNoHandler()},
                               CollisionType.WORLD_SOLID,
                               [CollisionType.VIEW_CONE]
                               )
    drawable_test_rect_2 = DrawableCollisionRect(test_rect_2)

    drawable_test_circle = DrawableCollisionCircle(view_cone.collision_circle)

    test_rect.normals["right"].should_skip = True
    test_rect_2.normals["left"].should_skip = True

    test_points = []
    for _ in range(0, 1000):
        test_points.append(pygame.math.Vector2(float(random.randint(10, 790)),
                                               float(random.randint(10, 590))))

    clock = pygame.time.Clock()
    while running:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mouse_pos = pygame.mouse.get_pos()
                    vec_to_mouse = [mouse_pos[0] - view_cone.origin_centre_position[0],
                                    mouse_pos[1] - view_cone.origin_centre_position[1]]
                    length = math.sqrt(vec_to_mouse[0] ** 2 + vec_to_mouse[1] ** 2)
                    if length > 0.0:
                        vec_to_mouse_norm = Vector2(vec_to_mouse[0] / length, vec_to_mouse[1] / length)

                        view_cone.set_facing_direction(vec_to_mouse_norm)

                if event.button == 3:
                    view_cone.set_position(Vector2(pygame.mouse.get_pos()))

        screen.blit(background, (0, 0))

        view_cone.update()

        for point in test_points:
            if view_cone.is_subject_visible(point):
                pygame.draw.line(screen, pygame.Color("#0000FF"), point, [point.x + 1, point.y + 1], 2)
            else:
                pygame.draw.line(screen, pygame.Color("#FF0000"), point, [point.x + 1, point.y + 1], 2)

        if collide_circle_with_rotated_rectangle(view_cone.collision_circle, test_rect):
            test_rect.add_frame_collided_shape(view_cone.collision_circle)
            view_cone.collision_circle.add_frame_collided_shape(test_rect)
        else:
            test_rect.clear_frame_collided_shapes()
            view_cone.collision_circle.clear_frame_collided_shapes()

        if collide_circle_with_rotated_rectangle(view_cone.collision_circle, test_rect_2):
            test_rect_2.add_frame_collided_shape(view_cone.collision_circle)
            view_cone.collision_circle.add_frame_collided_shape(test_rect_2)
        else:
            test_rect_2.clear_frame_collided_shapes()
            view_cone.collision_circle.clear_frame_collided_shapes()

        drawable_test_rect.update_collided_colours()
        drawable_test_rect_2.update_collided_colours()
        drawable_test_circle.update_collided_colours()
        drawable_test_rect.draw(screen)
        drawable_test_rect_2.draw(screen)
        # drawable_test_circle.draw(screen)
        view_cone.draw(screen)
        pygame.display.flip()


def test_line_seg_intersection():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))

    background = pygame.Surface((800, 600))
    background.fill(pygame.Color("#000000"))

    running = True
    view_cone = ViewCone([400, 300], [1.0, 0.0], fov=60, length=200)

    line_1 = Edge("line_1", Vector2(400.0, 200.0), Vector2(400.0, 400.0), 200.0)
    line_2 = Edge("line_1", Vector2(300.0, 300.0), Vector2(500.0, 300.0), 200.0)

    clock = pygame.time.Clock()
    while running:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mouse_pos = pygame.mouse.get_pos()
                    vec_to_mouse = [mouse_pos[0] - view_cone.origin_centre_position[0],
                                    mouse_pos[1] - view_cone.origin_centre_position[1]]
                    length = math.sqrt(vec_to_mouse[0] ** 2 + vec_to_mouse[1] ** 2)
                    if length > 0.0:
                        vec_to_mouse_norm = [vec_to_mouse[0] / length, vec_to_mouse[1] / length]

                        view_cone.set_facing_direction(vec_to_mouse_norm)

                if event.button == 3:
                    view_cone.set_position(pygame.mouse.get_pos())

        result = view_cone.line_seg_line_seg_x_sect(line_1, line_2, True)
        print(result['point'])

        screen.blit(background, (0, 0))

        pygame.draw.line(screen, pygame.Color("#FFFFFF"), line_1.a, line_1.b, 1)
        pygame.draw.line(screen, pygame.Color("#FFFFFF"), line_2.a, line_2.b, 1)

        pygame.display.flip()


if __name__ == "__main__":
    test_cone()



class CollisionType:
    """
    Types of collidable stuff in the game world. A way of identifying what sort of thing we just bumped into
    when colliding without getting too much more specific than that.
    """
    WORLD_SOLID = 0,
    WORLD_JUMP_THROUGH = 1,
    WORLD_PLATFORM_EDGE = 2,
    WORLD_JUMP_THROUGH_EDGE = 3,
    LADDERS = 4,
    PLAYER = 5,
    PLAYER_LADDER = 6,
    PLAYER_ATTACKS = 7,
    PLAYER_PROJECTILES = 8,
    AI = 9,
    AI_PROJECTILES = 10,
    AI_ATTACKS = 11,
    VIEW_CONE = 12,
    DOOR = 13,
    WATER = 14

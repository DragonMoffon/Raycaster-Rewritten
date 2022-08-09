import arcade
from math import pi, cos, sin

# Written by DragonMoffon.
# This is an implementation of the c++ code for a ray-caster found here: https://lodev.org/cgtutor/raycasting.html
# I take no credit for the maths or logic used in this implementation.


# The map has the y first and then the x, this makes the top left corner (0, 0).
MAP = (
    (1, 1, 1, 1, 1, 1, 1, 1, 1, 1),
    (1, 0, 0, 1, 0, 0, 0, 0, 0, 1),
    (1, 0, 1, 1, 0, 0, 0, 0, 0, 1),
    (1, 0, 0, 0, 0, 0, 0, 0, 0, 1),
    (1, 0, 0, 0, 0, 0, 0, 0, 0, 1),
    (1, 0, 0, 0, 0, 0, 0, 0, 0, 1),
    (1, 0, 0, 0, 0, 0, 0, 0, 0, 1),
    (1, 0, 1, 1, 1, 1, 1, 1, 0, 1),
    (1, 0, 0, 0, 0, 0, 0, 0, 0, 1),
    (1, 1, 1, 1, 1, 1, 1, 1, 1, 1)
)
MAP_X = len(MAP[0])
MAP_Y = len(MAP)

TILE_SIZE = 64

CAST_SCREEN_WIDTH = MAP_X * TILE_SIZE
CAST_SCREEN_HEIGHT = MAP_Y * TILE_SIZE

SPRITE_MAP: list[list[arcade.Sprite | None]] = [
    [None, None, None, None, None, None, None, None, None, None],
    [None, None, None, None, None, None, None, None, None, None],
    [None, None, None, None, None, None, None, None, None, None],
    [None, None, None, None, None, None, None, None, None, None],
    [None, None, None, None, None, None, None, None, None, None],
    [None, None, None, None, None, None, None, None, None, None],
    [None, None, None, None, None, None, None, None, None, None],
    [None, None, None, None, None, None, None, None, None, None],
    [None, None, None, None, None, None, None, None, None, None],
    [None, None, None, None, None, None, None, None, None, None]
]


def refresh_colors():
    for y in range(MAP_Y):
        for x in range(MAP_X):
            col = MAP[y][x] * 255
            SPRITE_MAP[y][x].color = (col, col, col)


class Player:
    speed = 0.2
    angular_speed = speed*pi

    def __init__(self, x, y, dir_x, dir_y, plane_x, plane_y):
        self.x = x
        self.y = y
        self.dir = (dir_x, dir_y)
        self.plane = (plane_x, plane_y)

    def handle_input(self, symbol):
        if symbol == arcade.key.A or symbol == arcade.key.LEFT:
            self.rotate(-self.angular_speed)
        elif symbol == arcade.key.D or symbol == arcade.key.RIGHT:
            self.rotate(self.angular_speed)

    def rotate(self, rad):
        _x, _y = self.dir
        self.dir = _x*cos(rad)-_y*sin(rad), _x*sin(rad)+_y*cos(rad)
        _x, _y = self.plane
        self.plane = _x*cos(rad)-_y*sin(rad), _x*sin(rad)+_y*cos(rad)

    def draw(self):
        s_x, s_y = self.x * TILE_SIZE, (MAP_Y-self.y) * TILE_SIZE
        arcade.draw_line(s_x, s_y, s_x+self.dir[0]*TILE_SIZE, s_y-self.dir[1]*TILE_SIZE, arcade.color.BLUE, 2)
        arcade.draw_line(s_x+(self.dir[0]-self.plane[0])*TILE_SIZE, s_y-(self.dir[1]-self.plane[1])*TILE_SIZE,
                         s_x+(self.dir[0]+self.plane[0])*TILE_SIZE, s_y-(self.dir[1]+self.plane[1])*TILE_SIZE,
                         arcade.color.BLUE, 2)

        arcade.draw_point(s_x, s_y, arcade.color.RADICAL_RED, 4)


class App(arcade.Window):

    def __init__(self):
        super().__init__(width=2*CAST_SCREEN_WIDTH, height=CAST_SCREEN_HEIGHT,
                         title="DragonMoffon's Raycaster", update_rate=1/60)
        self.background_color = arcade.color.DARK_GRAY

        # Tiles for map on left
        self.tiles = arcade.SpriteList()
        for y in range(MAP_Y):
            for x in range(MAP_X):
                col = MAP[y][x]*255
                tile = arcade.SpriteSolidColor(TILE_SIZE-2, TILE_SIZE-2, arcade.color.WHITE)
                tile.color = (col, col, col)
                tile.center_x = (x + 0.5) * TILE_SIZE
                tile.center_y = (MAP_Y - y - 0.5) * TILE_SIZE
                self.tiles.append(tile)
                SPRITE_MAP[y][x] = tile

        # Strips for render on right
        self.strips = arcade.SpriteList()
        for x in range(CAST_SCREEN_WIDTH):
            tile = arcade.SpriteSolidColor(1, 5, arcade.color.WHITE)
            tile.center_y = CAST_SCREEN_HEIGHT // 2 + 0.5
            tile.center_x = CAST_SCREEN_WIDTH + x + 0.5
            self.strips.append(tile)

        self.player = Player(5, 5, -1, 0, 0, -0.66)

    def on_key_press(self, symbol: int, modifiers: int):
        self.player.handle_input(symbol)

    def cast_rays(self):
        for x in range(0, CAST_SCREEN_WIDTH):
            camera_x = 2 * (x / CAST_SCREEN_WIDTH) - 1  # the x co-ord in camera space, similar to "angle"
            # ray dir x and y are the components of a vector which one could imagine slides along the camera plane.
            ray_dir_x = self.player.dir[0] + self.player.plane[0] * camera_x
            ray_dir_y = self.player.dir[1] + self.player.plane[1] * camera_x

            # the starting grid co-ord of the ray
            map_x, map_y = int(self.player.x), int(self.player.y)

            # the length the ray from one edge to the other
            delta_dist_x = abs(1 / ray_dir_x) if ray_dir_x else float("inf")
            delta_dist_y = abs(1 / ray_dir_y) if ray_dir_y else float("inf")

            # bool for if we hit a wall and whether the wall is NS or EW
            hit, side = 0, 0

            # calculate the integer steps on the X and Y
            # calculate the length from the starting position to the current edge on the x or y-side
            if ray_dir_x >= 0:
                step_x = 1
                side_dist_x = (map_x + 1 - self.player.x) * delta_dist_x
            else:
                step_x = -1
                side_dist_x = (self.player.x - map_x) * delta_dist_x

            if ray_dir_y >= 0:
                step_y = 1
                side_dist_y = (map_y + 1 - self.player.y) * delta_dist_y
            else:
                step_y = -1
                side_dist_y = (self.player.y - map_y) * delta_dist_y

            while not hit:
                # We only step in the shortest distance to make sure we don't cut through walls
                if side_dist_x < side_dist_y:
                    side_dist_x += delta_dist_x
                    map_x += step_x
                    side = 0
                else:
                    side_dist_y += delta_dist_y
                    map_y += step_y
                    side = 1

                SPRITE_MAP[map_y][map_x].color = arcade.color.DARK_YELLOW
                hit = 1 if MAP[map_y][map_x] else 0
            if side:
                perp_wall_dist = side_dist_y - delta_dist_y
                SPRITE_MAP[map_y][map_x].color = arcade.color.GREEN
                self.strips[x].color = arcade.color.GRAY
            else:
                self.strips[x].color = arcade.color.WHITE
                perp_wall_dist = side_dist_x - delta_dist_x
                SPRITE_MAP[map_y][map_x].color = arcade.color.YELLOW

            line_height = 1 if not perp_wall_dist else CAST_SCREEN_HEIGHT // (2*perp_wall_dist)
            self.strips[x].height = line_height

    def on_update(self, delta_time):
        print(1/delta_time)
        refresh_colors()
        self.cast_rays()

    def on_draw(self):
        self.clear()
        self.tiles.draw()
        self.strips.draw()
        self.player.draw()


if __name__ == '__main__':
    app = App()
    app.run()

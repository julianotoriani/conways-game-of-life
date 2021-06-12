import copy
from collections import deque

import pygame
from pygame import Surface
from pygame.locals import *

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720

CELL_SIZE = 10

GRID_SIZE_X = SCREEN_WIDTH // CELL_SIZE
GRID_SIZE_Y = SCREEN_HEIGHT // CELL_SIZE

print(f"{GRID_SIZE_X=} x {GRID_SIZE_Y}")
print(f"cells: {GRID_SIZE_X * GRID_SIZE_Y}")

SPACESHIP_LAYOUT = [
    [0, 1, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 1],
    [0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 1, 0],
    [0, 0, 1, 1, 0, 0, 0],
]

GLIDER_LAYOUT = [
    [0, 1, 0],
    [0, 1, 1],
    [1, 0, 1],
]

GOSPER_GLIDER_GUN_LAYOUT = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0],
    [0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
]

BACKGROUND_COLOR = pygame.Color(10, 10, 10)
GRID_COLOR = pygame.Color(20, 20, 20)
TEXT_COLOR = pygame.Color(200, 200, 200)

CELL_ALIVE_COLOR = pygame.Color(200, 200, 200)
CELL_DYING_COLOR = pygame.Color(255, 150, 150)
CELL_BIRTH_COLOR = pygame.Color(150, 255, 150)


class Game:
    def __init__(self, fps_cap=30):
        self.screen_size = SCREEN_WIDTH, SCREEN_HEIGHT
        self.fps_cap = fps_cap
        self.clock = pygame.time.Clock()
        self.screen = None
        self.font = None
        self.running = True
        self.pause = False
        self.debug = False
        self.create_cell_at_cursor = False
        self.overlay = True

        self.grid = [[False for _ in range(GRID_SIZE_Y)] for _ in range(GRID_SIZE_X)]

        self.snapshot = None
        self.save_snapshot = False
        self.history_size = 300
        self.history = deque(maxlen=self.history_size)

        self.step_forward = False
        self.rewind = False

    def spawn(self, pos, layout, convert_to_local=True):
        x, y = pos

        if convert_to_local:
            x = x // CELL_SIZE
            y = y // CELL_SIZE

        for col, rows in enumerate(layout):
            for row, value in enumerate(rows):
                self.grid[(x + row) % GRID_SIZE_X][(y + col) % GRID_SIZE_Y] = bool(value)

    def render_text(self, text, position):
        surface: Surface = self.font.render(text, True, TEXT_COLOR)
        bg_position = (position[0], position[1], surface.get_width(), surface.get_height())
        pygame.draw.rect(self.screen, BACKGROUND_COLOR, bg_position)
        self.screen.blit(surface, dest=position)

    def show_info(self):
        y = 30
        margin = 25

        self.render_text(f"<space> {'unpause' if self.pause else 'pause'}", (10, y))
        self.render_text(f"<D> debug: {self.debug}", (10, y))
        self.render_text(f"<H> spawn cosper glider gun", (10, y + margin * 1))
        self.render_text(f"<G> spawn glider", (10, y + margin * 2))
        self.render_text(f"<S> spawn spaceship", (10, y + margin * 3))
        self.render_text(f"<C> clear grid", (10, y + margin * 4))
        self.render_text(f"<arrow right> step forward", (10, y + margin * 5))
        self.render_text(f"<arrow left> step back", (10, y + margin * 6))
        self.render_text(f"<arrow up> rewind", (10, y + margin * 7))
        self.render_text(f"snapshots: {len(self.history)}/{self.history_size}", (10, y + margin * 8))
        self.render_text(f"<I> show/hide this text", (10, y + margin * 9))

    def cells(self):
        for row_index, row in enumerate(self.grid):
            for col_index, cell in enumerate(row):
                yield row_index, col_index, cell

    def evolve(self, x, y, cell):
        left = self.snapshot[x][(y - 1) % GRID_SIZE_Y]
        right = self.snapshot[x][(y + 1) % GRID_SIZE_Y]

        top = self.snapshot[(x - 1) % GRID_SIZE_X][y]
        bottom = self.snapshot[(x + 1) % GRID_SIZE_X][y]

        bottom_left = self.snapshot[(x + 1) % GRID_SIZE_X][(y - 1) % GRID_SIZE_Y]
        bottom_right = self.snapshot[(x + 1) % GRID_SIZE_X][(y + 1) % GRID_SIZE_Y]

        top_left = self.snapshot[(x - 1) % GRID_SIZE_X][(y - 1) % GRID_SIZE_Y]
        top_right = self.snapshot[(x - 1) % GRID_SIZE_X][(y + 1) % GRID_SIZE_Y]

        neighbor_count = sum([left, right, top, bottom, bottom_left, bottom_right, top_left, top_right])

        if cell:
            if neighbor_count < 2 or neighbor_count > 3:
                if not self.pause or self.step_forward:
                    self.save_snapshot = True
                    self.grid[x][y] = False
                return False

        elif neighbor_count == 3:
            if not self.pause or self.step_forward:
                self.grid[x][y] = True
                self.save_snapshot = True
            return True

        return cell

    def run(self):
        pygame.init()

        self.spawn((50, 0), GOSPER_GLIDER_GUN_LAYOUT, convert_to_local=False)

        self.font = pygame.font.Font(pygame.font.get_default_font(), 18)
        self.screen = pygame.display.set_mode(self.screen_size)

        while self.running:
            self.save_snapshot = False
            self.step_forward = False

            self.screen.fill(BACKGROUND_COLOR)
            self.process_events()

            if self.rewind:
                self.step_back()

            if self.create_cell_at_cursor:
                pos = pygame.mouse.get_pos()

                x = pos[0] // CELL_SIZE
                y = pos[1] // CELL_SIZE
                self.grid[x][y] = True

            self.draw_grid()

            self.snapshot = copy.deepcopy(self.grid)

            for x, y, cell in self.cells():
                new_cell_state = self.evolve(x, y, cell)

                cell_rect = (
                    CELL_SIZE * x,
                    CELL_SIZE * y,
                    CELL_SIZE,
                    CELL_SIZE,
                )

                if cell:
                    self.screen.fill(CELL_ALIVE_COLOR, cell_rect)

                if self.debug:
                    if cell and not new_cell_state:
                        self.screen.fill(CELL_DYING_COLOR, cell_rect)
                    elif not cell and new_cell_state:
                        self.screen.fill(CELL_BIRTH_COLOR, cell_rect)

            if self.save_snapshot:
                self.history.append(self.snapshot)

            if self.overlay:
                self.show_info()

            pygame.display.update()

            self.clock.tick(self.fps_cap)
        pygame.quit()

    def draw_grid(self):
        for x in range(0, SCREEN_WIDTH, CELL_SIZE):
            pygame.draw.line(self.screen, GRID_COLOR, (x, 0), (x, SCREEN_HEIGHT))
        for y in range(0, SCREEN_HEIGHT, CELL_SIZE):
            pygame.draw.line(self.screen, GRID_COLOR, (0, y), (SCREEN_WIDTH, y))

    def step_back(self):
        try:
            self.grid = self.history.pop()
        except IndexError:
            pass

    def clear(self):
        for x in range(GRID_SIZE_X):
            for y in range(GRID_SIZE_Y):
                self.grid[x][y] = False

    def process_events(self):
        events = pygame.event.get()

        for event in events:
            if event.type == QUIT:
                self.running = False

            if event.type == MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.create_cell_at_cursor = True
            elif event.type == MOUSEBUTTONUP and event.button == 1:
                self.create_cell_at_cursor = False

            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    self.running = False
                if event.key == K_i:
                    self.overlay = not self.overlay
                if event.key == K_d:
                    self.debug = not self.debug
                if event.key == K_SPACE:
                    self.pause = not self.pause
                if event.key == K_g:
                    self.spawn(pygame.mouse.get_pos(), GLIDER_LAYOUT)
                if event.key == K_h:
                    self.spawn(pygame.mouse.get_pos(), GOSPER_GLIDER_GUN_LAYOUT)
                if event.key == K_s:
                    self.spawn(pygame.mouse.get_pos(), SPACESHIP_LAYOUT)
                if event.key == K_RIGHT:
                    self.pause = True
                    self.step_forward = True
                if event.key == K_UP:
                    self.pause = True
                    self.rewind = True
                if event.key == K_LEFT:
                    self.pause = True
                    self.step_back()
                if event.key == K_c:
                    self.clear()

            elif event.type == KEYUP:
                if event.key == K_UP:
                    self.rewind = False


if __name__ == "__main__":
    game = Game()
    game.run()

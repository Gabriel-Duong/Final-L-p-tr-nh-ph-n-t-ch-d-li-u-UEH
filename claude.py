import pygame
import sys
from typing import List, Tuple, Set
import heapq
import random

class Position:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
    
    def __eq__(self, other):
        return self.x == other.x and self.y == other.y
    
    # Hash position để sử dụng nó như key trong set hoặc dictionary
    def __hash__(self) -> tuple:
        return hash((self.x, self.y))
    
    def __str__(self) -> str:
        return f"({self.x}, {self.y})"

class Cell:
    def __init__(self, position: Position, parent=None, status='free', g=0, h=0, f=0):
        self.position = position
        self.parent = parent
        self.status = status
        self.g = g
        self.h = h
        self.f = f
    
    def __lt__(self, other):
        return self.f < other.f

class AStar:
    def __init__(self, grid, start, dirt_positions, n, m):
        self.grid = grid
        self.start = start
        self.dirt_positions = dirt_positions
        self.n = n
        self.m = m
        self.dirt_weights = {pos: 1 for pos in dirt_positions}

    @staticmethod
    def chebyshev_distance(a, b):
        return max(abs(a[0] - b[0]), abs(a[1] - b[1]))

    def a_star_single_target(self, start, target):
        start_cell = Cell(Position(start[0], start[1]))
        target_cell = Cell(Position(target[0], target[1]))
        queue = []
        heapq.heappush(queue, (0, start_cell))  # (f(x), current cell)
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
        visited = set()
        visited.add((start_cell.position.x, start_cell.position.y))

        while queue:
            f, current_cell = heapq.heappop(queue)
            if current_cell.position == target_cell.position:
                return self.reconstruct_path(current_cell)
            for d in directions:
                neighbor_pos = (current_cell.position.x + d[0], current_cell.position.y + d[1])
                if 0 <= neighbor_pos[0] < self.n and 0 <= neighbor_pos[1] < self.m and neighbor_pos not in visited:
                    visited.add(neighbor_pos)
                    neighbor_cell = Cell(Position(neighbor_pos[0], neighbor_pos[1]), parent=current_cell)
                    h = self.chebyshev_distance(neighbor_pos, (target_cell.position.x, target_cell.position.y))
                    g = current_cell.g + 1
                    neighbor_cell.g = g
                    neighbor_cell.h = h
                    neighbor_cell.f = g + h
                    heapq.heappush(queue, (neighbor_cell.f, neighbor_cell))
        return None
    
    def reconstruct_path(self, cell):
        path = []
        while cell:
            path.append((cell.position.x, cell.position.y))
            cell = cell.parent
        return path[::-1]


    def a_star_cleaning(self):
        current_position = self.start
        queue_Astart = []
        heapq.heappush(queue_Astart, (0, current_position, [], [], self.dirt_weights))
        while queue_Astart:
            f, current, path, direction, dirt_weights_true = heapq.heappop(queue_Astart)
            start_pos = current
            if len(direction) == len(self.dirt_positions):
                for pos in self.dirt_positions:
                    self.dirt_positions.remove(pos)
                    self.dirt_weights.pop(pos, None)
                return path, f

            for node in {value for value in self.dirt_positions if value not in direction}:
                f_copy, current_copy, path_copy, direction_copy, dirt_weights_copy = f, current, path.copy(), direction.copy(), dirt_weights_true.copy()
                segment = self.a_star_single_target(start_pos, node)
                if segment:
                    path_copy.extend(segment)
                    for pos in dirt_weights_copy:
                        dirt_weights_copy[pos] += len(segment)-1
                        print(dirt_weights_copy)
                    cost = (len(segment)-1) + dirt_weights_copy[node]
                    direction_copy.append(node)
                    f_copy += cost
                    current_copy = node
                    heapq.heappush(queue_Astart, (f_copy, current_copy, path_copy, direction_copy, dirt_weights_copy))
        return None

class VacuumRobot:
    def __init__(self):
        pygame.init()
        self.CELL_SIZE = 60
        self.GRID_PADDING = 50
        self.LABEL_PADDING = 30  # Space for coordinate labels
        self.COLORS = {
            'white': (255, 255, 255),
            'black': (0, 0, 0),
            'red': (255, 0, 0),
            'gray': (128, 128, 128),
            'grid': (200, 200, 200),
            'text': (100, 100, 100)  # Color for coordinate labels
        }
        
    def initialize_grid(self):
        rows, cols = self.get_grid_size()
        self.rows, self.cols = rows, cols
        # Add extra padding for coordinate labels
        self.width = cols * self.CELL_SIZE + 2 * self.GRID_PADDING + self.LABEL_PADDING
        self.height = rows * self.CELL_SIZE + 2 * self.GRID_PADDING + self.LABEL_PADDING
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Vacuum Robot")
        self.grid = [[Cell(Position(x, y)) for x in range(cols)] for y in range(rows)]
        
    def get_grid_size(self) -> Tuple[int, int]:
        while True:
            try:
                size = input("Enter grid size (e.g., 8x10): ")
                cols, rows = map(int, size.lower().split('x'))
                return rows, cols
            except:
                print("Invalid format. Please use format like '8x10'")

    def draw_coordinates(self):
        font = pygame.font.Font(None, 24)
        
        # Draw column coordinates (x-axis)
        for col in range(self.cols):
            x = col * self.CELL_SIZE + self.GRID_PADDING + self.LABEL_PADDING
            y = self.height - self.GRID_PADDING + 10
            text = font.render(str(col), True, self.COLORS['text'])
            text_rect = text.get_rect(center=(x + self.CELL_SIZE/2, y))
            self.screen.blit(text, text_rect)

        # Draw row coordinates (y-axis)
        for row in range(self.rows):
            x = self.GRID_PADDING - 10
            y = self.height - (row + 1) * self.CELL_SIZE - self.GRID_PADDING - self.LABEL_PADDING
            text = font.render(str(row), True, self.COLORS['text'])
            text_rect = text.get_rect(center=(x, y + self.CELL_SIZE/2))
            self.screen.blit(text, text_rect)
        
    def draw_grid(self):
        self.screen.fill(self.COLORS['white'])
        
        # Draw cells
        for row in range(self.rows):
            for col in range(self.cols):
                cell = self.grid[row][col]
                x = col * self.CELL_SIZE + self.GRID_PADDING + self.LABEL_PADDING
                y = self.height - (row + 1) * self.CELL_SIZE - self.GRID_PADDING - self.LABEL_PADDING
                
                # Draw cell colors based on status
                if cell.status == 'start':
                    color = self.COLORS['red']
                elif cell.status == 'dirty':
                    color = self.COLORS['black']
                elif cell.status == 'path':
                    color = self.COLORS['gray']
                else:
                    color = self.COLORS['white']
                
                pygame.draw.rect(self.screen, color, 
                               (x, y, self.CELL_SIZE, self.CELL_SIZE))
                pygame.draw.rect(self.screen, self.COLORS['grid'],
                               (x, y, self.CELL_SIZE, self.CELL_SIZE), 1)
        
        # Draw coordinate labels
        self.draw_coordinates()
        pygame.display.flip()

    def get_clicked_cell(self) -> Tuple[int, int]:
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = event.pos
                    # Adjust for the coordinate labels padding
                    col = (x - self.GRID_PADDING - self.LABEL_PADDING) // self.CELL_SIZE
                    row = self.rows - 1 - (y - self.GRID_PADDING) // self.CELL_SIZE
                    if 0 <= row < self.rows and 0 <= col < self.cols:
                        return row, col
            pygame.time.wait(100)

    def clean_dirty_cells(self):
        dirty_cells = []
        
        print("Click to select start position")
        row, col = self.get_clicked_cell()
        start_pos = (row, col)
        self.grid[row][col].status = 'start'
        self.draw_grid()
        
        print("Click to select dirty cells (press SPACE when done)")
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    if dirty_cells:
                        return start_pos, dirty_cells
                if event.type == pygame.MOUSEBUTTONDOWN:
                    row, col = self.get_clicked_cell()
                    if self.grid[row][col].status == 'free':
                        self.grid[row][col].status = 'dirty'
                        dirty_cells.append((row, col))
                        self.draw_grid()
                pygame.time.wait(50)


    def print_path(self, path):
        print("\nComplete Path taken by the robot:")
        print("Start", end="")
        for i, pos in enumerate(path[1:], 1):
            print(f" -> ({pos[0]}, {pos[1]})", end="")
            if i % 5 == 0:
                print("\n     ", end="")
        print("\n")

    def run(self):
        self.initialize_grid()
        self.draw_grid()
        
        start_pos, dirty_cells = self.clean_dirty_cells()
        
        # Initialize A* algorithm
        astar = AStar(self.grid, start_pos, dirty_cells, self.rows, self.cols)
        path, cost = astar.a_star_cleaning()
        
        if path:
            # Visualize path
            for pos in path:
                if self.grid[pos[0]][pos[1]].status != 'start' and \
                   self.grid[pos[0]][pos[1]].status != 'dirty':
                    self.grid[pos[0]][pos[1]].status = 'path'
                self.draw_grid()
                pygame.time.wait(100)
            
            print("All dirty cells have been cleaned!")
            print(f"Total cost: {cost}")
            self.print_path(path)
        else:
            print("No valid path found!")
        
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
            pygame.time.wait(50)

if __name__ == "__main__":
    robot = VacuumRobot()
    robot.run()
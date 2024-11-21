import heapq
from typing import List, Tuple
import pygame
import sys
import random

#-------------------------------------------------------------------------------
# Lớp biểu diễn các toạ độ (x, y)
#-------------------------------------------------------------------------------
class Position:
    def __init__(self, x: int, y: int):
        self.x = x  # Tọa độ hàng
        self.y = y  # Tọa độ cột
    
    # So sánh hai vị trí
    def __eq__(self, other):
        return self.x == other.x and self.y == other.y
    
    # Hàm băm để sử dụng Position như là khóa trong set hoặc dictionary
    def __hash__(self):
        return hash((self.x, self.y))
    
    # Hàm in Position dưới dạng chuỗi "(x, y)"
    def __str__(self):
        return f"({self.x}, {self.y})"

#-------------------------------------------------------------------------------
# Lớp biểu diễn các ô
#-------------------------------------------------------------------------------
class Cell:
    def __init__(self, position: Position, parent=None, status='free', g=0, h=0, f=0):
        self.position = position  # Vị trí của ô
        self.parent = parent  # Lưu ô cha
        self.status = status  # Trạng thái ô (free, dirty, start, clean, path)
        self.g = g  # Chi phí từ điểm xuất phát đến ô này
        self.h = h  # Ước lượng chi phí từ ô này đến đích (hàm heuristic)
        self.f = f  # Tổng chi phí f = g + h
    
    # So sánh hai Cell dựa trên chi phí f để sắp xếp trong thuật toán A*
    def __lt__(self, other):
        return self.f < other.f

#-------------------------------------------------------------------------------
# Lớp AStar
#-------------------------------------------------------------------------------
class AStar:
    def __init__(self, grid: List[List[Cell]], m: int, n: int, moves: List[Tuple[int, int]]):
        self.grid = grid  # Lưới chứa các Cell
        self.m = m  # Số hàng
        self.n = n  # Số cột
        self.moves = moves  # Các di chuyển hợp lệ (8 hướng xung quanh)
    
    # Hàm khoảng cách Chebyshev giữa hai vị trí
    def chev_distance(self, pos1: Position, pos2: Position):
        return max(abs(pos1.x - pos2.x), abs(pos1.y - pos2.y))
    
    # Lấy các ô láng giềng của một ô
    def get_neighbors(self, cell: Cell):
        neighbors = []
        for dx, dy in self.moves:  # Duyệt qua các hướng di chuyển
            new_x = cell.position.x + dx
            new_y = cell.position.y + dy
            new_pos = Position(new_x, new_y)
            
            if 1 <= new_pos.x <= self.m and 1 <= new_pos.y <= self.n:
                # Tạo một ô mới làm láng giềng
                neighbor = Cell(
                    position=new_pos,
                    parent=cell,
                    status=self.grid[new_x-1][new_y-1].status,
                    g=cell.g + 1  # Chi phí di chuyển từ ô hiện tại
                )
                neighbors.append(neighbor)
        return neighbors
    
    # Hàm tìm đường từ start đến target sử dụng thuật toán A*
    def find_path(self, start: Position, target: Position):
        if start == target:
            return [start]
        
        start_cell = Cell(position=start)
        open_list = [] 
        closed_set = set() 
        
        heapq.heappush(open_list, start_cell)  # Đưa ô bắt đầu vào danh sách mở
        
        while open_list:
            current = heapq.heappop(open_list)  # Lấy ô có chi phí f thấp nhất
            
            if current.position == target:
                # Nếu đã đến đích, trả về đường đi
                path = []
                while current:
                    path.append(current.position)
                    current = current.parent
                return path[::-1]  # Đảo ngược đường đi để từ start đến target
            
            closed_set.add((current.position.x, current.position.y))
            
            # Duyệt qua các ô láng giềng
            for neighbor in self.get_neighbors(current):
                if (neighbor.position.x, neighbor.position.y) in closed_set:
                    continue
                neighbor.g = current.g + 1  # Cập nhật chi phí g từ điểm xuất phát đến ô láng giềng
                neighbor.h = self.chev_distance(neighbor.position, target)  # Ước lượng khoảng cách đến đích
                neighbor.f = neighbor.g + neighbor.h  # Tính chi phí tổng f
                
                heapq.heappush(open_list, neighbor)  # Đưa ô láng giềng vào danh sách mở
        
        return []  # Trả về đường đi rỗng nếu không tìm được đường

#-------------------------------------------------------------------------------
# Lớp Robot
#-------------------------------------------------------------------------------
class RobotVacuum:
    def __init__(self):
        pygame.init()
        self.CELL_SIZE = 50
        self.GRID_PADDING = 50
        self.LABEL_PADDING = 30
        self.COLORS = {
            'white': (248, 249, 250),
            'black': (33, 37, 41),
            'red': (186, 24, 27),
            'gray': (173, 181, 189),
            'pink': (73, 80, 87),
            'grid': (200, 200, 200),
            'text': (100, 100, 100)
        }
        self.font = pygame.font.Font(None, 24)
        self.moves = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]  # 8 hướng di chuyển

    # Hàm khởi tạo lưới
    def initialize_grid(self):
        self.m, self.n = self.get_grid_size()  # Nhận kích thước lưới từ người dùng
        self.width = self.n * self.CELL_SIZE + 2 * self.GRID_PADDING + self.LABEL_PADDING
        self.height = self.m * self.CELL_SIZE + 2 * self.GRID_PADDING + self.LABEL_PADDING
        self.screen = pygame.display.set_mode((self.width, self.height))  # Khởi tạo màn hình
        pygame.display.set_caption("Vacuum Robot")
        self.grid = [[Cell(Position(i, j)) for j in range(1, self.n+1)] for i in range(1, self.m+1)]  # Tạo lưới các ô
        self.cost = 0  # Biến để lưu chi phí (cost) của robot

    # Hàm lấy kích thước lưới từ người dùng
    def get_grid_size(self):
        while True:
            try:
                size = input("Enter grid size (rows x cols) (e.g., 8x10): ")
                rows, cols = map(int, size.lower().split('x'))
                return rows, cols
            except:
                print("Invalid format. Please use format like '8x10'")

    # Hàm vẽ các tọa độ trên lưới
    def draw_coordinates(self):
        for col in range(self.n):
            x = col * self.CELL_SIZE + self.GRID_PADDING + self.LABEL_PADDING
            text = self.font.render(str(col + 1), True, self.COLORS['text'])
            self.screen.blit(text, text.get_rect(
                center=(x + self.CELL_SIZE/2, self.height - self.GRID_PADDING + 10)))

        for row in range(self.m):
            y = self.height - (row + 1) * self.CELL_SIZE - self.GRID_PADDING - self.LABEL_PADDING
            text = self.font.render(str(row + 1), True, self.COLORS['text'])
            self.screen.blit(text, text.get_rect(
                center=(self.GRID_PADDING - 10, y + self.CELL_SIZE/2)))
    
    # Hàm vẽ lưới và các ô trên màn hình
    def draw_grid(self, path=[]):
        self.screen.fill(self.COLORS['white'])  # Đổ màu nền cho màn hình
        # Duyệt qua các ô trong lưới và vẽ chúng
        for i in range(self.m):
            for j in range(self.n):
                cell = self.grid[i][j]
                x = j * self.CELL_SIZE + self.GRID_PADDING + self.LABEL_PADDING
                y = self.height - (i + 1) * self.CELL_SIZE - self.GRID_PADDING - self.LABEL_PADDING

                # Xác định màu sắc của ô tùy thuộc vào trạng thái
                color = self.COLORS['white']
                if cell.status == 'start':
                    color = self.COLORS['red']
                elif cell.status == 'dirty':
                    color = self.COLORS['black']
                elif cell.status == 'path':
                    color = self.COLORS['gray']
                elif cell.status == 'clean':
                    color = self.COLORS['pink']

                pygame.draw.rect(self.screen, color, (x, y, self.CELL_SIZE, self.CELL_SIZE))  # Vẽ ô
                pygame.draw.rect(self.screen, self.COLORS['grid'], (x, y, self.CELL_SIZE, self.CELL_SIZE), 1)  # Vẽ viền ô

        self.draw_coordinates()  # Vẽ các tọa độ
        # Vẽ chi phí tổng cộng ở góc trên bên trái màn hình
        cost_text = self.font.render(f"Total cost: {self.cost}", True, self.COLORS['black'])
        self.screen.blit(cost_text, (self.GRID_PADDING-30, self.GRID_PADDING-30))
         # Vẽ các đường nối trong path (nếu có)
        if path:
            for i in range(len(path) - 1):
                start_pos = path[i]
                end_pos = path[i + 1]
                # Tính tọa độ màn hình của 2 ô (start và end)
                start_x = (start_pos.y - 1) * self.CELL_SIZE + self.GRID_PADDING + self.LABEL_PADDING
                start_y = self.height - (start_pos.x) * self.CELL_SIZE - self.GRID_PADDING - self.LABEL_PADDING
                end_x = (end_pos.y - 1) * self.CELL_SIZE + self.GRID_PADDING + self.LABEL_PADDING
                end_y = self.height - (end_pos.x) * self.CELL_SIZE - self.GRID_PADDING - self.LABEL_PADDING

                # Vẽ đường nối giữa các ô
                pygame.draw.line(self.screen, self.COLORS['red'], (start_x + self.CELL_SIZE // 2, start_y + self.CELL_SIZE // 2), (end_x + self.CELL_SIZE // 2, end_y + self.CELL_SIZE // 2), 3)

        pygame.display.flip()  # Cập nhật màn hình


    # Hàm nhận click chuột để chọn ô
    def get_clicked_cell(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = event.pos
                    j = (x - self.GRID_PADDING - self.LABEL_PADDING) // self.CELL_SIZE + 1
                    i = self.m - ((y - self.GRID_PADDING) // self.CELL_SIZE)
                    if 1 <= i <= self.m and 1 <= j <= self.n:
                        return i, j

    # Hàm chính điều khiển robot hút bụi và vẽ kết quả
    def clean_all_dirty_cells(self):
        start_i, start_j  = self.get_clicked_cell()
        start_pos  = Position(start_i, start_j)
        self.grid[start_i-1][start_j-1].status = 'start'
        self.draw_grid()
        dirty_positions = []

        while True:
            self.draw_grid
            for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONDOWN:
                    i, j  = self.get_clicked_cell()
                    if i == start_i and j == start_j: 
                        continue
                    dir_pos = Position(i, j)
                    dirty_positions.append(dir_pos)
                    self.draw_grid()  # Cập nhật màn hình
                    if self.grid[i-1][j-1].status == 'free':
                        self.grid[i-1][j-1].status = 'dirty'  # Đánh dấu ô dơ
                        self.draw_grid()  # Cập nhật màn hình

                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    if dirty_positions:
                        return self.solve(start_pos, dirty_positions)  # Tìm đường đi và giải quyết ô dơ                        
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

    # Hàm giải quyết ô dơ bằng thuật toán A* và tính toán chi phí
    def solve(self, start_pos: Position, dirty_positions: List[Position]):
        astar = AStar(self.grid, self.m, self.n, self.moves)
        current_pos = start_pos
        total_path = [current_pos]
        total_cost = 0
        remaining_dirt = set(dirty_positions)
        fee = 1

        # Duyệt qua các ô dơ và tìm đường đi tối ưu
        while remaining_dirt:
            best_next = None
            best_path = None
            best_total_estimated_cost = float('inf')

            # Duyệt từng ô dơ để đánh giá chi phí tối ưu
            for dirt_pos in remaining_dirt:
                path = astar.find_path(current_pos, dirt_pos)  # Tìm đường đến ô dơ tiếp theo
                if not path:
                    continue

                # Chi phí cho tới ô dơ hiện tại
                path_cost = len(path) - 1
                remaining_temp_dirt = remaining_dirt.copy()
                remaining_temp_dirt.remove(dirt_pos)

                inner_total_cost = path_cost
                inner_current_pos = dirt_pos
                inner_fee = fee + path_cost
                # Duyệt qua các ô dơ còn lại để tính toán chi phí tối ưu
                while remaining_temp_dirt:
                    best_inner_next = None
                    best_inner_path = None
                    best_inner_cost = float('inf')

                    for inner_dirt_pos in remaining_temp_dirt:
                        inner_path = astar.find_path(inner_current_pos, inner_dirt_pos) 
                        if inner_path:
                            inner_path_cost = len(inner_path) + astar.chev_distance(inner_current_pos, inner_dirt_pos)
                            if inner_path_cost < best_inner_cost:
                                best_inner_cost = inner_path_cost
                                best_inner_next = inner_dirt_pos
                                best_inner_path = inner_path

                    if best_inner_next is None:
                        break
                    
                    inner_fee += len(best_inner_path) - 1
                    inner_total_cost += best_inner_cost + inner_fee
                    inner_current_pos = best_inner_next
                    remaining_temp_dirt.remove(best_inner_next)
                # So sánh chi phí ước tính tổng cộng
                if inner_total_cost < best_total_estimated_cost:
                    best_total_estimated_cost = inner_total_cost
                    best_next = dirt_pos
                    best_path = path

            if best_next is None:
                return None, None

            current_pos = best_next
            remaining_dirt.remove(best_next)

            # Vẽ đường đi và đánh dấu ô dơ là sạch
            for pos in best_path[1:]:
                if self.grid[pos.x-1][pos.y-1].status == 'dirty':
                    self.grid[pos.x-1][pos.y-1].status = 'clean'
                elif self.grid[pos.x-1][pos.y-1].status != 'clean' and self.grid[pos.x-1][pos.y-1].status != 'start':
                    self.grid[pos.x-1][pos.y-1].status = 'path'
                fee += 1
                total_cost += 1
                if pos in dirty_positions:
                    total_cost += fee
                self.cost = total_cost
                self.draw_grid(total_path)  # Vẽ đường đi và các đường nối
                pygame.time.wait(200)
            print()    
            total_path.extend(best_path[1:])
            self.draw_grid(total_path)  # Vẽ đường đi và các đường nối
        return total_path, total_cost
    
    # Hàm điều khiển chính của chương trình
    def run(self):
        self.initialize_grid()  # Khởi tạo lưới
        self.draw_grid()  # Vẽ lưới ban đầu
        
        # Làm sạch các ô dơ
        path, cost = self.clean_all_dirty_cells()
        
        # Hiển thị kết quả đường đi và chi phí
        if path:
            print("\nPath completed!")
            print(f"Total cost: {cost}")
            print("\nComplete path taken by the robot:")
            print("Start", end="")
            for i, pos in enumerate(path[1:], 1):
                print(f" -> {pos}", end="" if i % 5 else "\n     ")
            print("\n")
        else:
            print("No valid path found!")
        
        # Giữ màn hình không tắt
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

# Chạy chương trình chính
if __name__ == "__main__":
    robot = RobotVacuum()
    robot.run()
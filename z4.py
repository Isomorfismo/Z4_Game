import pygame
import random
from itertools import product
from collections import deque
from copy import deepcopy

# =================== LOGICA ===================

MOD = 4
N = 4  # tablero NxN

def apply_press(board, r, c, k=1):
    # Suma k (mod 4) al bloque 3x3 centrado en (r,c), recortado a la rejilla
    if k % MOD == 0:
        return
    for i in range(max(0, r-1), min(N, r+2)):
        for j in range(max(0, c-1), min(N, c+2)):
            board[i][j] = (board[i][j] + k) % MOD

def apply_single(board, r, c, k=1):
    # Suma k (mod 4) solo a la casilla (r,c)
    board[r][c] = (board[r][c] + k) % MOD

def apply_press_matrix(board, P):
    out = deepcopy(board)
    for r in range(N):
        for c in range(N):
            k = P[r][c] % MOD
            if k:
                apply_press(out, r, c, k)
    return out

def mat_inv_mod4(M):
    n = len(M)
    A = [[M[i][j] % MOD for j in range(n)] for i in range(n)]
    I = [[1 if i == j else 0 for j in range(n)] for i in range(n)]
    for col in range(n):
        piv = None
        for r in range(col, n):
            if A[r][col] % MOD in (1, 3):
                piv = r
                break
        if piv is None:
            raise ValueError("Matriz no invertible mod 4")
        if piv != col:
            A[col], A[piv] = A[piv], A[col]
            I[col], I[piv] = I[piv], I[col]
        inv = 1 if A[col][col] % MOD == 1 else 3
        for j in range(n):
            A[col][j] = (A[col][j] * inv) % MOD
            I[col][j] = (I[col][j] * inv) % MOD
        for r in range(n):
            if r == col: continue
            factor = A[r][col] % MOD
            if factor:
                for j in range(n):
                    A[r][j] = (A[r][j] - factor * A[col][j]) % MOD
                    I[r][j] = (I[r][j] - factor * I[col][j]) % MOD
    return I

def vec_mul_mat_mod4(v, M):
    n = len(v)
    out = [0]*n
    for j in range(n):
        s = 0
        for i in range(n):
            s += v[i]*M[i][j]
        out[j] = s % MOD
    return out

T = [
    [1,1,0,0],
    [1,1,1,0],
    [0,1,1,1],
    [0,0,1,1],
]
T_INV = mat_inv_mod4(T)

def solve_min_presses(initial):
    best_P, best_cost = None, float('inf')
    for first_row in product(range(4), repeat=4):
        S = [row[:] for row in initial]
        P = [[0]*N for _ in range(N)]
        P[0] = list(first_row)
        for c in range(N):
            k = P[0][c]
            if k: apply_press(S, 0, c, k)
        feasible = True
        for r in range(1, N):
            target = [(-x) % MOD for x in S[r-1]]
            p_r = vec_mul_mat_mod4(target, T_INV)
            P[r] = p_r
            for c in range(N):
                k = P[r][c]
                if k: apply_press(S, r, c, k)
        if any(S[N-1][c] % MOD != 0 for c in range(N)): feasible = False
        if not feasible: continue
        cost = sum(sum(cell % MOD for cell in row) for row in P)
        if cost < best_cost:
            best_cost = cost
            best_P = [row[:] for row in P]
    if best_P is None: return None, None
    return best_P, best_cost

def next_hint(board):
    P, cost = solve_min_presses(board)
    if P is None or cost == 0: return None
    for r in range(N):
        for c in range(N):
            if P[r][c] % MOD != 0: return (r, c)
    return None

def optimal_move_sequence(board):
    P, cost = solve_min_presses(board)
    if P is None: return None
    seq = []
    for r in range(N):
        for c in range(N):
            k = P[r][c] % MOD
            for _ in range(k): seq.append((r, c))
    return seq

def is_solved(board):
    return all(board[r][c] % MOD == 0 for r in range(N) for c in range(N))

# =================== INTERFAZ PYGAME ===================

GRID_SIZE = N
TILE = 110
GRID_MARGIN = 25
PANEL_H = 180
W = GRID_MARGIN*2 + GRID_SIZE*TILE
H = GRID_MARGIN*2 + GRID_SIZE*TILE + PANEL_H

def hex_to_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

COLORS = {
    0: hex_to_rgb('#fe0000'),
    1: hex_to_rgb('#9aff01'),
    2: hex_to_rgb('#01ffff'),
    3: hex_to_rgb('#6700ff'),
}

BG = (18, 18, 24)
GRID_BG = (35, 35, 45)
LINE = (60, 60, 75)
WHITE = (240, 240, 245)
BTN_BG = (50, 50, 65)
BTN_BG_HOVER = (70, 70, 90)
BTN_TEXT = WHITE
HINT_BORDER = (255, 220, 0)

class Button:
    def __init__(self, rect, text, font, callback):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.callback = callback
        self.enabled = True

    def draw(self, surf, mouse_pos):
        color = BTN_BG
        if self.enabled and self.rect.collidepoint(mouse_pos):
            color = BTN_BG_HOVER
        pygame.draw.rect(surf, color, self.rect, border_radius=8)
        label = self.font.render(self.text, True, BTN_TEXT)
        surf.blit(label, label.get_rect(center=self.rect.center))

    def handle_event(self, event):
        if not self.enabled: return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos): self.callback()

def new_random_board():
    return [[random.randint(0, 3) for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

def draw_arrow(surf, rect, value):
    x, y, w, h = rect
    pad = int(min(w, h) * 0.22)
    cx, cy = x + w//2, y + h//2
    color = COLORS[value % 4]
    if value % 4 == 0:
        pts = [(cx, y + pad), (x + pad, y + h - pad), (x + w - pad, y + h - pad)]
    elif value % 4 == 1:
        pts = [(x + w - pad, cy), (x + pad, y + pad), (x + pad, y + h - pad)]
    elif value % 4 == 2:
        pts = [(cx, y + h - pad), (x + pad, y + pad), (x + w - pad, y + pad)]
    else:
        pts = [(x + pad, cy), (x + w - pad, y + pad), (x + w - pad, y + h - pad)]
    pygame.draw.polygon(surf, color, pts)

def main():
    pygame.init()
    pygame.display.set_caption("Z4 - Chebyshev")
    screen = pygame.display.set_mode((W, H))
    clock = pygame.time.Clock()

    font = pygame.font.SysFont(None, 28)
    big = pygame.font.SysFont(None, 32)
    tiny = pygame.font.SysFont(None, 22)

    board = new_random_board()
    moves = 0
    solving = False
    solved = False
    move_queue = deque()
    hint_cell = None
    step_delay_ms = 260
    next_step_time = 0
    customizing = False

    btn_w, btn_h, gap = 145, 44, 9
    base_y = GRID_MARGIN*2 + GRID_SIZE*TILE + 18
    buttons = []

    def on_hint():
        nonlocal hint_cell
        if solving or customizing: return
        h = next_hint(board)
        hint_cell = h

    def on_solve():
        nonlocal solving, move_queue, next_step_time, solved, hint_cell
        if solving or solved or customizing: return
        seq = optimal_move_sequence(board)
        if not seq: return
        hint_cell = None
        move_queue = deque(seq)
        solving = True
        next_step_time = pygame.time.get_ticks() + step_delay_ms

    def on_new():
        nonlocal board, moves, solving, solved, move_queue, hint_cell
        if customizing: return
        board = new_random_board()
        moves = 0
        solving = False
        solved = False
        move_queue.clear()
        hint_cell = None

    def on_customize():
        nonlocal customizing
        customizing = not customizing
        for b in buttons[1:]:
            b.enabled = not customizing

    buttons.append(Button((GRID_MARGIN, base_y, btn_w, btn_h), "Personalizar", big, on_customize))
    buttons.append(Button((GRID_MARGIN, base_y + 50, btn_w, btn_h), "Pista", big, on_hint))
    buttons.append(Button((GRID_MARGIN + btn_w + gap, base_y + 50, btn_w, btn_h), "Resolver", big, on_solve))
    buttons.append(Button((GRID_MARGIN + 2*(btn_w + gap), base_y + 50, btn_w, btn_h), "Nuevo", big, on_new))

    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            for b in buttons: b.handle_event(event)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if solving or solved: continue
                gx0, gy0 = GRID_MARGIN, GRID_MARGIN
                gx1, gy1 = gx0 + GRID_SIZE*TILE, gy0 + GRID_SIZE*TILE
                if gx0 <= event.pos[0] < gx1 and gy0 <= event.pos[1] < gy1:
                    c = (event.pos[0] - gx0) // TILE
                    r = (event.pos[1] - gy0) // TILE
                    if customizing:
                        apply_single(board, r, c, 1)
                    else:
                        apply_press(board, r, c, 1)
                        moves += 1
                        hint_cell = None
                        if is_solved(board): solved = True

        if solving and pygame.time.get_ticks() >= next_step_time:
            if move_queue:
                r, c = move_queue.popleft()
                apply_press(board, r, c, 1)
                moves += 1
                if is_solved(board) and not move_queue:
                    solving = False
                    solved = True
                next_step_time = pygame.time.get_ticks() + step_delay_ms
            else:
                solving = False
                solved = is_solved(board)

        screen.fill(BG)
        grid_rect = pygame.Rect(GRID_MARGIN-8, GRID_MARGIN-8, GRID_SIZE*TILE+16, GRID_SIZE*TILE+16)
        pygame.draw.rect(screen, GRID_BG, grid_rect, border_radius=12)

        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                x, y = GRID_MARGIN + c*TILE, GRID_MARGIN + r*TILE
                rect = (x, y, TILE, TILE)
                pygame.draw.rect(screen, (30, 30, 40), rect, border_radius=6)
                draw_arrow(screen, rect, board[r][c])
                pygame.draw.rect(screen, LINE, rect, width=2, border_radius=6)

        if hint_cell is not None:
            r, c = hint_cell
            hx, hy = GRID_MARGIN + c*TILE, GRID_MARGIN + r*TILE
            pygame.draw.rect(screen, HINT_BORDER, (hx-3, hy-3, TILE+6, TILE+6), width=3, border_radius=8)
            tip = tiny.render(f"Sugerencia: clic en (fila {r+1}, columna {c+1})", True, WHITE)
            screen.blit(tip, (GRID_MARGIN, GRID_MARGIN + GRID_SIZE*TILE + 150))

        status = f"Movimientos: {moves}"
        if solving: status += "   Resolviendo..."
        elif solved: status += "   Resuelto"
        label = font.render(status, True, WHITE)
        screen.blit(label, (GRID_MARGIN, GRID_MARGIN + GRID_SIZE*TILE + 180))

        inst = tiny.render("Haz clic en una casilla para sumar +1 (mod 4) a su vecindad 3x3", True, (200,200,210))
        screen.blit(inst, (GRID_MARGIN - 5, GRID_MARGIN + GRID_SIZE*TILE + 15))

        for b in buttons: b.draw(screen, mouse_pos)

        if customizing:
            act = tiny.render("Activado", True, (0, 200, 0))
            screen.blit(act, (buttons[0].rect.right + 12, buttons[0].rect.centery - 10))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()

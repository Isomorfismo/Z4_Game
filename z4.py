# Z4 - Isomorfismo 
# https://github.com/Isomorfismo/Z4
import pygame
import random
import math
import itertools
from collections import deque
from copy import deepcopy
import asyncio
import colorsys

# Configuraciones globales
current_topology = 'normal'  # topologías: 'normal', 'torus', 'cylinder', 'mobius', 'klein'
current_neighborhood = 'square'  # vecindades: 'square' (Moore), 'cross' (von Neumann)
current_mod = 4
current_n = 4

# =================== LOGICA ===================

MOD = current_mod
N = current_n  # tablero NxN

# =================== HELPERS: TOPOLOGÍA Y VECINDAD ===================

def get_neighborhood_offsets(neighborhood):
    """Retorna lista de offsets (di, dj) según la vecindad."""
    if neighborhood == 'square':
        # Moore neighborhood: 3x3
        return [(di, dj) for di in [-1, 0, 1] for dj in [-1, 0, 1]]
    elif neighborhood == 'cross':
        # von Neumann neighborhood: center + cardinals
        return [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)]
    else:
        return [(di, dj) for di in [-1, 0, 1] for dj in [-1, 0, 1]]

def apply_topology(r, c, di, dj, N, topology):
    """Aplica reglas de topología para mapear (r+di, c+dj) a coordenadas válidas.
    Retorna (i, j) o None si la celda está fuera de límites.
    """
    if topology == 'normal':
        # Regular 2D surface: no wrapping, clip out-of-bounds
        i, j = r + di, c + dj
        if not (0 <= i < N and 0 <= j < N):
            return None
        return (i, j)
    elif topology == 'torus':
        # Wrap both rows and columns
        return ((r + di) % N, (c + dj) % N)
    elif topology == 'cylinder':
        # Wrap rows, clip columns
        i = (r + di) % N
        j = c + dj
        if not (0 <= j < N):
            return None
        return (i, j)
    elif topology == 'mobius':
        # No vertical wrap, horizontal wrap with row flip
        i = r + di
        j = c + dj
        if not (0 <= i < N):
            return None
        if j < 0:
            j = N - 1
            i = N - 1 - i
        elif j >= N:
            j = 0
            i = N - 1 - i
        return (i, j)
    elif topology == 'klein':
        # Vertical wrap + horizontal wrap with row flip
        i = (r + di) % N
        j = c + dj
        if j < 0:
            j = N - 1
            i = N - 1 - i
        elif j >= N:
            j = 0
            i = N - 1 - i
        return (i, j)
    else:
        # Fallback: no wrapping
        i, j = r + di, c + dj
        if not (0 <= i < N and 0 <= j < N):
            return None
        return (i, j)

def apply_press(board, r, c, k=1, topology='torus', neighborhood='square'):
    """Suma k (mod MOD) a las casillas afectadas según topología y vecindad."""
    if k % MOD == 0:
        return
    
    offsets = get_neighborhood_offsets(neighborhood)
    for di, dj in offsets:
        result = apply_topology(r, c, di, dj, N, topology)
        if result is not None:
            i, j = result
            board[i][j] = (board[i][j] + k) % MOD

def apply_single(board, r, c, k=1):
    # Suma k (mod MOD) solo a la casilla (r,c)
    board[r][c] = (board[r][c] + k) % MOD

def apply_press_matrix(board, P, topology='torus', neighborhood='square'):
    """Aplica matriz de pulsaciones a un tablero."""
    out = deepcopy(board)
    for r in range(N):
        for c in range(N):
            k = P[r][c] % MOD
            if k:
                apply_press(out, r, c, k, topology, neighborhood)
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

def mod_inverse(a, m):
    for i in range(m):
        if (a * i) % m == 1:
            return i
    return None

def gaussian_elimination_mod(A, b):
    n = len(A)
    # Save original system for verification
    A_orig = [row[:] for row in A]
    b_orig = b[:]

    # Build augmented matrix
    aug = [A[i][:] + [b[i] % MOD] for i in range(n)]

    # RREF with proper pivot tracking (works over any Z/MOD, including composites)
    cur_pivot_row = 0          # next available row for a pivot
    pivot_row_for_col = {}     # col -> row that owns its pivot
    pivot_col_for_row = {}     # row -> col that it pivots on

    for col in range(n):
        # Find a row with an invertible entry in this column
        found = -1
        for row in range(cur_pivot_row, n):
            if aug[row][col] % MOD != 0 and mod_inverse(aug[row][col] % MOD, MOD) is not None:
                found = row
                break
        if found == -1:
            continue  # free variable column — handled by enumeration below

        # Swap found row to cur_pivot_row
        aug[cur_pivot_row], aug[found] = aug[found], aug[cur_pivot_row]

        # Scale pivot row so the pivot element becomes 1
        piv = aug[cur_pivot_row][col] % MOD
        inv = mod_inverse(piv, MOD)
        aug[cur_pivot_row] = [(v * inv) % MOD for v in aug[cur_pivot_row]]

        # Eliminate all other rows
        for row in range(n):
            if row == cur_pivot_row:
                continue
            factor = aug[row][col]
            if factor == 0:
                continue
            for j in range(n + 1):
                aug[row][j] = (aug[row][j] - factor * aug[cur_pivot_row][j]) % MOD

        pivot_row_for_col[col] = cur_pivot_row
        pivot_col_for_row[cur_pivot_row] = col
        cur_pivot_row += 1

    # Identify free (non-pivot) columns
    free_cols = [c for c in range(n) if c not in pivot_row_for_col]

    def candidate(free_vals):
        """Build a solution vector given values for free columns."""
        x = [0] * n
        for i, fc in enumerate(free_cols):
            x[fc] = free_vals[i]
        # Compute pivot variables from the reduced augmented matrix
        for pr in range(cur_pivot_row):
            pc = pivot_col_for_row[pr]
            val = aug[pr][n]
            for fc in free_cols:
                val = (val - aug[pr][fc] * x[fc]) % MOD
            x[pc] = val % MOD
        return x

    def is_valid(x):
        """Verify x satisfies the original system A_orig * x = b_orig (mod MOD)."""
        for i in range(n):
            if sum(A_orig[i][j] * x[j] for j in range(n)) % MOD != b_orig[i] % MOD:
                return False
        return True

    # Enumerate all combinations of free-variable values
    for free_vals in itertools.product(range(MOD), repeat=len(free_cols)):
        x = candidate(free_vals)
        if is_valid(x):
            return x

    return [0] * n  # no solution exists for this board state

def create_press_matrix(N, topology='torus', neighborhood='square'):
    """Crea la matriz de coeficientes para el sistema lineal de pulsaciones."""
    size = N * N
    A = [[0] * size for _ in range(size)]
    offsets = get_neighborhood_offsets(neighborhood)
    
    for k in range(size):
        r, c = divmod(k, N)
        for di, dj in offsets:
            result = apply_topology(r, c, di, dj, N, topology)
            if result is not None:
                i, j = result
                idx = i * N + j
                A[idx][k] = 1
    return A

def solve_min_presses(initial, topology='torus', neighborhood='square'):
    """Resuelve el sistema lineal para encontrar pulsaciones mínimas."""
    A = create_press_matrix(N, topology, neighborhood)
    b = [initial[i][j] for i in range(N) for j in range(N)]
    x = gaussian_elimination_mod(A, b)
    P = [[x[i*N + j] for j in range(N)] for i in range(N)]
    cost = sum(sum(cell for cell in row) for row in P)
    return P, cost

def next_hint(board, topology='torus', neighborhood='square'):
    """Encuentra la siguiente celda sugerida para presionar."""
    P, cost = solve_min_presses(board, topology, neighborhood)
    if P is None or cost == 0: return None
    for r in range(N):
        for c in range(N):
            if P[r][c] % MOD != 0: return (r, c)
    return None

def optimal_move_sequence(board, topology='torus', neighborhood='square'):
    """Retorna secuencia de movimientos para resolver el tablero."""
    P, cost = solve_min_presses(board, topology, neighborhood)
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
H = GRID_MARGIN*2 + GRID_SIZE*TILE + PANEL_H - 35

def generate_mod_palette(modulus, saturation=1.0, value=1.0):
    if modulus <= 0:
        return [(255, 0, 0)]
    palette = []
    for k in range(modulus):
        h = k / modulus
        r, g, b = colorsys.hsv_to_rgb(h, saturation, value)
        palette.append((int(r * 255), int(g * 255), int(b * 255)))
    return palette

PALETTE = generate_mod_palette(MOD)

BG = (18, 18, 24)
GRID_BG = (35, 35, 45)
LINE = (60, 60, 75)
WHITE = (240, 240, 245)
BTN_BG = (50, 50, 65)
BTN_BG_HOVER = (70, 70, 90)
BTN_TEXT = WHITE
HINT_BORDER = (255, 220, 0)

class Button:
    def __init__(self, rect, text, font, callback, text_color=BTN_TEXT):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.callback = callback
        self.enabled = True
        self.text_color = text_color

    def draw(self, surf, mouse_pos):
        color = BTN_BG
        if self.enabled and self.rect.collidepoint(mouse_pos):
            color = BTN_BG_HOVER
        pygame.draw.rect(surf, color, self.rect, border_radius=8)
        label = self.font.render(self.text, True, self.text_color)
        surf.blit(label, label.get_rect(center=self.rect.center))

    def handle_event(self, event):
        if not self.enabled: return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos): self.callback()

def new_random_board():
    return [[random.randint(0, MOD - 1) for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

def draw_arrow(surf, rect, value):
    x, y, w, h = rect
    cx, cy = x + w // 2, y + h // 2
    r = int(min(w, h) * 0.38)
    color = PALETTE[value % len(PALETTE)]

    # angle: 0 = up, rotates clockwise by 360/MOD per step
    angle = math.radians(value * 360.0 / MOD)
    cos_a, sin_a = math.cos(angle), math.sin(angle)

    def rot(px, py):
        return (cx + int(px * cos_a - py * sin_a),
                cy + int(px * sin_a + py * cos_a))

    # Arrow shape pointing up (before rotation).
    # Shaft: thin rectangle from tail to arrowhead base.
    # Head: wider triangle at the tip.
    sw = r * 0.22   # half shaft width
    hw = r * 0.52   # half head width
    tip_y   = -r          # tip of the head
    head_y  =  r * 0.08   # base of the head / top of shaft
    tail_y  =  r          # bottom of shaft

    pts = [
        rot( 0,      tip_y),    # tip
        rot(-hw,     head_y),   # head left
        rot(-sw,     head_y),   # shaft top-left
        rot(-sw,     tail_y),   # shaft bottom-left
        rot( sw,     tail_y),   # shaft bottom-right
        rot( sw,     head_y),   # shaft top-right
        rot( hw,     head_y),   # head right
    ]
    pygame.draw.polygon(surf, color, pts)

async def main():
    pygame.init()
    pygame.display.set_caption("Z4 - Isomorfismo")

    def compute_tile_for_grid(grid_size):
        max_tile_w = (W - 2 * GRID_MARGIN) // grid_size
        max_tile_h = (H - PANEL_H - 2 * GRID_MARGIN) // grid_size
        return max(24, min(max_tile_w, max_tile_h))

    global TILE
    TILE = compute_tile_for_grid(GRID_SIZE)

    def grid_origin_x():
        return (W - GRID_SIZE * TILE) // 2

    screen = pygame.display.set_mode((W, H))
    clock = pygame.time.Clock()

    font = pygame.font.SysFont(None, 28)
    big = pygame.font.SysFont(None, 32)
    tiny = pygame.font.SysFont(None, 22)
    
    num_font = pygame.font.SysFont(None, max(28, int(TILE * 0.75)), bold=True)

    board = new_random_board()
    moves = 0
    solving = False
    solved = False
    move_queue = deque()
    hint_cell = None
    step_delay_ms = 260
    next_step_time = 0
    customizing = False
    in_settings = False
    show_timer = False
    show_solver_warning = False
    timer_start = 0
    timer_elapsed = 0
    timer_running = True

    arrow_mode = True

    btn_w, btn_h, gap = 145, 44, 9
    base_y = GRID_MARGIN*2 + GRID_SIZE*TILE + 18
    buttons = []

    def on_simbol():
        nonlocal arrow_mode
        arrow_mode = not arrow_mode
        simbol_btn.text = "Flechas" if arrow_mode else "Numeros"

    def on_hint():
        nonlocal hint_cell, show_solver_warning
        if solving or customizing or in_settings: 
            return
        h = next_hint(board, current_topology, current_neighborhood)
        hint_cell = h
        show_solver_warning = True
        hint_btn.text_color = (0, 200, 0)

    def on_solve():
        nonlocal solving, move_queue, next_step_time, solved, hint_cell, show_solver_warning
        if solving or solved or customizing or in_settings: 
            return
        seq = optimal_move_sequence(board, current_topology, current_neighborhood)
        if not seq: 
            return
        hint_cell = None
        show_solver_warning = True
        move_queue = deque(seq)
        solving = True
        next_step_time = pygame.time.get_ticks() + step_delay_ms
        solve_btn.text_color = (0, 200, 0)

    def on_new():
        nonlocal board, moves, solving, solved, move_queue, hint_cell, timer_start, timer_elapsed, timer_running, show_solver_warning
        if customizing or in_settings: 
            return
        board = new_random_board()
        moves = 0
        solving = False
        solved = False
        move_queue.clear()
        hint_cell = None
        show_solver_warning = False
        timer_elapsed = 0
        timer_start = pygame.time.get_ticks()
        timer_running = True
        hint_btn.text_color = BTN_TEXT
        solve_btn.text_color = BTN_TEXT

    def on_customize():
        nonlocal customizing
        customizing = not customizing
        customize_btn.text_color = (0, 200, 0) if customizing else BTN_TEXT
        for b in buttons[1:]:
            b.enabled = not customizing

    def on_settings():
        nonlocal in_settings
        in_settings = not in_settings
        # Disable other buttons when in settings
        for b in buttons:
            if b != settings_btn:
                b.enabled = not in_settings

    def on_topology_next():
        global current_topology
        topologies = ['normal', 'torus', 'cylinder', 'mobius', 'klein']
        idx = topologies.index(current_topology)
        current_topology = topologies[(idx + 1) % len(topologies)]
        update_settings_buttons()

    def on_neighborhood_next():
        global current_neighborhood
        neighborhoods = ['square', 'cross']
        idx = neighborhoods.index(current_neighborhood)
        current_neighborhood = neighborhoods[(idx + 1) % len(neighborhoods)]
        update_settings_buttons()

    def on_mod_next():
        global current_mod
        mods = [2, 3, 4, 5]
        idx = mods.index(current_mod)
        current_mod = mods[(idx + 1) % len(mods)]
        update_settings_buttons()

    def on_n_next():
        global current_n
        ns = [3, 4, 5, 6, 7]
        idx = ns.index(current_n)
        current_n = ns[(idx + 1) % len(ns)]
        update_settings_buttons()

    def on_apply_settings():
            nonlocal in_settings, board, moves, solving, solved, move_queue, hint_cell, num_font, timer_start, timer_elapsed, timer_running, show_solver_warning
            global MOD, N, GRID_SIZE, TILE, PALETTE
            # Update globals
            MOD = current_mod
            N = current_n
            GRID_SIZE = N
            PALETTE = generate_mod_palette(MOD)
            # Keep window size static; only grid/button sizing changes.
            TILE = compute_tile_for_grid(GRID_SIZE)
            num_font = pygame.font.SysFont(None, max(28, int(TILE * 0.75)), bold=True)
            relayout_buttons()
            # Reset board
            board = new_random_board()
            moves = 0
            solving = False
            solved = False
            move_queue.clear()
            hint_cell = None
            show_solver_warning = False
            timer_elapsed = 0
            timer_start = pygame.time.get_ticks()
            timer_running = True
            hint_btn.text_color = BTN_TEXT
            solve_btn.text_color = BTN_TEXT
            in_settings = False
            # Re-enable buttons
            for b in buttons:
                b.enabled = True

    def update_settings_buttons():
        topology_btn.text = f"Top: {current_topology}"
        neighborhood_btn.text = f"Vec: {current_neighborhood}"
        mod_btn.text = f"Estados: {current_mod}"
        n_btn.text = f"Tamaño: {current_n}"

    def on_timer_toggle():
        nonlocal show_timer
        show_timer = not show_timer
        timer_btn.text = "Tiempo: ON" if show_timer else "Tiempo: OFF"
        timer_btn.text_color = (0, 200, 0) if show_timer else BTN_TEXT

    def relayout_buttons():
        panel_top = GRID_MARGIN + GRID_SIZE * TILE
        local_gap = 9
        local_btn_h = 44
        usable_w = W - 2 * GRID_MARGIN
        local_btn_w = max(110, (usable_w - 2 * local_gap) // 3)
        local_base_y = panel_top + 18

        customize_btn.rect = pygame.Rect((GRID_MARGIN, local_base_y, local_btn_w, local_btn_h))
        hint_btn.rect = pygame.Rect((GRID_MARGIN, local_base_y + 50, local_btn_w, local_btn_h))
        solve_btn.rect = pygame.Rect((GRID_MARGIN + local_btn_w + local_gap, local_base_y + 50, local_btn_w, local_btn_h))
        simbol_btn.rect = pygame.Rect((GRID_MARGIN + 2 * (local_btn_w + local_gap), local_base_y, local_btn_w, local_btn_h))
        new_btn.rect = pygame.Rect((GRID_MARGIN + 2 * (local_btn_w + local_gap), local_base_y + 50, local_btn_w, local_btn_h))
        settings_btn.rect = pygame.Rect((GRID_MARGIN + local_btn_w + local_gap, local_base_y, local_btn_w, local_btn_h))

        topology_btn.rect = pygame.Rect((GRID_MARGIN, local_base_y, local_btn_w, local_btn_h))
        neighborhood_btn.rect = pygame.Rect((GRID_MARGIN + local_btn_w + local_gap, local_base_y, local_btn_w, local_btn_h))
        mod_btn.rect = pygame.Rect((GRID_MARGIN + 2 * (local_btn_w + local_gap), local_base_y, local_btn_w, local_btn_h))
        n_btn.rect = pygame.Rect((GRID_MARGIN, local_base_y + 50, local_btn_w, local_btn_h))
        apply_btn.rect = pygame.Rect((GRID_MARGIN + local_btn_w + local_gap, local_base_y + 50, local_btn_w, local_btn_h))
        back_btn.rect = pygame.Rect((GRID_MARGIN + 2 * (local_btn_w + local_gap), local_base_y + 50, local_btn_w, local_btn_h))
        timer_btn.rect = pygame.Rect((GRID_MARGIN, local_base_y + 100, local_btn_w, local_btn_h))

    simbol_btn = Button(
        (GRID_MARGIN + 2*(btn_w + gap), base_y, btn_w, btn_h),
        "Flechas", big, on_simbol
    )
    customize_btn = Button((GRID_MARGIN, base_y, btn_w, btn_h), "Personalizar", big, on_customize)
    hint_btn = Button((GRID_MARGIN, base_y + 50, btn_w, btn_h), "Pista", big, on_hint)
    solve_btn = Button((GRID_MARGIN + btn_w + gap, base_y + 50, btn_w, btn_h), "Resolver", big, on_solve)
    new_btn = Button((GRID_MARGIN + 2*(btn_w + gap), base_y + 50, btn_w, btn_h), "Nuevo", big, on_new)
    buttons.append(customize_btn)
    buttons.append(hint_btn)
    buttons.append(solve_btn)
    buttons.append(simbol_btn)
    buttons.append(new_btn)
    settings_btn = Button((GRID_MARGIN + btn_w + gap, base_y, btn_w, btn_h), "Ajustes", big, on_settings)
    buttons.append(settings_btn)

    # Settings buttons
    topology_btn = Button((GRID_MARGIN, base_y, btn_w, btn_h), f"Top: {current_topology}", big, on_topology_next)
    neighborhood_btn = Button((GRID_MARGIN + btn_w + gap, base_y, btn_w, btn_h), f"Vec: {current_neighborhood}", big, on_neighborhood_next)
    mod_btn = Button((GRID_MARGIN + 2*(btn_w + gap), base_y, btn_w, btn_h), f"Estados: {current_mod}", big, on_mod_next)
    n_btn = Button((GRID_MARGIN, base_y + 50, btn_w, btn_h), f"Tamaño: {current_n}", big, on_n_next)
    apply_btn = Button((GRID_MARGIN + btn_w + gap, base_y + 50, btn_w, btn_h), "Aplicar", big, on_apply_settings)
    back_btn = Button((GRID_MARGIN + 2*(btn_w + gap), base_y + 50, btn_w, btn_h), "Volver", big, lambda: on_settings())
    timer_btn = Button((GRID_MARGIN, base_y + 100, btn_w, btn_h), "Tiempo: OFF", big, on_timer_toggle)
    settings_buttons = [topology_btn, neighborhood_btn, mod_btn, n_btn, apply_btn, back_btn, timer_btn]
    relayout_buttons()

    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if in_settings:
                for b in settings_buttons: b.handle_event(event)
            else:
                for b in buttons: b.handle_event(event)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if solving or solved or in_settings: continue
                gx0, gy0 = grid_origin_x(), GRID_MARGIN
                gx1, gy1 = gx0 + GRID_SIZE*TILE, gy0 + GRID_SIZE*TILE
                if gx0 <= event.pos[0] < gx1 and gy0 <= event.pos[1] < gy1:
                    c = (event.pos[0] - gx0) // TILE
                    r = (event.pos[1] - gy0) // TILE
                    if customizing:
                        apply_single(board, r, c, 1)
                    else:
                        apply_press(board, r, c, 1, current_topology, current_neighborhood)
                        moves += 1
                        hint_cell = None
                        if is_solved(board):
                            solved = True
                            if timer_running:
                                timer_elapsed = pygame.time.get_ticks() - timer_start
                                timer_running = False

        if solving and pygame.time.get_ticks() >= next_step_time:
            if move_queue:
                r, c = move_queue.popleft()
                apply_press(board, r, c, 1, current_topology, current_neighborhood)
                moves += 1
                if is_solved(board) and not move_queue:
                    solving = False
                    solved = True
                    if timer_running:
                        timer_elapsed = pygame.time.get_ticks() - timer_start
                        timer_running = False
                next_step_time = pygame.time.get_ticks() + step_delay_ms
            else:
                solving = False
                solved = is_solved(board)

        screen.fill(BG)
        gx0 = grid_origin_x()
        grid_rect = pygame.Rect(gx0 - 8, GRID_MARGIN - 8, GRID_SIZE*TILE+16, GRID_SIZE*TILE+16)
        pygame.draw.rect(screen, GRID_BG, grid_rect, border_radius=12)

        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                x, y = gx0 + c*TILE, GRID_MARGIN + r*TILE
                rect = (x, y, TILE, TILE)
                pygame.draw.rect(screen, (30, 30, 40), rect, border_radius=6)
                if arrow_mode:
                    draw_arrow(screen, rect, board[r][c])
                else:
                    value = board[r][c] % MOD
                    num = str(value)
                    num_label = num_font.render(num, True, PALETTE[value % len(PALETTE)])
                    screen.blit(num_label, num_label.get_rect(center=(x + TILE//2, y + TILE//2)))
                pygame.draw.rect(screen, LINE, rect, width=2, border_radius=6)

        if hint_cell is not None:
            r, c = hint_cell
            hx, hy = gx0 + c*TILE, GRID_MARGIN + r*TILE
            pygame.draw.rect(screen, HINT_BORDER, (hx-3, hy-3, TILE+6, TILE+6), width=3, border_radius=8)
            tip = tiny.render(f"Sugerencia: clic en (fila {r+1}, columna {c+1})", True, WHITE)
            screen.blit(tip, (gx0, GRID_MARGIN + GRID_SIZE*TILE + 118))

        if show_timer:
            elapsed_ms = timer_elapsed if not timer_running else pygame.time.get_ticks() - timer_start
            total_s = elapsed_ms // 1000
            mins = total_s // 60
            secs = total_s % 60
            tenths = (elapsed_ms % 1000) // 10
            timer_label = font.render(f"Tiempo: {mins:02d}:{secs:02d}.{tenths}", True, WHITE)
            screen.blit(timer_label, (gx0, GRID_MARGIN + GRID_SIZE*TILE + 140))

        status = f"Movimientos: {moves}"
        if solving: status += "   Resolviendo..."
        elif solved: status += "   Resuelto"
        label = font.render(status, True, WHITE)
        screen.blit(label, (gx0, GRID_MARGIN + GRID_SIZE*TILE + 162))

        if show_solver_warning:
            warning_line1 = "El boton de resolver/pista"
            warning_line2 = "puede ser inexacto o provocar"
            warning_line3 = "tirones en la version actual"
            warning1 = tiny.render(warning_line1, True, (255, 200, 0))
            warning2 = tiny.render(warning_line2, True, (255, 200, 0))
            warning3 = tiny.render(warning_line3, True, (255, 200, 0))
            warn_x = gx0 + 180
            warn_y = GRID_MARGIN + GRID_SIZE*TILE + 130
            screen.blit(warning1, (warn_x, warn_y))
            screen.blit(warning2, (warn_x, warn_y + 20))
            screen.blit(warning3, (warn_x, warn_y + 40))


        # if in_settings:
        #     inst = tiny.render("Configura el modo de juego, módulo y tamaño de tablero", True, (200,200,210))
        # else:
        #     inst = tiny.render(f"Haz clic en una casilla para sumar +1 (mod {MOD}) a su vecindad 3x3", True, (200,200,210))
        # screen.blit(inst, (GRID_MARGIN - 5, GRID_MARGIN + GRID_SIZE*TILE + 15))

        if in_settings:
            for b in settings_buttons: b.draw(screen, mouse_pos)
        else:
            for b in buttons: b.draw(screen, mouse_pos)

        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)

    pygame.quit()


if __name__ == "__main__":
    asyncio.run(main())

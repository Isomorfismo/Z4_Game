# The Z4 Game

Lights Out Z₄ with Chebyshev Neighborhood

This is a variant of the classic Lights Out puzzle, implemented in Python with Pygame.
Instead of binary lights, the game uses arrows with 4 possible states (mod 4 arithmetic).

Clicking a cell rotates all arrows in its 3×3 Chebyshev neighborhood (the cell and its 8 neighbors) by +1 mod 4.
The goal is to make all arrows point up (state 0).

✨ Features

- Z₄ mechanics: each cell has 4 states instead of 2.
- Chebyshev neighborhood: pressing affects the clicked cell and its surrounding 8.
- Optimal solver: uses modular linear algebra to compute a minimum-move solution.
- Hint system: shows a recommended next move.
- Auto-solver: demonstrates the minimum sequence of moves step by step.
- Customization mode: toggleable mode that lets you rotate individual cells (without affecting neighbors) to design your own puzzles.

🎮 Controls

Click on a cell → rotate its neighborhood by +1 (mod 4).

Buttons:
- Personalize: toggle customization mode (rotate single cells only).
- Hint: show an optimal next move.
- Solve: watch the puzzle auto-solve.
- New: generate a random board.

📦 Installation

Install dependencies:
- pip install pygame


🖼️ Screenshot

<img width="615" height="877" alt="image" src="https://github.com/user-attachments/assets/b65dd8cd-3d22-4f54-b92c-f83a4fd3aac9" />
<img width="615" height="877" alt="image" src="https://github.com/user-attachments/assets/94aa9a46-95a0-4d5e-9241-3863a4bd467e" />


🧮 How It Works

The game board is a 4×4 grid with states in ℤ₄.

Pressing a cell adds +1 mod 4 to all cells in its 3×3 neighborhood.

The solver builds and inverts a mod 4 matrix system to find an optimal solution.

Customization mode is useful for testing puzzles and creating your own challenges.

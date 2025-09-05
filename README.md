# The ℤ₄ Game

Lights Out ℤ₄ with Chebyshev/Moore Neighborhood

This is a variant of the classic Lights Out puzzle, implemented in Python with Pygame.
Instead of binary lights, the game uses arrows with 4 possible states (mod 4 arithmetic).

Clicking a cell rotates all arrows in its 3×3 Chebyshev neighborhood (Moore neighborhood when $r=1$) by +1 mod 4.
The goal is to make all arrows point up (state 0).

✨ Features

- ℤ₄ mechanics: each cell has 4 states instead of 2.
- Chebyshev neighborhood: pressing affects the clicked cell and its surrounding 8.
- Optimal solver: uses modular linear algebra to compute a minimum-move solution.
- Hint system: shows a recommended next move.
- Auto-solver: demonstrates the minimum sequence of moves step by step.
- Customization mode: toggleable mode that lets you rotate individual cells (without affecting neighbors) to design your own puzzles.
- Change visualization: choose between arrows and numbers to represent the current state of the board.

🎮 Controls

Click on a cell → rotate its neighborhood by +1 (mod 4).

Buttons:
- Personalize: toggle customization mode (rotate single cells only).
- Hint: show an optimal next move.
- Solve: watch the puzzle auto-solve.
- New: generate a random board.
- Arrows/Numbers: select the representation you prefer.

📦 Installation

Install dependencies:
- pip install pygame


🖼️ Screenshot

<img width="465" height="727" alt="image" src="https://github.com/user-attachments/assets/cc13589a-47ba-4e6f-97b7-593c8c54c14a" />
<img width="465" height="727" alt="image" src="https://github.com/user-attachments/assets/41050159-c95b-48c6-9a97-d45024fc4768" />
<img width="465" height="727" alt="image" src="https://github.com/user-attachments/assets/c74d822a-a5aa-43eb-8c3c-9ada19273d9c" />
<img width="465" height="727" alt="image" src="https://github.com/user-attachments/assets/4594f48e-9431-46b4-90a1-373910708eb1" />


🧮 How It Works

The game board is a 4×4 grid with states in ℤ₄.

Pressing a cell adds +1 mod 4 to all cells in its 3×3 neighborhood.

The solver builds and inverts a mod 4 matrix system to find an optimal solution.

Customization mode is useful for testing puzzles and creating your own challenges.


### INSPIRED BY THE [EXPONENTIAL IDLE](https://conicgames.github.io/exponentialidle/) GAME.

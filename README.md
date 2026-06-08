# Color Shape Tetris

A small Pygame falling-block game inspired by Tetris. Each tetromino shape has its own color.

## Run

```powershell
pip install -r requirements.txt
python tetris.py
```

## Controls

- Left/Right: move
- Up: rotate
- Down: soft drop
- Space: hard drop
- R: restart

# Machine Learning Library GUI

This CustomTkinter app provides themed tabs for NumPy, Pandas, Matplotlib, Seaborn, Scikit-learn, PyTorch, Keras, and TensorFlow. Each tab has an input area, a run button, an output area that shows the result and final solution, and an image preview panel for chart output. Pandas, Seaborn, and Scikit-learn also include dataset upload support for CSV, TSV, TXT, JSON, XLS, and XLSX files.

## Run

```powershell
pip install -r requirements.txt
python ml_library_gui.py
```

## How to interact with the app

- Select a library tab at the top of the window.
- Enter comma-separated numbers for NumPy, Matplotlib, PyTorch, Keras, or TensorFlow.
- Enter CSV-style data for Pandas, Seaborn, or Scikit-learn, or use the upload button to select a dataset.
- Click the tab's run button.
- Review the output field for the library result and the final solution summary.
- For Matplotlib and Seaborn runs, the generated chart automatically appears in the image preview section below the output.

# Lenny's Magical Adventure

An original Pygame 2D tilemap platformer with a moonlit 8-bit ghost theme. Guide Lenny through ten increasingly difficult levels, collect classic mushroom, fire flower, star, and 1-up power-ups, and reach the ghost house at the end of each stage. The final level is a platformed boss arena where the great ghost must be stomped three times before Marco is released from his cage.

The game generates its pixel-art sprite atlas in code and uses sprite-sheet frame extraction for characters, tiles, enemies, items, and effects.

## Build and run

```powershell
pip install -r requirements.txt
python lennys_magical_adventure.py
```

## Controls

- Left/Right arrows or A/D: move
- Space, Z, or Up: jump
- X: throw fireballs while using the fire flower
- R: restart the current level
- Escape: quit

## Objective

- Collect coins and power-ups while avoiding or stomping ghosts.
- Reach the ghost house to finish levels 1 through 9.
- In level 10, use the platforms to jump on the large ghost three times.
- Avoid the boss's blue fireballs and release Marco from the cage.

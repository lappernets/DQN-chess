## Installation

### Prerequisites

Ensure you have Python installed (recommended version: 3.8 or higher).

### Install Dependencies

Run the following command to install all required dependencies:

```bash
pip install -r requirements.txt
```

## Running the Game

1. Run the `menu_gui.py` script:
   ```bash
   python menu_gui.py
   ```
2. Click on the **Setup** button to generate the neural network file for the engine.
3. Click **Start** to launch the game.

## Features

- Play chess with a graphical interface using PyQt.
- AI opponent powered by Lc0 (Leela Chess Zero).
- Supports move validation, checkmate detection, and castling.
- Stores completed games in `.pgn` format.
- Uses `.pgn` files to train a neural network (`.h5`) for improved AI performance.

## File Structure

- `menu_gui.py` - Main script to launch the GUI.
- `requirements.txt` - Contains all dependencies required to run the project.
- `train/` - Directory where `.pgn` files are stored after each game.

## Contributions

Feel free to contribute by submitting issues and pull requests.

## License

This project is open-source and available under the MIT License.

---

Developed by Adithya J Menon,Aiswarya Shine

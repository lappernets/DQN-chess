import sys
import os
import chess
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.losses import MeanSquaredError  # Thêm dòng này

class ChessEngine:
    def __init__(self, model_path="chess_model.h5"):
        self.model = self.load_model(model_path)
        self.max_action_size = 218

    def load_model(self, model_path):
        """Load the trained model with error handling"""
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        try:
            # Custom objects for loading the model
            custom_objects = {
                'MeanSquaredError': MeanSquaredError
            }
            model = load_model(model_path, custom_objects=custom_objects)
            print(f"Successfully loaded model from {model_path}")
            return model
        except Exception as e:
            raise Exception(f"Error loading model: {str(e)}")

    def board_to_state(self, board):
        """Convert board position to neural network input state"""
        input_array = np.zeros((8, 8, 12))
        piece_map = board.piece_map()
        
        for square, piece in piece_map.items():
            row, col = divmod(square, 8)
            input_array[row, col, piece.piece_type - 1] = 1 if piece.color == chess.WHITE else -1
        
        return input_array.flatten().reshape(1, -1)

    def get_best_move(self, board):
        """Get the best move for the current position"""
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return None

        try:
            state = self.board_to_state(board)
            q_values = self.model.predict(state, verbose=0)[0]
            
            move_scores = {}
            for i, move in enumerate(legal_moves):
                if i < len(q_values):
                    move_scores[move] = q_values[i]
                else:
                    move_scores[move] = float('-inf')

            best_move = max(move_scores.items(), key=lambda x: x[1])[0]
            return best_move
        except Exception as e:
            print(f"Error in get_best_move: {str(e)}")
            return legal_moves[0]  # Return first legal move as fallback

def main():
    try:
        # Initialize engine with explicit model path
        model_path = os.path.abspath(r"c:\Users\Linhl\Downloads\Terminator-main\chess_model.h5")
        engine = ChessEngine(model_path)
        
        # Start UCI loop
        board = chess.Board()
        while True:
            try:
                command = input().strip()
            except EOFError:
                break

            if command == "uci":
                print("uciok")
            elif command == "isready":
                print("readyok")
            elif command == "ucinewgame":
                board = chess.Board()
            elif command.startswith("position"):
                parts = command.split()
                if "startpos" in parts:
                    board = chess.Board()
                elif "fen" in parts:
                    fen_index = parts.index("fen") + 1
                    fen = " ".join(parts[fen_index:fen_index+6])
                    board = chess.Board(fen)
                
                if "moves" in parts:
                    moves_index = parts.index("moves") + 1
                    for move in parts[moves_index:]:
                        board.push_uci(move)
            elif command.startswith("go"):
                try:
                    best_move = engine.get_best_move(board)
                    if best_move:
                        print(f"bestmove {best_move.uci()}")
                    else:
                        print("bestmove 0000")
                except Exception as e:
                    print(f"info string Error: {str(e)}")
                    print("bestmove 0000")
            elif command == "quit":
                break

    except Exception as e:
        print(f"Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
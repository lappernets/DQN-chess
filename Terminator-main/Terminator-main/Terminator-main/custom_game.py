
import pygame
import chess
import os
import logging
from engine import ChessEngine

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 800, 800
SIDE_PANEL_WIDTH = 300
SQUARE_SIZE = WIDTH // 8
WHITE, BLACK = (255, 255, 255), (0, 0, 0)
LIGHT_SQUARE = (238, 238, 210)
DARK_SQUARE = (118, 150, 86)
HIGHLIGHT_COLOR = (186, 202, 68)
MOVE_HIGHLIGHT = (214, 214, 189)
LAST_MOVE_HIGHLIGHT = (205, 210, 106)

# Create screen
screen = pygame.display.set_mode((WIDTH + SIDE_PANEL_WIDTH, HEIGHT))
pygame.display.set_caption("Chess vs AI")

# Load piece images
IMAGE_PATH = os.path.join(os.path.dirname(__file__), "images")
piece_images = {}
piece_names = {'p': 'pawn', 'r': 'rook', 'n': 'knight', 'b': 'bishop', 'q': 'queen', 'k': 'king'}

for piece, name in piece_names.items():
    for color in ['w', 'b']:
        try:
            image = pygame.image.load(os.path.join(IMAGE_PATH, f'{color}_{name}.png'))
            piece_images[f'{color}{piece}'] = pygame.transform.scale(image, (SQUARE_SIZE - 20, SQUARE_SIZE - 20))
        except Exception as e:
            logging.error(f"Failed to load image {color}_{name}.png: {str(e)}")

class ChessGame:
    def __init__(self):
        self.board = chess.Board()
        self.selected_square = None
        self.game_over = False
        self.winner = ""
        self.player_color = None
        self.last_move = None
        self.move_list = []
        self.font = pygame.font.SysFont('Arial', 20)
        self.thinking = False
        
        # Initialize AI engine with correct path
        try:
            model_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            model_path = os.path.join(model_dir, "chess_model.h5")
            
            if not os.path.exists(model_path):
                self.show_error_message("Model not found", 
                    f"Model not found at:\n{model_path}\nPlease train the model first!")
                pygame.quit()
                exit()
            
            logging.info(f"Loading model from: {model_path}")
            self.engine = ChessEngine(model_path)
            
        except Exception as e:
            logging.error(f"Failed to initialize AI: {str(e)}")
            self.show_error_message("Error", f"Failed to initialize AI: {str(e)}")
            pygame.quit()
            exit()
        
        self.choose_color()

    def show_error_message(self, title, message):
        screen = pygame.display.set_mode((400, 200))
        pygame.display.set_caption(title)
        
        running = True
        while running:
            screen.fill((240, 240, 240))
            
            font = pygame.font.SysFont('Arial', 20)
            lines = message.split('\n')
            y = 50
            for line in lines:
                text = font.render(line, True, (0, 0, 0))
                text_rect = text.get_rect(center=(200, y))
                screen.blit(text, text_rect)
                y += 30
            
            ok_btn = pygame.draw.rect(screen, (200, 200, 200), (150, 130, 100, 40))
            ok_text = font.render("OK", True, (0, 0, 0))
            ok_rect = ok_text.get_rect(center=(200, 150))
            screen.blit(ok_text, ok_rect)
            
            pygame.display.flip()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if ok_btn.collidepoint(event.pos):
                        running = False

    def choose_color(self):
        screen = pygame.display.set_mode((400, 200))
        pygame.display.set_caption("Choose Your Color")
        
        running = True
        while running:
            screen.fill((240, 240, 240))
            
            white_btn = pygame.draw.rect(screen, (255, 255, 255), (50, 70, 100, 50))
            black_btn = pygame.draw.rect(screen, (100, 100, 100), (250, 70, 100, 50))
            
            font = pygame.font.SysFont('Arial', 24)
            text = font.render("Choose your color:", True, (0, 0, 0))
            white_text = font.render("White", True, (0, 0, 0))
            black_text = font.render("Black", True, (255, 255, 255))
            
            screen.blit(text, (100, 20))
            screen.blit(white_text, (60, 80))
            screen.blit(black_text, (260, 80))
            
            pygame.display.flip()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if white_btn.collidepoint(event.pos):
                        self.player_color = True
                        running = False
                    elif black_btn.collidepoint(event.pos):
                        self.player_color = False
                        running = False
        
        screen = pygame.display.set_mode((WIDTH + SIDE_PANEL_WIDTH, HEIGHT))
        pygame.display.set_caption("Chess vs AI")

    def show_promotion_dialog(self, square):
        """Hiển thị dialog cho người chơi chọn quân khi phong cấp"""
        dialog_width, dialog_height = 400, 150
        dialog_x = (WIDTH - dialog_width) // 2
        dialog_y = (HEIGHT - dialog_height) // 2
        
        # Lưu màn hình hiện tại
        current_screen = screen.copy()
        
        # Vẽ dialog
        dialog_surface = pygame.Surface((dialog_width, dialog_height))
        dialog_surface.fill((240, 240, 240))
        
        # Tạo các nút cho từng quân cờ có thể chọn
        piece_types = [chess.QUEEN, chess.ROOK, chess.KNIGHT, chess.BISHOP]
        piece_names = ['queen', 'rook', 'knight', 'bishop']
        buttons = []
        button_width = 80
        spacing = (dialog_width - len(piece_types) * button_width) // (len(piece_types) + 1)
        
        color_prefix = 'w' if self.player_color else 'b'
        
        for i, (piece_type, piece_name) in enumerate(zip(piece_types, piece_names)):
            x = spacing + i * (button_width + spacing)
            y = 40
            piece_img = piece_images[f'{color_prefix}{piece_name[0]}']
            buttons.append((pygame.Rect(x, y, button_width, button_width), piece_type, piece_img))
        
        # Hiển thị dialog
        running = True
        chosen_piece = None
        
        while running:
            # Vẽ màn hình gốc
            screen.blit(current_screen, (0, 0))
            
            # Vẽ dialog
            screen.blit(dialog_surface, (dialog_x, dialog_y))
            
            # Vẽ tiêu đề
            title = self.font.render("Choose promotion piece:", True, (0, 0, 0))
            screen.blit(title, (dialog_x + 10, dialog_y + 10))
            
            # Vẽ các nút quân cờ
            for button, _, piece_img in buttons:
                button.x += dialog_x
                button.y += dialog_y
                pygame.draw.rect(screen, (200, 200, 200), button)
                screen.blit(piece_img, (button.x + (button_width - piece_img.get_width()) // 2,
                                      button.y + (button_width - piece_img.get_height()) // 2))
                button.x -= dialog_x
                button.y -= dialog_y
            
            pygame.display.flip()
            
            for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    for button, piece_type, _ in buttons:
                        button_rect = button.copy()
                        button_rect.x += dialog_x
                        button_rect.y += dialog_y
                        if button_rect.collidepoint(mouse_pos):
                            chosen_piece = piece_type
                            running = False
                            break
        
        return chosen_piece
    def handle_click(self, pos):
        if self.game_over:
            # Check for click to reset game
            if (WIDTH//4 <= pos[0] <= 3*WIDTH//4 and 
                HEIGHT//2 + 30 <= pos[1] <= HEIGHT//2 + 70):
                # Reset game state
                self.board = chess.Board()
                self.selected_square = None
                self.game_over = False
                self.winner = ""
                self.last_move = None
                self.move_list = []
                
                # Choose color again
                self.choose_color()
                
                # If AI plays white and player chooses black
                if not self.player_color:
                    self.make_ai_move()
                    
                return

        if self.thinking or self.board.turn != self.player_color:
            return

        if not (0 <= pos[0] < WIDTH and 0 <= pos[1] < HEIGHT):
            return

        col, row = pos[0] // SQUARE_SIZE, pos[1] // SQUARE_SIZE

        # Flip the coordinates if playing as Black
        if not self.player_color:
            col, row = 7 - col, 7 - row

        square = chess.square(col, 7 - row)

        if self.selected_square is None:
            piece = self.board.piece_at(square)
            if piece and piece.color == self.player_color:
                self.selected_square = square
        else:
            move = chess.Move(self.selected_square, square)
            
            # Check if it's a pawn promotion move
            piece = self.board.piece_at(self.selected_square)
            if piece and piece.piece_type == chess.PAWN:
                # For white pawns reaching 8th rank (rank 7 in 0-based)
                # For black pawns reaching 1st rank (rank 0 in 0-based)
                target_rank = chess.square_rank(square)
                if ((self.player_color and target_rank == 7) or 
                    (not self.player_color and target_rank == 0)):
                    # Show promotion dialog
                    promotion_piece = self.show_promotion_dialog(square)
                    if promotion_piece:
                        # Create promotion move
                        move = chess.Move(self.selected_square, square, promotion=promotion_piece)
                    else:
                        # User cancelled promotion, keep the piece selected
                        return
            
            if move in self.board.legal_moves:
                self.board.push(move)
                self.last_move = move
                self.move_list.append(move.uci())
                self.check_game_over()
                if not self.game_over:
                    self.make_ai_move()
            self.selected_square = None
            
    def make_ai_move(self):
        if not self.game_over and self.board.turn != self.player_color:
            self.thinking = True
            try:
                best_move = self.engine.get_best_move(self.board)
                if best_move and best_move in self.board.legal_moves:
                    # Kiểm tra nếu là nước đi phong cấp
                    if best_move.promotion:
                        # Nếu AI đi tới hàng cuối, chọn quân cờ phong cấp dựa trên trọng số
                        promotion_piece = self.get_best_promotion_piece(best_move)
                        best_move = chess.Move(best_move.from_square, best_move.to_square, promotion=promotion_piece)
                    
                    self.board.push(best_move)
                    self.last_move = best_move
                    self.move_list.append(best_move.uci())
                    self.check_game_over()
            except Exception as e:
                logging.error(f"AI Error: {str(e)}")
            finally:
                self.thinking = False

    def get_best_promotion_piece(self, move):
        # Trọng số của từng quân cờ
        piece_weights = {
            chess.QUEEN: 9,
            chess.ROOK: 5,
            chess.KNIGHT: 3,
            chess.BISHOP: 3
        }
        
        # Lấy vị trí của quân cờ phong cấp
        to_square = move.to_square
        
        # Lấy màu của quân cờ phong cấp
        color = self.board.turn
        
        # Tạo một bản sao của bàn cờ
        board_copy = self.board.copy()
        
        # Thử từng quân cờ phong cấp
        best_piece = None
        best_score = -float('inf')
        for piece in [chess.QUEEN, chess.ROOK, chess.KNIGHT, chess.BISHOP]:
            # Đặt quân cờ phong cấp lên bàn cờ
            board_copy.push(chess.Move(move.from_square, to_square, promotion=piece))
            
            # Đánh giá vị trí của quân cờ phong cấp
            score = self.evaluate_position(board_copy, color)
            
            # Cập nhật trọng số của quân cờ phong cấp
            score += piece_weights[piece]
            
            # Kiểm tra nếu đây là quân cờ phong cấp tốt nhất
            if score > best_score:
                best_score = score
                best_piece = piece
            
            # Undo nước đi
            board_copy.pop()
        
        return best_piece

    def evaluate_position(self, board, color):
        # Đánh giá vị trí của quân cờ trên bàn cờ
        # Đây là một hàm đánh giá đơn giản, bạn có thể thay thế bằng một hàm đánh giá phức tạp hơn
        score = 0
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece and piece.color == color:
                if piece.piece_type == chess.PAWN:
                    score += 1
                elif piece.piece_type == chess.KNIGHT or piece.piece_type == chess.BISHOP:
                    score += 3
                elif piece.piece_type == chess.ROOK:
                    score += 5
                elif piece.piece_type == chess.QUEEN:
                    score += 9
        return score
                
    def draw_board(self):
        for row in range(8):
            for col in range(8):
                # Flip the board if playing as Black
                display_row = 7 - row if not self.player_color else row
                display_col = 7 - col if not self.player_color else col
                
                color = LIGHT_SQUARE if (display_row + display_col) % 2 == 0 else DARK_SQUARE
                pygame.draw.rect(screen, color, 
                                (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

                square = chess.square(display_col, 7 - display_row)
                if self.selected_square == square:
                    self.highlight_square(col, row, HIGHLIGHT_COLOR)
                elif self.selected_square is not None:
                    move = chess.Move(self.selected_square, square)
                    if move in self.board.legal_moves:
                        self.highlight_square(col, row, MOVE_HIGHLIGHT)

                if self.last_move:
                    if square in [self.last_move.from_square, self.last_move.to_square]:
                        self.highlight_square(col, row, LAST_MOVE_HIGHLIGHT)
                                              
    def draw_pieces(self):
        for row in range(8):
            for col in range(8):
                # Flip the board if playing as Black
                display_row = 7 - row if not self.player_color else row
                display_col = 7 - col if not self.player_color else col
                
                piece = self.board.piece_at(chess.square(display_col, 7 - display_row))
                if piece:
                    piece_key = ('w' if piece.color else 'b') + piece.symbol().lower()
                    if piece_key in piece_images:
                        piece_img = piece_images[piece_key]
                        x = col * SQUARE_SIZE + (SQUARE_SIZE - piece_img.get_width()) // 2
                        y = row * SQUARE_SIZE + (SQUARE_SIZE - piece_img.get_height()) // 2
                        screen.blit(piece_img, (x, y))
                        
    def draw_side_panel(self):
        # Background
        pygame.draw.rect(screen, (240, 240, 240), 
                        (WIDTH, 0, SIDE_PANEL_WIDTH, HEIGHT))
        
        # Game information
        turn_text = "White" if self.board.turn else "Black"
        self.draw_text(f"Turn: {turn_text}", (WIDTH + 10, 10))
        self.draw_text(f"Playing as: {'White' if self.player_color else 'Black'}", 
                      (WIDTH + 10, 40))
        
        # Thinking status
        if self.thinking:
            self.draw_text("AI is thinking...", (WIDTH + 10, 70), (150, 0, 0))

        # Move list
        self.draw_text("Move History:", (WIDTH + 10, 100))
        for i, move in enumerate(self.move_list):
            y = 130 + i * 25
            if y < HEIGHT - 30:
                self.draw_text(f"{i+1}. {move}", (WIDTH + 10, y))

    def draw_text(self, text, pos, color=(0, 0, 0)):
        text_surface = self.font.render(text, True, color)
        screen.blit(text_surface, pos)

    def draw_game_over(self):
        s = pygame.Surface((WIDTH, HEIGHT))
        s.set_alpha(128)
        s.fill((0, 0, 0))
        screen.blit(s, (0, 0))
        
        font = pygame.font.SysFont('Arial', 48)
        text = font.render(self.winner, True, WHITE)
        text_rect = text.get_rect(center=(WIDTH//2, HEIGHT//2))
        screen.blit(text, text_rect)

        # Add restart button with hover effect
        restart_font = pygame.font.SysFont('Arial', 24)
        restart_text = restart_font.render("Click to play again", True, WHITE)
        restart_rect = restart_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 50))
        
        # Kiểm tra hover
        mouse_pos = pygame.mouse.get_pos()
        if restart_rect.inflate(20, 10).collidepoint(mouse_pos):
            # Hiệu ứng hover
            pygame.draw.rect(screen, (100, 100, 100), restart_rect.inflate(20, 10), border_radius=10)
        
        screen.blit(restart_text, restart_rect)

    def highlight_square(self, col, row, color):
        s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE))
        s.set_alpha(128)
        s.fill(color)
        screen.blit(s, (col * SQUARE_SIZE, row * SQUARE_SIZE))

    def make_ai_move(self):
        if not self.game_over and self.board.turn != self.player_color:
            self.thinking = True
            try:
                best_move = self.engine.get_best_move(self.board)
                if best_move and best_move in self.board.legal_moves:
                    self.board.push(best_move)
                    self.last_move = best_move
                    self.move_list.append(best_move.uci())
                    self.check_game_over()
            except Exception as e:
                logging.error(f"AI Error: {str(e)}")
            finally:
                self.thinking = False


    def check_game_over(self):
        if self.board.is_checkmate():
            self.game_over = True
            winner_color = "White" if not self.board.turn else "Black"
            self.winner = f"{winner_color} wins by checkmate!"
        elif self.board.is_stalemate():
            self.game_over = True
            self.winner = "Draw by stalemate"
        elif self.board.is_insufficient_material():
            self.game_over = True
            self.winner = "Draw by insufficient material"
        elif self.board.is_fifty_moves():
            self.game_over = True
            self.winner = "Draw by fifty-move rule"
        elif self.board.is_repetition():
            self.game_over = True
            self.winner = "Draw by repetition"

def main():
    try:
        game = ChessGame()
        clock = pygame.time.Clock()
        
        if not game.player_color:
            game.make_ai_move()

        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    game.handle_click(pygame.mouse.get_pos())

            game.draw_board()
            game.draw_pieces()
            game.draw_side_panel()
            if game.game_over:
                game.draw_game_over()
            
            pygame.display.flip()
            clock.tick(60)

    except Exception as e:
        logging.error(f"Game Error: {str(e)}")
    finally:
        pygame.quit()

if __name__ == "__main__":
    main()
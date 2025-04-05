import os
import chess
import chess.pgn
import numpy as np
import json
import logging
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.optimizers import Adam
import random
from collections import deque
from tensorflow.keras.losses import MeanSquaredError
import lime
import lime.lime_tabular
import shap
import matplotlib.pyplot as plt

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("training.log"),
        logging.StreamHandler()
    ]
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TRAIN_FOLDER = os.path.join(BASE_DIR, "train")
MODEL_PATH = "chess_model.h5"
Q_VALUES_PATH = "q_values_analysis.json"

class ModelExplainer:
    def __init__(self, model, state_size):
        self.model = model
        self.state_size = state_size
        self.feature_names = [
            f'Piece_{i//64}_{(i%64)//8}_{(i%64)%8}' for i in range(state_size)
        ]
        
    def explain_with_lime(self, state, legal_moves_count, env):
        """
        Use LIME to explain the model's decision
        """
        try:
            # Predict Q-values
            q_values = self.model.predict(state)[0]
            valid_q_values = q_values[:legal_moves_count]
            
            # Simple prediction function
            def predict_fn(X):
                return self.model.predict(X)
            
            # Sample data for LIME
            training_data = np.random.rand(100, self.state_size)
            
            # Create LIME explainer
            explainer = lime.lime_tabular.LimeTabularExplainer(
                training_data=training_data,
                feature_names=self.feature_names,
                class_names=[f'Action_{i}' for i in range(legal_moves_count)],
                mode='regression',
                verbose=True
            )
            
            # Explain each move
            explanations = {}
            for action in range(legal_moves_count):
                try:
                    explanation = explainer.explain_instance(
                        state[0], 
                        predict_fn, 
                        num_features=10,  # Limit to top 10 features
                        labels=(action,)
                    )
                    
                    # Filter and sort important features
                    important_features = [
                        (feat, imp) for feat, imp in explanation.as_list() 
                        if abs(imp) > 0.01
                    ]
                    important_features.sort(key=lambda x: abs(x[1]), reverse=True)
                    
                    # Get move details
                    move = env.action_to_move(action)
                    player_color = 'White' if env.board.turn == chess.WHITE else 'Black'
                    
                    explanations[str(action)] = {
                        'q_value': float(valid_q_values[action]),
                        'move': move,
                        'player': player_color,
                        'explanation': [
                            [str(feat), float(imp)] for feat, imp in important_features
                        ]
                    }
                    
                    # Print detailed explanation
                    print(f"\nAction {action} Explanation:")
                    print(f"Player: {player_color}")
                    print(f"Q-Value: {valid_q_values[action]:.4f}")
                    print("Top Influential Features:")
                    for feat, imp in important_features:
                        print(f"  {feat}: {imp:.4f}")
                
                except Exception as action_error:
                    print(f"Error explaining action {action}: {action_error}")
                    explanations[str(action)] = {
                        'q_value': float(valid_q_values[action]),
                        'player': "Unknown",
                        'explanation': []
                    }
            
            return explanations
        
        except Exception as e:
            logging.error(f"LIME explanation error: {str(e)}")
            return None
        
    def explain_with_shap(self, states):
        """
        Sử dụng SHAP để phân tích tầm quan trọng của features
        """
        try:
            # Tạo thư mục để lưu ảnh nếu chưa tồn tại
            explanation_dir = os.path.join(BASE_DIR, 'explanations')
            os.makedirs(explanation_dir, exist_ok=True)
            
            # Tạo SHAP explainer
            explainer = shap.KernelExplainer(self.model.predict, states[:100])
            shap_values = explainer.shap_values(states[:10])
            
            # Tạo summary plot
            plt.figure(figsize=(10, 6))
            shap.summary_plot(shap_values, states[:10], plot_type="bar")
            plt.title("SHAP Feature Importance")
            plt.tight_layout()
            
            # Lưu ảnh vào thư mục explanations
            shap_plot_path = os.path.join(explanation_dir, 'shap_feature_importance.png')
            plt.savefig(shap_plot_path)
            plt.close()
            
            logging.info(f"SHAP feature importance plot saved to {shap_plot_path}")
            
            return shap_values
        
        except Exception as e:
            logging.error(f"SHAP analysis error: {str(e)}")
            return None

    def save_lime_explanations(self, explanations, filename='lime_explanations.json'):
        """
        Lưu giải thích LIME vào file JSON
        """
        try:
            # Chuyển đổi các giá trị numpy thành float
            serializable_explanations = {}
            for action, data in explanations.items():
                serializable_explanations[action] = {
                    'q_value': float(data['q_value']),
                    'explanation': [
                        (str(feat), float(imp)) for feat, imp in data['explanation']
                    ]
                }
            
            with open(filename, 'w') as f:
                json.dump(serializable_explanations, f, indent=4)
            
            logging.info(f"LIME explanations saved to {filename}")
        
        except Exception as e:
            logging.error(f"Error saving LIME explanations: {str(e)}")
            
    def visualize_lime_explanations(self, explanations):
        """
        Create visualization for LIME explanations
        """
        explanation_dir = os.path.join(BASE_DIR, 'explanations')
        os.makedirs(explanation_dir, exist_ok=True)
        
        for action, details in explanations.items():
            features = [feat for feat, _ in details['explanation']]
            importances = [imp for _, imp in details['explanation']]
            
            plt.figure(figsize=(12, 6))
            plt.bar(features, importances, color='skyblue')
            plt.title(f'Feature Importance for Action {action}')
            plt.xlabel('Features')
            plt.ylabel('Importance')
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            lime_plot_path = os.path.join(explanation_dir, f'lime_explanation_action_{action}.png')
            plt.savefig(lime_plot_path)
            plt.close()
            
            logging.info(f"LIME explanation plot for action {action} saved to {lime_plot_path}")
            
class QValuesAnalyzer:
    def __init__(self):
        self.q_values_history = []
        self.analysis_results = {
            'total_episodes': 0,
            'avg_max_q_value': 0,
            'avg_min_q_value': 0,
            'avg_mean_q_value': 0,
            'q_value_variance': 0,
            'action_distribution': {}
        }

    def analyze_q_values(self, q_values, legal_moves_count):
        """
        Phân tích chi tiết Q-values
        """
        # Cắt Q-values theo số nước đi hợp lệ
        valid_q_values = q_values[:legal_moves_count]
        
        q_values_info = {
            'max_q_value': float(np.max(valid_q_values)),
            'min_q_value': float(np.min(valid_q_values)),
            'mean_q_value': float(np.mean(valid_q_values)),
            'median_q_value': float(np.median(valid_q_values)),
            'std_q_value': float(np.std(valid_q_values))
        }
        
        # Lưu vào lịch sử
        self.q_values_history.append(q_values_info)
        
        return q_values_info

    def update_analysis_results(self):
        """
        Cập nhật kết quả phân tích tổng thể
        """
        if not self.q_values_history:
            return
        
        # Tính toán các chỉ số tổng thể
        q_max_values = [entry['max_q_value'] for entry in self.q_values_history]
        q_min_values = [entry['min_q_value'] for entry in self.q_values_history]
        q_mean_values = [entry['mean_q_value'] for entry in self.q_values_history]
        
        self.analysis_results.update({
            'total_episodes': len(self.q_values_history),
            'avg_max_q_value': float(np.mean(q_max_values)),
            'avg_min_q_value': float(np.mean(q_min_values)),
            'avg_mean_q_value': float(np.mean(q_mean_values)),
            'q_value_variance': float(np.var(q_mean_values))
        })

    def save_analysis(self, filename=Q_VALUES_PATH):
        """
        Lưu kết quả phân tích vào file JSON
        """
        try:
            with open(filename, 'w') as f:
                json.dump(self.analysis_results, f, indent=4)
            logging.info(f"Q-values analysis saved to {filename}")
        except Exception as e:
            logging.error(f"Error saving Q-values analysis: {str(e)}")

class ChessEnvironment:
    def __init__(self):
        self.board = chess.Board()
        self.legal_moves = None
        self.update_legal_moves()

    def action_to_move(self, action_idx):
        """
        Chuyển đổi action index sang ký hiệu nước đi trong cờ vua
        
        Args:
            action_idx (int): Chỉ số của nước đi
        
        Returns:
            str: Ký hiệu nước đi (ví dụ 'E2E4')
        """
        if 0 <= action_idx < len(self.legal_moves):
            move = self.legal_moves[action_idx]
            return move.uci()
        return "Invalid Move"

    def get_state(self):
        """Return the current state as a flattened array"""
        input_array = np.zeros((8, 8, 12))
        piece_map = self.board.piece_map()
        
        for square, piece in piece_map.items():
            row, col = divmod(square, 8)
            input_array[row, col, piece.piece_type - 1] = 1 if piece.color == chess.WHITE else -1
        
        return input_array.flatten()

    def update_legal_moves(self):
        """Update the list of legal moves"""
        self.legal_moves = list(self.board.legal_moves)
        return len(self.legal_moves)

    def reset(self):
        """Reset the board and return the initial state"""
        self.board = chess.Board()
        self.update_legal_moves()
        return self.get_state()

    def step(self, action_idx):
        """Execute a move and return the next state, reward, and done flag"""
        if action_idx >= len(self.legal_moves):
            logging.warning("Invalid action index selected.")
            return self.get_state(), -10, True  # Invalid move penalty
        
        move = self.legal_moves[action_idx]
        
        # Handle promotion moves
        if move.promotion:
            move = chess.Move(move.from_square, move.to_square, promotion=chess.QUEEN)
        
        self.board.push(move)
        self.update_legal_moves()
        
        done = self.board.is_game_over()
        reward = self._calculate_reward(move)
        
        # Log the move and reward
        current_player = 'White' if self.board.turn == chess.BLACK else 'Black'
        logging.info(f"{current_player} executed move: {move.uci()}")
        
        return self.get_state(), reward, done

    def _calculate_reward(self, move):
        """Tính toán phần thưởng cho nước đi"""
        if self.board.is_game_over():
            if self.board.is_checkmate():
                return -2 if self.board.turn else 1  # Thua hoặc thắng
            
            # Các trường hợp hòa
            return 0.5

        # Các phần thưởng bổ sung
        reward = 0

        # Thưởng cho việc kiểm soát trung tâm
        center_squares = [chess.D4, chess.D5, chess.E4, chess.E5]
        if move.to_square in center_squares:
            reward += 0.1

        # Thưởng cho việc phát triển quân
        developing_squares = [
            chess.B1, chess.G1,  # Mã trắng
            chess.B8, chess.G8,  # Mã đen
            chess.C1, chess.F1,  # Tượng trắng
            chess.C8, chess.F8   # Tượng đen
        ]
        if move.to_square in developing_squares:
            reward += 0.2

        # Phạt cho việc di chuyển vua quá sớm
        piece = self.board.piece_at(move.from_square)
        if piece and piece.piece_type == chess.KING and len(self.board.move_stack) < 10:
            reward -= 0.3

        return reward

class DQNAgent:
    def __init__(self, state_size, max_action_size):
        self.state_size = state_size
        self.max_action_size = max_action_size
        self.memory = deque(maxlen=2000)
        self.gamma = 0.95
        self.epsilon = 1.0
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.learning_rate = 0.001
        self.model = self.build_model()
        
        # Thêm Q-values analyzer
        self.q_values_analyzer = QValuesAnalyzer()

    def build_model(self):
        model = Sequential([
            Dense(128, activation='relu', input_shape=(self.state_size,)),
            Dense(64, activation='relu'),
            Dense(self.max_action_size, activation='linear')
        ])
        model.compile(optimizer=Adam(learning_rate=self.learning_rate),
                     loss=MeanSquaredError())
        return model
    
    def remember(self, state, action, reward, next_state, done):
        """Lưu trữ trải nghiệm vào bộ nhớ"""
        self.memory.append((state, action, reward, next_state, done))

    def act(self, state, legal_moves_count, env):
        """
        Chọn hành động và phân tích Q-values
        
        Args:
            state: Trạng thái hiện tại
            legal_moves_count: Số lượng nước đi hợp lệ
            env: Môi trường chess để chuyển đổi action sang nước đi
        """
        if np.random.rand() <= self.epsilon:
            action = random.randrange(legal_moves_count)
            return action
        
        # Dự đoán Q-values
        act_values = self.model.predict(state, verbose=0)[0]
        
        # Phân tích Q-values
        q_values_info = self.q_values_analyzer.analyze_q_values(act_values, legal_moves_count)
        logging.info(f"Q-values analysis: {q_values_info}")
        
        # Chọn hành động có Q-value cao nhất
        action = np.argmax(act_values[:legal_moves_count])
        
        # Xác định người chơi hiện tại
        current_player = 'w' if env.board.turn == chess.WHITE else 'b'
        
        # Chuyển đổi action sang nước đi cụ thể
        chess_move = env.action_to_move(action)
        logging.info(f"Exploitation: {current_player} selected move {chess_move}")
        
        return action

    def replay(self, batch_size):
        """Huấn luyện mô hình từ các trải nghiệm"""
        if len(self.memory) < batch_size:
            return

        minibatch = random.sample(self.memory, batch_size)
        states = np.array([i[0] for i in minibatch])
        actions = np.array([i[1] for i in minibatch])
        rewards = np.array([i[2] for i in minibatch])
        next_states = np.array([i[3] for i in minibatch])
        dones = np.array([i[4] for i in minibatch])

        states = np.squeeze(states)
        next_states = np.squeeze(next_states)

        # Tính toán mục tiêu
        targets = rewards + self.gamma * (np.amax(self.model.predict(next_states, verbose=0), axis=1)) * (1 - dones)
        targets_full = self.model.predict(states, verbose=0)

        # Cập nhật Q-values
        ind = np.array([i for i in range(batch_size)])
        targets_full[[ind], [actions]] = targets

        # Huấn luyện mô hình
        self.model.fit(states, targets_full, epochs=1, verbose=0)

        # Giảm dần tỷ lệ khám phá
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

def main():
    # Initialize environment and agent
    env = ChessEnvironment()
    state_size = 8 * 8 * 12
    max_action_size = 218
    agent = DQNAgent(state_size, max_action_size)

    # Khởi tạo ModelExplainer
    model_explainer = ModelExplainer(agent.model, state_size)

    # Training parameters
    episodes = 1000
    batch_size = 32
    explanation_interval = 100  # Thực hiện giải thích sau mỗi 100 episode

    logging.info("Starting training...")

    for e in range(episodes):
        # Hiện rõ game thứ mấy
        print(f"\n=== Game {e+1}/{episodes} ===")

        state = env.reset()
        state = np.reshape(state, [1, state_size])
        total_reward = 0
        moves_made = 0
        done = False

        while not done:
            legal_moves_count = len(env.legal_moves)
            action = agent.act(state, legal_moves_count, env)
            
            # Chuyển đổi action sang nước đi
            chess_move = env.action_to_move(action)
            
            # Xác định người chơi hiện tại
            current_player = 'w' if env.board.turn == chess.WHITE else 'b'
            
            # Logging nước đi
            if np.random.rand() <= agent.epsilon:
                logging.info(f"Random exploration: {current_player} selected move {chess_move}")
            
            next_state, reward, done = env.step(action)
            next_state = np.reshape(next_state, [1, state_size])
            
            agent.remember(state, action, reward, next_state, done)
            state = next_state
            total_reward += reward
            moves_made += 1
            
            if len(agent.memory) > batch_size:
                agent.replay(batch_size)

            # Ngăn không cho game chạy quá lâu
            if moves_made > 300:
                break

        # Cập nhật kết quả phân tích Q-values
        agent.q_values_analyzer.update_analysis_results()

       # Thực hiện giải thích định kỳ
        print(f"\n=== Analyzing Game {e+1} ===")
        # LIME Explanation
        lime_explanations = model_explainer.explain_with_lime(state, legal_moves_count, env)
        if lime_explanations:
            model_explainer.save_lime_explanations(lime_explanations)
            model_explainer.visualize_lime_explanations(lime_explanations)
            
            # Print detailed explanations for each action
            for action, details in lime_explanations.items():
                print(f"\nAction {action} Explanation:")
                print(f"Move: {details['move']}")
                print(f"Q-Value: {details['q_value']:.4f}")
                print("Top Influential Features:")
                for feat, imp in details['explanation']:
                    print(f"  {feat}: {imp:.4f}")

    # Lưu mô hình và phân tích Q-values
    agent.model.save(MODEL_PATH)
    agent.q_values_analyzer.save_analysis()

    print(f"\nTraining completed!")
    print(f"Model saved to {MODEL_PATH}")
    print(f"Q-values analysis saved to {Q_VALUES_PATH}")

if __name__ == "__main__":
    main()
"""
Reinforcement Learning Trading Agent

Advanced RL agent using:
- Deep Q-Network (DQN) with experience replay
- Proximal Policy Optimization (PPO)
- Actor-Critic architecture
- Prioritized experience replay
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import random
import logging
import os
from datetime import datetime
import json

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    import torch.nn.functional as F
    from torch.distributions import Categorical
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

logger = logging.getLogger(__name__)


class TradingAction(Enum):
    HOLD = 0
    BUY = 1
    SELL = 2
    CLOSE = 3


@dataclass
class TradingState:
    """Current state of the trading environment"""
    prices: np.ndarray  # Recent price history
    position: int  # -1 (short), 0 (flat), 1 (long)
    entry_price: float
    unrealized_pnl: float
    balance: float
    indicators: Dict[str, float]

    def to_tensor(self) -> np.ndarray:
        """Convert state to neural network input"""
        features = list(self.prices[-20:])  # Last 20 prices normalized
        features.append(self.position)
        features.append(self.entry_price)
        features.append(self.unrealized_pnl)
        features.append(self.balance / 10000)  # Normalize balance

        # Add indicators
        for key in ['rsi', 'macd', 'bb_position', 'atr_ratio', 'momentum']:
            features.append(self.indicators.get(key, 0))

        return np.array(features, dtype=np.float32)


@dataclass
class Experience:
    """Single experience for replay buffer"""
    state: np.ndarray
    action: int
    reward: float
    next_state: np.ndarray
    done: bool


class PrioritizedReplayBuffer:
    """Experience replay buffer with prioritized sampling"""

    def __init__(self, capacity: int = 100000, alpha: float = 0.6):
        self.capacity = capacity
        self.alpha = alpha
        self.buffer = []
        self.priorities = np.zeros(capacity, dtype=np.float32)
        self.position = 0
        self.size = 0

    def push(self, experience: Experience, priority: float = 1.0):
        """Add experience to buffer"""
        if len(self.buffer) < self.capacity:
            self.buffer.append(experience)
        else:
            self.buffer[self.position] = experience

        self.priorities[self.position] = priority ** self.alpha
        self.position = (self.position + 1) % self.capacity
        self.size = min(self.size + 1, self.capacity)

    def sample(
        self,
        batch_size: int,
        beta: float = 0.4
    ) -> Tuple[List[Experience], np.ndarray, np.ndarray]:
        """Sample batch with priorities"""
        if self.size == 0:
            return [], np.array([]), np.array([])

        priorities = self.priorities[:self.size]
        probabilities = priorities / priorities.sum()

        indices = np.random.choice(
            self.size,
            size=min(batch_size, self.size),
            p=probabilities,
            replace=False
        )

        experiences = [self.buffer[i] for i in indices]

        # Importance sampling weights
        weights = (self.size * probabilities[indices]) ** (-beta)
        weights /= weights.max()

        return experiences, indices, weights

    def update_priorities(self, indices: np.ndarray, priorities: np.ndarray):
        """Update priorities for sampled experiences"""
        for idx, priority in zip(indices, priorities):
            self.priorities[idx] = (priority + 1e-6) ** self.alpha

    def __len__(self):
        return self.size


class DQNetwork(nn.Module):
    """Deep Q-Network with dueling architecture"""

    def __init__(
        self,
        state_size: int,
        action_size: int,
        hidden_size: int = 256
    ):
        super().__init__()

        # Shared feature layers
        self.feature_layers = nn.Sequential(
            nn.Linear(state_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, hidden_size),
            nn.ReLU()
        )

        # Value stream
        self.value_stream = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Linear(hidden_size // 2, 1)
        )

        # Advantage stream
        self.advantage_stream = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Linear(hidden_size // 2, action_size)
        )

    def forward(self, state: torch.Tensor) -> torch.Tensor:
        features = self.feature_layers(state)

        value = self.value_stream(features)
        advantage = self.advantage_stream(features)

        # Dueling DQN: Q = V + (A - mean(A))
        q_values = value + (advantage - advantage.mean(dim=1, keepdim=True))
        return q_values


class ActorCritic(nn.Module):
    """Actor-Critic network for PPO"""

    def __init__(
        self,
        state_size: int,
        action_size: int,
        hidden_size: int = 256
    ):
        super().__init__()

        # Shared layers
        self.shared = nn.Sequential(
            nn.Linear(state_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, hidden_size),
            nn.ReLU()
        )

        # Actor (policy)
        self.actor = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Linear(hidden_size // 2, action_size),
            nn.Softmax(dim=-1)
        )

        # Critic (value)
        self.critic = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Linear(hidden_size // 2, 1)
        )

    def forward(
        self,
        state: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        shared_features = self.shared(state)
        action_probs = self.actor(shared_features)
        value = self.critic(shared_features)
        return action_probs, value

    def get_action(self, state: torch.Tensor) -> Tuple[int, torch.Tensor]:
        action_probs, value = self.forward(state)
        dist = Categorical(action_probs)
        action = dist.sample()
        return action.item(), dist.log_prob(action), value


class TradingEnvironment:
    """Trading environment for RL training"""

    def __init__(
        self,
        data: pd.DataFrame,
        initial_balance: float = 10000,
        commission: float = 0.0002,
        leverage: float = 100,
        max_position_size: float = 0.1
    ):
        self.data = data
        self.initial_balance = initial_balance
        self.commission = commission
        self.leverage = leverage
        self.max_position_size = max_position_size

        self.reset()

    def reset(self) -> TradingState:
        """Reset environment to initial state"""
        self.current_step = 50  # Start after warmup period
        self.balance = self.initial_balance
        self.position = 0
        self.entry_price = 0
        self.trades = []
        self.total_pnl = 0

        return self._get_state()

    def _get_state(self) -> TradingState:
        """Get current state"""
        prices = self.data['close'].iloc[
            self.current_step - 20:self.current_step
        ].values

        # Normalize prices
        prices_normalized = (prices - prices.mean()) / (prices.std() + 1e-8)

        current_price = self.data['close'].iloc[self.current_step]

        # Calculate unrealized PnL
        if self.position != 0:
            pnl = (current_price - self.entry_price) * self.position
            unrealized_pnl = pnl / self.entry_price
        else:
            unrealized_pnl = 0

        # Calculate indicators
        indicators = self._calculate_indicators()

        return TradingState(
            prices=prices_normalized,
            position=self.position,
            entry_price=self.entry_price,
            unrealized_pnl=unrealized_pnl,
            balance=self.balance,
            indicators=indicators
        )

    def _calculate_indicators(self) -> Dict[str, float]:
        """Calculate technical indicators for current step"""
        close = self.data['close'].iloc[:self.current_step + 1]

        # RSI
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = (100 - (100 / (1 + rs))).iloc[-1]

        # MACD
        ema12 = close.ewm(span=12).mean()
        ema26 = close.ewm(span=26).mean()
        macd = (ema12 - ema26).iloc[-1]

        # Bollinger Band position
        sma20 = close.rolling(window=20).mean()
        std20 = close.rolling(window=20).std()
        bb_upper = sma20 + (std20 * 2)
        bb_lower = sma20 - (std20 * 2)
        bb_position = ((close.iloc[-1] - bb_lower.iloc[-1]) /
                       (bb_upper.iloc[-1] - bb_lower.iloc[-1] + 1e-8))

        # ATR ratio
        high = self.data['high'].iloc[:self.current_step + 1]
        low = self.data['low'].iloc[:self.current_step + 1]
        tr = pd.concat([
            high - low,
            abs(high - close.shift()),
            abs(low - close.shift())
        ], axis=1).max(axis=1)
        atr = tr.rolling(window=14).mean().iloc[-1]
        atr_ratio = atr / close.iloc[-1]

        # Momentum
        momentum = (close.iloc[-1] / close.iloc[-10] - 1) if len(close) >= 10 else 0

        return {
            'rsi': (rsi - 50) / 50 if not np.isnan(rsi) else 0,
            'macd': macd / close.iloc[-1] * 100 if not np.isnan(macd) else 0,
            'bb_position': (bb_position - 0.5) * 2 if not np.isnan(bb_position) else 0,
            'atr_ratio': atr_ratio if not np.isnan(atr_ratio) else 0,
            'momentum': momentum * 10 if not np.isnan(momentum) else 0
        }

    def step(
        self,
        action: int
    ) -> Tuple[TradingState, float, bool, Dict]:
        """Execute action and return new state, reward, done, info"""
        current_price = self.data['close'].iloc[self.current_step]
        reward = 0
        info = {}

        action_type = TradingAction(action)

        # Execute action
        if action_type == TradingAction.BUY and self.position <= 0:
            # Close short if exists
            if self.position < 0:
                pnl = (self.entry_price - current_price) * abs(self.position)
                self.balance += pnl
                reward += pnl / self.initial_balance * 100
                self.trades.append({
                    'type': 'close_short',
                    'price': current_price,
                    'pnl': pnl
                })

            # Open long
            position_size = self.balance * self.max_position_size * self.leverage
            cost = position_size * self.commission
            self.balance -= cost
            self.position = 1
            self.entry_price = current_price
            info['action'] = 'buy'

        elif action_type == TradingAction.SELL and self.position >= 0:
            # Close long if exists
            if self.position > 0:
                pnl = (current_price - self.entry_price) * self.position
                self.balance += pnl
                reward += pnl / self.initial_balance * 100
                self.trades.append({
                    'type': 'close_long',
                    'price': current_price,
                    'pnl': pnl
                })

            # Open short
            position_size = self.balance * self.max_position_size * self.leverage
            cost = position_size * self.commission
            self.balance -= cost
            self.position = -1
            self.entry_price = current_price
            info['action'] = 'sell'

        elif action_type == TradingAction.CLOSE and self.position != 0:
            # Close position
            if self.position > 0:
                pnl = (current_price - self.entry_price)
            else:
                pnl = (self.entry_price - current_price)

            self.balance += pnl * abs(self.position) * self.balance * self.max_position_size * self.leverage / self.entry_price
            reward += pnl / self.entry_price * 100
            self.trades.append({
                'type': 'close',
                'price': current_price,
                'pnl': pnl
            })
            self.position = 0
            self.entry_price = 0
            info['action'] = 'close'

        else:
            # Hold - small reward for holding profitable position
            if self.position != 0:
                unrealized = (current_price - self.entry_price) * self.position / self.entry_price
                reward += unrealized * 0.1  # Small reward for paper profits
            info['action'] = 'hold'

        # Move to next step
        self.current_step += 1
        done = self.current_step >= len(self.data) - 1

        # Penalize large drawdowns
        drawdown = (self.initial_balance - self.balance) / self.initial_balance
        if drawdown > 0.1:
            reward -= drawdown * 10

        # Bonus for profitable trades
        if self.balance > self.initial_balance:
            reward += 0.1

        next_state = self._get_state()
        info['balance'] = self.balance
        info['position'] = self.position

        return next_state, reward, done, info

    @property
    def state_size(self) -> int:
        """Size of state vector"""
        return 25  # 20 prices + position + entry + pnl + balance + 5 indicators

    @property
    def action_size(self) -> int:
        """Number of possible actions"""
        return len(TradingAction)


class TradingRLAgent:
    """
    Reinforcement Learning Trading Agent

    Supports both DQN and PPO algorithms with:
    - Prioritized experience replay
    - Double DQN
    - Dueling architecture
    - Target network soft updates
    """

    def __init__(
        self,
        state_size: int = 25,
        action_size: int = 4,
        algorithm: str = "dqn",  # "dqn" or "ppo"
        learning_rate: float = 0.0001,
        gamma: float = 0.99,
        epsilon_start: float = 1.0,
        epsilon_end: float = 0.01,
        epsilon_decay: float = 0.995,
        buffer_size: int = 100000,
        batch_size: int = 64,
        tau: float = 0.001,
        model_dir: str = "./models"
    ):
        self.state_size = state_size
        self.action_size = action_size
        self.algorithm = algorithm
        self.learning_rate = learning_rate
        self.gamma = gamma
        self.epsilon = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay = epsilon_decay
        self.batch_size = batch_size
        self.tau = tau
        self.model_dir = model_dir

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Initialize networks based on algorithm
        if algorithm == "dqn":
            self.policy_net = DQNetwork(state_size, action_size).to(self.device)
            self.target_net = DQNetwork(state_size, action_size).to(self.device)
            self.target_net.load_state_dict(self.policy_net.state_dict())
            self.optimizer = optim.Adam(
                self.policy_net.parameters(),
                lr=learning_rate
            )
        else:  # PPO
            self.actor_critic = ActorCritic(state_size, action_size).to(self.device)
            self.optimizer = optim.Adam(
                self.actor_critic.parameters(),
                lr=learning_rate
            )

        self.memory = PrioritizedReplayBuffer(buffer_size)
        self.training_history: List[Dict] = []
        self.is_trained = False

        os.makedirs(model_dir, exist_ok=True)
        logger.info(f"TradingRLAgent initialized with {algorithm} on {self.device}")

    def select_action(
        self,
        state: np.ndarray,
        training: bool = True
    ) -> int:
        """Select action using epsilon-greedy (DQN) or policy (PPO)"""
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)

        if self.algorithm == "dqn":
            # Epsilon-greedy for DQN
            if training and random.random() < self.epsilon:
                return random.randrange(self.action_size)

            with torch.no_grad():
                q_values = self.policy_net(state_tensor)
                return q_values.argmax(dim=1).item()

        else:  # PPO
            with torch.no_grad():
                action_probs, _ = self.actor_critic(state_tensor)
                if training:
                    dist = Categorical(action_probs)
                    return dist.sample().item()
                else:
                    return action_probs.argmax(dim=1).item()

    def store_experience(
        self,
        state: np.ndarray,
        action: int,
        reward: float,
        next_state: np.ndarray,
        done: bool
    ):
        """Store experience in replay buffer"""
        experience = Experience(state, action, reward, next_state, done)
        self.memory.push(experience, priority=abs(reward) + 1.0)

    def learn_dqn(self) -> Optional[float]:
        """Learn from experience replay (DQN)"""
        if len(self.memory) < self.batch_size:
            return None

        experiences, indices, weights = self.memory.sample(
            self.batch_size,
            beta=0.4
        )

        if not experiences:
            return None

        # Convert to tensors
        states = torch.FloatTensor(
            np.array([e.state for e in experiences])
        ).to(self.device)
        actions = torch.LongTensor(
            [e.action for e in experiences]
        ).unsqueeze(1).to(self.device)
        rewards = torch.FloatTensor(
            [e.reward for e in experiences]
        ).unsqueeze(1).to(self.device)
        next_states = torch.FloatTensor(
            np.array([e.next_state for e in experiences])
        ).to(self.device)
        dones = torch.FloatTensor(
            [e.done for e in experiences]
        ).unsqueeze(1).to(self.device)
        weights = torch.FloatTensor(weights).unsqueeze(1).to(self.device)

        # Current Q values
        current_q = self.policy_net(states).gather(1, actions)

        # Double DQN: use policy net to select action, target net to evaluate
        with torch.no_grad():
            next_actions = self.policy_net(next_states).argmax(1, keepdim=True)
            next_q = self.target_net(next_states).gather(1, next_actions)
            target_q = rewards + (1 - dones) * self.gamma * next_q

        # Compute loss with importance sampling weights
        td_errors = torch.abs(current_q - target_q).detach().cpu().numpy()
        loss = (weights * F.smooth_l1_loss(current_q, target_q, reduction='none')).mean()

        # Optimize
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.policy_net.parameters(), 1.0)
        self.optimizer.step()

        # Update priorities
        self.memory.update_priorities(indices, td_errors.flatten())

        # Soft update target network
        for target_param, policy_param in zip(
            self.target_net.parameters(),
            self.policy_net.parameters()
        ):
            target_param.data.copy_(
                self.tau * policy_param.data + (1 - self.tau) * target_param.data
            )

        # Decay epsilon
        self.epsilon = max(self.epsilon_end, self.epsilon * self.epsilon_decay)

        return loss.item()

    def learn_ppo(
        self,
        states: List[np.ndarray],
        actions: List[int],
        rewards: List[float],
        old_log_probs: List[torch.Tensor],
        values: List[torch.Tensor],
        dones: List[bool],
        epochs: int = 4,
        clip_epsilon: float = 0.2
    ) -> float:
        """Learn using PPO algorithm"""
        # Convert to tensors
        states_t = torch.FloatTensor(np.array(states)).to(self.device)
        actions_t = torch.LongTensor(actions).to(self.device)
        old_log_probs_t = torch.stack(old_log_probs).to(self.device)
        old_values_t = torch.stack(values).squeeze().to(self.device)

        # Calculate returns and advantages
        returns = []
        advantages = []
        R = 0

        for i in reversed(range(len(rewards))):
            if dones[i]:
                R = 0
            R = rewards[i] + self.gamma * R
            returns.insert(0, R)

        returns_t = torch.FloatTensor(returns).to(self.device)
        advantages_t = returns_t - old_values_t
        advantages_t = (advantages_t - advantages_t.mean()) / (advantages_t.std() + 1e-8)

        total_loss = 0

        for _ in range(epochs):
            # Get new policy
            action_probs, values = self.actor_critic(states_t)
            dist = Categorical(action_probs)
            new_log_probs = dist.log_prob(actions_t)
            entropy = dist.entropy().mean()

            # Ratio
            ratio = torch.exp(new_log_probs - old_log_probs_t)

            # Clipped objective
            surr1 = ratio * advantages_t
            surr2 = torch.clamp(ratio, 1 - clip_epsilon, 1 + clip_epsilon) * advantages_t
            policy_loss = -torch.min(surr1, surr2).mean()

            # Value loss
            value_loss = F.mse_loss(values.squeeze(), returns_t)

            # Total loss
            loss = policy_loss + 0.5 * value_loss - 0.01 * entropy

            self.optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.actor_critic.parameters(), 0.5)
            self.optimizer.step()

            total_loss += loss.item()

        return total_loss / epochs

    async def train(
        self,
        data: pd.DataFrame,
        episodes: int = 1000,
        max_steps: int = 1000
    ) -> Dict[str, Any]:
        """Train the RL agent on historical data"""
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch required for training")

        logger.info(f"Training RL agent for {episodes} episodes...")

        env = TradingEnvironment(data)
        episode_rewards = []
        episode_balances = []

        for episode in range(episodes):
            state = env.reset()
            state_array = state.to_tensor()

            episode_reward = 0
            episode_states = []
            episode_actions = []
            episode_rewards_list = []
            episode_log_probs = []
            episode_values = []
            episode_dones = []

            for step in range(max_steps):
                # Select action
                if self.algorithm == "dqn":
                    action = self.select_action(state_array, training=True)
                else:
                    state_tensor = torch.FloatTensor(state_array).unsqueeze(0).to(self.device)
                    action, log_prob, value = self.actor_critic.get_action(state_tensor)
                    episode_states.append(state_array)
                    episode_actions.append(action)
                    episode_log_probs.append(log_prob)
                    episode_values.append(value)

                # Take action
                next_state, reward, done, info = env.step(action)
                next_state_array = next_state.to_tensor()

                episode_reward += reward
                episode_rewards_list.append(reward)
                episode_dones.append(done)

                # Store experience for DQN
                if self.algorithm == "dqn":
                    self.store_experience(
                        state_array, action, reward, next_state_array, done
                    )
                    self.learn_dqn()

                state_array = next_state_array

                if done:
                    break

            # Learn for PPO at end of episode
            if self.algorithm == "ppo" and episode_states:
                self.learn_ppo(
                    episode_states,
                    episode_actions,
                    episode_rewards_list,
                    episode_log_probs,
                    episode_values,
                    episode_dones
                )

            episode_rewards.append(episode_reward)
            episode_balances.append(env.balance)

            if (episode + 1) % 100 == 0:
                avg_reward = np.mean(episode_rewards[-100:])
                avg_balance = np.mean(episode_balances[-100:])
                logger.info(
                    f"Episode {episode + 1}/{episodes}, "
                    f"Avg Reward: {avg_reward:.2f}, "
                    f"Avg Balance: {avg_balance:.2f}, "
                    f"Epsilon: {self.epsilon:.3f}"
                )

        self.is_trained = True
        self.save_model(f"rl_agent_{self.algorithm}.pt")

        return {
            "episodes": episodes,
            "final_avg_reward": np.mean(episode_rewards[-100:]),
            "final_avg_balance": np.mean(episode_balances[-100:]),
            "max_balance": max(episode_balances),
            "reward_history": episode_rewards,
            "balance_history": episode_balances
        }

    def get_trading_decision(
        self,
        state: TradingState
    ) -> Dict[str, Any]:
        """Get trading decision for live trading"""
        state_array = state.to_tensor()
        action = self.select_action(state_array, training=False)
        action_type = TradingAction(action)

        # Get confidence from Q-values or action probabilities
        state_tensor = torch.FloatTensor(state_array).unsqueeze(0).to(self.device)

        if self.algorithm == "dqn":
            with torch.no_grad():
                q_values = self.policy_net(state_tensor)
                probs = F.softmax(q_values, dim=1).cpu().numpy()[0]
                confidence = probs[action]
        else:
            with torch.no_grad():
                action_probs, _ = self.actor_critic(state_tensor)
                confidence = action_probs[0, action].item()

        # Map to trading signal
        if action_type == TradingAction.BUY:
            signal = "BUY"
        elif action_type == TradingAction.SELL:
            signal = "SELL"
        elif action_type == TradingAction.CLOSE:
            signal = "CLOSE"
        else:
            signal = "HOLD"

        return {
            "action": action_type.name,
            "signal": signal,
            "confidence": confidence,
            "current_position": state.position,
            "unrealized_pnl": state.unrealized_pnl,
            "timestamp": datetime.now().isoformat()
        }

    def save_model(self, filename: str):
        """Save model to disk"""
        path = os.path.join(self.model_dir, filename)

        if self.algorithm == "dqn":
            torch.save({
                'policy_net': self.policy_net.state_dict(),
                'target_net': self.target_net.state_dict(),
                'optimizer': self.optimizer.state_dict(),
                'epsilon': self.epsilon,
                'algorithm': self.algorithm,
                'state_size': self.state_size,
                'action_size': self.action_size
            }, path)
        else:
            torch.save({
                'actor_critic': self.actor_critic.state_dict(),
                'optimizer': self.optimizer.state_dict(),
                'algorithm': self.algorithm,
                'state_size': self.state_size,
                'action_size': self.action_size
            }, path)

        logger.info(f"RL model saved to {path}")

    def load_model(self, filename: str):
        """Load model from disk"""
        path = os.path.join(self.model_dir, filename)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Model not found at {path}")

        checkpoint = torch.load(path, map_location=self.device)

        self.algorithm = checkpoint['algorithm']
        self.state_size = checkpoint['state_size']
        self.action_size = checkpoint['action_size']

        if self.algorithm == "dqn":
            self.policy_net = DQNetwork(
                self.state_size,
                self.action_size
            ).to(self.device)
            self.target_net = DQNetwork(
                self.state_size,
                self.action_size
            ).to(self.device)
            self.policy_net.load_state_dict(checkpoint['policy_net'])
            self.target_net.load_state_dict(checkpoint['target_net'])
            self.epsilon = checkpoint.get('epsilon', 0.01)
        else:
            self.actor_critic = ActorCritic(
                self.state_size,
                self.action_size
            ).to(self.device)
            self.actor_critic.load_state_dict(checkpoint['actor_critic'])

        self.is_trained = True
        logger.info(f"RL model loaded from {path}")

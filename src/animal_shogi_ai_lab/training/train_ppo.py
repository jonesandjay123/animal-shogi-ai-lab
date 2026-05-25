from __future__ import annotations

import os


def train_ppo(timesteps: int = 1000) -> None:
    """Trains a PPO agent on the Animal Shogi environment."""
    try:
        from stable_baselines3 import PPO
    except ImportError:
        print("Error: stable-baselines3 is not installed.")
        print("Please install the reinforcement learning extra dependencies by running:")
        print("  pip install -e \".[dev,ui,rl]\"")
        return

    from animal_shogi_ai_lab.training.env import AnimalShogiEnv

    # Ensure output directories exist under gitignored paths
    os.makedirs("checkpoints", exist_ok=True)
    os.makedirs("runs", exist_ok=True)

    env = AnimalShogiEnv()

    tb_log = None
    try:
        import tensorboard  # noqa: F401
        tb_log = "runs/ppo_animal_shogi_tensorboard"
    except ImportError:
        print("TensorBoard is not installed. TensorBoard logging will be disabled.")

    # Use a simple MLP policy since the observation is flattened
    model = PPO(
        "MlpPolicy",
        env,
        verbose=1,
        tensorboard_log=tb_log,
    )

    print(f"Starting PPO training for {timesteps} timesteps...")
    model.learn(total_timesteps=timesteps)

    model_path = "checkpoints/ppo_animal_shogi_smoke_test"
    model.save(model_path)
    print(f"Training complete. Model saved to {model_path}")

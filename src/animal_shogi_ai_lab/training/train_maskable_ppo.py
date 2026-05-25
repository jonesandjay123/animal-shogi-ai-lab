from __future__ import annotations

import datetime
import json
import os


def train_maskable_ppo(timesteps: int = 100000, n_envs: int = 8, seed: int = 0) -> None:
    """Trains a MaskablePPO agent on the Animal Shogi environment."""
    try:
        from sb3_contrib import MaskablePPO
        from stable_baselines3.common.callbacks import CheckpointCallback
        from stable_baselines3.common.env_util import make_vec_env
    except ImportError:
        print("Error: stable-baselines3 and sb3-contrib are required for MaskablePPO training.")
        print("Please install the reinforcement learning dependencies by running:")
        print("  pip install -e \".[dev,ui,rl]\"")
        return

    from animal_shogi_ai_lab.training.env import AnimalShogiEnv

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    run_name = f"maskable_ppo_{timestamp}"

    # Paths
    run_dir = os.path.join("runs", "animal_shogi_maskable_ppo", run_name)
    checkpoint_dir = os.path.join("checkpoints", "animal_shogi_maskable_ppo", run_name)

    os.makedirs(run_dir, exist_ok=True)
    os.makedirs(checkpoint_dir, exist_ok=True)

    # Save training config
    config = {
        "timesteps": timesteps,
        "n_envs": n_envs,
        "seed": seed,
        "action_space_size": 132,
        "observation_shape": [126],
        "algorithm": "MaskablePPO",
    }
    config_path = os.path.join(checkpoint_dir, "config.json")
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

    print(f"Initializing vectorized environment with {n_envs} environments...")
    env = make_vec_env(
        AnimalShogiEnv,
        n_envs=n_envs,
        seed=seed,
    )

    tb_log = None
    try:
        import tensorboard  # noqa: F401
        tb_log = os.path.join("runs", "animal_shogi_maskable_ppo")
    except ImportError:
        print("TensorBoard is not installed. TensorBoard logging will be disabled.")

    model = MaskablePPO(
        "MlpPolicy",
        env,
        verbose=1,
        seed=seed,
        tensorboard_log=tb_log,
    )

    # Frequency callback (every 50,000 steps).
    # Save frequency must account for n_envs.
    save_freq = max(50000 // n_envs, 1)
    checkpoint_callback = CheckpointCallback(
        save_freq=save_freq,
        save_path=checkpoint_dir,
        name_prefix="ppo_maskable",
        save_replay_buffer=False,
    )

    print(f"Starting MaskablePPO training for {timesteps} timesteps...")
    print(f"Logging TensorBoard to: {run_dir}")
    print(f"Saving checkpoints and config to: {checkpoint_dir}")

    model.learn(
        total_timesteps=timesteps,
        callback=checkpoint_callback,
        tb_log_name=run_name,
    )

    final_model_path = os.path.join(checkpoint_dir, "final_model")
    model.save(final_model_path)
    print(f"Training complete. Final model saved to {final_model_path}.zip")

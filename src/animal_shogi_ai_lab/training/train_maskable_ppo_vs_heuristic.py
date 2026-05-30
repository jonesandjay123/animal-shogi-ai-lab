from __future__ import annotations

import datetime
import json
import os

from animal_shogi_ai_lab.engine import Player


def train_maskable_ppo_vs_heuristic(
    side: str = "BLACK",
    timesteps: int = 1000000,
    n_envs: int = 4,
    seed: int = 0,
    step_penalty: float = -0.0001,
) -> None:
    """Trains a MaskablePPO agent against a one-ply heuristic opponent."""
    try:
        from sb3_contrib import MaskablePPO
        from stable_baselines3.common.callbacks import CallbackList, CheckpointCallback
        from stable_baselines3.common.env_util import make_vec_env
    except ImportError:
        print("Error: stable-baselines3 and sb3-contrib are required for MaskablePPO training.")
        print("Please install the reinforcement learning dependencies by running:")
        print("  pip install -e \".[dev,ui,rl]\"")
        return

    from animal_shogi_ai_lab.agents import HeuristicAgent
    from animal_shogi_ai_lab.training.callbacks import ProgressEstimatorCallback
    from animal_shogi_ai_lab.training.env_vs_opponent import AnimalShogiVsOpponentEnv

    learning_player = Player.BLACK if side.upper() == "BLACK" else Player.WHITE

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    run_name = f"maskable_ppo_vs_heuristic_{side.lower()}_{timestamp}"

    run_dir = os.path.join("runs", "animal_shogi_maskable_ppo_vs_heuristic", run_name)
    checkpoint_dir = os.path.join(
        "checkpoints", "animal_shogi_maskable_ppo_vs_heuristic", run_name
    )

    os.makedirs(run_dir, exist_ok=True)
    os.makedirs(checkpoint_dir, exist_ok=True)

    config = {
        "timesteps": timesteps,
        "n_envs": n_envs,
        "seed": seed,
        "side": side.upper(),
        "opponent": "heuristic",
        "step_penalty": step_penalty,
        "action_space_size": 132,
        "observation_shape": [126],
        "algorithm": "MaskablePPO_vs_Heuristic",
    }
    config_path = os.path.join(checkpoint_dir, "config.json")
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

    print(
        f"Initializing vs-heuristic environment ({side.upper()}) "
        f"with {n_envs} environments..."
    )
    env = make_vec_env(
        AnimalShogiVsOpponentEnv,
        n_envs=n_envs,
        seed=seed,
        env_kwargs={
            "learning_player": learning_player,
            "opponent": HeuristicAgent(),
            "step_penalty": step_penalty,
        },
    )

    tb_log = None
    try:
        import tensorboard  # noqa: F401

        tb_log = os.path.join("runs", "animal_shogi_maskable_ppo_vs_heuristic")
    except ImportError:
        print("TensorBoard is not installed. TensorBoard logging will be disabled.")

    model = MaskablePPO(
        "MlpPolicy",
        env,
        verbose=0,
        seed=seed,
        tensorboard_log=tb_log,
    )

    save_freq = max(50000 // n_envs, 1)
    checkpoint_callback = CheckpointCallback(
        save_freq=save_freq,
        save_path=checkpoint_dir,
        name_prefix="ppo_maskable",
        save_replay_buffer=False,
    )

    progress_callback = ProgressEstimatorCallback(
        total_timesteps=timesteps,
        log_interval=min(10000, max(timesteps // 10, 1)),
    )

    callbacks = CallbackList([checkpoint_callback, progress_callback])

    print(f"Starting MaskablePPO vs Heuristic training for {timesteps} timesteps...")
    print(f"Saving checkpoints and config to: {checkpoint_dir}")

    model.learn(
        total_timesteps=timesteps,
        callback=callbacks,
        tb_log_name=run_name,
    )

    final_model_path = os.path.join(checkpoint_dir, "final_model")
    model.save(final_model_path)
    print(f"Training complete. Final model saved to {final_model_path}.zip")

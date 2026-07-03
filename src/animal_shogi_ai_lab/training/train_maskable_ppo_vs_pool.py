from __future__ import annotations

import datetime
import json
import os

from animal_shogi_ai_lab.engine import Player


def train_maskable_ppo_vs_pool(
    side: str = "BLACK",
    timesteps: int = 5000000,
    n_envs: int = 4,
    seed: int = 0,
    step_penalty: float = -0.0001,
    init_model: str | None = None,
    opponent_model: str | None = None,
    w_heuristic: float = 0.5,
    w_model: float = 0.3,
    w_random: float = 0.2,
) -> None:
    """Trains MaskablePPO against a weighted opponent pool.

    The pool mixes a one-ply heuristic, an optional frozen model, and a random
    agent. One opponent is sampled per episode per env. ``init_model`` warm
    starts the learner from an existing checkpoint instead of random weights.
    """
    try:
        from sb3_contrib import MaskablePPO
        from stable_baselines3.common.callbacks import CallbackList, CheckpointCallback
        from stable_baselines3.common.env_util import make_vec_env
    except ImportError:
        print("Error: stable-baselines3 and sb3-contrib are required for MaskablePPO training.")
        print("Please install the reinforcement learning dependencies by running:")
        print("  pip install -e \".[dev,ui,rl]\"")
        return

    from animal_shogi_ai_lab.agents import HeuristicAgent, RandomAgent
    from animal_shogi_ai_lab.agents.model_agent import ModelOpponentAgent
    from animal_shogi_ai_lab.agents.pool_agent import OpponentPoolAgent
    from animal_shogi_ai_lab.training.callbacks import ProgressEstimatorCallback
    from animal_shogi_ai_lab.training.env_vs_opponent import AnimalShogiVsOpponentEnv

    learning_player = Player.BLACK if side.upper() == "BLACK" else Player.WHITE

    frozen_model = None
    if opponent_model is not None:
        print(f"Loading frozen opponent model from: {opponent_model}")
        frozen_model = MaskablePPO.load(opponent_model)
    elif w_model > 0.0:
        print("No --opponent-model given; dropping the model slot from the pool.")
        w_model = 0.0

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    run_name = f"maskable_ppo_vs_pool_{side.lower()}_{timestamp}"

    run_dir = os.path.join("runs", "animal_shogi_maskable_ppo_vs_pool", run_name)
    checkpoint_dir = os.path.join("checkpoints", "animal_shogi_maskable_ppo_vs_pool", run_name)

    os.makedirs(run_dir, exist_ok=True)
    os.makedirs(checkpoint_dir, exist_ok=True)

    config = {
        "timesteps": timesteps,
        "n_envs": n_envs,
        "seed": seed,
        "side": side.upper(),
        "opponent": "pool",
        "pool_weights": {
            "heuristic": w_heuristic,
            "model": w_model,
            "random": w_random,
        },
        "opponent_model": opponent_model,
        "init_model": init_model,
        "step_penalty": step_penalty,
        "action_space_size": 132,
        "observation_shape": [126],
        "algorithm": "MaskablePPO_vs_Pool",
    }
    config_path = os.path.join(checkpoint_dir, "config.json")
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

    def make_pool() -> OpponentPoolAgent:
        opponents: list[tuple[object, float]] = [
            (HeuristicAgent(), w_heuristic),
            (RandomAgent(), w_random),
        ]
        if frozen_model is not None and w_model > 0.0:
            opponents.append((ModelOpponentAgent(model=frozen_model), w_model))
        return OpponentPoolAgent(opponents)

    print(
        f"Initializing vs-pool environment ({side.upper()}) with {n_envs} environments "
        f"(heuristic={w_heuristic}, model={w_model}, random={w_random})..."
    )
    env = make_vec_env(
        lambda: AnimalShogiVsOpponentEnv(
            learning_player=learning_player,
            opponent=make_pool(),
            step_penalty=step_penalty,
        ),
        n_envs=n_envs,
        seed=seed,
    )

    tb_log = None
    try:
        import tensorboard  # noqa: F401

        tb_log = os.path.join("runs", "animal_shogi_maskable_ppo_vs_pool")
    except ImportError:
        print("TensorBoard is not installed. TensorBoard logging will be disabled.")

    if init_model is not None:
        print(f"Warm starting learner from: {init_model}")
        model = MaskablePPO.load(init_model, env=env, tensorboard_log=tb_log)
    else:
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

    print(f"Starting MaskablePPO vs Pool training for {timesteps} timesteps...")
    print(f"Saving checkpoints and config to: {checkpoint_dir}")

    model.learn(
        total_timesteps=timesteps,
        callback=callbacks,
        tb_log_name=run_name,
        reset_num_timesteps=True,
    )

    final_model_path = os.path.join(checkpoint_dir, "final_model")
    model.save(final_model_path)
    print(f"Training complete. Final model saved to {final_model_path}.zip")

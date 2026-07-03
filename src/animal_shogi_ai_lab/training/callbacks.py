from __future__ import annotations

import time

from stable_baselines3.common.callbacks import BaseCallback


class ProgressEstimatorCallback(BaseCallback):
    """Callback for estimating and printing training progress, FPS, elapsed time, and ETA.

    Prints clean single-line messages periodically, which is highly compatible with log redirection.
    """

    def __init__(self, total_timesteps: int, log_interval: int = 10000, verbose: int = 0):
        super().__init__(verbose)
        self.total_timesteps = total_timesteps
        self.log_interval = log_interval
        self.start_time = None
        self.last_log_step = 0

    def _on_training_start(self) -> None:
        self.start_time = time.time()
        print(f"Training started at {time.strftime('%Y-%m-%d %H:%M:%S')}")

    def _on_step(self) -> bool:
        current_step = self.num_timesteps
        if self.last_log_step >= self.total_timesteps:
            return True
        reached_interval = current_step - self.last_log_step >= self.log_interval
        reached_total = current_step >= self.total_timesteps > self.last_log_step
        if reached_interval or reached_total:
            self.last_log_step = current_step
            elapsed = time.time() - self.start_time
            percentage = (current_step / self.total_timesteps) * 100

            # Calculate speed and remaining time estimation
            fps = current_step / elapsed if elapsed > 0 else 0.0
            remaining_steps = max(self.total_timesteps - current_step, 0)
            eta = remaining_steps / fps if fps > 0 else 0.0

            # Format to HH:MM:SS
            elapsed_str = time.strftime("%H:%M:%S", time.gmtime(elapsed))
            eta_str = time.strftime("%H:%M:%S", time.gmtime(eta))

            print(
                f"[Progress] {percentage:5.1f}% | "
                f"Steps: {current_step:,} / {self.total_timesteps:,} | "
                f"FPS: {fps:.0f} | "
                f"Elapsed: {elapsed_str} | "
                f"ETA: {eta_str}",
                flush=True,
            )
        return True


class TimeBudgetCallback(BaseCallback):
    """Stops training gracefully once a wall-clock budget is exhausted.

    Lets a run be sized by available time ("train for 75 minutes") instead of
    guessing a timestep count. The model is still saved by the caller after
    ``learn`` returns.
    """

    def __init__(self, max_minutes: float, verbose: int = 0):
        super().__init__(verbose)
        self.max_seconds = max_minutes * 60.0
        self.start_time: float | None = None

    def _on_training_start(self) -> None:
        self.start_time = time.monotonic()

    def _on_step(self) -> bool:
        if time.monotonic() - self.start_time >= self.max_seconds:
            print(
                f"[TimeBudget] {self.max_seconds / 60.0:.1f} minutes reached at "
                f"step {self.num_timesteps:,}; stopping training.",
                flush=True,
            )
            return False
        return True

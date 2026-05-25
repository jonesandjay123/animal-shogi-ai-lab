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
        if (
            current_step - self.last_log_step >= self.log_interval
            or current_step >= self.total_timesteps
        ):
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
                f"ETA: {eta_str}"
            )
        return True

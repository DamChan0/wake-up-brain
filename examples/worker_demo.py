def run_once(job: str) -> str:
    return f"completed: {job}"

from dataclasses import dataclass

@dataclass(frozen=True)
class WorkerConfig:
    name: str
    parallelism: int

WORKERS = (
    WorkerConfig("careful", 1),
    WorkerConfig("fast", 3),
)

def split_job(job: str, parallelism: int) -> list[str]:
    if parallelism < 1:
        raise ValueError("parallelism must be positive")
    return [f"{job} [part {index}]" for index in range(1, parallelism + 1)]

def run_all(job: str, configs: tuple[WorkerConfig, ...]) -> dict[str, list[str]]:
    return {
        config.name: [run_once(part) for part in split_job(job, config.parallelism)]
        for config in configs
    }

fast = next(config for config in WORKERS if config.name == "fast")
print(run_all("report", (fast,)))

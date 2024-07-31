from pathlib import Path


def get_config_folder(base_file: str) -> Path:
    base_folder = Path(__file__).parent.resolve()
    return Path(base_folder / base_file)

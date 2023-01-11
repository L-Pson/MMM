import pathlib
def readenv(key:str) -> str:
    file_path = pathlib.Path(__file__).parent.resolve() / "env" / key
    return pathlib.Path((file_path.read_text()))
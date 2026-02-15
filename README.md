# GetComics Downloader

A CLI tool to search for and download comics from [getcomics.info](https://getcomics.info).

## Features

- **Search:** Find comics by keywords.
- **Filter:** Filter results by date, issue number range.
- **Interactive:** Choose which issues to download from the search results.

## Installation

1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install beautifulsoup4==4.12.2 requests==2.28.2 rich==13.3.4
   ```

## Usage

```bash
python main.py "search query" [options]
```

### Global Usage (macOS/Linux)

For easier global access, you can add a function to your shell's configuration file (e.g., `~/.zshrc` or `~/.bashrc`).

1.  **Open your shell configuration file:**
    ```bash
    nano ~/.zshrc # or nano ~/.bashrc
    ```

2.  **Add the following function to the file:**

    ```bash
    getcomic(){
        local SCRIPT_PATH="SCRIPT_PATH/getcomics.info/main.py" # IMPORTANT: Update this path to your cloned repository

        if [ -z "$1" ]; then
            echo "Usage: getcomic \"comic name\""
            return 1
        fi

        (cd "$(dirname "$SCRIPT_PATH")" && python3 -W ignore "$(basename "$SCRIPT_PATH")" "$@")
    }
    ```

3.  **Save the file and reload your shell configuration:**
    ```bash
    source ~/.zshrc # or source ~/.bashrc
    ```

4.  **You can now use `getcomic` from anywhere:**
    ```bash
    getcomic "batman"
    ```

### Options

- `query`: Search term. Required if `-t` is not used.
- `-t`, `--tag`: Search by tag.
- `-date`, `--d`: Filter for comics newer than this date (YYYY-MM-DD).
- `-output`, `--o`: Download directory (default: current directory).
- `-min`: Minimum issue number filter.
- `-max`: Maximum issue number filter.
- `-results`, `--r`: Number of results to show (default: 15).
- `-verbose`, `--v`: Enable detailed output.

### Examples

**Search for Batman comics:**
```bash
python main.py "batman"
```

**Search for comics with the "marvel" tag:**
```bash
python main.py -t marvel
```

**Search for Spider-Man comics released after 2023-01-01:**
```bash
python main.py "spider-man" -date 2023-01-01
```

**Search for "Invincible" and download to a specific folder:**
```bash
python main.py "invincible" -output ~/Comics/Invincible
```

**Interactive Mode:**
After searching, the tool will display a list of found comics.
- Enter numbers separated by commas to download specific issues (e.g., `1, 3, 5`).
- Type `a` to download all found comics.
- Type `q` to quit.

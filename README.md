# GetComics Downloader
A TUI-Based CLI tool to search for and download comics from [getcomics.info](https://getcomics.info).

## Features
- **Interactive UI**: A user-friendly terminal interface for searching and downloading.
- **Search by Query**: Find comics by keywords.
- **Filter Results**: Filter comics by date or issue number range.
- **Next Page Navigation**: Browse through multiple pages of search results.
- **Direct and Mediafire Support**: Handles both direct downloads and Mediafire links (for aria2c).

## Planned Features
-   **Enhanced Search Filters**: Implement more advanced filtering options beyond just date and issue number (e.g., publisher, series status).
-   **Download Manager**: A dedicated section to view, pause, resume, or cancel active downloads.
-   **Aria2c Integration**: Support for `aria2c` for more efficient downloading, including segmented downloads and better error handling.
-   **Other Sources**: Extend website options to search and download from other comic/manga websites.
-   **Random Comic Recommendation**: Introduce a feature to recommend random comics for discovery.


# Installation
1.  **Clone the repository:**
    ```bash
    git clone https://github.com/UlucKaymak/GetComicsDownloader.git
    cd GetComicsDownloader
    ```
2.  **Install dependencies:**
    ```bash
    pip install beautifulsoup4==4.12.2 requests==2.28.2 rich==13.3.4
    ```

# Usage
You can run the script in two ways:

## 1. Command-Line Mode
You can also use command-line arguments to perform a quick search.

**Search for Batman comics:**
```bash
python main.py "batman"
```

**Search for Spider-Man comics released after 2023:**
```bash
python main.py "spiderman" -date 2023
```

### Command-Line Options

| Option                | Short | Description                                      |
| --------------------- | ----- | ------------------------------------------------ |
| `query`               |       | Search term.     |
| `--date`              | `-d`  | Filter for comics newer than this date (YYYY). |
| `--output`            | `-o`  | Download directory (default: `Downloads/Comics`).|
| `--min`               |       | Minimum issue number filter.                     |
| `--max`               |       | Maximum issue number filter.                     |
| `--results`           | `-r`  | Number of results to show (default: 15).         |
| `--verbose`           | `-v`  | Enable detailed log output.                      |


## 2. Interactive Mode (Recommended)
Run the script without any arguments to launch the interactive user interface:
```bash
python main.py
```
This will open a menu where you can choose to search by query or use a detailed search with more options.

### Global Usage (macOS/Linux)
For easier global access, you can add a function to your shell's configuration file (e.g., `~/.zshrc` or `~/.bashrc`).

1.  **Open your shell configuration file:**
    ```bash
    nano ~/.zshrc # or nano ~/.bashrc
    ```
2.  **Add the following function to the file.** Make sure to replace `"path/to/your/cloned/repo/main.py"` with the actual path to the `main.py` file in your system.
    ```bash
    getcomic(){
        python3 -W ignore "path/to/your/cloned/repo/main.py" "$@"
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

---
Made with 🎲 by [UlucKaymak](uluckaymak.com)

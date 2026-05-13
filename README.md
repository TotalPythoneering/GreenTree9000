# Forest Explorer Pro 🌲🟨

**Forest Explorer Pro** is a high-contrast, professional-grade recursive file manager built with Python and Tkinter. It features a unique "Terminal-style" Forest Green and Yellow aesthetic, designed for power users who need to sift through large directory structures quickly.

## ✨ Features

*   **Recursive Scanning:** Deep-scan directories for specific file types without UI freezing.
*   **LRU Memory:** Automatically persists your most recently used (LRU) folders and file extensions.
*   **Dual Preview:** Instant **Text Preview** for readable files and a formatted **Hex Dump** for binary files.
*   **Duplicate Hunter:** Fingerprint files by name and size to find redundant data instantly.
*   **Real-Time Filtering:** Debounced keyword search allows you to filter thousands of results as you type.
*   **Full File Management:** Right-click to **Rename**, **Delete**, **Open**, or **Show in Folder**.
*   **File Stats:** Detailed pop-up showing total size, temporal extremes (oldest/newest), and extension breakdowns.
*   **Tri-State Status:** Visual feedback on the scan button (Red: Ready, Yellow: Scanning, Green: Done).

## 🚀 Installation

Install directly from PyPI:

```bash
pip install forest-explorer-pro
```

## 🛠 Usage

Once installed, launch the application from your terminal or command prompt:

```bash
forest-explorer
```

## ⌨️ Shortcuts & Interaction

*   **Single Click:** Update the side preview pane.
*   **Double Click:** Launch the file in your system's default application.
*   **Right Click:** Access the context menu for file operations (Rename/Delete/Open Folder).
*   **Column Headers:** Click any column header to sort alphabetically or numerically.

## 📁 Persistence
The application saves a `history.json` file in its installation directory to remember your favorite folders and extensions between sessions.

## ⚖️ License
This project is licensed under the MIT License - see the LICENSE file for details.

---
*Built with ❤️ for the Python community.*

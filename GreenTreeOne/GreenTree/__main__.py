# MISSION: Create a file-type exploration tool.
# STATUS: Testing release.
# VERSION: 0.1.0
# NOTES: So far so good.
# DATE: 2026-05-12 12:23:42
# FILE: __main__.py
# AUTHOR: Randall Nagy
#
import tkinter as tk
from .gtmain import UltimateForestExplorer

def main():
    root = tk.Tk()
    app = UltimateForestExplorer(root)
    root.mainloop()

if __name__ == "__main__":
    main()

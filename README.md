
# Crop Breeder Assistant 🌾

**Crop Breeder Assistant** is a Python utility designed to automate crop breeding in games (e.g., *Minecraft* with the *Industrial Craft 2* / *GregTech* mod). The script uses Optical Character Recognition (OCR) to read seed stats from the screen, saves their locations, and helps you select the best specimens for crossbreeding.

<img width="444" height="299" alt="python_EFnO2rPhIw" src="https://github.com/user-attachments/assets/04ab1897-2b2b-4d85-b846-1d34e54467b6" />

https://github.com/user-attachments/assets/b28a87de-d20d-4a98-a876-4271122b6a96

https://github.com/user-attachments/assets/5f159a1c-491f-4cd9-a554-0a47a10782e1

## ✨ Key Features

*   **🔍 Stat Scanning**: Instantly reads `Growth` (Gr), `Gain` (Ga), and `Resistance` (Re) stats from item tooltips.
*   **📂 "Page" System**: Supports multiple inventories or chests by allowing you to switch between virtual storage "pages".
*   **🖥️ Visual Overlay**: Draws markers directly over the game window, showing the location of each scanned seed.
*   **📊 Analytics**:
    *   Automatically identifies the best seeds based on a calculated score.
    *   Color-codes seeds for quick identification: 🟡 Best (Gold), 🟢 Good (Green), 🔴 Bad (Red), 🟤 Brown: Absolute Worst (Lowest Score).
*   **🖱️ Interactive**: Remove a seed from the database simply by clicking its marker on the screen.

## 🛠️ Requirements

To run this script, you need to install the following dependencies:

1.  **Python 3.8+**
2.  **Tesseract OCR**:
    *   Download and install [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki).
    *   Ensure the executable path in the script matches your installation path (e.g., `C:\Program Files\Tesseract-OCR\tesseract.exe`).
    *   Tesseract does not know the minecraft font. I used the model from here https://hayden.gg/blog/minecraft-ocr-with-pytesseract/.
3.  **Python Libraries**:
    ```bash
    pip install pyautogui opencv-python numpy pytesseract keyboard mouse
    ```
    *(Note: `tkinter` is usually included with standard Python distributions).*

## 🚀 Launch and Usage

1.  Run the script from your terminal:
    ```bash
    python cropBreeder.py
    ```
2.  Open your inventory in the game.
3.  Use the hotkeys to control the assistant:
4.  You may need to adjust the text detection parameters.

| Key | Action |
| :--- | :--- |
| **`Z`** | **Scan**: Hover your cursor over a seed and press Z. The script will read its stats. |
| **`ENTER`** | **Analyze**: Calculates the best seeds across all pages and updates the marker colors. |
| **`C`** | **New Page**: Creates a new "page" (use when moving to the next chest). |
| **`X`** | **Reset**: Completely clears all scanned seed data. |
| **`⬅️ / ➡️`** | **Navigate**: Switch between pages (chests). |

4.  **Deletion**: To remove a seed from the database, simply click on its on-screen marker.

## ⚙️ Configuration

You can customize constants at the beginning of the `cropBreeder.py` file to match your screen resolution or game interface:

```python
# Screen capture area settings (adjust to fit the tooltip size)
OFFSET_X = 20
OFFSET_Y = -8
CROP_W = 60
CROP_H = 70

# Path to Tesseract (if different)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

## 🔧 How It Works

1.  **Capture**: When `Z` is pressed, `pyautogui` takes a screenshot of the area near the cursor.
2.  **Preprocessing**: `OpenCV` filters the image, isolating only the text colors used for stats in the mod (green, orange, gray).
3.  **OCR**: `Pytesseract` recognizes the numbers from the processed image.
4.  **Overlay**: A transparent, click-through `tkinter` window draws circles over the screen that remain in place, as their coordinates are fixed upon scanning.

## 📝 Notes

*   This script is designed for Windows only due to its use of `ctypes` and `windll` for window transparency.
*   For best results, run your game in **Windowed** or **Borderless Window** mode. The overlay may not appear in fullscreen mode.
*   I didn't check the detection accurately enough. Mistakes are possible. Ideally, check and compare the seeds parameters during the analysis.
It is best to build your own model for tesseract https://github.com/ignwombat/tesseract-custom-font

## 🤝 Author

Developed by **Quark-Coder**.[1]

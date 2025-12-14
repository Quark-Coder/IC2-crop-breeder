import pyautogui
import cv2
import numpy as np
import pytesseract
import keyboard
import threading
import tkinter as tk
import ctypes
from ctypes import windll
import mouse 

CFG_BLOCK = r'--oem 3 --psm 6 -c tessedit_char_whitelist=GrGaRe0123456789'
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    ctypes.windll.user32.SetProcessDPIAware()

OFFSET_X = 20
OFFSET_Y = -8
CROP_W = 60
CROP_H = 70
DELETE_RADIUS = 20 
OVERLAY_OFFSET_X = OFFSET_X + CROP_W + 2
OVERLAY_OFFSET_Y = OFFSET_Y + 2 
OVERLAY_LINE_SPACING = 20 

SELECTION_RATE = 0.40

scanned_seeds = []
current_page = 1
max_page = 1
overlay_canvas = None
root = None
tooltip_timer = None
is_tracking = False

seed_colors = {} 

def preprocess_image(img):
    img = np.array(img)
    target_colors = [(168, 168, 168), (0, 168, 0), (252, 168, 0), (0, 168, 168)]
    tolerance = 10
    combined_mask = np.zeros(img.shape[:2], dtype=np.uint8)
    for color in target_colors:
        lower = np.array([max(0, c - tolerance) for c in color])
        upper = np.array([min(255, c + tolerance) for c in color])
        mask = cv2.inRange(img, lower, upper)
        combined_mask = cv2.bitwise_or(combined_mask, mask)
    result = cv2.bitwise_not(combined_mask)
    scale = 4
    result = cv2.resize(result, None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)
    result = cv2.copyMakeBorder(result, 10, 10, 10, 10, cv2.BORDER_CONSTANT, value=255)
    return result

def parse_stats(text):
    import re
    data = {'Gr': 0, 'Ga': 0, 'Re': 0}
    def find(pat, txt):
        match = re.search(pat + r'.*?([0-9Ooe]+)', txt, re.IGNORECASE)
        if match:
            try:
                char_seq = match.group(1)
                val = char_seq.replace('O','0').replace('o','0').replace('e','6')
                return int(val)
            except: pass
        return 0
    data['Gr'] = find(r'[Gg6][r1Il]', text) 
    data['Ga'] = find(r'[Gg6][a04q]', text) 
    data['Re'] = find(r'[Rr][ec]', text) 
    return data

def scan_worker():
    global scanned_seeds, max_page, seed_colors
    try:
        x, y = pyautogui.position()
        left, top = int(x + OFFSET_X), int(y + OFFSET_Y)
        screenshot = pyautogui.screenshot(region=(left, top, CROP_W, CROP_H))
        processed = preprocess_image(screenshot)
        text = pytesseract.image_to_string(processed, config=CFG_BLOCK, lang='mc')
        stats = parse_stats(text)
        
        if stats['Gr'] == 0 and stats['Ga'] == 0: return

        new_id = 1
        if scanned_seeds:
            new_id = max(s['id'] for s in scanned_seeds) + 1
        
        score = stats['Gr'] + stats['Ga']
        
        seed_data = {
            'id': new_id,
            'x': x,
            'y': y,
            'Gr': stats['Gr'],
            'Ga': stats['Ga'],
            'Re': stats['Re'],
            'score': score,
            'page': current_page
        }

        scanned_seeds.append(seed_data)
        seed_colors[new_id] = "white"
        
        if current_page == max_page:
            draw_marker(seed_data)
        else:
            switch_page(max_page)

        start_tooltip_tracking(stats)
        update_page_indicator()

    except Exception as e:
        print(f"Error: {e}")

def on_click():
    global scanned_seeds, seed_colors
    try:
        mx, my = pyautogui.position()
        closest_seed = None
        min_dist = float('inf')
        
        current_page_seeds = [s for s in scanned_seeds if s['page'] == current_page]
        
        for seed in current_page_seeds:
            dist = ((seed['x'] - mx)**2 + (seed['y'] - my)**2)**0.5
            if dist < min_dist:
                min_dist = dist
                closest_seed = seed
        
        if closest_seed and min_dist <= DELETE_RADIUS:
            scanned_seeds.remove(closest_seed)
            if closest_seed['id'] in seed_colors:
                del seed_colors[closest_seed['id']]
            
            if overlay_canvas:
                overlay_canvas.delete(f"seed_{closest_seed['id']}")
    except Exception as e:
        print(f"Click error: {e}")


def next_chest():
    global current_page, max_page
    
    current_page_seeds = [s for s in scanned_seeds if s['page'] == current_page]
    
    if not current_page_seeds:
        print(f">>> Page {current_page} is empty! Scan something first.")
        return

    overlay_canvas.delete("marker")
    
    max_page += 1
    current_page = max_page
    print(f">>> New Page Created: {current_page}")
    update_page_indicator()

def switch_page(target_page):
    global current_page
    if target_page < 1 or target_page > max_page: return
    current_page = target_page
    redraw_current_page()
    update_page_indicator()

def redraw_current_page():
    if overlay_canvas is None: return
    overlay_canvas.delete("marker")
    
    page_seeds = [s for s in scanned_seeds if s['page'] == current_page]
    
    for seed in page_seeds:
        color = seed_colors.get(seed['id'], "white")
        draw_marker(seed, color)

def update_page_indicator():
    if overlay_canvas is None: return
    overlay_canvas.delete("page_indicator")
    w = root.winfo_screenwidth()
    text = f"CHEST {current_page} / {max_page}"
    overlay_canvas.create_text(w//2, 150, text=text, fill="#00FFFF", 
                               font=("Arial", 16, "bold"), tags="page_indicator")

def analyze_seeds():
    global scanned_seeds, seed_colors
    
    if not scanned_seeds: return

    for s in scanned_seeds:
        s['vol_score'] = (s['Gr'] + 1) * (s['Ga'] + 1) * (s['Re'] + 1)

    sorted_gr = sorted(scanned_seeds, key=lambda s: s['Gr'], reverse=True)
    sorted_ga = sorted(scanned_seeds, key=lambda s: s['Ga'], reverse=True)
    sorted_re = sorted(scanned_seeds, key=lambda s: s['Re'], reverse=True)

    limit = max(1, int(len(scanned_seeds) * SELECTION_RATE))
    
    top_gr = set(s['id'] for s in sorted_gr[:limit])
    top_ga = set(s['id'] for s in sorted_ga[:limit])
    top_re = set(s['id'] for s in sorted_re[:limit])

    green_ids = top_gr.intersection(top_ga).intersection(top_re)
    green_seeds_objects = [s for s in scanned_seeds if s['id'] in green_ids]

    if not green_seeds_objects:
        sorted_by_vol = sorted(scanned_seeds, key=lambda s: s['vol_score'], reverse=True)
        limit_vol = max(1, int(len(scanned_seeds) * 0.2)) 
        green_seeds_objects = sorted_by_vol[:limit_vol]
        green_ids = set(s['id'] for s in green_seeds_objects)

    if green_seeds_objects:
        absolute_best = max(green_seeds_objects, key=lambda s: s['vol_score'])
    else:
        absolute_best = max(scanned_seeds, key=lambda s: s['vol_score'])

    absolute_worst = min(scanned_seeds, key=lambda s: s['vol_score'])

    selected_count = 0
    
    for seed in scanned_seeds:
        sid = seed['id']
        
        if sid == absolute_best['id']:
            col = "#FFD700"
            selected_count += 1
        elif sid == absolute_worst['id'] and sid != absolute_best['id']:
            col = "#8B4513"
        elif sid in green_ids:
            col = "#00ff00"
            selected_count += 1
        else:
            col = "#ff3333"
            
        seed_colors[sid] = col

    redraw_current_page()

    print("\n" + "="*40)
    print(f"📊 GLOBAL RESULT (ALL PAGES.): {selected_count} .")
    print("-" * 40)
    
    raw_score = absolute_best['Gr'] * absolute_best['Ga'] * absolute_best['Re']
    print(f"🏆 GLOBAL CHAMPION (ID {absolute_best['id']} on Pg {absolute_best['page']})")
    print(f"   Gr:{absolute_best['Gr']} | Ga:{absolute_best['Ga']} | Re:{absolute_best['Re']}")
    print(f"   Score: {raw_score}")
    print("-" * 20)

    if green_seeds_objects:
        min_gr = min(green_seeds_objects, key=lambda s: s['Gr'])
        max_gr = max(green_seeds_objects, key=lambda s: s['Gr'])
        min_re = min(green_seeds_objects, key=lambda s: s['Re'])
        max_re = max(green_seeds_objects, key=lambda s: s['Re'])
        print(f"🌱 Growth: {min_gr['Gr']} .. {max_gr['Gr']}")
        print(f"🛡️ Resist: {min_re['Re']} .. {max_re['Re']}")
    print("="*40 + "\n")

def reset_all():
    global scanned_seeds, current_page, max_page, seed_colors
    scanned_seeds = []
    seed_colors = {}
    current_page = 1
    max_page = 1
    overlay_canvas.delete("all")
    update_page_indicator()
    print("=== FULL RESET ===")

def draw_marker(seed, color="white"):
    x, y = seed['x'], seed['y']
    sid = seed['id']
    r = 13
    unique_tag = f"seed_{sid}"
    overlay_canvas.delete(unique_tag)
    
    overlay_canvas.create_oval(x-r, y-r, x+r, y+r, fill="black", outline=color, width=2, tags=(unique_tag, "marker"))
    overlay_canvas.create_text(x, y, text=str(sid), fill=color, font=("Arial", 11, "bold"), tags=(unique_tag, "marker"))

def start_tooltip_tracking(stats):
    global tooltip_timer, is_tracking
    if overlay_canvas is None: return
    overlay_canvas.delete("tooltip")
    if tooltip_timer is not None: root.after_cancel(tooltip_timer)
    
    font_spec = ("Consolas", 13, "bold")
    color = "#cccaca"
    overlay_canvas.create_text(0, 0, text=str(stats['Gr']), fill=color, font=font_spec, anchor="nw", tags=("tooltip", "tt_gr"))
    overlay_canvas.create_text(0, 0, text=str(stats['Ga']), fill=color, font=font_spec, anchor="nw", tags=("tooltip", "tt_ga"))
    overlay_canvas.create_text(0, 0, text=str(stats['Re']), fill=color, font=font_spec, anchor="nw", tags=("tooltip", "tt_re"))
    
    is_tracking = True
    update_tooltip_position()
    tooltip_timer = root.after(3000, stop_tracking)

def update_tooltip_position():
    global is_tracking
    if not is_tracking: return
    try:
        mx, my = pyautogui.position()
        base_x = mx + OVERLAY_OFFSET_X
        base_y = my + OVERLAY_OFFSET_Y
        overlay_canvas.coords("tt_gr", base_x, base_y)
        overlay_canvas.coords("tt_ga", base_x, base_y + OVERLAY_LINE_SPACING)
        overlay_canvas.coords("tt_re", base_x, base_y + (OVERLAY_LINE_SPACING * 2))
        overlay_canvas.tag_raise("tooltip")
        root.after(8, update_tooltip_position)
    except: pass

def stop_tracking():
    global is_tracking
    is_tracking = False
    overlay_canvas.delete("tooltip")

def set_click_through(hwnd):
    GWL_EXSTYLE = -20
    WS_EX_LAYERED = 0x80000
    WS_EX_TRANSPARENT = 0x20
    style = windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style | WS_EX_LAYERED | WS_EX_TRANSPARENT)

def gui_thread():
    global root, overlay_canvas
    root = tk.Tk()
    root.overrideredirect(True)
    w, h = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry(f"{w}x{h}+0+0")
    root.lift()
    root.wm_attributes("-topmost", True)
    root.wm_attributes("-disabled", True)
    root.wm_attributes("-alpha", 0.75)
    TRANS_KEY = '#010000'
    root.wm_attributes("-transparentcolor", TRANS_KEY)
    root.configure(bg=TRANS_KEY)
    
    overlay_canvas = tk.Canvas(root, width=w, height=h, bg=TRANS_KEY, highlightthickness=0)
    overlay_canvas.pack()
    root.update()
    set_click_through(windll.user32.GetParent(root.winfo_id()))
    
    update_page_indicator() 
    root.mainloop()

if __name__ == "__main__":
    print("=== CROP BREEDER By Quark-Coder ===")
    print("[Z] - Scan | [ENTER] - Analyze ALL Pages")
    print("[C] - NEW PAGE | [X] - FULL RESET")
    print("[LEFT/RIGHT] - Navigate Pages")

    t = threading.Thread(target=gui_thread, daemon=True)
    t.start()
    mouse.on_click(on_click)
    
    keyboard.add_hotkey('z', lambda: threading.Thread(target=scan_worker).start())
    keyboard.add_hotkey('enter', lambda: threading.Thread(target=analyze_seeds).start())
    keyboard.add_hotkey('c', next_chest)
    keyboard.add_hotkey('x', reset_all)
    keyboard.add_hotkey('left', lambda: switch_page(current_page - 1))
    keyboard.add_hotkey('right', lambda: switch_page(current_page + 1))
    keyboard.wait()

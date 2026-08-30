import cv2
import mediapipe as mp
import numpy as np
import random
import pygame
import os
import math
import time
import colorsys 
from threading import Thread
from collections import deque

# ================================
# CONFIG / ASSETS
# ================================
FRAME_W, FRAME_H = 640, 480
ASSET_FOLDER = "assets"
SNAPSHOT_FOLDER = "snapshots"
os.makedirs(ASSET_FOLDER, exist_ok=True)
os.makedirs(SNAPSHOT_FOLDER, exist_ok=True)
HIGHSCORE_FILE = "highscore.txt"

# --- SETTING KESULITAN (TETAP) ---
LEVEL_SETTINGS = {
    1: {"spawn": 45, "grav": 0.18, "speed_min": 10, "speed_max": 13, "bomb": 0.0},
    2: {"spawn": 35, "grav": 0.25, "speed_min": 12, "speed_max": 15, "bomb": 0.05},
    3: {"spawn": 28, "grav": 0.30, "speed_min": 13, "speed_max": 17, "bomb": 0.15},
    4: {"spawn": 20, "grav": 0.44, "speed_min": 15, "speed_max": 20, "bomb": 0.25},
    5: {"spawn": 14, "grav": 0.50, "speed_min": 18, "speed_max": 25, "bomb": 0.35},
}

# Variable Dinamis
current_level = 1
CUR_SPAWN_INTERVAL = 30
CUR_GRAVITY = 0.36
CUR_SPEED_MIN = 13
CUR_SPEED_MAX = 18
CUR_BOMB_CHANCE = 0.12

TARGET_FRUIT_SIZE = 100  
NOSE_SLASH_MIN_DIST = 6
NOSE_SLASH_SPEED_REQ = 0 

# Powerup Variables
freeze_timer = 0
FREEZE_DURATION = 150 
SLOW_FACTOR = 0.2 
frenzy_timer = 0
FRENZY_DURATION = 150 
FRENZY_SPAWN_RATE = 5 

# UI & Interaction Config
BUTTON_HOLD_TIME = 30 # Butuh 30 frame (1 detik) hold untuk klik tombol (Anti Kepencet)
hover_timers = {} # Menyimpan progress hold setiap tombol

# Smart Capture Config
frame_buffer = deque(maxlen=15) # Menyimpan 15 frame terakhir untuk dipilih yang paling tajam

# ==========================================
# AUDIO SYSTEM
# ==========================================
pygame.mixer.init()

cut_sound_path = os.path.join(ASSET_FOLDER, "cut.wav")
splash_sound_path = os.path.join(ASSET_FOLDER, "splash.wav")
bomb_sound_path = os.path.join(ASSET_FOLDER, "bomb.wav")
shutter_sound_path = os.path.join(ASSET_FOLDER, "shutter.wav") 

cut_sound = None
splash_sound = None
bomb_sound = None
shutter_sound = None

try:
    if os.path.exists(cut_sound_path): cut_sound = pygame.mixer.Sound(cut_sound_path)
    if os.path.exists(splash_sound_path): splash_sound = pygame.mixer.Sound(splash_sound_path)
    if os.path.exists(bomb_sound_path): bomb_sound = pygame.mixer.Sound(bomb_sound_path)
    if os.path.exists(shutter_sound_path): shutter_sound = pygame.mixer.Sound(shutter_sound_path)
    
    if cut_sound: cut_sound.set_volume(0.5)
    if splash_sound: splash_sound.set_volume(0.7)
    if bomb_sound: bomb_sound.set_volume(1.0)
except: pass

bgm_files = {
    "menu": os.path.join(ASSET_FOLDER, "bgm_menu.wav"),
    "play": os.path.join(ASSET_FOLDER, "bgm_play.wav"),
    "frenzy": os.path.join(ASSET_FOLDER, "bgm_frenzy.wav")
}
current_music_state = None

def play_music(state):
    global current_music_state
    if current_music_state == state: return 
    path = bgm_files.get(state)
    if path and os.path.exists(path):
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.play(-1)
            pygame.mixer.music.set_volume(0.5)
            current_music_state = state
        except: pass

def stop_all_audio():
    try:
        pygame.mixer.music.stop()
        pygame.mixer.stop()
        pygame.mixer.quit()
    except: pass

# ==========================================
# INPUT MOUSE & KAMERA SYSTEM
# ==========================================
mouse_x, mouse_y = 0, 0
mouse_clicked = False
camera_active = False 

def mouse_callback(event, x, y, flags, param):
    global mouse_x, mouse_y, mouse_clicked
    if event == cv2.EVENT_MOUSEMOVE:
        mouse_x, mouse_y = x, y
    elif event == cv2.EVENT_LBUTTONDOWN:
        mouse_clicked = True
    elif event == cv2.EVENT_LBUTTONUP:
        mouse_clicked = False

# [BARU] Fungsi menghitung ketajaman gambar (Laplacian Variance)
def calculate_sharpness(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var()

# [BARU] Fungsi mengambil frame terbaik dari buffer
def get_best_frame_from_buffer():
    if not frame_buffer: return None
    best_frame = None
    max_sharpness = -1
    
    # Cek semua frame di buffer, cari yang paling tajam
    for f in frame_buffer:
        sharpness = calculate_sharpness(f)
        if sharpness > max_sharpness:
            max_sharpness = sharpness
            best_frame = f
    
    return best_frame if best_frame is not None else frame_buffer[-1]

mp_face = mp.solutions.face_mesh
face_mesh = mp_face.FaceMesh(min_detection_confidence=0.5, min_tracking_confidence=0.5)

# ==========================================
# CLASS MULTITHREADING KAMERA
# ==========================================
class WebcamStream:
    def __init__(self, src=0):
        self.src = src
        self.stream = None
        self.grabbed = False
        self.frame = None
        self.stopped = True
        self.thread = None
    def start(self):
        if self.stopped:
            self.stream = cv2.VideoCapture(self.src)
            (self.grabbed, self.frame) = self.stream.read()
            self.stopped = False
            self.thread = Thread(target=self.update, args=())
            self.thread.start()
        return self
    def update(self):
        while True:
            if self.stopped:
                if self.stream: self.stream.release()
                return
            (self.grabbed, self.frame) = self.stream.read()
    def read(self): return self.frame
    def stop(self):
        self.stopped = True
        if self.thread: self.thread.join()
        self.stream = None 

video_stream = WebcamStream(src=0)

# ================================
# LOADER & UTILS
# ================================
def load_png(name):
    p = os.path.join(ASSET_FOLDER, name)
    if not os.path.exists(p): return None
    return cv2.imread(p, cv2.IMREAD_UNCHANGED)

def load_high_score():
    if not os.path.exists(HIGHSCORE_FILE): return 0
    try:
        with open(HIGHSCORE_FILE, "r") as f: return int(f.read())
    except: return 0

def save_high_score(new_score):
    with open(HIGHSCORE_FILE, "w") as f: f.write(str(new_score))

high_score = load_high_score()

FRUIT_LIST = [
    ("apel.png", "apel_half1.png", "apel_half2.png", (0, 0, 255)),
    ("pisang.png", "pisang_half1.png", "pisang_half2.png", (0, 255, 255)),
    ("jeruk.png", "jeruk_half1.png", "jeruk_half2.png", (0, 165, 255)),
    ("kiwi.png", "kiwi_half1.png", "kiwi_half2.png", (0, 200, 0)),
    ("lemon.png", "lemon_half1.png", "lemon_half2.png", (0, 255, 255)),
    ("nanas.png", "nanas_half1.png", "nanas_half2.png", (0, 215, 255)),
    ("pir.png", "pir_half1.png", "pir_half2.png", (150, 255, 150)),
    ("stroberi.png", "stroberi_half1.png", "stroberi_half2.png", (50, 50, 200)),
]

fruit_defs = []
for full_name, h1_name, h2_name, color in FRUIT_LIST:
    full = load_png(full_name)
    h1 = load_png(h1_name); h2 = load_png(h2_name)
    if full is None: continue
    if h1 is None or h2 is None:
        h, w = full.shape[:2]
        h1 = full[:, :w//2].copy(); h2 = full[:, w//2:].copy()
    fruit_defs.append({"name": full_name, "full": full, "h1": h1, "h2": h2, "color": color})

bomb_img = load_png("bomb.png")
BOMB_ENABLED = (bomb_img is not None)
ice_banana_img = load_png("pisang_biru.png")
ICE_BANANA_ENABLED = (ice_banana_img is not None)
gold_apple_img = load_png("apel_emas.png")
GOLD_APPLE_ENABLED = (gold_apple_img is not None)

def overlay_png(bg, fg, x, y, angle=0, scale=1.0):
    if fg is None: return bg
    h_fg, w_fg = fg.shape[:2]
    if scale == 1.0: w_new, h_new = w_fg, h_fg; fg_scaled = fg
    else:
        w_new = int(w_fg * scale); h_new = int(h_fg * scale)
        if w_new <= 0 or h_new <= 0: return bg
        fg_scaled = cv2.resize(fg, (w_new, h_new), interpolation=cv2.INTER_NEAREST)

    if angle != 0:
        center = (w_new // 2, h_new // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        abs_cos = abs(M[0, 0]); abs_sin = abs(M[0, 1])
        nW = int(h_new * abs_sin + w_new * abs_cos)
        nH = int(h_new * abs_cos + w_new * abs_sin)
        M[0, 2] += (nW / 2) - center[0]; M[1, 2] += (nH / 2) - center[1]
        fg_scaled = cv2.warpAffine(fg_scaled, M, (nW, nH), flags=cv2.INTER_NEAREST, borderMode=cv2.BORDER_CONSTANT, borderValue=(0,0,0,0))
        w_new = nW; h_new = nH

    x1 = int(round(x)); y1 = int(round(y))
    if x1 + w_new <= 0 or y1 + h_new <= 0 or x1 >= bg.shape[1] or y1 >= bg.shape[0]: return bg
    rx1 = max(0, x1); ry1 = max(0, y1)
    rx2 = min(bg.shape[1], x1 + w_new); ry2 = min(bg.shape[0], y1 + h_new)
    fg_x1 = rx1 - x1; fg_y1 = ry1 - y1
    fg_x2 = fg_x1 + (rx2 - rx1); fg_y2 = fg_y1 + (ry2 - ry1)
    if fg_x2 <= fg_x1 or fg_y2 <= fg_y1: return bg

    alpha = fg_scaled[fg_y1:fg_y2, fg_x1:fg_x2, 3:4] / 255.0
    bg_sub = bg[ry1:ry2, rx1:rx2]
    fg_sub = fg_scaled[fg_y1:fg_y2, fg_x1:fg_x2, :3]
    bg[ry1:ry2, rx1:rx2] = (alpha * fg_sub + (1 - alpha) * bg_sub).astype(np.uint8)
    return bg

particles = []
def create_juice_particles(cx, cy, color, count=15):
    for _ in range(count):
        particles.append({"x": cx, "y": cy, "vx": random.uniform(-4,4), "vy": random.uniform(-6,-1), "life": random.randint(14,30), "color": color})
def create_bomb_particles(cx, cy, count=25):
    for _ in range(count):
        particles.append({"x": cx, "y": cy, "vx": random.uniform(-6,6), "vy": random.uniform(-6,2), "life": random.randint(20,40), "color": (0,0,255)})
def update_particles(frame):
    for p in particles[:]:
        p["vy"] += 0.22; p["x"] += p["vx"]; p["y"] += p["vy"]
        alpha = max(0.2, p["life"]/40)
        col = (int(p["color"][0]*alpha), int(p["color"][1]*alpha), int(p["color"][2]*alpha))
        cv2.circle(frame, (int(p["x"]), int(p["y"])), 3, col, -1)
        p["life"] -= 1
        if p["life"] <= 0: particles.remove(p)

entities = []
def spawn_entity():
    global CUR_BOMB_CHANCE, CUR_SPEED_MIN, CUR_SPEED_MAX, frenzy_timer
    is_frenzy = (frenzy_timer > 0)

    if not is_frenzy and BOMB_ENABLED and random.random() < CUR_BOMB_CHANCE:
        scale = TARGET_FRUIT_SIZE / max(bomb_img.shape[0], bomb_img.shape[1])
        speed = random.uniform(CUR_SPEED_MIN, CUR_SPEED_MAX)
        entities.append({"type":"bomb", "img": bomb_img, "x": random.randint(40, FRAME_W-120), "y": FRAME_H+40, "vx": random.uniform(-3,3), "vy": -speed, "rot": 0, "rot_speed": random.uniform(-8,8), "scale": scale})
        return

    if not is_frenzy and GOLD_APPLE_ENABLED and random.random() < 0.03:
        scale = TARGET_FRUIT_SIZE / max(gold_apple_img.shape[0], gold_apple_img.shape[1])
        speed = random.uniform(CUR_SPEED_MIN, CUR_SPEED_MAX)
        entities.append({"type": "gold_apple", "img": gold_apple_img, "x": random.randint(40, FRAME_W-120), "y": FRAME_H+40, "vx": random.uniform(-3,3), "vy": -speed, "rot": 0, "rot_speed": random.uniform(-10,10), "scale": scale, "state": "full"})
        return

    if not is_frenzy and ICE_BANANA_ENABLED and random.random() < 0.05:
        scale = TARGET_FRUIT_SIZE / max(ice_banana_img.shape[0], ice_banana_img.shape[1])
        speed = random.uniform(CUR_SPEED_MIN, CUR_SPEED_MAX)
        entities.append({"type": "ice_banana", "img": ice_banana_img, "x": random.randint(40, FRAME_W-120), "y": FRAME_H+40, "vx": random.uniform(-3,3), "vy": -speed, "rot": 0, "rot_speed": random.uniform(-10,10), "scale": scale, "state": "full"})
        return

    if not fruit_defs: return
    defn = random.choice(fruit_defs)
    full_raw = defn["full"]; h_raw, w_raw = full_raw.shape[:2]
    spawn_scale = TARGET_FRUIT_SIZE / max(h_raw, w_raw)
    w_new = int(w_raw * spawn_scale); h_new = int(h_raw * spawn_scale)
    full_scaled = cv2.resize(full_raw, (w_new, h_new), interpolation=cv2.INTER_AREA)
    h1_scaled = cv2.resize(defn["h1"], (0,0), fx=spawn_scale, fy=spawn_scale); h2_scaled = cv2.resize(defn["h2"], (0,0), fx=spawn_scale, fy=spawn_scale)
    speed = random.uniform(CUR_SPEED_MIN, CUR_SPEED_MAX)
    entities.append({
        "type": "fruit", "name": defn["name"], "img_full": full_scaled, "img_h1": h1_scaled, "img_h2": h2_scaled,
        "w": w_new, "h": h_new, "x": random.randint(10, FRAME_W-w_new-10), "y": FRAME_H+40,
        "vx": random.uniform(-3,3), "vy": -speed, "rot": random.uniform(-40,40), "rot_speed": random.uniform(-9,9),
        "state": "full", "half_pos": None, "half_v": None, "half_rot": 0, "half_rot_speed": 0, "color": defn["color"]
    })

def segment_circle_intersection(p1, p2, circle_center, radius):
    x1, y1 = p1; x2, y2 = p2; cx, cy = circle_center
    dx, dy = x2 - x1, y2 - y1
    if dx == 0 and dy == 0: return False
    t = ((cx - x1) * dx + (cy - y1) * dy) / (dx*dx + dy*dy)
    t = max(0, min(1, t))
    closest_x = x1 + t * dx; closest_y = y1 + t * dy
    dist_sq = (cx - closest_x)**2 + (cy - closest_y)**2
    return dist_sq < (radius * radius)

# [MODIFIED] Tombol dengan Loading Bar (Hold to Click)
def draw_button_with_progress(frame, btn_id, text, x, y, w, h, color, nose_pos, active=True):
    global hover_timers
    
    # Init timer jika belum ada
    if btn_id not in hover_timers:
        hover_timers[btn_id] = 0

    is_hovering = False
    if active and nose_pos:
        if (x < nose_pos[0] < x+w) and (y < nose_pos[1] < y+h):
            is_hovering = True
    
    # Cek Mouse juga
    mouse_hover = False
    if active and (x < mouse_x < x+w) and (y < mouse_y < y+h):
        mouse_hover = True
        if mouse_clicked: # Mouse langsung klik, gak perlu nunggu
            hover_timers[btn_id] = BUTTON_HOLD_TIME + 1
            is_hovering = True

    # Update Timer Logic
    if is_hovering:
        hover_timers[btn_id] += 1
    else:
        hover_timers[btn_id] = max(0, hover_timers[btn_id] - 2) # Turun perlahan kalau lepas

    # Progress (0.0 to 1.0)
    progress = min(1.0, hover_timers[btn_id] / BUTTON_HOLD_TIME)

    # Warna dasar (sedikit gelap)
    base_color = (int(color[0]*0.6), int(color[1]*0.6), int(color[2]*0.6))
    if not active: base_color = (50, 50, 50)

    # Gambar Background Tombol
    cv2.rectangle(frame, (x, y), (x+w, y+h), base_color, -1)
    
    # Gambar Progress Bar (Isian)
    if active and progress > 0:
        fill_w = int(w * progress)
        cv2.rectangle(frame, (x, y), (x+fill_w, y+h), color, -1)

    # Border
    border_col = (255, 255, 255) if active else (100, 100, 100)
    cv2.rectangle(frame, (x, y), (x+w, y+h), border_col, 2)

    # Text
    text_col = (255, 255, 255) if active else (150, 150, 150)
    font = cv2.FONT_HERSHEY_SIMPLEX
    tsize = cv2.getTextSize(text, font, 0.7, 2)[0]
    tx = x + (w - tsize[0]) // 2
    ty = y + (h + tsize[1]) // 2
    cv2.putText(frame, text, (tx, ty), font, 0.7, text_col, 2)

    # Return True jika triggered
    if hover_timers[btn_id] >= BUTTON_HOLD_TIME:
        hover_timers[btn_id] = 0 # Reset setelah klik
        return True
    return False

def draw_fancy_trail(frame, points, score_best):
    if len(points) < 2: return
    style = "BASIC"
    if score_best >= 50: style = "RAINBOW"
    elif score_best >= 20: style = "FIRE"

    for i in range(1, len(points)):
        thickness = int(6 * (i / len(points)) + 1)
        if style == "RAINBOW":
            hue = (time.time() * 0.8 + i * 0.05) % 1.0
            r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
            color = (int(b*255), int(g*255), int(r*255)) 
        elif style == "FIRE":
            progress = i / len(points)
            color = (0, int(255 * progress), 255)
        else:
            color = (200, 200, 255)
        cv2.line(frame, points[i-1], points[i], color, thickness)

def set_difficulty(level):
    global current_level, CUR_SPAWN_INTERVAL, CUR_GRAVITY, CUR_SPEED_MIN, CUR_SPEED_MAX, CUR_BOMB_CHANCE
    current_level = level
    settings = LEVEL_SETTINGS.get(level, LEVEL_SETTINGS[3])
    CUR_SPAWN_INTERVAL = settings["spawn"]
    CUR_GRAVITY = settings["grav"]
    CUR_SPEED_MIN = settings["speed_min"]
    CUR_SPEED_MAX = settings["speed_max"]
    CUR_BOMB_CHANCE = settings["bomb"]

# ================================
# MAIN LOOP
# ================================
STATE_MENU, STATE_LEVEL_SELECT, STATE_READY, STATE_PLAY, STATE_GAMEOVER, STATE_SNAPSHOT, STATE_PRE_RECAP = 0,1,2,3,4,5,6
game_state = STATE_MENU
score = 0; timer_frames = 0; nose_prev = None
trail_points = []; nose_history = deque(maxlen=5); state_timer = 0 

# Variable List Recap
photo_gallery = [] 
current_slide_idx = 0

cv2.namedWindow("Game")
cv2.setMouseCallback("Game", mouse_callback)

blank_frame = np.zeros((FRAME_H, FRAME_W, 3), dtype=np.uint8)

try:
    while True:
        # LOGIKA KAMERA ON/OFF
        if camera_active:
            frame = video_stream.read()
            if frame is None: 
                frame = blank_frame.copy()
            else:
                frame = cv2.flip(frame, 1)
                frame = cv2.resize(frame, (FRAME_W, FRAME_H))
                # Simpan frame ke buffer untuk Anti-Blur
                frame_buffer.append(frame.copy())
        else:
            frame = blank_frame.copy()
            cv2.putText(frame, "KAMERA MATI", (210, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (100,100,100), 2)

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        nose = None
        if camera_active:
            results = face_mesh.process(rgb)
            if results.multi_face_landmarks:
                lm = results.multi_face_landmarks[0].landmark[4]
                nose_raw = (int(lm.x * FRAME_W), int(lm.y * FRAME_H))
                nose_history.append(nose_raw)
                avg_x = int(sum(p[0] for p in nose_history) / len(nose_history))
                avg_y = int(sum(p[1] for p in nose_history) / len(nose_history))
                nose = (avg_x, avg_y)
                cv2.circle(frame, nose, 6, (0,255,255), -1)
            else:
                nose_history.clear()

            if nose: trail_points.append(nose)
            if len(trail_points) > 20: trail_points.pop(0)
            draw_fancy_trail(frame, trail_points, high_score)
        else:
            nose_history.clear()
            trail_points.clear()

        if state_timer > 0: state_timer -= 1
        input_allowed = (state_timer == 0)

        # 1. MENU UTAMA
        if game_state == STATE_MENU:
            play_music("menu") 
            # Title yang lebih rapi
            cv2.putText(frame, "FRUIT NINJA NOSE", (140, 100), cv2.FONT_HERSHEY_DUPLEX, 1.2, (255, 255, 255), 3)
            cv2.putText(frame, f"High Score: {high_score}", (230, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 215, 0), 2)
            
            # Tombol Menu Utama (Tengah)
            start_color = (0, 200, 0) if camera_active else (50, 50, 50)
            if draw_button_with_progress(frame, "btn_start", "START GAME", 220, 200, 200, 60, start_color, nose, active=(input_allowed and camera_active)):
                game_state = STATE_LEVEL_SELECT; state_timer = 30 
            
            if draw_button_with_progress(frame, "btn_exit", "EXIT", 220, 280, 200, 60, (0, 0, 200), nose, active=input_allowed):
                break

            # Tombol Kamera (Kiri Bawah)
            if not camera_active:
                if draw_button_with_progress(frame, "btn_cam_on", "CAM ON", 50, 380, 120, 50, (0, 200, 200), nose, active=input_allowed):
                    video_stream.start(); camera_active = True; state_timer = 20 
            else:
                if draw_button_with_progress(frame, "btn_cam_off", "CAM OFF", 50, 380, 120, 50, (150, 50, 50), nose, active=input_allowed):
                    video_stream.stop(); camera_active = False; state_timer = 20

            # Tombol Reset (Kanan Bawah)
            if draw_button_with_progress(frame, "btn_reset", "RESET", 470, 380, 120, 50, (200, 50, 50), nose, active=input_allowed):
                high_score = 0; save_high_score(0)
                cv2.putText(frame, "RESET!", (490, 370), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        # 2. PILIH LEVEL
        elif game_state == STATE_LEVEL_SELECT:
            cv2.putText(frame, "PILIH KESULITAN", (180, 80), cv2.FONT_HERSHEY_DUPLEX, 1.0, (255, 255, 0), 2)
            btn_w, btn_h = 70, 70; gap = 20
            total_w = (5 * btn_w) + (4 * gap); start_x = (FRAME_W - total_w) // 2; btn_y = 300
            
            for lvl in range(1, 6):
                bx = start_x + (lvl-1)*(btn_w+gap)
                col = (50, 255 - (lvl*40), 50 + (lvl*40))
                # Menggunakan ID unik untuk tiap tombol level
                if draw_button_with_progress(frame, f"lvl_{lvl}", str(lvl), bx, btn_y, btn_w, btn_h, col, nose, active=input_allowed):
                    set_difficulty(lvl); game_state = STATE_READY; state_timer = 30

        # 3. READY
        elif game_state == STATE_READY:
            play_music("play")
            cv2.putText(frame, f"LEVEL {current_level}", (220,180), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0,255,255), 3)
            cv2.putText(frame, "SIAP...", (250,250), cv2.FONT_HERSHEY_SIMPLEX, 2.0, (0,255,0), 4)
            cv2.imshow("Game", frame); cv2.waitKey(800)
            
            game_state = STATE_PLAY; score = 0; timer_frames = 60 * 30
            entities.clear(); particles.clear(); freeze_timer = 0; frenzy_timer = 0; spawn_counter = 0
            photo_gallery = [] # Reset list foto
            frame_buffer.clear() # Clear buffer
            continue

        # 4. GAMEPLAY
        elif game_state == STATE_PLAY:
            if not camera_active: game_state = STATE_MENU; continue

            is_frozen = (freeze_timer > 0); is_frenzy = (frenzy_timer > 0)
            if is_frenzy: play_music("frenzy")
            else: play_music("play")

            time_scale = SLOW_FACTOR if is_frozen else 1.0
            
            if is_frozen:
                freeze_timer -= 1; cv2.putText(frame, "FREEZE MODE!", (220, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 0), 3); cv2.rectangle(frame, (0,0), (FRAME_W, FRAME_H), (255, 255, 0), 5) 
            elif is_frenzy:
                frenzy_timer -= 1; cv2.putText(frame, "FRENZY!!!", (240, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 4); cv2.rectangle(frame, (0,0), (FRAME_W, FRAME_H), (0, 0, 255), 8) 

            spawn_counter += 1
            current_interval = FRENZY_SPAWN_RATE if is_frenzy else CUR_SPAWN_INTERVAL
            if spawn_counter % current_interval == 0: spawn_entity()

            for e in entities[:]:
                e["x"] += e["vx"] * time_scale; e["y"] += e["vy"] * time_scale
                e["vy"] += CUR_GRAVITY * time_scale
                e["rot"] += e.get("rot_speed", 0) * 0.35 * time_scale
                if e["y"] > FRAME_H + 200: 
                    if e in entities: entities.remove(e)
                    continue
                
                if e["type"] in ["bomb", "ice_banana", "gold_apple"]:
                    frame = overlay_png(frame, e["img"], e["x"], e["y"], e["rot"], e["scale"])
                    if e["type"] == "ice_banana":
                          cx, cy = int(e["x"] + (e["img"].shape[1]*e["scale"])/2), int(e["y"] + (e["img"].shape[0]*e["scale"])/2)
                          cv2.circle(frame, (cx, cy), 40, (255, 255, 0), 3)
                    if e["type"] == "gold_apple":
                          cx, cy = int(e["x"] + (e["img"].shape[1]*e["scale"])/2), int(e["y"] + (e["img"].shape[0]*e["scale"])/2)
                          cv2.circle(frame, (cx, cy), 40, (0, 165, 255), 4)
                else:
                    if e["state"]=="full": frame = overlay_png(frame, e["img_full"], e["x"], e["y"], e["rot"])
                    else:
                        if e["img_h1"] is not None: frame = overlay_png(frame, e["img_h1"], e["half_pos"][0][0], e["half_pos"][0][1], e["half_rot"])
                        if e["img_h2"] is not None: frame = overlay_png(frame, e["img_h2"], e["half_pos"][1][0], e["half_pos"][1][1], -e["half_rot"])
                        for i in (0,1): 
                            e["half_pos"][i][0]+=e["half_v"][i][0] * time_scale
                            e["half_pos"][i][1]+=e["half_v"][i][1] * time_scale
                            e["half_v"][i][1]+=CUR_GRAVITY * time_scale
                        e["half_rot"]+=e["half_rot_speed"] * time_scale

            # COLLISION
            if nose_prev and nose:
                dist = math.hypot(nose[0]-nose_prev[0], nose[1]-nose_prev[1])
                if dist > NOSE_SLASH_MIN_DIST and dist >= NOSE_SLASH_SPEED_REQ:
                    for e in entities[:]:
                        if e["type"] == "bomb":
                            cx, cy = e["x"] + (e["img"].shape[1]*e["scale"])/2, e["y"] + (e["img"].shape[0]*e["scale"])/2
                            radius = (e["img"].shape[0]*e["scale"]) * 0.4
                            if segment_circle_intersection(nose_prev, nose, (cx, cy), radius):
                                create_bomb_particles(cx, cy); score = max(0, score-10)
                                if bomb_sound: bomb_sound.play()
                                entities.remove(e)
                        elif e["type"] == "ice_banana":
                            cx, cy = e["x"] + (e["img"].shape[1]*e["scale"])/2, e["y"] + (e["img"].shape[0]*e["scale"])/2
                            radius = (e["img"].shape[0]*e["scale"]) * 0.45
                            if segment_circle_intersection(nose_prev, nose, (cx, cy), radius):
                                score += 5; freeze_timer = FREEZE_DURATION; frenzy_timer = 0
                                create_juice_particles(cx, cy, (255, 255, 0), count=30)
                                if splash_sound: splash_sound.play()
                                entities.remove(e)
                        elif e["type"] == "gold_apple":
                            cx, cy = e["x"] + (e["img"].shape[1]*e["scale"])/2, e["y"] + (e["img"].shape[0]*e["scale"])/2
                            radius = (e["img"].shape[0]*e["scale"]) * 0.45
                            if segment_circle_intersection(nose_prev, nose, (cx, cy), radius):
                                score += 10; frenzy_timer = FRENZY_DURATION; freeze_timer = 0
                                create_juice_particles(cx, cy, (0, 165, 255), count=40)
                                if splash_sound: splash_sound.play()
                                entities.remove(e)
                        elif e["state"]=="full":
                            cx, cy = e["x"] + e["w"]/2, e["y"] + e["h"]/2
                            radius = max(e["w"], e["h"]) * 0.45
                            if segment_circle_intersection(nose_prev, nose, (cx, cy), radius):
                                e["state"]="cut"; score+=1
                                e["half_pos"]=[[e["x"],e["y"]], [e["x"]+e["w"]//2,e["y"]]]
                                e["half_v"]=[[-3,-7], [3,-7]]
                                e["half_rot"]=e["rot"]; e["half_rot_speed"]=random.uniform(-10,10)
                                create_juice_particles(cx, cy, e["color"])
                                if splash_sound: splash_sound.play()
                                if cut_sound: cut_sound.play()

            update_particles(frame)
            
            # --- [SMART CAPTURE LOGIC] ---
            # Mengambil frame terbaik dari buffer (paling tidak blur)
            capture_moment = False
            best_img = None

            if timer_frames == 1300 or timer_frames == 700 or timer_frames <= 0:
                capture_moment = True
                best_img = get_best_frame_from_buffer() # <-- Menggunakan fungsi baru anti-blur

            if timer_frames == 1300: 
                filename = os.path.join(SNAPSHOT_FOLDER, f"game_{int(time.time())}_1.jpg")
                if best_img is not None:
                    cv2.imwrite(filename, best_img)
                    photo_gallery.append(best_img)
                
            elif timer_frames == 700: 
                filename = os.path.join(SNAPSHOT_FOLDER, f"game_{int(time.time())}_2.jpg")
                if best_img is not None:
                    cv2.imwrite(filename, best_img)
                    photo_gallery.append(best_img)
            
            timer_frames -= 1
            cv2.putText(frame, f"Lv.{current_level} Score: {score}", (20,40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2)
            cv2.putText(frame, f"{timer_frames//30}", (FRAME_W-60,40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200,255,200), 2)
            
            # --- WAKTU HABIS ---
            if timer_frames <= 0: 
                # Simpan foto terakhir (Foto ke-3)
                filename = os.path.join(SNAPSHOT_FOLDER, f"game_{int(time.time())}_3.jpg")
                if best_img is not None:
                    cv2.imwrite(filename, best_img)
                    photo_gallery.append(best_img)
                
                # Fallback jika gallery kosong (sangat jarang terjadi)
                while len(photo_gallery) < 3:
                    photo_gallery.append(frame.copy())
                photo_gallery = photo_gallery[-3:] 

                # Masuk ke PRE_RECAP
                game_state = STATE_PRE_RECAP 
                state_timer = 180 
                
                if score > high_score: high_score = score; save_high_score(high_score)

        # 5. STATE PRE_RECAP
        elif game_state == STATE_PRE_RECAP:
            if len(photo_gallery) > 0:
                frame = photo_gallery[-1].copy()
                frame = cv2.addWeighted(frame, 0.5, np.zeros(frame.shape, dtype=np.uint8), 0.5, 0)
            
            cv2.putText(frame, "WAKTU HABIS!", (180, 220), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)
            cv2.putText(frame, "SIAP-SIAP LIHAT RECAP...", (140, 270), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

            if state_timer <= 0:
                game_state = STATE_SNAPSHOT 
                state_timer = 200 
                current_slide_idx = -1

        # 6. STATE SNAPSHOT (Slideshow)
        elif game_state == STATE_SNAPSHOT:
            slide_duration = 50
            new_slide_idx = 2 - (state_timer // slide_duration) 
            new_slide_idx = max(0, min(2, new_slide_idx)) 

            if new_slide_idx != current_slide_idx:
                current_slide_idx = new_slide_idx
                if shutter_sound: shutter_sound.play() 
            
            if len(photo_gallery) > current_slide_idx:
                frame = photo_gallery[current_slide_idx].copy()
            
            cv2.rectangle(frame, (0, 0), (FRAME_W, 60), (0,0,0), -1) 
            cv2.putText(frame, "RECAP GAMEPLAY", (200, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
            cv2.putText(frame, f"Foto {current_slide_idx+1}/3", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 1)
            
            if state_timer <= 0:
                game_state = STATE_GAMEOVER

        # 7. GAMEOVER
        elif game_state == STATE_GAMEOVER:
            frame = blank_frame.copy()

            cv2.putText(frame, "GAME OVER", (170,120), cv2.FONT_HERSHEY_SIMPLEX, 2.0, (0,0,255), 4)
            cv2.putText(frame, f"Final Score: {score}", (200,200), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255,255,255), 2)
            cv2.putText(frame, f"Best: {high_score}", (240, 250), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,215,0), 2)
            
            # Tombol Menu di tengah bawah
            if draw_button_with_progress(frame, "btn_main_menu", "MENU UTAMA", 220, 320, 200, 70, (100,200,100), nose, active=input_allowed):
                game_state = STATE_MENU; state_timer = 30 

        nose_prev = nose
        if mouse_clicked: mouse_clicked = False
        cv2.imshow("Game", frame)
        if cv2.waitKey(1) & 0xFF == 27: break

finally:
    stop_all_audio()
    if video_stream.stream: video_stream.stop()
    cv2.destroyAllWindows()
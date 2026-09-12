import tkinter as tk
from tkinter import ttk, messagebox
import serial
import threading
import time
import math

PORT = "COM6"
BAUD = 115200
CX, CY, RADIUS = 360, 380, 330
MAX_DISTANCE = 200
DANGER_DISTANCE = 30
WARNING_DISTANCE = 50

ser = None
running = True
scan_paused = False
locked = False
current_angle = 90
current_distance = -1
selected_target = None
target_counter = 0
targets = {}
detections = []
lock = threading.Lock()


def connect_serial():
    global ser
    try:
        ser = serial.Serial(PORT, BAUD, timeout=0.1)
        time.sleep(2)
        return True
    except Exception as e:
        messagebox.showerror("Serial Error", f"Could not open {PORT}:\n{e}")
        return False


def send_command(command):
    if ser and ser.is_open:
        try:
            ser.write((command + "\n").encode())
        except Exception:
            pass


def classify_speed(speed):
    if abs(speed) < 3:
        return "STATIONARY"
    if speed < -50:
        return "FAST APPROACH"
    if speed < 0:
        return "APPROACHING"
    return "MOVING AWAY"


def update_target(angle, distance):
    global target_counter
    now = time.time()
    best_id = None
    best_score = 999999

    with lock:
        for tid, t in targets.items():
            if now - t["last_seen"] > 2.0:
                continue
            angle_diff = abs(angle - t["angle"])
            distance_diff = abs(distance - t["distance"])
            if angle_diff <= 10 and distance_diff <= 25:
                score = angle_diff + distance_diff * 0.2
                if score < best_score:
                    best_score = score
                    best_id = tid

        if best_id is None:
            target_counter += 1
            best_id = f"T{target_counter:02d}"
            targets[best_id] = {
                "angle": angle,
                "distance": distance,
                "last_seen": now,
                "previous_distance": distance,
                "previous_time": now,
                "speed": 0.0,
                "status": "STATIONARY",
            }
        else:
            t = targets[best_id]
            dt = now - t["previous_time"]
            speed = 0.0
            if dt > 0:
                speed = (distance - t["previous_distance"]) / dt
            t["speed"] = speed
            t["status"] = classify_speed(speed)
            t["previous_distance"] = distance
            t["previous_time"] = now
            t["angle"] = angle
            t["distance"] = distance
            t["last_seen"] = now

        detections.append((angle, distance, now))
        if len(detections) > 300:
            del detections[:-300]


def cleanup_targets():
    now = time.time()
    with lock:
        stale = [tid for tid, t in targets.items()
                 if now - t["last_seen"] > 2.0 and tid != selected_target]
        for tid in stale:
            del targets[tid]


def serial_reader():
    global current_angle, current_distance
    while running:
        if ser and ser.is_open:
            try:
                line = ser.readline().decode(errors="ignore").strip()
                if line and "," in line:
                    a, d = line.split(",", 1)
                    angle = int(float(a))
                    distance = float(d)
                    if 0 <= angle <= 180 and distance > 0:
                        current_angle = angle
                        current_distance = distance
                        update_target(angle, distance)
            except Exception:
                pass
        time.sleep(0.005)


def play():
    global scan_paused, locked
    scan_paused = False
    locked = False
    send_command("R")
    status_var.set("SCANNING")


def pause():
    global scan_paused, locked
    scan_paused = True
    locked = False
    send_command("P")
    status_var.set("PAUSED")


def home():
    global locked
    locked = False
    send_command("H")
    status_var.set("HOME 90°")


def left():
    send_command("L")


def right():
    send_command("D")


def lock_target():
    global selected_target, locked
    if selected_target in targets:
        angle = int(targets[selected_target]["angle"])
        send_command(f"A{angle}")
        locked = True
        status_var.set(f"LOCKED {selected_target}")


def unlock_target():
    global locked
    locked = False
    send_command("R")
    status_var.set("SCANNING")


def apply_range():
    try:
        start = int(start_var.get())
        end = int(end_var.get())
        if 0 <= start < end <= 180:
            send_command(f"G{start},{end}")
            status_var.set(f"RANGE {start}°–{end}°")
    except ValueError:
        pass


def change_speed(value):
    send_command(f"V{int(float(value))}")


def change_step(value):
    send_command(f"Q{int(float(value))}")


def on_target_select(event=None):
    global selected_target
    item = tree.selection()
    if item:
        selected_target = tree.item(item[0], "values")[0]


def draw_radar():
    canvas.delete("all")

    # Background/radar rings
    canvas.create_oval(CX-RADIUS, CY-RADIUS, CX+RADIUS, CY+RADIUS, outline="#1f6f3a", width=2)
    for cm in (50, 100, 150, 200):
        r = RADIUS * cm / MAX_DISTANCE
        canvas.create_arc(CX-r, CY-r, CX+r, CY+r, start=0, extent=180,
                          outline="#164f2c", width=1)
        canvas.create_text(CX+r-12, CY-r+12, text=f"{cm}cm", fill="#4caf72", font=("Consolas", 9))

    for a in range(0, 181, 30):
        rad = math.radians(180-a)
        x = CX + RADIUS * math.cos(rad)
        y = CY - RADIUS * math.sin(rad)
        canvas.create_line(CX, CY, x, y, fill="#123d24")
        canvas.create_text(x, y, text=f"{a}°", fill="#4caf72", font=("Consolas", 9))

    # Danger zone
    r = RADIUS * DANGER_DISTANCE / MAX_DISTANCE
    canvas.create_arc(CX-r, CY-r, CX+r, CY+r, start=0, extent=180,
                      outline="#aa3333", width=2)

    # Fading detections
    now = time.time()
    with lock:
        recent = list(detections)
    for a, d, timestamp in recent:
        age = now - timestamp
        if age > 3:
            continue
        r = min(RADIUS, RADIUS * d / MAX_DISTANCE)
        rad = math.radians(180-a)
        x = CX + r * math.cos(rad)
        y = CY - r * math.sin(rad)
        canvas.create_oval(x-3, y-3, x+3, y+3, fill="#d33", outline="")

    # Beam
    rad = math.radians(180-current_angle)
    bx = CX + RADIUS * math.cos(rad)
    by = CY - RADIUS * math.sin(rad)
    canvas.create_line(CX, CY, bx, by, fill="#39d96f", width=3)

    # Target markers
    with lock:
        items = list(targets.items())
    for tid, t in items:
        d = t["distance"]
        if d > MAX_DISTANCE:
            continue
        r = RADIUS * d / MAX_DISTANCE
        rad = math.radians(180-t["angle"])
        x = CX + r * math.cos(rad)
        y = CY - r * math.sin(rad)
        radius = 8 if tid == selected_target else 5
        canvas.create_oval(x-radius, y-radius, x+radius, y+radius, outline="#ff4444", width=2)
        canvas.create_text(x+18, y-12, text=tid, fill="#ff7777", font=("Consolas", 9, "bold"))

    canvas.create_text(CX, 25, text="ULTRASONIC RADAR", fill="#65e38c", font=("Consolas", 20, "bold"))
    canvas.create_text(CX, CY+25, text=f"{current_angle}°   {current_distance:.1f} cm" if current_distance > 0 else f"{current_angle}°   --", fill="#65e38c", font=("Consolas", 12))


def update_ui():
    cleanup_targets()
    angle_var.set(f"{current_angle}°")
    distance_var.set(f"{current_distance:.1f} cm" if current_distance > 0 else "--")

    for item in tree.get_children():
        tree.delete(item)
    with lock:
        items = list(targets.items())
    for tid, t in items:
        tree.insert("", "end", values=(tid, f"{t['angle']:.0f}°", f"{t['distance']:.1f}", f"{t['speed']:.1f}", t["status"]))

    alarm = "CLEAR"
    for _, t in items:
        if t["distance"] <= DANGER_DISTANCE:
            alarm = "CRITICAL"
            break
        if t["distance"] <= WARNING_DISTANCE:
            alarm = "WARNING"
    alarm_var.set(alarm)
    draw_radar()
    root.after(50, update_ui)


def close_app():
    global running
    running = False
    try:
        if ser:
            ser.close()
    except Exception:
        pass
    root.destroy()


root = tk.Tk()
root.title("Ultrasonic Radar Scanner")
root.geometry("1250x760")
root.configure(bg="#07130c")
root.protocol("WM_DELETE_WINDOW", close_app)

style = ttk.Style()
try:
    style.theme_use("clam")
except Exception:
    pass
style.configure("Treeview", background="#0d1c13", foreground="#7ee99a", fieldbackground="#0d1c13", rowheight=25)
style.configure("Treeview.Heading", background="#183522", foreground="#8af0a5")

main = tk.Frame(root, bg="#07130c")
main.pack(fill="both", expand=True)

canvas = tk.Canvas(main, width=740, height=740, bg="#050b07", highlightthickness=0)
canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)

panel = tk.Frame(main, bg="#0b1a10", width=430)
panel.pack(side="right", fill="y", padx=10, pady=10)
panel.pack_propagate(False)

tk.Label(panel, text="RADAR CONTROL", bg="#0b1a10", fg="#79ed98", font=("Consolas", 18, "bold")).pack(pady=12)

btn_frame = tk.Frame(panel, bg="#0b1a10")
btn_frame.pack()
for text, cmd in [("▶ PLAY", play), ("⏸ PAUSE", pause), ("🎯 LOCK TARGET", lock_target), ("🔓 UNLOCK", unlock_target), ("◀ LEFT 5°", left), ("🏠 HOME 90°", home), ("RIGHT 5° ▶", right)]:
    tk.Button(btn_frame, text=text, command=cmd, width=17, bg="#173522", fg="#9af5b1", activebackground="#265537", activeforeground="white", relief="flat", font=("Consolas", 10, "bold")).pack(pady=3)

status_var = tk.StringVar(value="CONNECTING...")
alarm_var = tk.StringVar(value="CLEAR")
angle_var = tk.StringVar(value="--")
distance_var = tk.StringVar(value="--")

tk.Label(panel, text="STATUS", bg="#0b1a10", fg="#6ea77e", font=("Consolas", 9)).pack(pady=(15, 0))
tk.Label(panel, textvariable=status_var, bg="#0b1a10", fg="#8af0a5", font=("Consolas", 13, "bold")).pack()

tk.Label(panel, text="ALARM", bg="#0b1a10", fg="#6ea77e", font=("Consolas", 9)).pack(pady=(10, 0))
tk.Label(panel, textvariable=alarm_var, bg="#0b1a10", fg="#ff6666", font=("Consolas", 15, "bold")).pack()

tk.Label(panel, text="LIVE", bg="#0b1a10", fg="#6ea77e", font=("Consolas", 9)).pack(pady=(10, 0))
tk.Label(panel, textvariable=angle_var, bg="#0b1a10", fg="#9af5b1", font=("Consolas", 12)).pack()
tk.Label(panel, textvariable=distance_var, bg="#0b1a10", fg="#9af5b1", font=("Consolas", 12)).pack()

tk.Label(panel, text="TARGETS", bg="#0b1a10", fg="#79ed98", font=("Consolas", 12, "bold")).pack(pady=(15, 5))
cols = ("ID", "ANGLE", "DIST", "SPEED", "STATUS")
tree = ttk.Treeview(panel, columns=cols, show="headings", height=8)
for c in cols:
    tree.heading(c, text=c)
    tree.column(c, width=70 if c != "STATUS" else 105, anchor="center")
tree.pack(padx=8, fill="x")
tree.bind("<<TreeviewSelect>>", on_target_select)

tk.Label(panel, text="SCAN RANGE", bg="#0b1a10", fg="#79ed98", font=("Consolas", 12, "bold")).pack(pady=(15, 4))
range_frame = tk.Frame(panel, bg="#0b1a10")
range_frame.pack()
start_var = tk.StringVar(value="0")
end_var = tk.StringVar(value="180")
tk.Entry(range_frame, textvariable=start_var, width=6, bg="#102218", fg="white", insertbackground="white").pack(side="left", padx=3)
tk.Label(range_frame, text="to", bg="#0b1a10", fg="white").pack(side="left")
tk.Entry(range_frame, textvariable=end_var, width=6, bg="#102218", fg="white", insertbackground="white").pack(side="left", padx=3)
tk.Button(range_frame, text="APPLY", command=apply_range, bg="#173522", fg="#9af5b1", relief="flat").pack(side="left", padx=5)

tk.Label(panel, text="SCAN SPEED (delay ms)", bg="#0b1a10", fg="#79ed98", font=("Consolas", 10)).pack(pady=(12, 0))
speed_scale = tk.Scale(panel, from_=30, to=500, orient="horizontal", command=change_speed, bg="#0b1a10", fg="#9af5b1", highlightthickness=0)
speed_scale.set(120)
speed_scale.pack(fill="x", padx=15)

tk.Label(panel, text="SCAN STEP (degrees)", bg="#0b1a10", fg="#79ed98", font=("Consolas", 10)).pack(pady=(8, 0))
step_scale = tk.Scale(panel, from_=1, to=10, orient="horizontal", command=change_step, bg="#0b1a10", fg="#9af5b1", highlightthickness=0)
step_scale.set(5)
step_scale.pack(fill="x", padx=15)

tk.Label(panel, text="Space Play/Pause   P Pause   R Resume\nL Left   D Right   H Home   T Lock", bg="#0b1a10", fg="#5f8f6d", font=("Consolas", 8)).pack(side="bottom", pady=10)


def key_handler(event):
    key = event.keysym.lower()
    if key == "space":
        pause() if not scan_paused else play()
    elif key == "p": pause()
    elif key == "r": play()
    elif key == "l": left()
    elif key == "d": right()
    elif key == "h": home()
    elif key == "t": lock_target()

root.bind("<Key>", key_handler)

if connect_serial():
    status_var.set("SCANNING")
    threading.Thread(target=serial_reader, daemon=True).start()
else:
    status_var.set("SERIAL ERROR")

update_ui()
root.mainloop()

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.gridspec as gridspec
import asyncio
import threading
import time
import sys
import signal
from bleak import BleakClient, BleakScanner
from matplotlib.widgets import Button, CheckButtons

# ─────────────────────────────────────────────────────────────────────────────
# Simulation & control parameters
dt = 0.1
L = 2.0
drone_body_radius = 1.5
rotor_radius = 1.2
base_speed = 10
yaw_adjust_factor = 0.2
k_p, k_r = 0.3, 0.3
z_pitch, z_roll = 0.5, 0.5

# ─────────────────────────────────────────────────────────────────────────────
# State holders
state = {'x': 0.0, 'y': 0.0, 'z': 2.5, 'yaw': 0.0}
rotor_angle = 0.0

# Game
targets = []
coord_texts = []
game_start_time = None
best_time = None
difficult_mode = False

# Bluetooth
NOTIFY_UUID = "00002a6e-0000-1000-8000-00805f9b34fb"
bt_devices = []
bt_client = None
is_connected = False
bt_data_lock = threading.Lock()
bt_knob1_x = bt_knob1_y = bt_knob2_x = bt_knob2_y = 0.0
bt_mode = "Manual"
bt_status_text = "Bluetooth: Not connected"

# 自动退出程序的标志
program_start_time = time.time()
auto_exit_enabled = True
auto_exit_delay = 5  # 5秒后自动退出

# ─────────────────────────────────────────────────────────────────────────────
# Cleanup on exit
def cleanup_resources():
    global bt_client, is_connected
    is_connected = False
    if bt_client:
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(bt_client.disconnect())
            loop.close()
        except:
            pass

signal.signal(signal.SIGINT, lambda s,f: (cleanup_resources(), sys.exit(0)))
if sys.platform!='win32':
    signal.signal(signal.SIGTERM, lambda s,f: (cleanup_resources(), sys.exit(0)))
if sys.platform=='win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# ─────────────────────────────────────────────────────────────────────────────
# Knob for manual control
class Knob:
    def __init__(self, ax, radius=1.0):
        self.ax = ax
        self.radius = radius
        self.value = np.array([0.0,0.0])
        circle = plt.Circle((0,0),radius,fill=False,lw=2)
        ax.add_patch(circle)
        self.indicator, = ax.plot([0],[0],'ro',markersize=8)
        self.active = False

    def update(self, x, y):
        if x is None or y is None: return
        r = np.hypot(x,y)
        if r>self.radius:
            x,y = x*self.radius/r, y*self.radius/r
        self.value = np.array([x,y])
        self.indicator.set_data([x],[y])
        self.ax.figure.canvas.draw()

# ─────────────────────────────────────────────────────────────────────────────
# Dropdown & toolbar for Bluetooth
class Dropdown:
    def __init__(self, ax, width=0.4, height=0.05, x=0.5, y=0.05):
        self.ax = ax; self.fig = ax.figure
        self.items = []
        self.selected_item = None
        self.button = Button(plt.axes([x-width/2,y,width,height]),
                             "Select Device", color='lightgoldenrodyellow')
        self.button.on_clicked(self.toggle_menu)
        self.menu_visible = False
        self.menu_buttons = []

    def set_items(self, items):
        self.items = items
        if self.menu_visible: self.show_menu()

    def toggle_menu(self, event):
        if self.menu_visible: self.hide_menu()
        else: self.show_menu()

    def show_menu(self):
        self.hide_menu()
        for i,item in enumerate(self.items):
            y_pos = 0.05 + (i+1)*0.05
            ax_i = plt.axes([0.5-0.2, y_pos, 0.4, 0.05])
            btn = Button(ax_i, item, color='white')
            btn.on_clicked(lambda evt, it=item: self.select(it))
            self.menu_buttons.append((ax_i,btn))
        self.menu_visible = True
        self.fig.canvas.draw_idle()

    def hide_menu(self):
        for ax_i,btn in self.menu_buttons:
            btn.disconnect_events()
            self.fig.delaxes(ax_i)
        self.menu_buttons.clear()
        self.menu_visible = False
        self.fig.canvas.draw_idle()

    def select(self, item):
        self.selected_item = item
        self.button.label.set_text(item)
        self.hide_menu()

class ToolbarButton:
    def __init__(self, ax, label, callback, x,y,width=0.1,height=0.05):
        btn = Button(plt.axes([x,y,width,height]), label, color='lightblue')
        btn.on_clicked(callback)
        self.button = btn

# ─────────────────────────────────────────────────────────────────────────────
# Bluetooth functions (from code2)
async def scan_bluetooth_devices():
    global bt_devices, bt_status_text
    bt_status_text = "Scanning..."
    try:
        devices = await BleakScanner.discover()
        bt_devices.clear()
        for d in devices:
            if d.name:
                bt_devices.append({"name":d.name,"address":d.address})
        bt_status_text = f"Found {len(bt_devices)} devices"
        dropdown.set_items([d["name"] for d in bt_devices])
    except Exception as e:
        bt_status_text = f"Scan error: {e}"

def thread_scan_devices():
    asyncio.run(scan_bluetooth_devices())

def connect_callback(event):
    if not dropdown.selected_item:
        print("Please select a device first")
        return
    for dev in bt_devices:
        if dev["name"]==dropdown.selected_item:
            threading.Thread(target=thread_connect_device, args=(dev,), daemon=True).start()
            return

async def connect_to_device(dev):
    global bt_client, is_connected, bt_status_text, bt_mode
    bt_status_text="Connecting..."
    try:
        client = BleakClient(dev["address"], timeout=10.0)
        await client.connect()
        if client.is_connected:
            bt_client = client
            is_connected = True
            bt_status_text = "Connected"
            await client.start_notify(NOTIFY_UUID, notification_handler)
            bt_mode = "Bluetooth"
            mode_button.button.label.set_text(f"Mode: {bt_mode}")
            plt.draw()
            while client.is_connected:
                await asyncio.sleep(0.1)
    except Exception as e:
        bt_status_text=f"Conn error: {e}"
        bt_client=None
        is_connected=False

def thread_connect_device(dev):
    asyncio.run(connect_to_device(dev))

def disconnect_callback(event):
    threading.Thread(target=thread_disconnect_device, daemon=True).start()

async def disconnect_device():
    global bt_client, is_connected, bt_status_text, bt_mode
    if not bt_client:
        bt_status_text="No device"
        return
    is_connected=False
    bt_mode="Manual"
    mode_button.button.label.set_text(f"Mode: {bt_mode}")
    plt.draw()
    try: await bt_client.disconnect()
    except: pass
    bt_client=None
    bt_status_text="Disconnected"
    with bt_data_lock:
        global bt_knob1_x, bt_knob1_y, bt_knob2_x, bt_knob2_y
        bt_knob1_x=bt_knob1_y=bt_knob2_x=bt_knob2_y=0.0

def thread_disconnect_device():
    asyncio.run(disconnect_device())

def notification_handler(sender, data):
    global bt_knob1_x, bt_knob1_y, bt_knob2_x, bt_knob2_y
    try:
        text = data.decode('utf-8').strip()
        if text.startswith('[') and text.endswith(']'):
            parts = [p.strip() for p in text[1:-1].split(',')]
            vals = [float(p) for p in parts if p]
            while len(vals)<4: vals.append(0.0)
            with bt_data_lock:
                bt_knob2_x, bt_knob2_y = vals[0]/100, vals[1]/100
                bt_knob1_x, bt_knob1_y = vals[2]/100, vals[3]/100
    except:
        pass

def toggle_mode_callback(event):
    global bt_mode, bt_status_text
    if bt_mode=="Manual" and is_connected:
        bt_mode="Bluetooth"
        bt_status_text="Bluetooth mode"
    else:
        bt_mode="Manual"
        bt_status_text="Manual mode"
        knob1.update(0,0); knob2.update(0,0)
    mode_button.button.label.set_text(f"Mode: {bt_mode}")
    plt.draw()

# ─────────────────────────────────────────────────────────────────────────────
# Build the figure
fig = plt.figure(figsize=(12,10))
gs = gridspec.GridSpec(2,2, height_ratios=[9,1], hspace=0.3)
gs.update(bottom=0.2)

ax3d = fig.add_subplot(gs[0,:], projection='3d')
ax3d.set_xlim(-10,10); ax3d.set_ylim(-10,10); ax3d.set_zlim(-1,10)
ax3d.set_xlabel('X'); ax3d.set_ylabel('Y'); ax3d.set_zlabel('Z')
ax3d.set_title('Quadcopter Game + Bluetooth')

elapsed_text = fig.text(0.02,0.95,'Time: 0.00s')
best_text    = fig.text(0.02,0.90,'Best: --')
drone_text   = fig.text(0.70,0.95,'Drone: (0.00,0.00,2.50)')

ax_knob_left  = fig.add_subplot(gs[1,0])
ax_knob_right = fig.add_subplot(gs[1,1])
for ax in (ax_knob_left,ax_knob_right):
    ax.set_xlim(-1,1); ax.set_ylim(-1,1)
    ax.set_aspect('equal'); ax.set_xticks([]); ax.set_yticks([])
ax_knob_left.set_title('Knob 2 (Pitch & Roll)')
ax_knob_right.set_title('Knob 1 (Thrust & Yaw)')
knob2 = Knob(ax_knob_left)
knob1 = Knob(ax_knob_right)

fig.canvas.mpl_connect('button_press_event',
    lambda e: (setattr(knob1,'active',True), knob1.update(e.xdata,e.ydata))
              if e.inaxes==knob1.ax and bt_mode=='Manual'
              else (setattr(knob2,'active',True), knob2.update(e.xdata,e.ydata))
              if e.inaxes==knob2.ax and bt_mode=='Manual' else None)
fig.canvas.mpl_connect('motion_notify_event',
    lambda e: knob1.update(e.xdata,e.ydata) if knob1.active else knob2.update(e.xdata,e.ydata) if knob2.active else None)
fig.canvas.mpl_connect('button_release_event',
    lambda e: (knob1.update(0,0), setattr(knob1,'active',False),
               knob2.update(0,0), setattr(knob2,'active',False)))

# Create Game UI
btn_game_ax   = fig.add_axes([0.82,0.40,0.12,0.05])
btn_game      = Button(btn_game_ax,   'Create Game')
check_ax      = fig.add_axes([0.82,0.33,0.12,0.05])
check_game    = CheckButtons(check_ax, ['Difficult'], [False])
#check_game.on_clicked(lambda label: setattr(globals(), 'difficult_mode', not difficult_mode))
def on_toggle(label):
    global difficult_mode
    difficult_mode = not difficult_mode

check_game.on_clicked(on_toggle)

def create_game(event):
    global game_start_time, targets, coord_texts, state
    for txt in coord_texts: txt.remove()
    coord_texts.clear(); targets.clear()
    state.update(x=0.0,y=0.0,z=2.5)
    state['yaw'] = np.random.uniform(np.pi/2,3*np.pi/2) if difficult_mode else 0.0
    xlim,ylim,zlim = ax3d.get_xlim(), ax3d.get_ylim(), ax3d.get_zlim()
    for i in range(3):
        while True:
            tx = np.random.uniform(xlim[0]+1,xlim[1]-1)
            ty = np.random.uniform(ylim[0]+1,ylim[1]-1)
            tz = np.random.uniform(1,5)
            if np.linalg.norm([tx-state['x'],ty-state['y'],tz-state['z']])>drone_body_radius:
                break
        targets.append((tx,ty,tz))
        coord_texts.append(fig.text(0.02,0.80 - i*0.03,
                                    f'T{i+1}: ({tx:.1f},{ty:.1f},{tz:.1f})'))
    game_start_time = time.time()
    elapsed_text.set_text('Time: 0.00s')

btn_game.on_clicked(create_game)

# Bluetooth panel
ax_bt = fig.add_axes(plt.subplot2grid((10,1),(9,0),rowspan=1))
ax_bt.axis('off')
dropdown         = Dropdown(ax_bt)
refresh_button   = ToolbarButton(ax_bt, "Refresh",   lambda e: threading.Thread(target=thread_scan_devices,daemon=True).start(), x=0.05, y=0.05)
connect_button   = ToolbarButton(ax_bt, "Connect",   connect_callback, x=0.17, y=0.05)
disconnect_button= ToolbarButton(ax_bt, "Disconnect", disconnect_callback, x=0.29, y=0.05)
mode_button      = ToolbarButton(ax_bt, f"Mode: {bt_mode}", toggle_mode_callback, x=0.83, y=0.05)

bt_status = ax_bt.text(0.5,0.15,bt_status_text,ha='center',transform=ax_bt.transAxes)

# Drawing & animation
def circle_points(center, radius, n=50):
    θ = np.linspace(0,2*np.pi,n)
    return (center[0]+radius*np.cos(θ),
            center[1]+radius*np.sin(θ),
            np.full_like(θ,center[2]))

def draw_scene():
    xlim,ylim,zlim = ax3d.get_xlim(),ax3d.get_ylim(),ax3d.get_zlim()
    elev,azim = ax3d.elev,ax3d.azim
    ax3d.cla()
    ax3d.set_xlim(xlim); ax3d.set_ylim(ylim); ax3d.set_zlim(zlim)
    ax3d.view_init(elev=elev,azim=azim)
    for tx,ty,tz in targets:
        ax3d.scatter(tx,ty,0, c='gray',marker='o',s=50,alpha=0.3)
        ax3d.scatter(tx,ty,tz,c='magenta',marker='X',s=100)
    x,y,z,yaw = state['x'],state['y'],state['z'],state['yaw']
    ax3d.scatter(x,y,0,c='gray',marker='o',s=150,alpha=0.3)
    ax3d.scatter(x,y,z,c='k',marker='o',s=100)
    fx,fy = x-0.5*np.sin(yaw), y+0.5*np.cos(yaw)
    ax3d.scatter(fx,fy,z,c='yellow',marker='o',s=150)
    motors = [(( L/np.sqrt(2),  L/np.sqrt(2)),'A',1),
              (( L/np.sqrt(2), -L/np.sqrt(2)),'B',-1),
              ((-L/np.sqrt(2), -L/np.sqrt(2)),'A',1),
              ((-L/np.sqrt(2),  L/np.sqrt(2)),'B',-1)]
    R = np.array([[np.cos(yaw),-np.sin(yaw)],[np.sin(yaw),np.cos(yaw)]])
    for (lx,ly),prop,spin in motors:
        gp = R.dot([lx,ly]) + np.array([x,y])
        mx,my = gp; rel=gp-np.array([x,y])
        fwd = rel.dot([-np.sin(yaw),np.cos(yaw)])/L
        rt  = rel.dot([ np.cos(yaw),np.sin(yaw)])/L
        sf_yaw = (1-2*knob1.value[0]*yaw_adjust_factor) if prop=='A' else (1+2*knob1.value[0]*yaw_adjust_factor)
        tilt   = 1-2*k_p*knob2.value[1]*fwd-2*k_r*knob2.value[0]*rt
        sf     = sf_yaw*tilt
        mz     = z - z_pitch*knob2.value[1]*fwd - z_roll*knob2.value[0]*rt
        ax3d.plot([x,mx],[y,my],[z,mz],c='b')
        cx,cy,cz = circle_points((mx,my,mz),rotor_radius)
        ax3d.plot(cx,cy,cz,c='k')
        ang = -spin*rotor_angle*sf
        ll = rotor_radius
        x1,y1 = mx-ll*np.cos(ang), my-ll*np.sin(ang)
        x2,y2 = mx+ll*np.cos(ang), my+ll*np.sin(ang)
        ax3d.plot([x1,x2],[y1,y2],[mz,mz],c=('red' if prop=='A' else 'green'),lw=3)

def update(frame):
    global rotor_angle, state, game_start_time, best_time
        
    # Bluetooth override
    if bt_mode=="Bluetooth" and is_connected:
        with bt_data_lock:
            k1x,k1y = bt_knob1_x,bt_knob1_y
            k2x,k2y = bt_knob2_x,bt_knob2_y
        knob1.update(k1x,k1y); knob2.update(k2x,k2y)
        bt_status.set_text(bt_status_text)
    # else manual knobs
    k1x,k1y = knob1.value; k2x,k2y = knob2.value

    # physics
    rs = base_speed*(1+k1y) if k1y>=0 else base_speed*(1+0.5*k1y)
    rotor_angle += rs*dt
    state['z'] += (rs/base_speed-1)*4*dt
    state['yaw'] += (-k1x*(np.pi/8))*dt
    dx,dy = 2*k2x*dt,2*k2y*dt
    state['x'] += np.cos(state['yaw'])*dx - np.sin(state['yaw'])*dy
    state['y'] += np.sin(state['yaw'])*dx + np.cos(state['yaw'])*dy

    drone_text.set_text(f'Drone: ({state["x"]:.2f},{state["y"]:.2f},{state["z"]:.2f})')

    # game logic
    if game_start_time is not None:
        elapsed = time.time()-game_start_time
        elapsed_text.set_text(f'Time: {elapsed:.2f}s')
        to_rm = [i for i,(tx,ty,tz) in enumerate(targets)
                 if np.linalg.norm([state['x']-tx,state['y']-ty,state['z']-tz])<drone_body_radius]
        for i in sorted(to_rm,reverse=True):
            targets.pop(i); coord_texts.pop(i).remove()
        if not targets:
            if best_time is None or elapsed<best_time:
                best_time=elapsed; best_text.set_text(f'Best: {best_time:.2f}s')
            game_start_time=None

    draw_scene()
    return []

ani = FuncAnimation(fig, update, interval=50)
threading.Thread(target=thread_scan_devices,daemon=True).start()
fig.canvas.mpl_connect('close_event', lambda e: (cleanup_resources(), sys.exit(0)))
fig.canvas.mpl_connect('key_press_event', lambda e: plt.close(fig) if e.key=='escape' else None)

plt.show()

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter import colorchooser
from PIL import Image, ImageTk
import numpy as np
import os

class Viewer3DApp:
    def __init__(self, root):
        self.root = root
        self.root.title("3D Viewer")
        
        # Initialize variables
        self.mouse_mode = tk.StringVar(value="Arcball")
        self.show_skymap = tk.BooleanVar(value=False)
        self.show_axes = tk.BooleanVar(value=True)
        self.bg_color = {'R': tk.StringVar(value='255'),
                        'G': tk.StringVar(value='255'),
                        'B': tk.StringVar(value='255')}
        self.material_color = {'R': tk.StringVar(value='230'),
                             'G': tk.StringVar(value='230'),
                             'B': tk.StringVar(value='230')}
        self.point_size = tk.DoubleVar(value=1.0)
        
        # Initialize 3D model data
        self.model_data = None
        self.camera_pos = np.array([0, 0, 5])
        self.camera_target = np.array([0, 0, 0])
        self.camera_up = np.array([0, 1, 0])
        
        # Create main menu
        self.create_menu()
        
        # Create main content area
        self.create_main_content()
        
        # Create right sidebar
        self.create_sidebar()

    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open...", command=self.open_file)
        file_menu.add_command(label="Open Samples...", command=self.open_samples)
        file_menu.add_command(label="Export Current Image...", command=self.export_image)
        file_menu.add_separator()
        file_menu.add_command(label="Quit", command=self.root.quit)
        
        # Settings menu
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Preferences", command=self.show_preferences)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)

    def create_main_content(self):
        # Create canvas for 3D view
        self.canvas = tk.Canvas(self.root, bg='white', width=600, height=400)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Bind mouse events
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)

    def create_sidebar(self):
        sidebar = ttk.Frame(self.root)
        sidebar.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=5)
        
        # Tabs
        tab_frame = ttk.Frame(sidebar)
        tab_frame.pack(fill=tk.X, pady=5)
        ttk.Button(tab_frame, text="General Settings", command=self.show_general_settings).pack(side=tk.LEFT, padx=2)
        ttk.Button(tab_frame, text="AI Settings", command=self.show_ai_settings).pack(side=tk.LEFT, padx=2)
        
        # View controls
        view_frame = ttk.LabelFrame(sidebar, text="View controls")
        view_frame.pack(fill=tk.X, pady=5)
        
        # Mouse controls
        ttk.Label(view_frame, text="Mouse controls").pack(anchor=tk.W)
        mouse_buttons = ttk.Frame(view_frame)
        mouse_buttons.pack(fill=tk.X)
        for btn_text in ["Arcball", "Fly", "Model", "Sun", "Environment"]:
            ttk.Radiobutton(mouse_buttons, text=btn_text, variable=self.mouse_mode, 
                           value=btn_text, command=self.update_mouse_mode).pack(side=tk.LEFT, padx=2, pady=2)
        
        # Background color
        bg_frame = ttk.Frame(view_frame)
        bg_frame.pack(fill=tk.X, pady=5)
        ttk.Label(bg_frame, text="BG Color").pack(side=tk.LEFT)
        for channel in ['R', 'G', 'B']:
            ttk.Entry(bg_frame, width=4, textvariable=self.bg_color[channel]).pack(side=tk.LEFT, padx=2)
            ttk.Label(bg_frame, text=f":{255}").pack(side=tk.LEFT)
        ttk.Button(bg_frame, text="Pick", command=self.pick_bg_color).pack(side=tk.LEFT, padx=5)
        
        # Show options
        ttk.Checkbutton(view_frame, text="Show skymap", variable=self.show_skymap, 
                       command=self.update_view).pack(anchor=tk.W)
        ttk.Checkbutton(view_frame, text="Show axes", variable=self.show_axes, 
                       command=self.update_view).pack(anchor=tk.W)
        
        # Lighting profiles
        light_frame = ttk.LabelFrame(sidebar, text="Lighting profiles")
        light_frame.pack(fill=tk.X, pady=5)
        self.lighting_profile = ttk.Combobox(light_frame, values=["Bright day with sun at +Y [default]", 
                                                                "Studio lighting", "Outdoor overcast",
                                                                "Night scene"])
        self.lighting_profile.set("Bright day with sun at +Y [default]")
        self.lighting_profile.pack(fill=tk.X, pady=2)
        self.lighting_profile.bind("<<ComboboxSelected>>", self.update_lighting)
        
        # Material settings
        material_frame = ttk.LabelFrame(sidebar, text="Material settings")
        material_frame.pack(fill=tk.X, pady=5)
        
        # Material type
        ttk.Label(material_frame, text="Type").pack(anchor=tk.W)
        self.material_type = ttk.Combobox(material_frame, values=["Lit", "Unlit", "PBR", "Wireframe"])
        self.material_type.set("Lit")
        self.material_type.pack(fill=tk.X, pady=2)
        self.material_type.bind("<<ComboboxSelected>>", self.update_material)
        
        # Material selection
        ttk.Label(material_frame, text="Material").pack(anchor=tk.W)
        self.material = ttk.Combobox(material_frame, values=["Polished ceramic [default]",
                                                           "Rough metal", "Plastic",
                                                           "Glass", "Wood"])
        self.material.set("Polished ceramic [default]")
        self.material.pack(fill=tk.X, pady=2)
        self.material.bind("<<ComboboxSelected>>", self.update_material)
        
        # Material color
        color_frame = ttk.Frame(material_frame)
        color_frame.pack(fill=tk.X, pady=5)
        ttk.Label(color_frame, text="Color").pack(side=tk.LEFT)
        for channel in ['R', 'G', 'B']:
            ttk.Entry(color_frame, width=4, textvariable=self.material_color[channel]).pack(side=tk.LEFT, padx=2)
            ttk.Label(color_frame, text=f":{230}").pack(side=tk.LEFT)
        ttk.Button(color_frame, text="Pick", command=self.pick_material_color).pack(side=tk.LEFT, padx=5)
        
        # Point size
        ttk.Label(material_frame, text="Point size").pack(anchor=tk.W)
        point_size_scale = ttk.Scale(material_frame, from_=0.1, to=10.0, variable=self.point_size, 
                                   orient=tk.HORIZONTAL, command=self.update_point_size)
        point_size_scale.pack(fill=tk.X, pady=2)

    # Event handlers
    def open_file(self):
        filetypes = [
            ('3D Models', '*.obj;*.stl;*.ply;*.fbx'),
            ('OBJ files', '*.obj'),
            ('STL files', '*.stl'),
            ('PLY files', '*.ply'),
            ('FBX files', '*.fbx'),
            ('All files', '*.*')
        ]
        filename = filedialog.askopenfilename(title="Open 3D Model", filetypes=filetypes)
        if filename:
            try:
                self.load_3d_model(filename)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load model: {str(e)}")
        
    def open_samples(self):
        samples_window = tk.Toplevel(self.root)
        samples_window.title("Sample Models")
        samples_window.geometry("300x400")
        
        samples = ["Cube", "Sphere", "Teapot", "Bunny", "Dragon"]
        for sample in samples:
            ttk.Button(samples_window, text=sample,
                      command=lambda s=sample: self.load_sample_model(s)).pack(pady=5)
        
    def export_image(self):
        if not self.model_data:
            messagebox.showwarning("Warning", "No model loaded to export")
            return
            
        filename = filedialog.asksaveasfilename(
            title="Export Image",
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), 
                      ("JPEG files", "*.jpg"),
                      ("All files", "*.*")]
        )
        if filename:
            try:
                # Get the canvas content and save as image
                self.canvas.postscript(file="temp.eps")
                img = Image.open("temp.eps")
                img.save(filename)
                os.remove("temp.eps")
                messagebox.showinfo("Success", "Image exported successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export image: {str(e)}")
        
    def show_preferences(self):
        prefs_window = tk.Toplevel(self.root)
        prefs_window.title("Preferences")
        prefs_window.geometry("400x300")
        
        # Add preference options here
        ttk.Label(prefs_window, text="Preferences will be added here").pack(pady=20)
        
    def show_about(self):
        about_text = """3D Viewer Application
Version 1.0
Created with Python and Tkinter
        
A simple 3D model viewer with basic manipulation capabilities."""
        
        messagebox.showinfo("About 3D Viewer", about_text)
        
    def show_general_settings(self):
        settings_window = tk.Toplevel(self.root)
        settings_window.title("General Settings")
        settings_window.geometry("400x300")
        
        # Add general settings here
        ttk.Label(settings_window, text="General settings will be added here").pack(pady=20)
        
    def show_ai_settings(self):
        ai_window = tk.Toplevel(self.root)
        ai_window.title("AI Settings")
        ai_window.geometry("400x300")
        
        # Add AI settings here
        ttk.Label(ai_window, text="AI settings will be added here").pack(pady=20)
        
    def update_mouse_mode(self):
        mode = self.mouse_mode.get()
        self.canvas.config(cursor="crosshair" if mode in ["Model", "Sun"] else "arrow")
        
    def update_view(self):
        self.render_scene()
        
    def update_point_size(self, value):
        self.render_scene()
        
    def update_lighting(self, event):
        self.render_scene()
        
    def update_material(self, event):
        self.render_scene()
        
    def pick_bg_color(self):
        color = colorchooser.askcolor(title="Choose Background Color")
        if color[0]:
            r, g, b = [int(x) for x in color[0]]
            self.bg_color['R'].set(str(r))
            self.bg_color['G'].set(str(g))
            self.bg_color['B'].set(str(b))
            self.canvas.configure(bg=color[1])
            
    def pick_material_color(self):
        color = colorchooser.askcolor(title="Choose Material Color")
        if color[0]:
            r, g, b = [int(x) for x in color[0]]
            self.material_color['R'].set(str(r))
            self.material_color['G'].set(str(g))
            self.material_color['B'].set(str(b))
            self.render_scene()
            
    def load_3d_model(self, filename):
        # Here you would implement actual 3D model loading
        self.model_data = {"filename": filename}
        self.render_scene()
        
    def load_sample_model(self, sample_name):
        # Here you would load built-in sample models
        self.model_data = {"sample": sample_name}
        self.render_scene()
        
    def render_scene(self):
        if not self.model_data:
            return
            
        # Here you would implement actual 3D rendering
        self.canvas.delete("all")
        self.canvas.create_text(300, 200, text=f"Rendering: {self.model_data.get('filename') or self.model_data.get('sample')}")
        
    def on_canvas_click(self, event):
        self.last_x = event.x
        self.last_y = event.y
        
    def on_canvas_drag(self, event):
        dx = event.x - self.last_x
        dy = event.y - self.last_y
        
        mode = self.mouse_mode.get()
        if mode == "Arcball":
            self.rotate_camera(dx, dy)
        elif mode == "Fly":
            self.move_camera(dx, dy)
            
        self.last_x = event.x
        self.last_y = event.y
        self.render_scene()
        
    def on_canvas_release(self, event):
        pass
        
    def on_mouse_wheel(self, event):
        # Zoom in/out
        self.camera_pos[2] += event.delta/120
        self.render_scene()
        
    def rotate_camera(self, dx, dy):
        # Implement camera rotation
        pass
        
    def move_camera(self, dx, dy):
        # Implement camera movement
        pass

if __name__ == "__main__":
    root = tk.Tk()
    app = Viewer3DApp(root)
    root.mainloop()
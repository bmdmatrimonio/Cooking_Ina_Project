import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk
from tkinterdnd2 import TkinterDnD, DND_FILES
from timer_audio import CookingTimer
from recipe_parser import parse_recipe_file, recipe_to_timer_data

# Loads recipe sections from the parser

class CookingInaGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Cooking Ina - Digital Cooking Assistant")
        self.root.geometry("650x580")
        
        # Rescaling Feature & Minimum Window Boundary
        self.root.resizable(True, True)
        self.root.minsize(550, 500)
        
        # Color Palette (Burnt Rust Theme)
        self.bg_color = "#9E472A"         # Deep rust background
        self.card_bg = "#B05638"          # Lighter clay shade for inner timer card
        self.primary_orange = "#C46849"   # Warm terracotta tone for main buttons
        self.hover_orange = "#D67A5B"     # Soft clay hover state
        self.text_light = "#FFFFFF"       # White text for contrast on dark background
        self.accent_green = "#4CAF50"     # Green for advancing to the next step
        self.ilovepdf_red = "#E53935"     # Bold red for iLovePDF style button
        
        self.root.configure(fg_color=self.bg_color)
        
        # Initialize Backend Timer (30 minutes = 1800 seconds)
        self.timer = CookingTimer(initial_seconds=1800)
        
        # Store current recipe details globally across views
        self.current_recipe_title = "Recipe: Adobo Placeholder"
        # Added by Ran-Ran - default recipe section
        self.recipe_sections = [{
            "name": "Default Step",
            "time": "30 mins",
            "duration_seconds": 1800,
            "steps": ["Marinate the pork and chicken for 30 minutes."]
        }]
        self.recipe_steps = self.recipe_sections[0]["steps"]
        self.current_step_index = 0
        
        # Overlay frame tracking for fake modals
        self.overlay_frame = None
        
        # Start the app on the Main Menu
        self.show_main_menu()

    def clear_window(self):
        """Helper method to destroy all widgets currently on the screen."""
        self.close_modal()
        for widget in self.root.winfo_children():
            widget.destroy()

    # Added by Ran-Ran - show the current cooking section
    def get_current_step_text(self):
        """Display all instructions belonging to the current cooking stage."""
        if (
            hasattr(self, "recipe_sections")
            and self.recipe_sections
            and 0 <= self.current_step_index < len(self.recipe_sections)
        ):
            section = self.recipe_sections[self.current_step_index]

            # Show all instructions in the current section
            instructions = "\n".join(
                f"{index}. {step}"
                for index, step in enumerate(section["steps"], start=1)
            )

            return (
                f"{section['name']}\n"
                f"Time: {section['time']}\n\n"
                f"{instructions}"
            )

        return "Prepare ingredients."

    # Modal Overlay Creation & Management
    def create_modal_overlay(self, width=480, height=450):
        """Creates a centered fake window layer over the current screen."""
        self.close_modal()
        
        # Darkened transparent backdrop covering full root area
        self.overlay_frame = ctk.CTkFrame(self.root, fg_color="#522213", corner_radius=0)
        self.overlay_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        # Centered 'Fake Window' Box
        modal_box = ctk.CTkFrame(
            self.overlay_frame, 
            fg_color=self.bg_color, 
            corner_radius=16, 
            border_width=2, 
            border_color=self.primary_orange,
            width=width, 
            height=height
        )
        modal_box.place(relx=0.5, rely=0.5, anchor="center")
        modal_box.pack_propagate(False) # Keep fixed modal dimensions
        return modal_box

    def close_modal(self):
        """Destroys active overlay modal if present."""
        if self.overlay_frame is not None and self.overlay_frame.winfo_exists():
            self.overlay_frame.destroy()
            self.overlay_frame = None

    # Main Menu Screen
    def show_main_menu(self):
        """Builds and displays the main menu screen with vertical stacking."""
        self.clear_window()
        
        if self.timer.is_running:
            self.timer.pause()

        self.menu_container = ctk.CTkFrame(self.root, fg_color="transparent")
        self.menu_container.pack(fill="both", expand=True, padx=20, pady=40)

        self.menu_title = ctk.CTkLabel(
            self.menu_container, 
            text="Cooking Ina", 
            font=("Georgia", 56, "bold"), 
            text_color=self.text_light
        )
        self.menu_title.pack(pady=(20, 35))

        self.button_frame = ctk.CTkFrame(self.menu_container, fg_color="transparent")
        self.button_frame.pack(pady=10)

        button_font = ("Helvetica", 14, "bold")
        btn_width = 240
        btn_height = 46

        self.btn_manual = ctk.CTkButton(
            self.button_frame, text="Manual Entry", font=button_font,
            fg_color=self.primary_orange, hover_color=self.hover_orange, 
            width=btn_width, height=btn_height, command=self.show_manual_entry_modal
        )
        self.btn_manual.pack(pady=10)

        self.btn_file = ctk.CTkButton(
            self.button_frame, text="Upload Recipe File", font=button_font,
            fg_color=self.primary_orange, hover_color=self.hover_orange, 
            width=btn_width, height=btn_height, command=self.show_file_upload_screen
        )
        self.btn_file.pack(pady=10)

        self.btn_metrics = ctk.CTkButton(
            self.button_frame, text="Check Local Metrics", font=button_font,
            fg_color=self.primary_orange, hover_color=self.hover_orange, 
            width=btn_width, height=btn_height, command=self.on_check_metrics
        )
        self.btn_metrics.pack(pady=10)

    # Manual Modal Entry Screen
    def show_manual_entry_modal(self):
        """Displays centered fake window for recipe step entry."""
        modal_box = self.create_modal_overlay(width=480, height=440)

        # Header bar with close button
        header = ctk.CTkFrame(modal_box, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=(12, 5))
        
        modal_title = ctk.CTkLabel(header, text="Manual Recipe Entry", font=("Helvetica", 16, "bold"), text_color=self.text_light)
        modal_title.pack(side="left")

        close_btn = ctk.CTkButton(header, text="✕", font=("Helvetica", 14, "bold"), fg_color="transparent", 
                                  hover_color=self.hover_orange, text_color=self.text_light, width=30, height=30, command=self.close_modal)
        close_btn.pack(side="right")

        # Added by Ran-Ran
        self.recipe_sections = []
        self.recipe_steps = []

        self.popup_container = ctk.CTkScrollableFrame(modal_box, fg_color="transparent")
        self.popup_container.pack(fill="both", expand=True, padx=15, pady=(5, 15))

        self.recipe_title_entry = ctk.CTkEntry(
            self.popup_container, 
            placeholder_text="Enter Recipe Title (e.g., Chicken Adobo)",
            font=("Helvetica", 14, "bold"),
            height=40,
            fg_color=self.card_bg,
            text_color=self.text_light,
            placeholder_text_color="#E0E0E0",
            border_width=0
        )
        self.recipe_title_entry.pack(fill="x", pady=(0, 10))

        steps_header = ctk.CTkLabel(
            self.popup_container, text="Steps", font=("Helvetica", 16, "bold"), text_color=self.text_light, anchor="w"
        )
        steps_header.pack(fill="x", pady=(5, 5))

        self.steps_list_frame = ctk.CTkFrame(self.popup_container, fg_color="transparent")
        self.steps_list_frame.pack(fill="x", pady=5)

        self.add_step_container = ctk.CTkFrame(self.popup_container, fg_color="transparent")
        self.add_step_container.pack(fill="x", pady=8)

        self.render_add_step_button()

        self.start_recipe_btn = ctk.CTkButton(
            self.popup_container,
            text="Start Cooking",
            font=("Helvetica", 14, "bold"),
            fg_color=self.accent_green,
            hover_color="#388E3C",
            height=40,
            command=self.start_manual_recipe
        )
        self.start_recipe_btn.pack(fill="x", pady=(12, 5))

    def render_add_step_button(self):
        """Displays Pomofocus-style + Add Step button box."""
        for widget in self.add_step_container.winfo_children():
            widget.destroy()

        add_btn = ctk.CTkButton(
            self.add_step_container,
            text="+ Add Step",
            font=("Helvetica", 14, "bold"),
            fg_color="#8C3E24",
            hover_color=self.hover_orange,
            text_color=self.text_light,
            border_width=2,
            border_color="#C46849",
            height=48,
            corner_radius=8,
            command=self.show_add_step_form
        )
        add_btn.pack(fill="x")

    def show_add_step_form(self):
        """Reveals step input textbox inside fake window."""
        for widget in self.add_step_container.winfo_children():
            widget.destroy()

        form_card = ctk.CTkFrame(self.add_step_container, fg_color=self.text_light, corner_radius=10)
        form_card.pack(fill="x", pady=5)

        input_label = ctk.CTkLabel(form_card, text="What is the next step?", font=("Helvetica", 12, "bold"), text_color="#333333")
        input_label.pack(anchor="w", padx=12, pady=(10, 4))

        self.step_text_input = ctk.CTkTextbox(form_card, width=380, height=70, font=("Helvetica", 13), fg_color="#F4F4F4", text_color="#333333")
        self.step_text_input.pack(fill="x", padx=12, pady=4)

        action_frame = ctk.CTkFrame(form_card, fg_color="transparent")
        action_frame.pack(fill="x", padx=12, pady=(4, 10))

        cancel_btn = ctk.CTkButton(
            action_frame, text="Cancel", font=("Helvetica", 12),
            fg_color="transparent", text_color="#666666", hover_color="#E0E0E0",
            width=70, height=28, command=self.render_add_step_button
        )
        cancel_btn.pack(side="left")

        save_btn = ctk.CTkButton(
            action_frame, text="Save Step", font=("Helvetica", 12, "bold"),
            fg_color="#343A40", hover_color="#212529", text_color=self.text_light,
            width=80, height=28, command=self.save_step_item
        )
        save_btn.pack(side="right")

    def save_step_item(self):
        """Saves typed step into local step array."""
        text = self.step_text_input.get("1.0", "end-1c").strip()
        if text:
            self.recipe_steps.append(text)

            # Added by Ran-Ran - keep manual steps as sections
            self.recipe_sections.append({
                "name": f"Step {len(self.recipe_sections) + 1}",
                "time": "30 mins",
                "duration_seconds": 1800,
                "steps": [text]
            })
            
            step_card = ctk.CTkFrame(self.steps_list_frame, fg_color=self.card_bg, corner_radius=8)
            step_card.pack(fill="x", pady=3)
            
            step_lbl = ctk.CTkLabel(
                step_card, 
                text=f"Step {len(self.recipe_steps)}: {text}", 
                font=("Helvetica", 12, "bold"), 
                text_color=self.text_light, 
                wraplength=360, justify="left", anchor="w"
            )
            step_lbl.pack(fill="x", padx=10, pady=8)

        self.render_add_step_button()

    def start_manual_recipe(self):
        title = self.recipe_title_entry.get().strip()
        if title:
            self.current_recipe_title = f"Recipe: {title}"
        elif self.recipe_steps:
            self.current_recipe_title = "Recipe: Custom Recipe"
        else:
            self.recipe_steps = ["Prepare ingredients."]
            self.current_recipe_title = "Recipe: Quick Timer"

        # Added by Ran-Ran - prepare manual sections
        if not self.recipe_sections and self.recipe_steps:
            self.recipe_sections = [{
                "name": "Recipe Step",
                "time": "30 mins",
                "duration_seconds": 1800,
                "steps": self.recipe_steps
            }]
        self.current_step_index = 0
        self.close_modal()
        self.show_timer_screen()

    # File Upload Screen
    def show_file_upload_screen(self):
        """Displays file selector section."""
        self.clear_window()

        # Navigation Bar
        nav_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        nav_frame.pack(fill="x", padx=20, pady=(15, 0))

        back_btn = ctk.CTkButton(
            nav_frame, text="<- Back to Menu", font=("Helvetica", 13, "bold"),
            fg_color="#8D8D8D", hover_color="#707070", width=120, height=30, command=self.show_main_menu
        )
        back_btn.pack(side="left")

        # Main Centered Content Area
        upload_container = ctk.CTkFrame(self.root, fg_color="transparent")
        upload_container.pack(expand=True, fill="both", padx=20, pady=20)

        # Main Header
        upload_title = ctk.CTkLabel(
            upload_container, text="Import Recipe File", font=("Helvetica", 36, "bold"), text_color=self.text_light
        )
        upload_title.pack(pady=(20, 8))

        upload_subtitle = ctk.CTkLabel(
            upload_container, 
            text="Upload your recipe document (PDF, TXT, JSON) to start cooking instantly.", 
            font=("Helvetica", 14), text_color="#E0E0E0", wraplength=480
        )
        upload_subtitle.pack(pady=(0, 40))

        # File Drop Area
        action_box = ctk.CTkFrame(upload_container, fg_color="transparent")
        action_box.pack(expand=True)

        select_file_btn = ctk.CTkButton(
            action_box,
            text="Select Recipe File",
            font=("Helvetica", 20, "bold"),
            fg_color=self.ilovepdf_red,
            hover_color="#D32F2F",
            text_color=self.text_light,
            width=280,
            height=65,
            corner_radius=12,
            command=self.browse_file_dialog
        )
        select_file_btn.pack(pady=(0, 10))

        drop_hint_lbl = ctk.CTkLabel(
            action_box, text="or drop file here", font=("Helvetica", 13), text_color="#D0D0D0"
        )
        drop_hint_lbl.pack()

        action_box.drop_target_register(DND_FILES)
        action_box.dnd_bind('<<Drop>>', self.on_file_drop)

    def on_file_drop(self, event):
        """Reads a dropped recipe file using the recipe parser backend."""
        file_path = event.data.strip('{}')
        self.load_recipe_file(file_path)

    def browse_file_dialog(self):
        """Opens native OS file chooser and parses the selected recipe."""
        file_path = filedialog.askopenfilename(
            title="Select Recipe File",
            filetypes=[("Recipe Documents", "*.txt *.json *.pdf"), ("All Files", "*.*")]
        )

        if file_path:
            self.load_recipe_file(file_path)

    def load_recipe_file(self, file_path):
        # Load and prepare the selected recipe
        """Loads a structured recipe using the parsing backend."""
        if not file_path.lower().endswith(('.txt', '.json', '.pdf')):
            print("Invalid file format. Please upload a .txt, .json, or .pdf")
            return

        try:
            recipe = parse_recipe_file(file_path)
            title, sections = recipe_to_timer_data(recipe)

            if not sections:
                print("No recipe sections were found in the selected file.")
                return

            # Added by Ran-Ran - keep the parsed sections
            self.recipe_sections = sections
            self.recipe_steps = [
                step
                for section in sections
                for step in section["steps"]
            ]

            self.current_recipe_title = f"Recipe: {title}"
            self.current_step_index = 0

            self.show_timer_screen()

        except Exception as error:
            print(f"Error reading recipe file: {error}")

    # Added by Ran-Ran - get the current section time
    def get_current_section_duration(self):
        """Return the timer duration for the current cooking stage."""
        if (
            hasattr(self, "recipe_sections")
            and self.recipe_sections
            and 0 <= self.current_step_index < len(self.recipe_sections)
        ):
            return self.recipe_sections[self.current_step_index].get(
                "duration_seconds",
                1800
            )

        return 1800

    # Timer screen with Mid-Cook Step Creation
    def show_timer_screen(self):
        """Builds and displays the core timer screen."""
        self.clear_window()
        # Added by Ran-Ran - use the section timer
        duration = self.get_current_section_duration()
        self.timer.reset(duration)

        self.main_container = ctk.CTkFrame(self.root, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=20, pady=15)
        
        # Top Nav Section
        self.top_nav_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.top_nav_frame.pack(fill="x")
        
        self.back_btn = ctk.CTkButton(
            self.top_nav_frame, text="<- Back to Menu", font=("Helvetica", 13, "bold"),
            fg_color="#8D8D8D", hover_color="#707070", width=120, height=30, command=self.show_main_menu
        )
        self.back_btn.pack(side="left")

        # Quick + Add Step Button active during timer phase
        self.add_step_timer_btn = ctk.CTkButton(
            self.top_nav_frame, text="+ Add Step", font=("Helvetica", 13, "bold"),
            fg_color=self.primary_orange, hover_color=self.hover_orange, 
            width=100, height=30, command=self.show_mid_cook_add_step_modal
        )
        self.add_step_timer_btn.pack(side="right")
        
        # Recipe Info Section
        self.header_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.header_frame.pack(fill="x", pady=(5, 10))
        
        self.title_label = ctk.CTkLabel(
            self.header_frame, text=self.current_recipe_title, font=("Helvetica", 22, "bold"), text_color=self.text_light
        )
        self.title_label.pack(pady=(0, 5))
        
        self.step_label = ctk.CTkLabel(
            self.header_frame, text=self.get_current_step_text(), font=("Helvetica", 15), text_color=self.text_light, wraplength=500
        )
        self.step_label.pack(fill="x")
        
        # Middle Section: Centered Timer Card
        self.timer_box = ctk.CTkFrame(self.main_container, fg_color=self.card_bg, corner_radius=20)
        self.timer_box.pack(expand=True, pady=10)
        
        self.timer_label = ctk.CTkLabel(
            self.timer_box, text="30:00", font=("Helvetica", 76, "bold"), text_color=self.text_light
        )
        self.timer_label.pack(padx=45, pady=15)
        
        # Bottom Controls
        self.controls_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.controls_frame.pack(pady=10)
        
        self.start_btn = ctk.CTkButton(
            self.controls_frame, text="Start", font=("Helvetica", 14, "bold"),
            fg_color=self.primary_orange, hover_color=self.hover_orange, text_color=self.text_light, width=110, height=36, command=self.on_start
        )
        self.start_btn.grid(row=0, column=0, padx=8)
        
        self.pause_btn = ctk.CTkButton(
            self.controls_frame, text="Pause", font=("Helvetica", 14, "bold"),
            fg_color=self.primary_orange, hover_color=self.hover_orange, text_color=self.text_light, width=110, height=36, command=self.on_pause
        )
        self.pause_btn.grid(row=0, column=1, padx=8)
        
        self.extend_btn = ctk.CTkButton(
            self.controls_frame, text="+1 Min", font=("Helvetica", 14, "bold"),
            fg_color=self.primary_orange, hover_color=self.hover_orange, text_color=self.text_light, width=110, height=36, command=self.on_extend
        )
        self.extend_btn.grid(row=0, column=2, padx=8)
        
        # Footer Step Controls
        self.nav_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.nav_frame.pack(pady=(10, 5))
        
        self.repeat_btn = ctk.CTkButton(
            self.nav_frame, text="Repeat Step", font=("Helvetica", 13),
            fg_color="#8D8D8D", hover_color="#707070", width=130, height=34, command=self.on_repeat
        )
        self.repeat_btn.grid(row=0, column=0, padx=10)
        
        self.next_btn = ctk.CTkButton(
            self.nav_frame, text="Next Step ->", font=("Helvetica", 13, "bold"),
            fg_color=self.accent_green, hover_color="#388E3C", width=130, height=34, command=self.on_next_step
        )
        self.next_btn.grid(row=0, column=1, padx=10)

        self.update_timer_display()

    # Dynamic Step Creation Prompt During Cooking
    def show_mid_cook_add_step_modal(self):
        """Allows adding extra steps during active timer without resetting countdown."""
        modal_box = self.create_modal_overlay(width=420, height=280)

        header = ctk.CTkFrame(modal_box, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=(15, 5))
        
        modal_title = ctk.CTkLabel(header, text="Add Step Mid-Cook", font=("Helvetica", 16, "bold"), text_color=self.text_light)
        modal_title.pack(side="left")

        close_btn = ctk.CTkButton(header, text="✕", font=("Helvetica", 14, "bold"), fg_color="transparent", 
                                  hover_color=self.hover_orange, text_color=self.text_light, width=30, height=30, command=self.close_modal)
        close_btn.pack(side="right")

        content = ctk.CTkFrame(modal_box, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=15, pady=10)

        self.mid_cook_textbox = ctk.CTkTextbox(content, height=90, font=("Helvetica", 13), fg_color="#F4F4F4", text_color="#333333")
        self.mid_cook_textbox.pack(fill="x", pady=(0, 15))

        save_step_btn = ctk.CTkButton(
            content, text="Add Step to Recipe", font=("Helvetica", 14, "bold"),
            fg_color=self.accent_green, hover_color="#388E3C", height=38, command=self.save_mid_cook_step
        )
        save_step_btn.pack(fill="x")

    def save_mid_cook_step(self):
        """Saves added step and updates timer view labels instantly."""
        text = self.mid_cook_textbox.get("1.0", "end-1c").strip()
        if text:
            # Added by Ran-Ran - add to the current section
            if hasattr(self, "recipe_sections") and self.recipe_sections:
                self.recipe_sections[self.current_step_index]["steps"].append(text)
            self.recipe_steps.append(text)
            self.step_label.configure(text=self.get_current_step_text())
        self.close_modal()

    # Backend Timer & Nav Handlers
    def update_timer_display(self):
        if hasattr(self, 'timer_label') and self.timer_label.winfo_exists():
            self.timer_label.configure(text=self.timer.get_time_formatted())

    def tick(self):
        if self.timer.is_running and hasattr(self, 'timer_label') and self.timer_label.winfo_exists():
            self.timer.decrement()
            self.update_timer_display()
            if self.timer.is_running:
                self.root.after(1000, self.tick)

    def on_start(self):
        if not self.timer.is_running and self.timer.start():
            self.tick()
    
    def on_pause(self):
        self.timer.pause()
    
    def on_extend(self):
        self.timer.extend(60)
        self.update_timer_display()
    
    # Added by Ran-Ran - repeat the current section
    def on_repeat(self):
        self.timer.reset(self.get_current_section_duration())
        self.update_timer_display()
    
    # Added by Ran-Ran - move between cooking sections
    def on_next_step(self):
        """Move to the next cooking stage and load its timer duration."""
        if (
            hasattr(self, "recipe_sections")
            and self.current_step_index < len(self.recipe_sections) - 1
        ):
            self.current_step_index += 1

            section = self.recipe_sections[self.current_step_index]

            self.step_label.configure(
                text=self.get_current_step_text()
            )

            self.timer.reset(
                section.get("duration_seconds", 1800)
            )

            self.update_timer_display()
        else:
            self.step_label.configure(
                text="All Steps Completed! Bon Appétit!"
            )

    def on_check_metrics(self):
        print("Backend hook: Check Local Metrics")

# Class that supports both CustomTkinter and DnD(drag and drop) events
class CustomDnDWindow(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TkdndVersion = TkinterDnD._require(self)

if __name__ == "__main__":
    ctk.set_appearance_mode("Light")
    # Use the new merged window as the root
    root = CustomDnDWindow() 
    app = CookingInaGUI(root)
    root.mainloop()
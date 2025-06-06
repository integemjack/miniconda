import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import matplotlib
from matplotlib import font_manager
import glob
import os

# Set font configuration
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Liberation Sans']
plt.rcParams['axes.unicode_minus'] = False

class ToolTip:
    """Create a tooltip for a given widget"""
    def __init__(self, widget, text='widget info'):
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.tipwindow = None

    def enter(self, event=None):
        self.showtip()

    def leave(self, event=None):
        self.hidetip()

    def showtip(self):
        if self.tipwindow or not self.text:
            return
        x, y, cx, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 25
        y = y + cy + self.widget.winfo_rooty() + 25
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                      background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                      font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

class DataPlotter:
    def __init__(self, root):
        self.root = root
        self.root.title("Data Visualization Tool")
        self.root.geometry("1500x900")  # Increase width to accommodate longer attribute names
        
        # Show progress window
        progress_window = tk.Toplevel(root)
        progress_window.title("Loading...")
        progress_window.geometry("300x100")
        progress_window.resizable(False, False)
        progress_window.grab_set()
        
        # Center the progress window
        progress_window.transient(root)
        progress_window.update_idletasks()
        x = (progress_window.winfo_screenwidth() // 2) - (300 // 2)
        y = (progress_window.winfo_screenheight() // 2) - (100 // 2)
        progress_window.geometry(f"300x100+{x}+{y}")
        
        progress_label = ttk.Label(progress_window, text="Combining CSV files...", font=("Arial", 10))
        progress_label.pack(pady=30)
        
        # Update the window
        progress_window.update()
        
        # First, combine CSV files
        try:
            self.combine_csv_files()
            progress_label.config(text="Loading data...")
            progress_window.update()
        except Exception as e:
            progress_window.destroy()
            messagebox.showerror("Error", f"Error combining CSV files: {str(e)}")
            self.root.destroy()
            return
        
        # Read data
        try:
            self.df = pd.read_csv("combined.csv")
            print(f"Successfully loaded data with {len(self.df)} rows")
            progress_label.config(text="Setting up interface...")
            progress_window.update()
        except FileNotFoundError:
            progress_window.destroy()
            messagebox.showerror("Error", "Cannot find combined.csv file!\nPlease ensure log_*.csv files exist in the current directory.")
            self.root.destroy()
            return
        except Exception as e:
            progress_window.destroy()
            messagebox.showerror("Error", f"Error reading file: {str(e)}")
            self.root.destroy()
            return
        
        # Get all columns except time
        self.columns = [col for col in self.df.columns if col != 'time']
        
        # Get source file information
        self.source_files = glob.glob("log_*.csv")
        self.source_files.sort(key=lambda f: int(f.split('_')[-1].split('.')[0]))
        
        # Initialize checkbox variables
        self.checkbox_vars = {}
        for col in self.columns:
            self.checkbox_vars[col] = tk.BooleanVar(value=True)
        
        self.setup_ui()
        self.update_plot()
        
        # Close progress window
        progress_window.destroy()
    
    def create_tooltip(self, widget, text):
        """Create a tooltip for a widget"""
        ToolTip(widget, text)
    
    def combine_csv_files(self):
        """Combine all log_*.csv files into combined.csv"""
        # Get and sort all CSV files based on the timestamp in the filename
        csv_files = glob.glob("logs/log_*.csv")
        
        if not csv_files:
            raise FileNotFoundError("No log_*.csv files found in the current directory")
        
        csv_files.sort(key=lambda f: int(f.split('_')[-1].split('.')[0]))
        
        print(f"Found {len(csv_files)} CSV files to combine:")
        for file in csv_files:
            print(f"  - {file}")
        
        # Read each file into a DataFrame and concatenate them
        try:
            combined_df = pd.concat((pd.read_csv(f) for f in csv_files), ignore_index=True)
        except Exception as e:
            raise Exception(f"Error reading CSV files: {str(e)}")
        
        # Write the combined DataFrame to a CSV file
        combined_df.to_csv("combined.csv", index=False)
        
        print(f"Combined CSV file 'combined.csv' has been created with {len(combined_df)} rows")
    
    def setup_ui(self):
        # Create menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Refresh Data", command=self.refresh_data)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        
        # Create main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left control panel
        control_frame = ttk.LabelFrame(main_frame, text="Control Panel", padding=10)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        control_frame.config(width=280)  # Set minimum width
        
        # Title
        title_label = ttk.Label(control_frame, text="Select attributes to display:", 
                               font=("Arial", 12, "bold"))
        title_label.pack(pady=(0, 10))
        
        # Create scrollable frame for checkboxes
        checkboxes_container = ttk.Frame(control_frame)
        checkboxes_container.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        canvas = tk.Canvas(checkboxes_container, height=300)
        scrollbar = ttk.Scrollbar(checkboxes_container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Create checkboxes
        for col in self.columns:
            cb = ttk.Checkbutton(
                scrollable_frame,
                text=f"{col}",
                variable=self.checkbox_vars[col],
                command=self.update_plot,
                width=25  # Set wider width for checkbox text
            )
            cb.pack(anchor=tk.W, pady=2, padx=5, fill=tk.X)
            
            # Add tooltip for long attribute names
            self.create_tooltip(cb, f"Attribute: {col}")
        
        canvas.pack(fill="both", expand=True, side="left")
        scrollbar.pack(fill="y", side="right")
        
        # Select all/deselect all buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(pady=10, fill=tk.X)
        
        select_all_btn = ttk.Button(button_frame, text="Select All", command=self.select_all)
        select_all_btn.pack(pady=2, fill=tk.X)
        
        deselect_all_btn = ttk.Button(button_frame, text="Deselect All", command=self.deselect_all)
        deselect_all_btn.pack(pady=2, fill=tk.X)
        
        # Add data information
        info_frame = ttk.LabelFrame(control_frame, text="Data Information", padding=5)
        info_frame.pack(pady=10, fill=tk.X)
        
        info_text = f"Total data points: {len(self.df)}\n"
        info_text += f"Time range: {self.df['time'].min():.2f} - {self.df['time'].max():.2f}\n"
        info_text += f"Available attributes: {len(self.columns)}\n"
        info_text += f"Source files: {len(self.source_files)} files"
        
        info_label = ttk.Label(info_frame, text=info_text, font=("Arial", 9))
        info_label.pack()
        
        # Add source files list
        files_frame = ttk.Frame(info_frame)
        files_frame.pack(pady=(5, 0), fill=tk.X)
        
        files_title = ttk.Label(files_frame, text="Source Files:", font=("Arial", 8, "bold"))
        files_title.pack(anchor=tk.W)
        
        # Show first few files and total count
        if len(self.source_files) <= 4:
            files_text = "\n".join([f"{i:2d}. {file}" for i, file in enumerate(self.source_files, 1)])
        else:
            files_text = f"1. {self.source_files[0]}\n2. {self.source_files[1]}\n"
            files_text += f"... ({len(self.source_files)-3} more files)\n"
            files_text += f"{len(self.source_files):2d}. {self.source_files[-1]}"
        
        files_label = ttk.Label(files_frame, text=files_text, font=("Arial", 7), 
                               foreground="gray", justify=tk.LEFT)
        files_label.pack(anchor=tk.W, pady=(2, 0))
        
        # Right chart area
        plot_frame = ttk.LabelFrame(main_frame, text="Data Chart", padding=5)
        plot_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Create matplotlib figure
        self.fig, self.ax = plt.subplots(figsize=(12, 8))
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Add toolbar
        toolbar_frame = ttk.Frame(plot_frame)
        toolbar_frame.pack(fill=tk.X)
        
        from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
        toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        toolbar.update()
    
    def select_all(self):
        for var in self.checkbox_vars.values():
            var.set(True)
        self.update_plot()
    
    def deselect_all(self):
        for var in self.checkbox_vars.values():
            var.set(False)
        self.update_plot()
    
    def update_plot(self):
        # Clear current figure
        self.ax.clear()
        
        # Get selected columns
        selected_columns = [col for col, var in self.checkbox_vars.items() if var.get()]
        
        if not selected_columns:
            self.ax.text(0.5, 0.5, 'Please select at least one attribute to display', 
                        horizontalalignment='center', verticalalignment='center',
                        transform=self.ax.transAxes, fontsize=16, 
                        fontweight='bold', color='red')
            self.canvas.draw()
            return
        
        # Create color mapping
        colors = plt.cm.Set1(np.linspace(0, 1, len(selected_columns)))
        if len(selected_columns) > 9:
            colors = plt.cm.tab20(np.linspace(0, 1, len(selected_columns)))
        
        # Plot selected data
        for i, col in enumerate(selected_columns):
            self.ax.plot(self.df['time'], self.df[col], 
                        label=col, color=colors[i], linewidth=1.5, alpha=0.8)
        
        # Set figure properties
        self.ax.set_xlabel('Time', fontsize=14, fontweight='bold')
        self.ax.set_ylabel('Value', fontsize=14, fontweight='bold')
        self.ax.set_title(f'Data Time Series Plot (Showing {len(selected_columns)} attributes)', 
                         fontsize=16, fontweight='bold', pad=20)
        
        # Set legend
        if len(selected_columns) <= 10:
            self.ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=10)
        else:
            self.ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', 
                          fontsize=8, ncol=2)
        
        # Add grid
        self.ax.grid(True, alpha=0.3, linestyle='--')
        
        # Beautify axes
        self.ax.tick_params(axis='both', which='major', labelsize=10)
        
        # Auto adjust layout
        self.fig.tight_layout()
        
        # Refresh canvas
        self.canvas.draw()
    
    def refresh_data(self):
        """Refresh data by re-combining CSV files and reloading"""
        try:
            # Show progress dialog
            progress = tk.Toplevel(self.root)
            progress.title("Refreshing...")
            progress.geometry("250x80")
            progress.resizable(False, False)
            progress.grab_set()
            progress.transient(self.root)
            
            # Center the dialog
            progress.update_idletasks()
            x = (progress.winfo_screenwidth() // 2) - (250 // 2)
            y = (progress.winfo_screenheight() // 2) - (80 // 2)
            progress.geometry(f"250x80+{x}+{y}")
            
            label = ttk.Label(progress, text="Refreshing data...", font=("Arial", 10))
            label.pack(pady=25)
            progress.update()
            
            # Re-combine files
            self.combine_csv_files()
            
            # Reload data
            self.df = pd.read_csv("combined.csv")
            
            # Update source files info
            self.source_files = glob.glob("log_*.csv")
            self.source_files.sort(key=lambda f: int(f.split('_')[-1].split('.')[0]))
            
            # Close progress dialog
            progress.destroy()
            
            # Update the plot
            self.update_plot()
            
            # Update info panel (need to recreate it)
            messagebox.showinfo("Success", f"Data refreshed successfully!\nLoaded {len(self.df)} data points from {len(self.source_files)} files.")
            
        except Exception as e:
            if 'progress' in locals():
                progress.destroy()
            messagebox.showerror("Error", f"Error refreshing data: {str(e)}")
    
    def show_about(self):
        """Show about dialog"""
        about_text = """Data Visualization Tool v2.0

This tool automatically combines log_*.csv files and creates 
interactive time series plots with selectable attributes.

Features:
• Automatic CSV file combination
• Interactive plot with zoom/pan
• Attribute selection with checkboxes
• Data refresh capability
• Export functionality

Created for data analysis and visualization."""
        
        messagebox.showinfo("About", about_text)

def main():
    try:
        root = tk.Tk()
        
        # Set window icon (if available)
        try:
            root.iconbitmap('icon.ico')
        except:
            pass
        
        app = DataPlotter(root)
        
        # Set close event
        def on_closing():
            if messagebox.askokcancel("Exit", "Are you sure you want to exit?"):
                root.destroy()
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        root.mainloop()
        
    except Exception as e:
        messagebox.showerror("Error", f"Failed to start application: {str(e)}")

if __name__ == "__main__":
    main() 
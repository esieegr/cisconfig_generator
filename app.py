"""Simple Tkinter GUI for the Cisco config generator."""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from generator import generate_full_config
try:
    # prefer analyzer_core which is a clean implementation
    from analyzer_core import analyze_options
except Exception:
    # fallback to analyzer if present
    from analyzer import analyze_options


class ConfigApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Cisco Config Generator")
        self.geometry("900x700")

        self._build_ui()

    def _build_ui(self):
        frm = ttk.Frame(self)
        frm.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        left = ttk.Frame(frm)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0,10))

        ttk.Label(left, text="Hostname").pack(anchor=tk.W)
        self.hostname = tk.Entry(left, width=30)
        self.hostname.pack()

        ttk.Label(left, text="Interfaces (one per line: name ip/cidr desc)").pack(anchor=tk.W, pady=(10,0))
        self.interfaces = tk.Text(left, width=40, height=10)
        self.interfaces.pack()

        self.mpls_var = tk.BooleanVar()
        ttk.Checkbutton(left, text="Enable MPLS", variable=self.mpls_var).pack(anchor=tk.W, pady=(10,0))

        ttk.Label(left, text="OSPF process id").pack(anchor=tk.W, pady=(10,0))
        self.ospf_pid = tk.Entry(left, width=10)
        self.ospf_pid.pack()

        ttk.Label(left, text="OSPF networks (one per line, CIDR or 'ip wildcard area')").pack(anchor=tk.W, pady=(10,0))
        self.ospf_networks = tk.Text(left, width=40, height=6)
        self.ospf_networks.pack()

        ttk.Label(left, text="BGP ASN").pack(anchor=tk.W, pady=(10,0))
        self.bgp_asn = tk.Entry(left, width=20)
        self.bgp_asn.pack()

        ttk.Label(left, text="BGP neighbors (one per line, e.g. '1.2.3.4 remote-as 65001')").pack(anchor=tk.W, pady=(10,0))
        self.bgp_neighbors = tk.Text(left, width=40, height=6)
        self.bgp_neighbors.pack()

        btn_frame = ttk.Frame(left)
        btn_frame.pack(fill=tk.X, pady=(10,0))
        ttk.Button(btn_frame, text="Generate", command=self.generate).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Export", command=self.export).pack(side=tk.LEFT, padx=(10,0))
        ttk.Button(btn_frame, text="Analyze", command=self.analyze).pack(side=tk.LEFT, padx=(10,0))

        # include recommendations when generating/exporting
        self.include_recs_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(btn_frame, text="Include recommendations", variable=self.include_recs_var).pack(side=tk.LEFT, padx=(10,0))

        right = ttk.Frame(frm)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        ttk.Label(right, text="Generated config").pack(anchor=tk.W)
        self.output = tk.Text(right, wrap=tk.NONE)
        self.output.pack(fill=tk.BOTH, expand=True)

        # Bottom panel for issues/recommendations
        bottom = ttk.Frame(right)
        bottom.pack(fill=tk.X)
        ttk.Label(bottom, text="Issues and recommendations").pack(anchor=tk.W)
        self.recs_box = tk.Text(bottom, height=8, wrap=tk.WORD)
        self.recs_box.pack(fill=tk.X)

    def generate(self):
        options = {
            "hostname": self.hostname.get(),
            "interfaces": self.interfaces.get("1.0", tk.END),
            "mpls": self.mpls_var.get(),
            "ospf_pid": self.ospf_pid.get(),
            "ospf_networks": self.ospf_networks.get("1.0", tk.END),
            "bgp_asn": self.bgp_asn.get(),
            "bgp_neighbors": self.bgp_neighbors.get("1.0", tk.END),
        }
        cfg = generate_full_config(options)
        # include recommendations if requested
        if self.include_recs_var.get():
            analysis = analyze_options(options)
            for title, snippet in analysis.get("recommendations", []):
                cfg += "\n! Recommendation: " + title + "\n" + snippet + "\n"
        self.output.delete("1.0", tk.END)
        self.output.insert(tk.END, cfg)

    def analyze(self):
        options = {
            "hostname": self.hostname.get(),
            "interfaces": self.interfaces.get("1.0", tk.END),
            "mpls": self.mpls_var.get(),
            "ospf_pid": self.ospf_pid.get(),
            "ospf_networks": self.ospf_networks.get("1.0", tk.END),
            "bgp_asn": self.bgp_asn.get(),
            "bgp_neighbors": self.bgp_neighbors.get("1.0", tk.END),
        }
        analysis = analyze_options(options)
        self.recs_box.delete("1.0", tk.END)
        if analysis.get("issues"):
            self.recs_box.insert(tk.END, "Issues:\n")
            for it in analysis["issues"]:
                self.recs_box.insert(tk.END, f" - {it}\n")
        if analysis.get("recommendations"):
            self.recs_box.insert(tk.END, "\nRecommendations:\n")
            for title, snippet in analysis["recommendations"]:
                self.recs_box.insert(tk.END, f"* {title}\n{snippet}\n\n")

    def export(self):
        cfg = self.output.get("1.0", tk.END).strip()
        if not cfg:
            messagebox.showwarning("No config", "Please generate a config first.")
            return
        # if include_recs is checked but output was not generated with recs, regenerate
        if self.include_recs_var.get() and "! Recommendation:" not in cfg:
            self.generate()
            cfg = self.output.get("1.0", tk.END).strip()
        path = filedialog.asksaveasfilename(defaultextension=".cfg", filetypes=[("Config files","*.cfg"), ("Text files","*.txt"), ("All files","*.*")])
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(cfg)
            messagebox.showinfo("Saved", f"Configuration exported to {path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file: {e}")


if __name__ == "__main__":
    app = ConfigApp()
    app.mainloop()

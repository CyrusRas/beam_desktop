"""Beam Designer desktop application. Run with: python main.py"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import beam_io
from beam_csv import export_csv
from beam_pdf import create_report
from beam_analysis import PointLoad, UniformLoad, analyze
from diagrams import draw_beam, draw_diagram
from member_data import LUMBER_SIZES, STEEL, STEEL_GRADES, WOOD, get_member


FOREST = "#174d35"
PALE = "#f2f7f3"
INK = "#1e2a22"
MUTED = "#526158"


class BeamDesigner(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Beam Designer · Preliminary Analysis")
        self.geometry("1450x920")
        self.minsize(1080, 720)
        self.configure(bg=PALE)
        self.point_rows = []
        self.uniform_rows = []
        self.current_file = None
        self.dirty = False
        self._loading = False
        self.last_analysis = None
        self.last_points = []
        self.last_uniforms = []
        self.last_member = None
        self._style()
        self._build()
        self._example(clean=True)

    def _style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background=PALE)
        style.configure("Card.TFrame", background="white")
        style.configure("TLabel", background=PALE, foreground=INK, font=("Segoe UI", 10))
        style.configure("Title.TLabel", background=FOREST, foreground="white", font=("Segoe UI", 18, "bold"))
        style.configure("Sub.TLabel", background=FOREST, foreground="#d7e5db", font=("Segoe UI", 10))
        style.configure("Section.TLabel", background="white", foreground=FOREST, font=("Segoe UI", 12, "bold"))
        style.configure("Metric.TLabel", background="white", foreground=INK, font=("Segoe UI", 11, "bold"))
        style.configure("Hint.TLabel", background="white", foreground=MUTED, font=("Segoe UI", 9))
        style.configure("TButton", padding=(9, 6), font=("Segoe UI", 10, "bold"))
        style.configure("Forest.TButton", background=FOREST, foreground="white")
        style.map("Forest.TButton", background=[("active", "#226443")])
        style.configure("TEntry", padding=5)
        style.configure("TCombobox", padding=4)

    def _build(self):
        menu = tk.Menu(self)
        file_menu = tk.Menu(menu, tearoff=False)
        file_menu.add_command(label="Save", accelerator="Ctrl+S", command=self._save)
        file_menu.add_command(label="Open…", accelerator="Ctrl+O", command=self._open)
        menu.add_cascade(label="File", menu=file_menu)
        self.configure(menu=menu)
        self.bind("<Control-s>", lambda _event: self._save())
        self.bind("<Control-o>", lambda _event: self._open())
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        header = tk.Frame(self, bg=FOREST, height=70, highlightbackground="#c9a227", highlightthickness=0)
        header.pack(fill="x")
        header.pack_propagate(False)
        ttk.Label(header, text="Beam Designer", style="Title.TLabel").pack(side="left", padx=(20, 8), pady=10)
        ttk.Label(header, text="Preliminary beam analysis", style="Sub.TLabel").pack(side="left", pady=(20, 10))
        logo = tk.Canvas(header, width=80, height=54, bg=FOREST, highlightthickness=0)
        logo.pack(side="right", padx=18)
        logo.create_polygon(4, 48, 28, 9, 43, 33, 55, 15, 76, 48, fill="#eaf3ed", outline="")
        logo.create_polygon(21, 20, 28, 9, 36, 22, 29, 18, fill="#c9a227", outline="")
        logo.create_polygon(49, 24, 55, 15, 63, 28, 56, 23, fill="#c9a227", outline="")
        logo.create_line(4, 48, 76, 48, fill="white", width=2)

        root = ttk.Panedwindow(self, orient="horizontal")
        root.pack(fill="both", expand=True, padx=12, pady=12)
        side = ttk.Frame(root, width=350)
        self.side_canvas = tk.Canvas(side, bg=PALE, highlightthickness=0, width=350)
        scroll = ttk.Scrollbar(side, orient="vertical", command=self.side_canvas.yview)
        self.side_inner = ttk.Frame(self.side_canvas)
        self.side_inner.bind("<Configure>", lambda _e: self.side_canvas.configure(scrollregion=self.side_canvas.bbox("all")))
        self.side_canvas.create_window((0, 0), window=self.side_inner, anchor="nw", width=330)
        self.side_canvas.configure(yscrollcommand=scroll.set)
        self.side_canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        root.add(side, weight=0)
        self.analysis_panel = ttk.Frame(root)
        root.add(self.analysis_panel, weight=1)

        self.span = tk.StringVar(value="40")
        self.support = tk.StringVar(value="Simply supported")
        self.member_type = tk.StringVar(value="Steel W-shape")
        self.shape = tk.StringVar(value="W12x26")
        self.grade = tk.StringVar(value="ASTM A992")
        self.species = tk.StringVar(value="Douglas Fir-Larch No. 2")
        self.size = tk.StringVar(value="2x10")
        self._section(self.side_inner, "Beam and supports")
        self._field(self.side_inner, "Support condition", ttk.Combobox(self.side_inner, textvariable=self.support,
                    values=("Simply supported", "Cantilever"), state="readonly"))
        self._field(self.side_inner, "Span (ft)", ttk.Entry(self.side_inner, textvariable=self.span))
        self._section(self.side_inner, "Point loads")
        self.point_box = ttk.Frame(self.side_inner)
        self.point_box.pack(fill="x", padx=10)
        ttk.Button(self.side_inner, text="+ Add point load", command=self._add_point).pack(anchor="w", padx=10, pady=4)
        self._section(self.side_inner, "Uniform loads")
        self.uniform_box = ttk.Frame(self.side_inner)
        self.uniform_box.pack(fill="x", padx=10)
        ttk.Button(self.side_inner, text="+ Add uniform load", command=self._add_uniform).pack(anchor="w", padx=10, pady=4)
        self._section(self.side_inner, "Member")
        self._field(self.side_inner, "Member type", ttk.Combobox(self.side_inner, textvariable=self.member_type,
                    values=("Steel W-shape", "Lumber"), state="readonly"))
        self.member_fields = ttk.Frame(self.side_inner)
        self.member_fields.pack(fill="x")
        self._build_member_fields()
        self._section(self.side_inner, "Deflection limit")
        ttk.Label(self.side_inner, text="Fixed at L / 360", style="Hint.TLabel").pack(anchor="w", padx=12, pady=(0, 8))
        ttk.Label(self.side_inner, text="Self-weight is not added automatically; enter it as a uniform load.",
                  style="Hint.TLabel", wraplength=300).pack(anchor="w", padx=12, pady=5)
        actions = ttk.Frame(self.side_inner)
        actions.pack(fill="x", padx=10, pady=10)
        ttk.Button(actions, text="Run analysis", style="Forest.TButton", command=self._run).pack(side="left", fill="x", expand=True, padx=(0, 4))
        ttk.Button(actions, text="Reset", command=self._reset_example).pack(side="left", fill="x", expand=True, padx=(4, 0))

        self.title_label = ttk.Label(self.analysis_panel, text="40 ft simply supported beam", style="Section.TLabel")
        self.title_label.pack(anchor="w", pady=(3, 2))
        self.member_caption = ttk.Label(self.analysis_panel, text="W12x26 steel · example load case", style="Hint.TLabel")
        self.member_caption.pack(anchor="w", pady=(0, 9))
        self.file_status = ttk.Label(self.analysis_panel, text="", style="Hint.TLabel")
        self.file_status.pack(anchor="w", pady=(0, 5))
        self.error_label = tk.Label(self.analysis_panel, text="", fg="#8d261f", bg="#fff0ee", anchor="w", padx=10, pady=8)
        self.error_label.pack(fill="x", pady=(0, 6))

        self.beam_canvas = self._canvas_card(self.analysis_panel, "Beam and applied loads", 145)
        charts = ttk.Frame(self.analysis_panel)
        charts.pack(fill="both", expand=True)
        charts.columnconfigure(0, weight=1)
        charts.columnconfigure(1, weight=1)
        charts.rowconfigure(0, weight=1)
        charts.rowconfigure(1, weight=1)
        self.shear_canvas = self._chart_card(charts, "Shear diagram · kip", "Positive upward on left face", 0, 0)
        self.moment_canvas = self._chart_card(charts, "Moment diagram · kip-ft", "Positive sagging", 0, 1)
        self.deflection_canvas = self._chart_card(charts, "Deflection diagram · in", "Downward positive", 1, 0, colspan=2)
        self.results_frame = tk.Frame(self.analysis_panel, bg="white", highlightbackground="#d5dfd7", highlightthickness=1)
        self.results_frame.pack(fill="x", pady=(8, 0))
        results_header = tk.Frame(self.results_frame, bg="white")
        results_header.pack(fill="x", padx=12, pady=(8, 3))
        ttk.Label(results_header, text="Results summary", style="Section.TLabel").pack(side="left", anchor="w")
        ttk.Button(results_header, text="Export results CSV", style="Forest.TButton",
                   command=self._export_csv).pack(side="right")
        ttk.Button(results_header, text="Export report PDF", style="Forest.TButton",
                   command=self._export_pdf).pack(side="right", padx=(0, 6))
        self.results_text = tk.Text(self.results_frame, height=6, wrap="word", bg="white", fg=INK,
                                    font=("Segoe UI", 10), relief="flat", padx=12, pady=2)
        self.results_text.pack(fill="x")
        self.checks_label = ttk.Label(self.results_frame, text="", style="Metric.TLabel", wraplength=820)
        self.checks_label.pack(anchor="w", padx=12, pady=(0, 5))
        ttk.Label(self.analysis_panel, text="Not checked: shear strength and bearing. The shear diagram is not a capacity check. Buckling and other design requirements are outside this tool.",
                  style="Hint.TLabel", wraplength=1000).pack(anchor="w", pady=(7, 0))
        for variable in (self.span, self.support, self.member_type, self.shape, self.grade, self.species, self.size):
            variable.trace_add("write", self._mark_dirty)
        self.member_type.trace_add("write", lambda *_: self._refresh_member_fields())
        self.bind("<Configure>", self._redraw_on_resize)

    def _section(self, parent, text):
        frame = tk.Frame(parent, bg=FOREST, height=29)
        frame.pack(fill="x", padx=5, pady=(9, 4))
        frame.pack_propagate(False)
        tk.Label(frame, text=text, bg=FOREST, fg="white", font=("Segoe UI", 10, "bold"), anchor="w").pack(fill="both", padx=9)

    def _field(self, parent, label, widget):
        frame = ttk.Frame(parent)
        frame.pack(fill="x", padx=10, pady=4)
        ttk.Label(frame, text=label).pack(anchor="w", pady=(0, 2))
        widget.pack(fill="x")

    def _build_member_fields(self):
        self.steel_frame = ttk.Frame(self.member_fields)
        self._field(self.steel_frame, "Steel W-shape", ttk.Combobox(self.steel_frame, textvariable=self.shape,
                    values=tuple(STEEL), state="readonly"))
        self._field(self.steel_frame, "Steel grade", ttk.Combobox(self.steel_frame, textvariable=self.grade,
                    values=tuple(STEEL_GRADES), state="readonly"))
        self.wood_frame = ttk.Frame(self.member_fields)
        self._field(self.wood_frame, "Species and grade", ttk.Combobox(self.wood_frame, textvariable=self.species,
                    values=tuple(WOOD), state="readonly"))
        self._field(self.wood_frame, "Lumber size", ttk.Combobox(self.wood_frame, textvariable=self.size,
                    values=tuple(LUMBER_SIZES), state="readonly"))
        self._refresh_member_fields()

    def _refresh_member_fields(self):
        self.steel_frame.pack_forget()
        self.wood_frame.pack_forget()
        (self.steel_frame if self.member_type.get() == "Steel W-shape" else self.wood_frame).pack(fill="x")

    def _canvas_card(self, parent, title, height):
        frame = tk.Frame(parent, bg="white", highlightbackground="#d5dfd7", highlightthickness=1)
        frame.pack(fill="x", pady=(0, 8))
        tk.Label(frame, text=title, bg="white", fg=FOREST, font=("Segoe UI", 10, "bold"), anchor="w").pack(fill="x", padx=10, pady=(7, 0))
        canvas = tk.Canvas(frame, height=height, bg="white", highlightthickness=0)
        canvas.pack(fill="x", expand=True, padx=6, pady=3)
        return canvas

    def _chart_card(self, parent, title, subtitle, row, col, colspan=1):
        frame = tk.Frame(parent, bg="white", highlightbackground="#d5dfd7", highlightthickness=1)
        frame.grid(row=row, column=col, columnspan=colspan, sticky="nsew", padx=4, pady=4)
        tk.Label(frame, text=title, bg="white", fg=FOREST, font=("Segoe UI", 10, "bold"), anchor="w").pack(fill="x", padx=9, pady=(6, 0))
        tk.Label(frame, text=subtitle, bg="white", fg=MUTED, font=("Segoe UI", 9), anchor="w").pack(fill="x", padx=9)
        canvas = tk.Canvas(frame, height=180, bg="white", highlightthickness=0)
        canvas.pack(fill="both", expand=True, padx=3, pady=3)
        return canvas

    def _load_row(self, container, values, names, is_point):
        frame = ttk.LabelFrame(container, text="Point load" if is_point else "Uniform load")
        frame.pack(fill="x", pady=3)
        variables = {name: tk.StringVar(value=str(values[name])) for name in names}
        for variable in variables.values():
            variable.trace_add("write", self._mark_dirty)
        fields = [(("Magnitude (kip)" if is_point else "Intensity (kip/ft)"), "magnitude"), ("Direction", "direction")]
        if is_point:
            fields.append(("Position (ft)", "position"))
        else:
            fields.extend([("Start (ft)", "start"), ("End (ft)", "end")])
        for label, key in fields:
            row = ttk.Frame(frame)
            row.pack(fill="x", padx=5, pady=2)
            ttk.Label(row, text=label, width=17).pack(side="left")
            if key == "direction":
                widget = ttk.Combobox(row, textvariable=variables[key], values=("Down", "Up"), state="readonly", width=9)
            else:
                widget = ttk.Entry(row, textvariable=variables[key], width=11)
            widget.pack(side="right", fill="x", expand=True)
        rows = self.point_rows if is_point else self.uniform_rows
        remove = ttk.Button(frame, text="Remove", command=lambda: self._remove_row(frame, rows))
        remove.pack(anchor="e", padx=5, pady=(1, 5))
        rows.append((frame, variables))

    def _remove_row(self, frame, rows):
        rows[:] = [row for row in rows if row[0] is not frame]
        frame.destroy()
        self._mark_dirty()

    def _add_point(self, values=None):
        self._load_row(self.point_box, values or {"magnitude": "2", "direction": "Down", "position": "20"},
                       ("magnitude", "direction", "position"), True)
        self._mark_dirty()

    def _add_uniform(self, values=None):
        self._load_row(self.uniform_box, values or {"magnitude": "1", "direction": "Down", "start": "0", "end": "40"},
                       ("magnitude", "direction", "start", "end"), False)
        self._mark_dirty()

    def _example(self, clean=False):
        self._loading = True
        try:
            for frame, _ in self.point_rows + self.uniform_rows:
                frame.destroy()
            self.point_rows.clear()
            self.uniform_rows.clear()
            self.span.set("40")
            self.support.set("Simply supported")
            self.member_type.set("Steel W-shape")
            self.shape.set("W12x26")
            self.grade.set("ASTM A992")
            self.species.set("Douglas Fir-Larch No. 2")
            self.size.set("2x10")
            self._add_uniform({"magnitude": "1", "direction": "Down", "start": "0", "end": "40"})
        finally:
            self._loading = False
        self.current_file = None
        self.dirty = not clean
        self._update_file_status()
        self._run()

    def _reset_example(self):
        if self._confirm_unsaved():
            self._example(clean=False)

    def _mark_dirty(self, *_):
        if self._loading:
            return
        self.dirty = True
        self._update_file_status()

    def _update_file_status(self):
        if not hasattr(self, "file_status"):
            return
        if self.current_file:
            label = f"File: {self.current_file}"
        else:
            label = "Not saved"
        self.file_status.configure(text=label + (" · unsaved changes" if self.dirty else ""))
        title = "Beam Designer"
        if self.current_file:
            title += f" — {self.current_file}"
        if self.dirty:
            title += " *"
        self.title(title)

    def _current_config(self):
        member = {"type": self.member_type.get()}
        if self.member_type.get() == "Steel W-shape":
            member.update({"shape": self.shape.get(), "grade": self.grade.get()})
        else:
            member.update({"species": self.species.get(), "size": self.size.get()})
        points = []
        for _, fields in self.point_rows:
            points.append({
                "magnitude_kip": fields["magnitude"].get(),
                "direction": fields["direction"].get(),
                "position_ft": fields["position"].get(),
            })
        uniforms = []
        for _, fields in self.uniform_rows:
            uniforms.append({
                "intensity_kip_per_ft": fields["magnitude"].get(),
                "direction": fields["direction"].get(),
                "start_ft": fields["start"].get(),
                "end_ft": fields["end"].get(),
            })
        return beam_io.normalize_config({
            "format": beam_io.FORMAT_NAME,
            "version": beam_io.FORMAT_VERSION,
            "beam": {
                "support": self.support.get(),
                "span_ft": self.span.get(),
                "member": member,
                "deflection_limit": {"type": "span_ratio", "denominator": beam_io.DEFLECTION_LIMIT_DENOMINATOR},
            },
            "loads": {"point": points, "uniform": uniforms},
        })

    def _save(self):
        if self.current_file:
            path = self.current_file
        else:
            path = filedialog.asksaveasfilename(
                parent=self, title="Save Beam Designer file",
                defaultextension=".beam.json",
                filetypes=(("Beam Designer files", "*.beam.json"), ("JSON files", "*.json"), ("All files", "*.*")),
            )
            if not path:
                return False
        try:
            beam_io.save_config(path, self._current_config())
        except (OSError, ValueError) as exc:
            messagebox.showerror("Could not save beam", str(exc), parent=self)
            return False
        self.current_file = path
        self.dirty = False
        self._update_file_status()
        return True

    def _confirm_unsaved(self):
        if not self.dirty:
            return True
        choice = messagebox.askyesnocancel(
            "Unsaved changes", "Save changes to the current beam before continuing?", parent=self,
        )
        if choice is None:
            return False
        if choice:
            return self._save()
        return True

    def _open(self):
        path = filedialog.askopenfilename(
            parent=self, title="Open Beam Designer file",
            filetypes=(("Beam Designer files", "*.beam.json"), ("JSON files", "*.json"), ("All files", "*.*")),
        )
        if not path:
            return
        try:
            config = beam_io.load_config(path)
        except (OSError, ValueError) as exc:
            messagebox.showerror("Could not open beam", str(exc), parent=self)
            return
        if not self._confirm_unsaved():
            return
        self._apply_config(config, path)

    def _apply_config(self, config, path):
        beam = config["beam"]
        member = beam["member"]
        self._loading = True
        try:
            for frame, _ in self.point_rows + self.uniform_rows:
                frame.destroy()
            self.point_rows.clear()
            self.uniform_rows.clear()
            self.support.set(beam["support"])
            self.span.set(str(beam["span_ft"]))
            self.member_type.set(member["type"])
            if member["type"] == "Steel W-shape":
                self.shape.set(member["shape"])
                self.grade.set(member["grade"])
            else:
                self.species.set(member["species"])
                self.size.set(member["size"])
            for load in config["loads"]["point"]:
                self._add_point({
                    "magnitude": load["magnitude_kip"], "direction": load["direction"],
                    "position": load["position_ft"],
                })
            for load in config["loads"]["uniform"]:
                self._add_uniform({
                    "magnitude": load["intensity_kip_per_ft"], "direction": load["direction"],
                    "start": load["start_ft"], "end": load["end_ft"],
                })
        finally:
            self._loading = False
        self.current_file = path
        self.dirty = False
        self._update_file_status()
        self._run()

    def _on_close(self):
        if self._confirm_unsaved():
            self.destroy()

    def _collect_loads(self):
        points, uniforms = [], []
        for _, fields in self.point_rows:
            sign = -1 if fields["direction"].get() == "Down" else 1
            points.append(PointLoad(sign*float(fields["magnitude"].get()), float(fields["position"].get())))
        for _, fields in self.uniform_rows:
            sign = -1 if fields["direction"].get() == "Down" else 1
            uniforms.append(UniformLoad(sign*float(fields["magnitude"].get()), float(fields["start"].get()), float(fields["end"].get())))
        return points, uniforms

    def _run(self):
        try:
            points, uniforms = self._collect_loads()
            cantilever = self.support.get() == "Cantilever"
            member = get_member(self.member_type.get(), self.shape.get(), self.grade.get(), self.species.get(), self.size.get())
            result = analyze(float(self.span.get()), cantilever, points, uniforms, member)
        except (ValueError, KeyError, ZeroDivisionError) as exc:
            self.error_label.configure(text=str(exc))
            self.last_analysis = None
            self.last_points = []
            self.last_uniforms = []
            self.last_member = None
            return None
        self.error_label.configure(text="")
        self.title_label.configure(text=f"{result.span:g} ft {'cantilever' if cantilever else 'simply supported beam'}")
        self.member_caption.configure(text=f"{member.label} · {len(points)+len(uniforms)} applied load(s)")
        self.results_text.configure(state="normal")
        self.results_text.delete("1.0", "end")
        reaction = f"{'Fixed-end reaction' if cantilever else 'Reaction at A'}: {result.reaction_a:.2f} kip ({'up' if result.reaction_a >= 0 else 'down'})"
        if cantilever:
            reaction += f" · fixed-end reaction moment: {abs(result.reaction_moment):.2f} kip-ft ({'ccw' if result.reaction_moment >= 0 else 'cw'})"
        else:
            reaction += f" · Reaction B: {result.reaction_b:.2f} kip ({'up' if result.reaction_b >= 0 else 'down'})"
        self.results_text.insert("end", reaction + "\n")
        self.results_text.insert("end", f"Maximum |V| = {result.max_shear:.2f} kip at x = {result.shear_x:.2f} ft · Maximum |M| = {result.max_moment:.2f} kip-ft at x = {result.moment_x:.2f} ft\n")
        direction = "down" if result.deflection_down else "up"
        self.results_text.insert("end", f"Maximum |deflection| = {result.max_deflection:.3f} in ({direction}) at x = {result.deflection_x:.2f} ft · L/360 = {result.limit:.3f} in\n")
        self.results_text.insert("end", f"S = {member.section_modulus:.2f} in³ · I = {member.inertia:.1f} in⁴ · E = {member.elastic_modulus:.0f} ksi · Fb = {member.allowable_bending:.2f} ksi\n")
        self.results_text.insert("end", f"Maximum bending stress = {result.bending_stress:.2f} ksi · {member.note}")
        self.results_text.configure(state="disabled")
        self.checks_label.configure(text=f"{'PASS' if result.bending_pass else 'FAIL'}  Bending: {result.bending_stress:.2f} / {member.allowable_bending:.2f} ksi      {'PASS' if result.deflection_pass else 'FAIL'}  Deflection: {result.max_deflection:.3f} / {result.limit:.3f} in")
        self._draw(result, points, uniforms)
        self.last_analysis = result
        self.last_points = list(points)
        self.last_uniforms = list(uniforms)
        self.last_member = member
        return result

    def _export_csv(self):
        result = self._run()
        if result is None:
            return
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Export beam response as CSV",
            initialfile="beam_results.csv",
            defaultextension=".csv",
            filetypes=(("CSV files", "*.csv"), ("All files", "*.*")),
        )
        if not path:
            return
        try:
            destination = export_csv(path, result, self.last_points)
        except OSError as exc:
            messagebox.showerror("Could not export CSV", str(exc), parent=self)
            return
        messagebox.showinfo("CSV exported", f"Beam response table saved to:\n{destination}", parent=self)

    def _export_pdf(self):
        result = self._run()
        if result is None:
            return
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Save preliminary beam report",
            initialfile="beam_report.pdf",
            defaultextension=".pdf",
            filetypes=(("PDF files", "*.pdf"), ("All files", "*.*")),
        )
        if not path:
            return
        try:
            destination = create_report(
                path, result, self.last_points, self.last_uniforms, self.last_member,
            )
        except (OSError, ValueError) as exc:
            messagebox.showerror("Could not create PDF report", str(exc), parent=self)
            return
        messagebox.showinfo("PDF report saved", f"Calculation sheet saved to:\n{destination}", parent=self)

    def _draw(self, result, points, uniforms):
        draw_beam(self.beam_canvas, result.span, result.cantilever, points, uniforms)
        draw_diagram(self.shear_canvas, result.xs, result.shears, result.span, "kip", "V + upward")
        draw_diagram(self.moment_canvas, result.xs, result.moments, result.span, "kip-ft", "M + sagging")
        draw_diagram(self.deflection_canvas, result.xs, result.deflections, result.span, "in", "down +", invert=True)

    def _redraw_on_resize(self, event):
        if event.widget is self and hasattr(self, "beam_canvas"):
            self.after_idle(lambda: self._run())


if __name__ == "__main__":
    BeamDesigner().mainloop()

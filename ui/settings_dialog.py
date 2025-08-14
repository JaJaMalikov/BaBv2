from __future__ import annotations

from typing import Optional, Any

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QDialogButtonBox, QSpinBox, QDoubleSpinBox, QHBoxLayout,
    QLineEdit, QPushButton, QFileDialog, QGroupBox, QCheckBox, QTabWidget,
    QListWidget, QListWidgetItem, QAbstractItemView, QScrollArea, QWidget, QComboBox, QListView, QLabel, QSplitter
)
from PySide6.QtCore import Qt, QSize, QRectF
from PySide6.QtGui import QIcon, QColor, QPainter, QPixmap, QPainterPath

class IconStrip(QListWidget):
    """Icon list that arranges items in 1 or 2 rows, with labels under icons.

    rows: 0 -> auto (wrap by width), 1 -> single row, 2 -> exactly two rows.
    """
    def __init__(self, parent: Optional[QWidget] = None, rows: int = 0) -> None:  # type: ignore[name-defined]
        super().__init__(parent)
        self._fixed_rows: int = max(0, min(2, rows))
        self.setViewMode(QListView.IconMode)
        # For fixed two rows, build columns vertically to guarantee 2 rows regardless of width.
        self.setFlow(QListView.LeftToRight if self._fixed_rows == 1 else QListView.TopToBottom)
        self.setWrapping(False)
        self.setMovement(QListView.Snap)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setResizeMode(QListView.Adjust)
        self.setSpacing(8)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setFrameShape(QListWidget.NoFrame)
        self.setSelectionMode(QAbstractItemView.NoSelection)
        self.setStyleSheet("QListWidget{background:transparent;} QListWidget::item{margin:2px;}")
        # Initialize grid size for accurate layout
        self.setGridSize(self._cell_size())

    def resizeEvent(self, event):  # type: ignore[override]
        super().resizeEvent(event)
        self._adjust_height()

    def setIconSize(self, size: QSize) -> None:  # type: ignore[override]
        super().setIconSize(size)
        self.setGridSize(self._cell_size())
        self._adjust_height()

    def _cell_size(self) -> QSize:
        icon = self.iconSize()
        fm = self.fontMetrics()
        # Add generous padding so the label is never clipped
        w = icon.width() + 20
        h = icon.height() + fm.height() + 20
        return QSize(max(24, w), max(24, h))

    def _adjust_height(self) -> None:
        cell = self._cell_size()
        if self._fixed_rows == 1:
            rows = 1
        elif self._fixed_rows == 2:
            rows = 2
        else:
            viewport_w = max(1, self.viewport().width())
            per_row = max(1, (viewport_w + self.spacing()) // (cell.width() + self.spacing()))
            count = max(1, self.count())
            rows = (count + per_row - 1) // per_row
        total_h = rows * cell.height() + max(0, rows - 1) * self.spacing() + 8
        self.setFixedHeight(total_h)


class SettingsDialog(QDialog):
    """Lightweight settings dialog to tweak common app parameters."""

    def __init__(self, parent: Optional[Any] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Paramètres")
        self.setModal(True)
        self.resize(760, 560)
        self.setMinimumSize(520, 380)

        main_layout = QVBoxLayout(self)
        tabs = QTabWidget(self)
        main_layout.addWidget(tabs)

        # --- Tab: Apparence ---
        tab_app = QGroupBox()
        form = QFormLayout(tab_app)
        form.setLabelAlignment(Qt.AlignRight)

        # Only UI-related settings are exposed here

        # --- UI section: icon directory and default panel sizes ---
        self.icon_dir_edit = QLineEdit()
        self.icon_dir_browse = QPushButton("Parcourir…")
        icon_layout = QHBoxLayout()
        icon_layout.addWidget(self.icon_dir_edit)
        icon_layout.addWidget(self.icon_dir_browse)
        form.addRow("Dossier d'icônes:", icon_layout)

        # Default overlay sizes
        self.lib_w = QSpinBox()
        self.lib_h = QSpinBox()
        self.insp_w = QSpinBox()
        self.insp_h = QSpinBox()
        for sp in (self.lib_w, self.lib_h, self.insp_w, self.insp_h):
            sp.setRange(150, 2000)
        lib_size_layout = QHBoxLayout()
        lib_size_layout.addWidget(self.lib_w)
        lib_size_layout.addWidget(self.lib_h)
        insp_size_layout = QHBoxLayout()
        insp_size_layout.addWidget(self.insp_w)
        insp_size_layout.addWidget(self.insp_h)
        form.addRow("Taille défaut Bibliothèque (W,H):", lib_size_layout)
        form.addRow("Taille défaut Inspecteur (W,H):", insp_size_layout)

        # Default overlay positions
        self.lib_x = QSpinBox()
        self.lib_y = QSpinBox()
        self.insp_x = QSpinBox()
        self.insp_y = QSpinBox()
        self.cust_x = QSpinBox()
        self.cust_y = QSpinBox()
        self.cust_w = QSpinBox()
        self.cust_h = QSpinBox()
        for sp in (self.lib_x, self.lib_y, self.insp_x, self.insp_y, self.cust_x, self.cust_y):
            sp.setRange(0, 10000)
        for sp in (self.cust_w, self.cust_h):
            sp.setRange(100, 2000)
        lib_pos_layout = QHBoxLayout()
        lib_pos_layout.addWidget(self.lib_x)
        lib_pos_layout.addWidget(self.lib_y)
        insp_pos_layout = QHBoxLayout()
        insp_pos_layout.addWidget(self.insp_x)
        insp_pos_layout.addWidget(self.insp_y)
        cust_pos_layout = QHBoxLayout()
        cust_pos_layout.addWidget(self.cust_x)
        cust_pos_layout.addWidget(self.cust_y)
        form.addRow("Position défaut Bibliothèque (X,Y):", lib_pos_layout)
        form.addRow("Position défaut Inspecteur (X,Y):", insp_pos_layout)
        form.addRow("Position défaut Custom (X,Y):", cust_pos_layout)
        cust_size_layout = QHBoxLayout()
        cust_size_layout.addWidget(self.cust_w)
        cust_size_layout.addWidget(self.cust_h)
        form.addRow("Taille défaut Custom (W,H):", cust_size_layout)

        # form is attached to tab_app via its parent; do not add to main layout to avoid double-parent warning

        # (Removed legacy checkbox builder: visibility is controlled directly in icon lists)

        # Icon size
        self.icon_size_spin = QSpinBox()
        self.icon_size_spin.setRange(16, 128)
        self.icon_size_spin.setSingleStep(4)
        form.addRow("Taille icône overlays:", self.icon_size_spin)

        tabs.addTab(tab_app, "Apparence")

        # --- Tab: Overlays / Builder ---
        tab_over_inner = QWidget()
        over_layout = QVBoxLayout(tab_over_inner)
        # (builder checkboxes removed to keep the UI compact)

        # Order lists (QListWidget-based)
        order_form = QFormLayout()
        self.list_main_order = QListWidget()
        self.list_main_order.setDragDropMode(QAbstractItemView.InternalMove)
        self.list_quick_order = QListWidget()
        self.list_quick_order.setDragDropMode(QAbstractItemView.InternalMove)
        self.list_custom_order = QListWidget()
        self.list_custom_order.setDragDropMode(QAbstractItemView.InternalMove)
        # Compact heights: Quick needs only one row
        # self.list_main_order.setFixedHeight(120)
        self.list_quick_order.setFixedHeight(80)
        # self.list_custom_order.setFixedHeight(120)
        order_form.addRow("Ordre Main:", self.list_main_order)
        order_form.addRow("Ordre Quick:", self.list_quick_order)
        order_form.addRow("Ordre Custom:", self.list_custom_order)
        self.cb_custom_visible = QCheckBox("Afficher l'overlay Custom")
        over_layout.addLayout(order_form)
        over_layout.addWidget(self.cb_custom_visible)
        # Put overlays content into a scroll area to keep dialog compact
        over_scroll = QScrollArea()
        over_scroll.setWidgetResizable(True)
        over_scroll.setWidget(tab_over_inner)
        tabs.addTab(over_scroll, "Overlays")

        # --- Tab: Icônes ---
        tab_icons_inner = QWidget()
        icons_layout = QHBoxLayout(tab_icons_inner)
        icons_layout.setContentsMargins(8, 8, 8, 8)
        icons_layout.setSpacing(10)

        # List of icon keys with current icon preview
        self.list_icons = QListWidget()
        self.list_icons.setViewMode(QListView.IconMode)
        self.list_icons.setFlow(QListView.LeftToRight)
        self.list_icons.setWrapping(True)
        self.list_icons.setResizeMode(QListView.Adjust)
        self.list_icons.setSpacing(8)
        self.list_icons.setIconSize(QSize(32, 32))
        self.list_icons.setSelectionMode(QAbstractItemView.SingleSelection)

        # Right side controls
        icons_controls = QWidget()
        icons_form = QFormLayout(icons_controls)
        icons_form.setLabelAlignment(Qt.AlignRight)
        self.lbl_key = QLabel("—")
        self.lbl_path = QLineEdit()
        self.lbl_path.setReadOnly(True)
        self.btn_pick_icon = QPushButton("Choisir un fichier…")
        self.btn_reset_icon = QPushButton("Réinitialiser cet icône")
        self.btn_reset_all = QPushButton("Réinitialiser tous")
        icons_form.addRow("Clé:", self.lbl_key)
        icons_form.addRow("Fichier:", self.lbl_path)
        row_btns = QHBoxLayout()
        row_btns.addWidget(self.btn_pick_icon)
        row_btns.addWidget(self.btn_reset_icon)
        row_btns.addStretch(1)
        row_wrap = QWidget()
        row_wrap.setLayout(row_btns)
        icons_form.addRow("Actions:", row_wrap)
        icons_form.addRow("", self.btn_reset_all)

        splitter = QSplitter()
        splitter.addWidget(self.list_icons)
        splitter.addWidget(icons_controls)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        icons_layout.addWidget(splitter)

        icons_scroll = QScrollArea()
        icons_scroll.setWidgetResizable(True)
        icons_scroll.setWidget(tab_icons_inner)
        tabs.addTab(icons_scroll, "Icônes")

        # --- Tab: Onion ---
        tab_onion = QWidget()
        onion_form = QFormLayout(tab_onion)
        self.prev_count = QSpinBox()
        self.prev_count.setRange(0, 10)
        self.next_count = QSpinBox()
        self.next_count.setRange(0, 10)
        self.opacity_prev = QDoubleSpinBox()
        self.opacity_prev.setRange(0.0, 1.0)
        self.opacity_prev.setSingleStep(0.05)
        self.opacity_next = QDoubleSpinBox()
        self.opacity_next.setRange(0.0, 1.0)
        self.opacity_next.setSingleStep(0.05)
        onion_form.addRow("Fantômes précédents:", self.prev_count)
        onion_form.addRow("Fantômes suivants:", self.next_count)
        onion_form.addRow("Opacité précédents:", self.opacity_prev)
        onion_form.addRow("Opacité suivants:", self.opacity_next)
        tabs.addTab(tab_onion, "Onion")

        # --- Tab: Styles (friendly controls) ---
        # Styles tab content inside a scroll area to avoid height squeezing
        tab_style_inner = QWidget()
        style_layout = QHBoxLayout(tab_style_inner)
        controls = QWidget()
        controls_layout = QFormLayout(controls)
        controls_layout.setLabelAlignment(Qt.AlignRight)
        # Presets
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(["Light", "Dark", "High Contrast", "Custom"])
        controls_layout.addRow("Preset:", self.preset_combo)
        # Color pickers (edit + button)
        self._swatches = {}
        def mk_color_row(title: str):
            le = QLineEdit()
            btn = QPushButton("…")
            btn.setFixedWidth(28)
            # Swatch showing current color
            sw = QLabel()
            sw.setFixedSize(24, 16)
            sw.setStyleSheet("QLabel{border:1px solid #A0AEC0; border-radius:3px; background:#FFFFFF;}")
            row = QHBoxLayout()
            row.setSpacing(6)
            row.addWidget(sw)
            row.addWidget(le)
            row.addWidget(btn)
            row.addStretch(1)
            wrap = QWidget()
            wrap.setLayout(row)
            controls_layout.addRow(title, wrap)
            self._swatches[le] = sw
            # Live update swatch on text change
            le.textChanged.connect(lambda _=None, e=le: self._update_swatch(e))
            return le, btn
        self.bg_edit, self.bg_btn = mk_color_row("Fond appli:")
        self.text_edit, self.text_btn = mk_color_row("Texte:")
        self.accent_edit, self.accent_btn = mk_color_row("Accent:")
        self.hover_edit, self.hover_btn = mk_color_row("Survol:")
        self.panel_edit, self.panel_btn = mk_color_row("Fond panneaux:")
        self.border_edit, self.border_btn = mk_color_row("Bordure panneaux:")
        self.group_edit, self.group_btn = mk_color_row("Titre de groupe:")
        # Numeric controls
        self.opacity_spin = QSpinBox()
        self.opacity_spin.setRange(0, 100)
        self.opacity_spin.setSuffix(" %")
        self.radius_spin = QSpinBox()
        self.radius_spin.setRange(0, 24)
        self.radius_spin.setSuffix(" px")
        self.font_spin = QSpinBox()
        self.font_spin.setRange(8, 18)
        self.font_spin.setSuffix(" pt")
        controls_layout.addRow("Opacité panneau:", self.opacity_spin)
        controls_layout.addRow("Coins arrondis:", self.radius_spin)
        controls_layout.addRow("Taille police:", self.font_spin)
        # Action buttons
        actions = QHBoxLayout()
        self.btn_preview = QPushButton("Prévisualiser")
        self.btn_save_custom = QPushButton("Enregistrer comme Custom")
        actions.addWidget(self.btn_preview)
        actions.addWidget(self.btn_save_custom)
        actions_wrap = QWidget()
        actions_wrap.setLayout(actions)
        controls_layout.addRow("", actions_wrap)

        # Preview area (richer, demonstrates most style params)
        self.preview_root = QWidget()
        preview_layout = QVBoxLayout(self.preview_root)
        preview_layout.setContentsMargins(12, 12, 12, 12)
        preview_layout.setSpacing(10)

        # Title
        title = QLabel("Aperçu du thème")
        preview_layout.addWidget(title)

        # Import preview-specific widgets to match stylesheet selectors
        from ui.draggable_widget import PanelOverlay, DraggableHeader

        # Fake workspace background (shows bg color behind semi-transparent panel)
        bg_wrap = QWidget()
        bg_layout = QVBoxLayout(bg_wrap)
        bg_layout.setContentsMargins(0, 0, 0, 0)
        bg_layout.setSpacing(8)

        # Panel overlay with header to visualize panel_bg, opacity, border and header
        panel = PanelOverlay(bg_wrap)
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(8, 8, 8, 8)
        panel_layout.setSpacing(8)
        header = DraggableHeader(panel, panel)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(8, 6, 8, 6)
        header_label = QLabel("Panneau / Overlay")
        header_layout.addWidget(header_label)
        header_layout.addStretch(1)

        panel_layout.addWidget(header)

        # Content area: group box to show group title color
        gb = QGroupBox("Propriétés")
        gb_form = QFormLayout(gb)
        gb_form.setLabelAlignment(Qt.AlignRight)

        # ToolButtons bar to show hover/checked/accent
        from PySide6.QtWidgets import QToolButton
        tb_bar = QHBoxLayout()
        tb1 = QToolButton()
        tb1.setText("Outil 1")
        tb1.setCheckable(True)
        tb1.setChecked(True)
        tb2 = QToolButton()
        tb2.setText("Outil 2")
        tb3 = QToolButton()
        tb3.setText("Outil 3")
        tb_bar.addWidget(tb1)
        tb_bar.addWidget(tb2)
        tb_bar.addWidget(tb3)
        tb_bar.addStretch(1)
        tb_wrap = QWidget()
        tb_wrap.setLayout(tb_bar)
        gb_form.addRow("Outils:", tb_wrap)

        # Inputs to show line edit + combo focus/accent
        self.prev_input = QLineEdit()
        self.prev_input.setPlaceholderText("Texte…")
        combo = QComboBox()
        combo.addItems(["Premier", "Second", "Troisième"])
        gb_form.addRow("Champ:", self.prev_input)
        gb_form.addRow("Choix:", combo)

        # Checkbox to show indicator style
        self.prev_chk = QCheckBox("Activer l'option")
        gb_form.addRow("Option:", self.prev_chk)

        # List to show hover/selected background
        lst = QListWidget()
        for i in range(1, 6):
            QListWidgetItem(f"Élément {i}", lst)
        lst.setCurrentRow(1)
        gb_form.addRow("Liste:", lst)

        panel_layout.addWidget(gb)

        # Primary action (QPushButton also visible under global text/background)
        self.prev_btn = QPushButton("Action primaire")
        panel_layout.addWidget(self.prev_btn)

        bg_layout.addWidget(panel)
        preview_layout.addWidget(bg_wrap)
        preview_layout.addStretch(1)

        style_layout.addWidget(controls, 2)
        style_layout.addWidget(self.preview_root, 3)
        style_scroll = QScrollArea()
        style_scroll.setWidgetResizable(True)
        style_scroll.setWidget(tab_style_inner)
        tabs.addTab(style_scroll, "Styles")

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        main_layout.addWidget(btns)

        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        self.icon_dir_browse.clicked.connect(self._on_browse_icons)
        # Color pickers
        color_rows = [
            (self.bg_edit, self.bg_btn), (self.text_edit, self.text_btn), (self.accent_edit, self.accent_btn),
            (self.hover_edit, self.hover_btn), (self.panel_edit, self.panel_btn), (self.border_edit, self.border_btn),
            (self.group_edit, self.group_btn)
        ]
        for le, btn in color_rows:
            btn.clicked.connect(lambda _, e=le: self._pick_color_into(e))
            # Live preview on color text change
            le.textChanged.connect(lambda _=None: self._preview_theme())
        # Presets & actions
        self.preset_combo.currentTextChanged.connect(self._load_preset_values)
        self.btn_preview.clicked.connect(self._preview_theme)
        self.btn_save_custom.clicked.connect(self._save_params_as_custom)
        # Live preview on numeric changes
        self.opacity_spin.valueChanged.connect(lambda _=None: self._preview_theme())
        self.radius_spin.valueChanged.connect(lambda _=None: self._preview_theme())
        self.font_spin.valueChanged.connect(lambda _=None: self._preview_theme())

        # Build icon-based lists for builder
        self._init_icon_lists()
        self.icon_size_spin.valueChanged.connect(self._apply_list_icon_size)

        # Initialize swatches from default/preset values
        self._load_preset_values(self.preset_combo.currentText())
        self._update_all_swatches()
        # Initial preview render
        self._preview_theme()

        # Init icons tab
        self._init_icons_tab()
        self.list_icons.currentItemChanged.connect(self._on_icon_item_changed)
        self.btn_pick_icon.clicked.connect(self._choose_icon_file)
        self.btn_reset_icon.clicked.connect(self._reset_icon_file)
        self.btn_reset_all.clicked.connect(self._reset_all_icons)

    def showEvent(self, event) -> None:  # type: ignore[override]
        super().showEvent(event)
        # No special handling needed

    def _on_browse_icons(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Choisir un dossier d'icônes")
        if path:
            self.icon_dir_edit.setText(path)

    # --- Styles helpers (simple) ---
    def _pick_color_into(self, edit: QLineEdit) -> None:
        from PySide6.QtWidgets import QColorDialog
        col = QColorDialog.getColor()
        if col.isValid():
            edit.setText(col.name())
            self._update_swatch(edit)

    def _params_from_ui(self) -> dict:
        return {
            'bg_color': self.bg_edit.text() or '#E2E8F0',
            'text_color': self.text_edit.text() or '#1A202C',
            'accent_color': self.accent_edit.text() or '#E53E3E',
            'hover_color': self.hover_edit.text() or '#E3E6FD',
            'panel_bg': self.panel_edit.text() or '#F7F8FC',
            'panel_opacity': (self.opacity_spin.value() / 100.0),
            'panel_border': self.border_edit.text() or '#D0D5DD',
            'group_title_color': self.group_edit.text() or '#2D3748',
            'radius': self.radius_spin.value(),
            'font_size': self.font_spin.value(),
        }

    def _load_preset_values(self, name: str) -> None:
        if name.lower() == 'light':
            self.bg_edit.setText('#E2E8F0')
            self.text_edit.setText('#1A202C')
            self.accent_edit.setText('#E53E3E')
            self.hover_edit.setText('#E3E6FD')
            self.panel_edit.setText('#F7F8FC')
            self.border_edit.setText('#D0D5DD')
            self.group_edit.setText('#2D3748')
            self.opacity_spin.setValue(90)
            self.radius_spin.setValue(12)
            self.font_spin.setValue(10)
        elif name.lower() == 'dark':
            self.bg_edit.setText('#1F2937')
            self.text_edit.setText('#E2E8F0')
            self.accent_edit.setText('#EF4444')
            self.hover_edit.setText('#374151')
            self.panel_edit.setText('#1F2937')
            self.border_edit.setText('#374151')
            self.group_edit.setText('#E5E7EB')
            self.opacity_spin.setValue(92)
            self.radius_spin.setValue(12)
            self.font_spin.setValue(10)
        elif name.lower() == 'high contrast':
            self.bg_edit.setText('#000000')
            self.text_edit.setText('#FFFFFF')
            self.accent_edit.setText('#FFD600')
            self.hover_edit.setText('#333333')
            self.panel_edit.setText('#000000')
            self.border_edit.setText('#FFFFFF')
            self.group_edit.setText('#FFFFFF')
            self.opacity_spin.setValue(100)
            self.radius_spin.setValue(0)
            self.font_spin.setValue(11)
        # Update swatches when preset changes and refresh preview
        self._update_all_swatches()
        self._preview_theme()
        # Custom keeps current entries

    def _preview_theme(self) -> None:
        from ui.styles import build_stylesheet
        css = build_stylesheet(self._params_from_ui())
        # Apply to dedicated preview container so we don't affect the whole dialog
        try:
            self.preview_root.setStyleSheet(css)
            # Move focus to input to demonstrate accent focus border
            self.prev_input.setFocus()
        except Exception:
            pass

    def _save_params_as_custom(self) -> None:
        from PySide6.QtCore import QSettings
        from ui.styles import build_stylesheet
        css = build_stylesheet(self._params_from_ui())
        s = QSettings("JaJa", "Macronotron")
        s.setValue('ui/custom_stylesheet', css)
        s.setValue('ui/theme', 'custom')

    # --- Swatch helpers ---
    def _update_swatch(self, edit: QLineEdit) -> None:
        sw = self._swatches.get(edit)
        if not sw:
            return
        # Special rendering for panel background: show checkerboard + opacity
        if edit is self.panel_edit:
            try:
                w, h = sw.width(), sw.height()
                pix = QPixmap(w, h)
                pix.fill(Qt.transparent)
                p = QPainter(pix)
                p.setRenderHint(QPainter.Antialiasing, True)
                path = QPainterPath()
                path.addRoundedRect(QRectF(0, 0, w, h), 3, 3)
                p.setClipPath(path)
                # Checkerboard background
                s = 4
                c1 = QColor('#FFFFFF')
                c2 = QColor('#C7CBD1')
                for y in range(0, h, s):
                    for x in range(0, w, s):
                        p.fillRect(x, y, s, s, c1 if ((x // s + y // s) % 2 == 0) else c2)
                # Overlay panel color with opacity from spin
                color = QColor(edit.text().strip() or '#FFFFFF')
                if not color.isValid():
                    color = QColor('#FFFFFF')
                alpha = max(0.0, min(1.0, self.opacity_spin.value() / 100.0))
                color.setAlphaF(alpha)
                p.fillRect(QRectF(0, 0, w, h), color)
                p.end()
                # Keep border via stylesheet; set pixmap for fill
                sw.setStyleSheet("QLabel{border:1px solid #A0AEC0; border-radius:3px; background:transparent;}")
                sw.setPixmap(pix)
            except Exception:
                # Fallback to flat color
                col = edit.text().strip() or '#FFFFFF'
                if not col.startswith('#') and not col.startswith('rgb'):
                    col = '#FFFFFF'
                sw.setStyleSheet(f"QLabel{{border:1px solid #A0AEC0; border-radius:3px; background:{col};}}")
        else:
            col = edit.text().strip() or '#FFFFFF'
            # Basic validation: ensure it looks like a color string
            if not col.startswith('#') and not col.startswith('rgb'):
                col = '#FFFFFF'
            sw.setPixmap(QPixmap())
            sw.setStyleSheet(f"QLabel{{border:1px solid #A0AEC0; border-radius:3px; background:{col};}}")

    def _update_all_swatches(self) -> None:
        for le in self._swatches.keys():
            self._update_swatch(le)

        # Re-render panel swatch when opacity changes
        try:
            self.opacity_spin.valueChanged.connect(lambda _=None: self._update_swatch(self.panel_edit))
        except Exception:
            pass

    # --- Icon lists (builder) ---
    def _apply_list_icon_size(self) -> None:
        size = self.icon_size_spin.value()
        for lw in (self.list_main_order, self.list_quick_order, self.list_custom_order):
            lw.setIconSize(QSize(size, size))
            try:
                lw.viewport().update()
            except Exception:
                pass

    def _init_icon_lists(self) -> None:
        from ui.icons import (
            icon_save, icon_open, icon_scene_size, icon_background, icon_reset_scene, icon_reset_ui,
            icon_library, icon_inspector, icon_timeline, get_icon, icon_plus, icon_minus, icon_fit, icon_rotate, icon_onion
        )
        # Configure lists to show icons horizontally with wrapping
        for lw in (self.list_main_order, self.list_quick_order, self.list_custom_order):
            lw.setViewMode(QListView.IconMode)
            lw.setFlow(QListView.LeftToRight)
            lw.setWrapping(True)
            lw.setMovement(QListView.Snap)
            lw.setDragDropMode(QAbstractItemView.InternalMove)
            lw.setResizeMode(QListView.Adjust)
            lw.setSpacing(8)
            lw.setIconSize(QSize(self.icon_size_spin.value(), self.icon_size_spin.value()))

        self._main_specs = [
            ("save", "Sauver", icon_save()),
            ("load", "Charger", icon_open()),
            ("scene_size", "Scène", icon_scene_size()),
            ("background", "Fond", icon_background()),
            ("settings", "Paramètres", get_icon('layers')),
            ("reset_scene", "Reset scène", icon_reset_scene()),
            ("reset_ui", "Reset UI", icon_reset_ui()),
            ("toggle_library", "Lib", icon_library()),
            ("toggle_inspector", "Insp", icon_inspector()),
            ("toggle_timeline", "Time", icon_timeline()),
            ("toggle_custom", "Custom", get_icon('layers')),
        ]
        self._quick_specs = [
            ("zoom_out", "-", icon_minus()),
            ("zoom_in", "+", icon_plus()),
            ("fit", "Fit", icon_fit()),
            ("handles", "Rot", icon_rotate()),
            ("onion", "Onion", icon_onion()),
        ]
        # Custom can use both
        self._custom_specs = self._main_specs + self._quick_specs

    def populate_icon_list(self, lw: QListWidget, order_keys: list[str], visibility_map: dict[str, bool], specs: list[tuple[str, str, QIcon]]) -> None:
        lw.clear()
        spec_map = {k: (label, icon) for (k, label, icon) in [(k, lbl, ic) for (k, lbl, ic) in specs]}
        for key in order_keys:
            if key not in spec_map:
                continue
            label, icon = spec_map[key]
            # Icon with label under it
            item = QListWidgetItem(icon, label)
            item.setData(Qt.UserRole, key)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsDragEnabled | Qt.ItemIsSelectable)
            item.setCheckState(Qt.Checked if visibility_map.get(key, True) else Qt.Unchecked)
            lw.addItem(item)
        # No special height handling

    def extract_icon_list(self, lw: QListWidget) -> tuple[list[str], dict[str, bool]]:
        order: list[str] = []
        vis: dict[str, bool] = {}
        for i in range(lw.count()):
            it = lw.item(i)
            key = it.data(Qt.UserRole)
            order.append(key)
            vis[key] = (it.checkState() == Qt.Checked)
        return order, vis

    # (no IconStrip helpers)

    # --- Icons tab helpers ---
    def _init_icons_tab(self) -> None:
        # Canonical keys we expose to customize
        self._icon_keys = [
            'save','open','scene_size','background','settings','reset_scene','reset_ui',
            'library','inspector','timeline','layers',
            'zoom_out','zoom_in','fit','handles','onion',
            'delete','duplicate','link','link_off','close',
            'objets','puppet','open_menu','close_menu','close_menu_inv','new_file',
            'chevron_left','chevron_right','plus','minus','rotate'
        ]
        self._populate_icons_list()
        if self.list_icons.count():
            self.list_icons.setCurrentRow(0)

    def _populate_icons_list(self) -> None:
        from ui.icons import get_icon
        from PySide6.QtCore import QSettings
        self.list_icons.clear()
        s = QSettings("JaJa", "Macronotron")
        for key in self._icon_keys:
            icon = get_icon(key)
            it = QListWidgetItem(icon, key)
            it.setData(Qt.UserRole, key)
            # Mark custom ones with asterisk and tooltip
            path = s.value(f"ui/icon_override/{key}")
            if path:
                it.setText(f"{key} *")
                it.setToolTip(str(path))
            self.list_icons.addItem(it)

    def _on_icon_item_changed(self, current: Optional[QListWidgetItem], previous: Optional[QListWidgetItem]) -> None:
        from PySide6.QtCore import QSettings
        if not current:
            self.lbl_key.setText("—")
            self.lbl_path.setText("")
            return
        key = current.data(Qt.UserRole)
        self.lbl_key.setText(str(key))
        s = QSettings("JaJa", "Macronotron")
        self.lbl_path.setText(str(s.value(f"ui/icon_override/{key}") or ""))

    def _choose_icon_file(self) -> None:
        from PySide6.QtWidgets import QFileDialog
        item = self.list_icons.currentItem()
        if not item:
            return
        key = item.data(Qt.UserRole)
        path, _ = QFileDialog.getOpenFileName(self, "Choisir une icône", "", "Images (*.svg *.png *.jpg *.bmp *.ico)")
        if not path:
            return
        from PySide6.QtCore import QSettings
        s = QSettings("JaJa", "Macronotron")
        s.setValue(f"ui/icon_override/{key}", path)
        self.lbl_path.setText(path)
        self._refresh_icons_runtime()
        self._populate_icons_list()

    def _reset_icon_file(self) -> None:
        item = self.list_icons.currentItem()
        if not item:
            return
        key = item.data(Qt.UserRole)
        from PySide6.QtCore import QSettings
        s = QSettings("JaJa", "Macronotron")
        s.remove(f"ui/icon_override/{key}")
        self.lbl_path.setText("")
        self._refresh_icons_runtime()
        self._populate_icons_list()

    def _reset_all_icons(self) -> None:
        from PySide6.QtCore import QSettings
        s = QSettings("JaJa", "Macronotron")
        s.beginGroup("ui/icon_override")
        s.remove("")
        s.endGroup()
        self._refresh_icons_runtime()
        self._populate_icons_list()

    def _refresh_icons_runtime(self) -> None:
        # Clear cache and refresh action/overlay icons on the main window
        try:
            import ui.icons as app_icons
            app_icons.clear_cache()
            from ui.icons import (
                icon_scene_size, icon_background, icon_library, icon_inspector, icon_timeline,
                icon_save, icon_open, icon_reset_ui, icon_reset_scene
            )
            mw = self.parent()
            # Actions
            if hasattr(mw, 'save_action'):
                mw.save_action.setIcon(icon_save())
            if hasattr(mw, 'load_action'):
                mw.load_action.setIcon(icon_open())
            if hasattr(mw, 'scene_size_action'):
                mw.scene_size_action.setIcon(icon_scene_size())
            if hasattr(mw, 'background_action'):
                mw.background_action.setIcon(icon_background())
            if hasattr(mw, 'reset_scene_action'):
                mw.reset_scene_action.setIcon(icon_reset_scene())
            if hasattr(mw, 'reset_ui_action'):
                mw.reset_ui_action.setIcon(icon_reset_ui())
            if hasattr(mw, 'toggle_library_action'):
                mw.toggle_library_action.setIcon(icon_library())
            if hasattr(mw, 'toggle_inspector_action'):
                mw.toggle_inspector_action.setIcon(icon_inspector())
            if hasattr(mw, 'timeline_dock'):
                mw.timeline_dock.toggleViewAction().setIcon(icon_timeline())
            # Overlay buttons
            if hasattr(mw, 'view'):
                mw.view.refresh_overlay_icons(mw)
                mw.view.apply_menu_settings_main()
                mw.view.apply_menu_settings_quick()
        except Exception:
            pass

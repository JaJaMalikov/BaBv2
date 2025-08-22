"""Module for the settings dialog, allowing users to customize the application."""

from __future__ import annotations

import logging
from typing import Any, Optional

from PySide6.QtCore import QRectF, QSettings, QSize, Qt
from PySide6.QtGui import (
    QAction,
    QColor,
    QIcon,
    QKeySequence,
    QPainter,
    QPainterPath,
    QPixmap,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QKeySequenceEdit,
    QLabel,
    QLineEdit,
    QListView,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QSplitter,
    QTabWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from ui.draggable_widget import DraggableHeader, PanelOverlay
from ui.styles import build_stylesheet
from .theme_settings import DEFAULT_CUSTOM_PARAMS, THEME_PARAMS


class IconStrip(QListWidget):
    """Icon list that arranges items in 1 or 2 rows, with labels under icons."""

    def __init__(self, parent: Optional[QWidget] = None, rows: int = 0) -> None:  # type: ignore[name-defined]
        """
        Initializes the IconStrip widget.

        Args:
            parent: The parent widget.
            rows: The number of fixed rows (0 for auto, 1 for single, 2 for double).
        """
        super().__init__(parent)
        self._fixed_rows: int = max(0, min(2, rows))
        self.setViewMode(QListView.IconMode)
        # For fixed two rows, build columns vertically to guarantee 2 rows regardless of width.
        self.setFlow(
            QListView.LeftToRight if self._fixed_rows == 1 else QListView.TopToBottom
        )
        self.setWrapping(False)
        self.setMovement(QListView.Snap)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setResizeMode(QListView.Adjust)
        self.setSpacing(8)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setFrameShape(QListWidget.NoFrame)
        self.setSelectionMode(QAbstractItemView.NoSelection)
        self.setStyleSheet(
            "QListWidget{background:transparent;} QListWidget::item{margin:2px;}"
        )
        # Initialize grid size for accurate layout
        self.setGridSize(self._cell_size())

    def resizeEvent(self, event):  # type: ignore[override]
        """
        Handles the resize event to adjust the height of the widget.

        Args:
            event: The resize event.
        """
        super().resizeEvent(event)
        self._adjust_height()

    def setIconSize(self, size: QSize) -> None:  # type: ignore[override]
        """
        Sets the icon size and adjusts the grid size and height accordingly.

        Args:
            size: The new icon size.
        """
        super().setIconSize(size)
        self.setGridSize(self._cell_size())
        self._adjust_height()

    def _cell_size(self) -> QSize:
        """Calculates the size of a cell in the list view."""
        icon = self.iconSize()
        fm = self.fontMetrics()
        # Add generous padding so the label is never clipped
        w = icon.width() + 20
        h = icon.height() + fm.height() + 20
        return QSize(max(24, w), max(24, h))

    def _adjust_height(self) -> None:
        """Adjusts the height of the widget based on the number of rows."""
        cell = self._cell_size()
        if self._fixed_rows == 1:
            rows = 1
        elif self._fixed_rows == 2:
            rows = 2
        else:
            viewport_w = max(1, self.viewport().width())
            per_row = max(
                1, (viewport_w + self.spacing()) // (cell.width() + self.spacing())
            )
            count = max(1, self.count())
            rows = (count + per_row - 1) // per_row
        total_h = rows * cell.height() + max(0, rows - 1) * self.spacing() + 8
        self.setFixedHeight(total_h)


class SettingsDialog(QDialog):
    """A dialog for managing application settings."""

    def __init__(self, parent: Optional[Any] = None) -> None:
        """
        Initializes the SettingsDialog.

        Args:
            parent: The parent widget.
        """
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
        for sp in (
            self.lib_x,
            self.lib_y,
            self.insp_x,
            self.insp_y,
            self.cust_x,
            self.cust_y,
        ):
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

        # Icon size
        self.icon_size_spin = QSpinBox()
        self.icon_size_spin.setRange(16, 128)
        self.icon_size_spin.setSingleStep(4)
        form.addRow("Taille icône overlays:", self.icon_size_spin)

        tabs.addTab(tab_app, "Apparence")

        # --- Tab: Raccourcis ---
        tab_keys = QWidget()
        keys_form = QFormLayout(tab_keys)
        keys_form.setLabelAlignment(Qt.AlignRight)
        self._key_form = keys_form
        self._shortcut_edits: dict[str, QKeySequenceEdit] = {}
        tabs.addTab(tab_keys, "Raccourcis")

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
        self.list_icons.setDragDropMode(QAbstractItemView.NoDragDrop)
        self.list_icons.setMovement(QListView.Static)
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
        controls_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
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
            sw.setStyleSheet(
                "QLabel{border:1px solid #A0AEC0; border-radius:3px; background:#FFFFFF;}"
            )
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
            return le, btn, wrap

        # Variant: add a color row into a specific form layout (for Timeline tab)
        def mk_color_row_into(form_layout: QFormLayout, title: str):
            le = QLineEdit()
            btn = QPushButton("…")
            btn.setFixedWidth(28)
            sw = QLabel()
            sw.setFixedSize(24, 16)
            sw.setStyleSheet(
                "QLabel{border:1px solid #A0AEC0; border-radius:3px; background:#FFFFFF;}"
            )
            row = QHBoxLayout()
            row.setSpacing(6)
            row.addWidget(sw)
            row.addWidget(le)
            row.addWidget(btn)
            row.addStretch(1)
            wrap = QWidget()
            wrap.setLayout(row)
            form_layout.addRow(title, wrap)
            self._swatches[le] = sw
            # Only swatch update here (no live app preview for timeline)
            le.textChanged.connect(lambda _=None, e=le: self._update_swatch(e))
            btn.clicked.connect(lambda _, e=le: self._pick_color_into(e))
            return le, btn, wrap

        self.bg_edit, self.bg_btn, wrap_bg = mk_color_row("Fond application:")
        self.text_edit, self.text_btn, wrap_text = mk_color_row("Texte (global):")
        self.accent_edit, self.accent_btn, wrap_accent = mk_color_row(
            "Couleur d'accent:"
        )
        self.hover_edit, self.hover_btn, wrap_hover = mk_color_row("Couleur de survol:")
        self.panel_edit, self.panel_btn, wrap_panel = mk_color_row("Fond des panneaux:")
        self.border_edit, self.border_btn, wrap_border = mk_color_row(
            "Bordure des panneaux:"
        )
        # Header (overlays) colors
        self.header_bg_edit, self.header_bg_btn, wrap_hbg = mk_color_row(
            "Fond des en-têtes:"
        )
        self.header_text_edit, self.header_text_btn, wrap_htxt = mk_color_row(
            "Texte des en-têtes:"
        )
        self.header_border_edit, self.header_border_btn, wrap_hb = mk_color_row(
            "Bordure des en-têtes:"
        )
        # Scene background color (no image)
        self.scene_bg_edit, self.scene_bg_btn, wrap_scene = mk_color_row(
            "Fond de la scène:"
        )
        # Tooltips colors
        self.tooltip_bg_edit, self.tooltip_bg_btn, wrap_tipbg = mk_color_row(
            "Fond des info‑bulles:"
        )
        self.tooltip_text_edit, self.tooltip_text_btn, wrap_tiptext = mk_color_row(
            "Texte des info‑bulles:"
        )
        self.group_edit, self.group_btn, wrap_group = mk_color_row("Titres de groupe:")
        # Inputs & lists & checkboxes (exposés du stylesheet)
        self.input_bg_edit, self.input_bg_btn, wrap_inbg = mk_color_row("Champ: fond:")
        self.input_border_edit, self.input_border_btn, wrap_inb = mk_color_row(
            "Champ: bordure:"
        )
        self.input_text_edit, self.input_text_btn, wrap_int = mk_color_row(
            "Champ: texte:"
        )
        self.input_focus_bg_edit, self.input_focus_bg_btn, wrap_infbg = mk_color_row(
            "Champ focus: fond:"
        )
        self.input_focus_border_edit, self.input_focus_border_btn, wrap_infb = (
            mk_color_row("Champ focus: bordure:")
        )
        self.list_hover_edit, self.list_hover_btn, wrap_lh = mk_color_row(
            "Liste: survol:"
        )
        self.list_sel_bg_edit, self.list_sel_bg_btn, wrap_lsb = mk_color_row(
            "Liste: sélection fond:"
        )
        self.list_sel_text_edit, self.list_sel_text_btn, wrap_lst = mk_color_row(
            "Liste: sélection texte:"
        )
        self.cb_un_bg_edit, self.cb_un_bg_btn, wrap_cub = mk_color_row(
            "Case non cochée: fond:"
        )
        self.cb_un_border_edit, self.cb_un_border_btn, wrap_cubd = mk_color_row(
            "Case non cochée: bordure:"
        )
        self.cb_ch_bg_edit, self.cb_ch_bg_btn, wrap_ccb = mk_color_row(
            "Case cochée: fond:"
        )
        self.cb_ch_border_edit, self.cb_ch_border_btn, wrap_ccbd = mk_color_row(
            "Case cochée: bordure:"
        )
        self.cb_ch_hover_edit, self.cb_ch_hover_btn, wrap_cch = mk_color_row(
            "Case cochée: survol:"
        )
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
        # Font family
        self.font_family_edit = QLineEdit()
        controls_layout.addRow("Opacité panneau:", self.opacity_spin)
        controls_layout.addRow("Coins arrondis:", self.radius_spin)
        controls_layout.addRow("Taille police:", self.font_spin)
        controls_layout.addRow("Police (famille):", self.font_family_edit)
        # Action buttons
        actions = QHBoxLayout()
        self.btn_import_profile = QPushButton("Importer profil…")
        self.btn_export_profile = QPushButton("Exporter profil…")
        self.btn_reset_profile = QPushButton("Réinitialiser défaut (Dark)")
        actions.addStretch(1)
        actions.addWidget(self.btn_import_profile)
        actions.addWidget(self.btn_export_profile)
        actions.addWidget(self.btn_reset_profile)
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

        style_layout.addWidget(controls, 1)
        # Supprime l’aperçu: pas ajouté à la mise en page
        style_scroll = QScrollArea()
        style_scroll.setWidgetResizable(True)
        style_scroll.setWidget(tab_style_inner)
        tabs.addTab(style_scroll, "Styles")

        # --- Tab: Timeline ---
        tab_tl = QWidget()
        tl_form = QFormLayout(tab_tl)
        tl_form.setLabelAlignment(Qt.AlignRight)
        self.tl_bg, _, tl_bg_wrap = mk_color_row_into(tl_form, "Fond timeline:")
        self.tl_ruler_bg, _, _ = mk_color_row_into(tl_form, "Fond règle:")
        self.tl_track_bg, _, _ = mk_color_row_into(tl_form, "Fond piste:")
        self.tl_tick, _, _ = mk_color_row_into(tl_form, "Graduations:")
        self.tl_tick_major, _, _ = mk_color_row_into(tl_form, "Graduations (majeures):")
        self.tl_playhead, _, _ = mk_color_row_into(tl_form, "Playhead:")
        self.tl_kf, _, _ = mk_color_row_into(tl_form, "Keyframe:")
        self.tl_kf_hover, _, _ = mk_color_row_into(tl_form, "Keyframe (hover):")
        self.tl_inout_alpha = QSpinBox()
        self.tl_inout_alpha.setRange(0, 255)
        self.tl_inout_alpha.setValue(30)
        # Rows already added via mk_color_row_into
        tl_form.addRow("Opacité In/Out (0-255):", self.tl_inout_alpha)
        tabs.addTab(tab_tl, "Timeline")

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        main_layout.addWidget(btns)

        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        self.icon_dir_browse.clicked.connect(self._on_browse_icons)
        # Color pickers
        color_rows = [
            (self.bg_edit, self.bg_btn),
            (self.text_edit, self.text_btn),
            (self.accent_edit, self.accent_btn),
            (self.hover_edit, self.hover_btn),
            (self.panel_edit, self.panel_btn),
            (self.border_edit, self.border_btn),
            (self.header_bg_edit, self.header_bg_btn),
            (self.header_text_edit, self.header_text_btn),
            (self.header_border_edit, self.header_border_btn),
            (self.group_edit, self.group_btn),
            (self.tooltip_bg_edit, self.tooltip_bg_btn),
            (self.tooltip_text_edit, self.tooltip_text_btn),
            # Inputs/lists/checkboxes
            (self.input_bg_edit, self.input_bg_btn),
            (self.input_border_edit, self.input_border_btn),
            (self.input_text_edit, self.input_text_btn),
            (self.input_focus_bg_edit, self.input_focus_bg_btn),
            (self.input_focus_border_edit, self.input_focus_border_btn),
            (self.list_hover_edit, self.list_hover_btn),
            (self.list_sel_bg_edit, self.list_sel_bg_btn),
            (self.list_sel_text_edit, self.list_sel_text_btn),
            (self.cb_un_bg_edit, self.cb_un_bg_btn),
            (self.cb_un_border_edit, self.cb_un_border_btn),
            (self.cb_ch_bg_edit, self.cb_ch_bg_btn),
            (self.cb_ch_border_edit, self.cb_ch_border_btn),
            (self.cb_ch_hover_edit, self.cb_ch_hover_btn),
        ]
        for le, btn in color_rows:
            btn.clicked.connect(lambda _, e=le: self._pick_color_into(e))
            # Met à jour uniquement les pastilles (pas de prévisualisation live)
            le.textChanged.connect(lambda _=None, e=le: self._update_swatch(e))
            # Presets & actions
            # Track style controls to toggle visibility (keep preset combo visible)
            self._style_wraps = [
                wrap_bg,
                wrap_text,
                wrap_accent,
                wrap_hover,
                wrap_panel,
                wrap_border,
                wrap_hbg,
                wrap_htxt,
                wrap_hb,
                wrap_scene,
                wrap_tipbg,
                wrap_tiptext,
                wrap_group,
                wrap_inbg,
                wrap_inb,
                wrap_int,
                wrap_infbg,
                wrap_infb,
                wrap_lh,
                wrap_lsb,
                wrap_lst,
                wrap_cub,
                wrap_cubd,
                wrap_ccb,
                wrap_ccbd,
                wrap_cch,
            ]
        self._style_fields = [
            self.opacity_spin,
            self.radius_spin,
            self.font_spin,
            self.font_family_edit,
        ]

        def _on_preset_changed(name: str) -> None:
            self._load_preset_values(name)
            is_custom = name.strip().lower() == "custom"
            # Toggle style selectors only
            for w in self._style_wraps:
                w.setVisible(is_custom)
            for w in self._style_fields:
                w.setVisible(is_custom)
            # Pas d’aperçu

        self.preset_combo.currentTextChanged.connect(_on_preset_changed)
        # Pas de boutons Prévisualiser / Enregistrer custom / Appliquer
        # Désactive l’aperçu live

        # Réduit la gêne des SpinBox: largeur et molette
        def _no_wheel(sp):
            sp.setFocusPolicy(Qt.StrongFocus)
            sp.wheelEvent = lambda e: e.ignore()
            sp.setMaximumWidth(100)

        for sp in (
            self.opacity_spin,
            self.radius_spin,
            self.font_spin,
            self.icon_size_spin,
            self.tl_inout_alpha,
            self.prev_count,
            self.next_count,
        ):
            _no_wheel(sp)

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

    def set_shortcut_actions(self, actions: dict[str, QAction]) -> None:
        """
        Populate the shortcuts tab with editors for each action.

        Args:
            actions: A dictionary of action names to QAction objects.
        """
        # Clear previous rows
        while self._key_form.rowCount():
            self._key_form.removeRow(0)
        self._shortcut_edits.clear()
        for key, action in actions.items():
            edit = QKeySequenceEdit(action.shortcut())
            label = action.text().split(" (")[0]
            self._key_form.addRow(f"{label}:", edit)
            self._shortcut_edits[key] = edit

    def get_shortcuts(self) -> dict[str, str]:
        """
        Return the edited shortcuts as a mapping.

        Returns:
            A dictionary of action names to shortcut strings.
        """
        result: dict[str, str] = {}
        for key, edit in self._shortcut_edits.items():
            result[key] = edit.keySequence().toString(QKeySequence.NativeText)
        return result

    def showEvent(self, event) -> None:  # type: ignore[override]
        """
        Handles the show event of the dialog.

        Args:
            event: The show event.
        """
        super().showEvent(event)
        # No special handling needed

    def _on_browse_icons(self) -> None:
        """Opens a dialog to browse for an icon directory."""
        path = QFileDialog.getExistingDirectory(self, "Choisir un dossier d'icônes")
        if path:
            self.icon_dir_edit.setText(path)

    def _pick_color_into(self, edit: QLineEdit) -> None:
        """
        Opens a color dialog and sets the selected color to the given line edit.

        Args:
            edit: The line edit to set the color to.
        """
        col = QColorDialog.getColor()
        if col.isValid():
            edit.setText(col.name())
            self._update_swatch(edit)

    def _params_from_ui(self) -> dict:
        """Returns a dictionary of style parameters from the UI controls."""
        params: dict[str, Any] = {}
        for p in THEME_PARAMS:
            widget = getattr(self, p.widget, None)
            if widget is None:
                continue
            val = widget.value() if hasattr(widget, "value") else widget.text()
            if p.percent:
                val = val / 100.0
            if isinstance(val, str) and not val and p.fallback:
                val = params.get(p.fallback, DEFAULT_CUSTOM_PARAMS[p.key])
            if isinstance(val, str) and not val:
                val = DEFAULT_CUSTOM_PARAMS[p.key]
            params[p.key] = val
        return params

    def _load_preset_values(self, name: str) -> None:
        """
        Loads the style parameters for the given preset name.

        Args:
            name: The name of the preset to load.
        """
        if name.lower() == "light":
            self.bg_edit.setText("#E2E8F0")
            self.text_edit.setText("#1A202C")
            self.accent_edit.setText("#E53E3E")
            self.hover_edit.setText("#E3E6FD")
            self.panel_edit.setText("#F7F8FC")
            self.border_edit.setText("#D0D5DD")
            self.group_edit.setText("#2D3748")
            self.opacity_spin.setValue(90)
            self.radius_spin.setValue(12)
            self.font_spin.setValue(10)
        elif name.lower() == "dark":
            self.bg_edit.setText("#1F2937")
            self.text_edit.setText("#E2E8F0")
            self.accent_edit.setText("#EF4444")
            self.hover_edit.setText("#374151")
            self.panel_edit.setText("#1F2937")
            self.border_edit.setText("#374151")
            self.group_edit.setText("#E5E7EB")
            self.opacity_spin.setValue(92)
            self.radius_spin.setValue(12)
            self.font_spin.setValue(10)
        elif name.lower() == "high contrast":
            self.bg_edit.setText("#000000")
            self.text_edit.setText("#FFFFFF")
            self.accent_edit.setText("#FFD600")
            self.hover_edit.setText("#333333")
            self.panel_edit.setText("#000000")
            self.border_edit.setText("#FFFFFF")
            self.group_edit.setText("#FFFFFF")
            self.opacity_spin.setValue(100)
            self.radius_spin.setValue(0)
            self.font_spin.setValue(11)
        # Update swatches when preset changes and refresh preview
        self._update_all_swatches()
        self._preview_theme()
        # Custom keeps current entries

    def _preview_theme(self) -> None:
        """Applies the current style parameters to the preview widget."""
        css = build_stylesheet(self._params_from_ui())
        # Apply to dedicated preview container so we don't affect the whole dialog
        try:
            self.preview_root.setStyleSheet(css)
            # Move focus to input to demonstrate accent focus border
            self.prev_input.setFocus()
        except (RuntimeError, AttributeError):
            logging.exception("Theme preview failed")

    def _save_params_as_custom(self) -> None:
        """Saves the current style parameters as a custom theme."""
        css = build_stylesheet(self._params_from_ui())
        from ui.settings_keys import ORG, APP, UI_CUSTOM_STYLESHEET, UI_THEME
        s = QSettings(ORG, APP)
        s.setValue(UI_CUSTOM_STYLESHEET, css)
        s.setValue(UI_THEME, "custom")

    def _update_swatch(self, edit: QLineEdit) -> None:
        """
        Updates the color swatch for the given line edit.

        Args:
            edit: The line edit to update the swatch for.
        """
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
                c1 = QColor("#FFFFFF")
                c2 = QColor("#C7CBD1")
                for y in range(0, h, s):
                    for x in range(0, w, s):
                        p.fillRect(
                            x, y, s, s, c1 if ((x // s + y // s) % 2 == 0) else c2
                        )
                # Overlay panel color with opacity from spin
                color = QColor(edit.text().strip() or "#FFFFFF")
                if not color.isValid():
                    color = QColor("#FFFFFF")
                alpha = max(0.0, min(1.0, self.opacity_spin.value() / 100.0))
                color.setAlphaF(alpha)
                p.fillRect(QRectF(0, 0, w, h), color)
                p.end()
                # Keep border via stylesheet; set pixmap for fill
                sw.setStyleSheet(
                    "QLabel{border:1px solid #A0AEC0; border-radius:3px; background:transparent;}"
                )
                sw.setPixmap(pix)
            except (ValueError, TypeError, RuntimeError):
                logging.exception("Panel swatch render failed")
                # Fallback to flat color
                col = edit.text().strip() or "#FFFFFF"
                if not col.startswith("#") and not col.startswith("rgb"):
                    col = "#FFFFFF"
                sw.setStyleSheet(
                    f"QLabel{{border:1px solid #A0AEC0; border-radius:3px; background:{col};}}"
                )
        else:
            col = edit.text().strip() or "#FFFFFF"
            # Basic validation: ensure it looks like a color string
            if not col.startswith("#") and not col.startswith("rgb"):
                col = "#FFFFFF"
            sw.setPixmap(QPixmap())
            sw.setStyleSheet(
                f"QLabel{{border:1px solid #A0AEC0; border-radius:3px; background:{col};}}"
            )

    def _update_all_swatches(self) -> None:
        """Updates all color swatches."""
        for le in self._swatches.keys():
            self._update_swatch(le)

        # Re-render panel swatch when opacity changes
        try:
            self.opacity_spin.valueChanged.connect(
                lambda _=None: self._update_swatch(self.panel_edit)
            )
        except (RuntimeError, AttributeError):
            logging.exception("Failed to connect opacity spin change")

    def _apply_list_icon_size(self) -> None:
        """Applies the icon size to the icon lists."""
        size = self.icon_size_spin.value()
        for lw in (
            self.list_main_order,
            self.list_quick_order,
            self.list_custom_order,
        ):
            lw.setIconSize(QSize(size, size))
            try:
                lw.viewport().update()
            except (RuntimeError, AttributeError):
                logging.exception("Viewport update failed for icon list")

    def _init_icon_lists(self) -> None:
        """Initializes the icon lists for the overlay builder."""
        from ui.icons import (
            get_icon,
            icon_background,
            icon_fit,
            icon_inspector,
            icon_library,
            icon_minus,
            icon_onion,
            icon_open,
            icon_plus,
            icon_reset_scene,
            icon_reset_ui,
            icon_rotate,
            icon_save,
            icon_scene_size,
            icon_timeline,
        )

        # Configure lists to show icons horizontally with wrapping
        for lw in (
            self.list_main_order,
            self.list_quick_order,
            self.list_custom_order,
        ):
            lw.setViewMode(QListView.IconMode)
            lw.setFlow(QListView.LeftToRight)
            lw.setWrapping(True)
            lw.setMovement(QListView.Snap)
            lw.setDragDropMode(QAbstractItemView.InternalMove)
            lw.setResizeMode(QListView.Adjust)
            lw.setSpacing(8)
            lw.setIconSize(
                QSize(self.icon_size_spin.value(), self.icon_size_spin.value())
            )

        self._main_specs = [
            ("save", "Sauver", icon_save()),
            ("load", "Charger", icon_open()),
            ("scene_size", "Scène", icon_scene_size()),
            ("background", "Fond", icon_background()),
            ("add_light", "Lumière", get_icon("plus")),
            ("settings", "Paramètres", get_icon("layers")),
            ("reset_scene", "Reset scène", icon_reset_scene()),
            ("reset_ui", "Reset UI", icon_reset_ui()),
            ("toggle_library", "Lib", icon_library()),
            ("toggle_inspector", "Insp", icon_inspector()),
            ("toggle_timeline", "Time", icon_timeline()),
            ("toggle_custom", "Custom", get_icon("layers")),
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

    def populate_icon_list(
        self,
        lw: QListWidget,
        order_keys: list[str],
        visibility_map: dict[str, bool],
        specs: list[tuple[str, str, QIcon]],
    ) -> None:
        """
        Populates an icon list with items.

        Args:
            lw: The list widget to populate.
            order_keys: The order of the icons.
            visibility_map: A map of icon visibility.
            specs: The specifications for the icons.
        """
        lw.clear()
        spec_map = {
            k: (label, icon)
            for (k, label, icon) in [(k, lbl, ic) for (k, lbl, ic) in specs]
        }
        for key in order_keys:
            if key not in spec_map:
                continue
            label, icon = spec_map[key]
            # Icon with label under it
            item = QListWidgetItem(icon, label)
            item.setData(Qt.UserRole, key)
            item.setFlags(
                item.flags()
                | Qt.ItemIsUserCheckable
                | Qt.ItemIsEnabled
                | Qt.ItemIsDragEnabled
                | Qt.ItemIsSelectable
            )
            item.setCheckState(
                Qt.Checked if visibility_map.get(key, True) else Qt.Unchecked
            )
            lw.addItem(item)
        # No special height handling

    def extract_icon_list(self, lw: QListWidget) -> tuple[list[str], dict[str, bool]]:
        """
        Extracts the order and visibility of icons from a list widget.

        Args:
            lw: The list widget to extract from.

        Returns:
            A tuple containing the order of the icons and a map of their visibility.
        """
        order: list[str] = []
        vis: dict[str, bool] = {}
        for i in range(lw.count()):
            it = lw.item(i)
            key = it.data(Qt.UserRole)
            order.append(key)
            vis[key] = it.checkState() == Qt.Checked
        return order, vis

    def _init_icons_tab(self) -> None:
        """Initializes the icons tab with only actually used icon keys."""
        used: set[str] = set()
        try:
            from ui.menu_defaults import (
                MAIN_DEFAULT_ORDER,
                QUICK_DEFAULT_ORDER,
                CUSTOM_DEFAULT_ORDER,
            )

            used |= set(MAIN_DEFAULT_ORDER)
            used |= set(QUICK_DEFAULT_ORDER)
            used |= set(CUSTOM_DEFAULT_ORDER)
        except Exception:
            pass
        # Include keys from overlay/spec lists (built in _init_icon_lists)
        used |= {k for (k, _label, _ic) in getattr(self, "_main_specs", [])}
        used |= {k for (k, _label, _ic) in getattr(self, "_quick_specs", [])}
        # Include runtime actions registered on the main window (auto-updates when new actions added)
        mw = self.parent()
        if hasattr(mw, "shortcuts") and isinstance(getattr(mw, "shortcuts"), dict):
            try:
                used |= set(mw.shortcuts.keys())
            except Exception:
                pass
        # Always-used infrastructure icons (overlay chevrons and layers fallback)
        used |= {
            "open_menu",
            "close_menu",
            "close_menu_inv",
            "chevron_left",
            "chevron_right",
            "layers",
        }
        self._icon_keys = sorted(used)
        self._populate_icons_list()
        if self.list_icons.count():
            self.list_icons.setCurrentRow(0)

    def _populate_icons_list(self) -> None:
        """Populates the list of customizable icons."""
        from ui.icons import get_icon

        self.list_icons.clear()
        # Uniform grid for cleaner alignment
        from ui.settings_keys import ORG, APP, UI_ICON_SIZE, UI_ICON_OVERRIDE
        raw = QSettings(ORG, APP).value(UI_ICON_SIZE, 32)
        try:
            from ui.ui_profile import _int as _to_int
        except Exception:
            _to_int = lambda v, d=32: int(v) if v is not None else d  # type: ignore
        icon_h = max(16, min(128, int(_to_int(raw, 32))))
        cell_w = max(64, icon_h + 48)
        cell_h = max(64, icon_h + 32)
        self.list_icons.setIconSize(QSize(icon_h, icon_h))
        self.list_icons.setGridSize(QSize(cell_w, cell_h))
        s = QSettings(ORG, APP)
        for key in self._icon_keys:
            icon = get_icon(key)
            it = QListWidgetItem(icon, key)
            it.setData(Qt.UserRole, key)
            # Mark custom ones with asterisk and tooltip
            path = s.value(UI_ICON_OVERRIDE(key))
            if path:
                it.setText(f"{key} *")
                it.setToolTip(str(path))
            self.list_icons.addItem(it)

    def _on_icon_item_changed(
        self, current: Optional[QListWidgetItem], previous: Optional[QListWidgetItem]
    ) -> None:
        """
        Handles the current item changed signal of the icons list.

        Args:
            current: The current item.
            previous: The previous item.
        """
        if not current:
            self.lbl_key.setText("—")
            self.lbl_path.setText("")
            return
        key = current.data(Qt.UserRole)
        self.lbl_key.setText(str(key))
        from ui.settings_keys import ORG, APP, UI_ICON_OVERRIDE
        s = QSettings(ORG, APP)
        self.lbl_path.setText(str(s.value(UI_ICON_OVERRIDE(key)) or ""))

    def _choose_icon_file(self) -> None:
        """Opens a file dialog to choose an icon file."""
        from PySide6.QtWidgets import QFileDialog

        item = self.list_icons.currentItem()
        if not item:
            return
        key = item.data(Qt.UserRole)
        path, _ = QFileDialog.getOpenFileName(
            self, "Choisir une icône", "", "Images (*.svg *.png *.jpg *.bmp *.ico)"
        )
        if not path:
            return
        from ui.settings_keys import ORG, APP, UI_ICON_OVERRIDE
        s = QSettings(ORG, APP)
        s.setValue(UI_ICON_OVERRIDE(key), path)
        self.lbl_path.setText(path)
        self._refresh_icons_runtime()
        self._populate_icons_list()

    def _reset_icon_file(self) -> None:
        """Resets the icon file for the currently selected icon."""
        item = self.list_icons.currentItem()
        if not item:
            return
        key = item.data(Qt.UserRole)
        from ui.settings_keys import ORG, APP, UI_ICON_OVERRIDE
        s = QSettings(ORG, APP)
        s.remove(UI_ICON_OVERRIDE(key))
        self.lbl_path.setText("")
        self._refresh_icons_runtime()
        self._populate_icons_list()

    def _reset_all_icons(self) -> None:
        """Resets all custom icon files."""
        from ui.settings_keys import ORG, APP, UI_ICON_OVERRIDE_GROUP
        s = QSettings(ORG, APP)
        s.beginGroup(UI_ICON_OVERRIDE_GROUP)
        s.remove("")
        s.endGroup()
        self._refresh_icons_runtime()
        self._populate_icons_list()

    def _refresh_icons_runtime(self) -> None:
        """Refreshes the icons in the main window at runtime."""
        # Clear cache and refresh action/overlay icons on the main window
        try:
            import ui.icons as app_icons

            app_icons.clear_cache()
            from ui.icons import (
                icon_background,
                icon_inspector,
                icon_library,
                icon_open,
                icon_reset_scene,
                icon_reset_ui,
                icon_save,
                icon_scene_size,
                icon_timeline,
            )

            mw = self.parent()
            # Actions
            if hasattr(mw, "save_action"):
                mw.save_action.setIcon(icon_save())
            if hasattr(mw, "load_action"):
                mw.load_action.setIcon(icon_open())
            if hasattr(mw, "scene_size_action"):
                mw.scene_size_action.setIcon(icon_scene_size())
            if hasattr(mw, "background_action"):
                mw.background_action.setIcon(icon_background())
            if hasattr(mw, "reset_scene_action"):
                mw.reset_scene_action.setIcon(icon_reset_scene())
            if hasattr(mw, "reset_ui_action"):
                mw.reset_ui_action.setIcon(icon_reset_ui())
            if hasattr(mw, "toggle_library_action"):
                mw.toggle_library_action.setIcon(icon_library())
            if hasattr(mw, "toggle_inspector_action"):
                mw.toggle_inspector_action.setIcon(icon_inspector())
            if hasattr(mw, "timeline_dock"):
                mw.timeline_dock.toggleViewAction().setIcon(icon_timeline())
            # Overlay buttons
            if hasattr(mw, "view"):
                mw.view.refresh_overlay_icons(mw)
                mw.view.apply_menu_settings_main()
                mw.view.apply_menu_settings_quick()
        except (RuntimeError, ImportError, AttributeError):
            logging.exception("Failed to refresh icons at runtime")

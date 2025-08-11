import logging
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QGraphicsPixmapItem, QGraphicsItem
from PySide6.QtSvgWidgets import QGraphicsSvgItem


class _ObjectItemMixin:
    def set_context(self, main_window, obj_name):
        self._mw = main_window
        self._obj_name = obj_name
        # Activer la sélection (stroke par défaut)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)

    def itemChange(self, change, value):
        mw = getattr(self, "_mw", None)
        name = getattr(self, "_obj_name", None)
        if not mw or not name or getattr(mw, "_suspend_item_updates", False):
            return super().itemChange(change, value)
        if change in (
            QGraphicsItem.ItemPositionHasChanged,
            QGraphicsItem.ItemRotationHasChanged,
            QGraphicsItem.ItemScaleHasChanged,
            QGraphicsItem.ItemSelectedHasChanged,
        ):
            try:
                obj = mw.scene_model.objects.get(name)
                if obj:
                    obj.x, obj.y = self.x(), self.y()
                    obj.rotation = self.rotation()
                    obj.scale = self.scale()
                    obj.z = int(self.zValue())
                    kf = mw.scene_model.keyframes.get(mw.scene_model.current_frame)
                    if kf is not None:
                        kf.objects[name] = obj.to_dict()
                if change == QGraphicsItem.ItemSelectedHasChanged and bool(value):
                    mw.select_object_in_inspector(name)
            except Exception as e:
                logging.error(f"Error in itemChange for {name}: {e}")
        return super().itemChange(change, value)


class ObjectPixmapItem(_ObjectItemMixin, QGraphicsPixmapItem):
    def __init__(self, file_path: str):
        super().__init__(QPixmap(file_path))


class ObjectSvgItem(_ObjectItemMixin, QGraphicsSvgItem):
    def __init__(self, file_path: str):
        super().__init__(file_path)

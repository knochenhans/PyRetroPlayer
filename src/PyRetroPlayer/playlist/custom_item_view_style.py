from typing import Optional

from PySide6.QtGui import (
    QPainter,
)
from PySide6.QtWidgets import (
    QProxyStyle,
    QStyle,
    QStyleOption,
    QWidget,
)


class CustomItemViewStyle(QProxyStyle):
    def __init__(self, style: Optional[QStyle] = None):
        super().__init__(style)

    def drawPrimitive(
        self,
        element: QStyle.PrimitiveElement,
        option: QStyleOption,
        painter: QPainter,
        widget: Optional[QWidget] = None,
    ):
        if (
            element == QStyle.PrimitiveElement.PE_IndicatorItemViewItemDrop
            and not option.rect.isNull()
        ):
            opt = QStyleOption(option)
            opt.rect.setLeft(0)
            if widget:
                opt.rect.setRight(widget.width())

            pen = painter.pen()
            pen.setWidth(3)
            painter.setPen(pen)

            super().drawPrimitive(element, opt, painter, widget)
            return
        super().drawPrimitive(element, option, painter, widget)

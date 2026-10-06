"""Controles de fecha que mantienen el calendario emergente sincronizado con el tema."""

from PyQt6.QtCore import QObject, QDate, Qt
from PyQt6.QtGui import QColor, QFont, QTextCharFormat
from PyQt6.QtWidgets import QDateEdit

from ui.theme.theme_manager import get_theme_manager


class _CalendarThemeBinder(QObject):
    """Actualiza los formatos de un calendario mientras vive su selector."""

    def __init__(self, date_edit: QDateEdit):
        super().__init__(date_edit)
        self._calendar = date_edit.calendarWidget()
        self._calendar.setMinimumSize(294, 230)
        self._calendar.setGridVisible(False)
        self._theme_manager = get_theme_manager()
        self._theme_manager.theme_changed.connect(self._apply_calendar_theme)
        self._calendar.currentPageChanged.connect(self._apply_month_edge_formats)
        self._apply_calendar_theme(self._theme_manager.current())

    def _apply_calendar_theme(self, theme_name: str) -> None:
        tokens = self._theme_manager.tokens(theme_name)
        calendar = self._calendar
        self._text_secondary = tokens["text_secondary"]

        calendar.setDateTextFormat(QDate(), QTextCharFormat())

        weekday_format = QTextCharFormat()
        weekday_format.setForeground(QColor(tokens["text_primary"]))
        for day in (
            Qt.DayOfWeek.Monday,
            Qt.DayOfWeek.Tuesday,
            Qt.DayOfWeek.Wednesday,
            Qt.DayOfWeek.Thursday,
            Qt.DayOfWeek.Friday,
        ):
            calendar.setWeekdayTextFormat(day, weekday_format)

        weekend_format = QTextCharFormat()
        weekend_format.setForeground(QColor(tokens["text_secondary"]))
        calendar.setWeekdayTextFormat(Qt.DayOfWeek.Saturday, weekend_format)
        calendar.setWeekdayTextFormat(Qt.DayOfWeek.Sunday, weekend_format)

        header_format = QTextCharFormat()
        header_format.setForeground(QColor(tokens["text_secondary"]))
        calendar.setHeaderTextFormat(header_format)

        self._apply_month_edge_formats()

    def _apply_month_edge_formats(
        self, year: int | None = None, month: int | None = None
    ) -> None:
        calendar = self._calendar
        year = year or calendar.yearShown()
        month = month or calendar.monthShown()
        first_day = QDate(year, month, 1)
        offset = (
            first_day.dayOfWeek() - calendar.firstDayOfWeek().value + 7
        ) % 7
        first_visible_day = first_day.addDays(-offset)
        for day_offset in range(42):
            calendar.setDateTextFormat(
                first_visible_day.addDays(day_offset), QTextCharFormat()
            )
        muted_format = QTextCharFormat()
        muted_format.setForeground(QColor(self._text_secondary))

        for day_offset in range(42):
            day = first_visible_day.addDays(day_offset)
            if day.month() != month:
                calendar.setDateTextFormat(day, muted_format)

        today = QDate.currentDate()
        if today.year() == year and today.month() == month:
            tokens = self._theme_manager.tokens()
            today_format = QTextCharFormat()
            today_format.setForeground(QColor(tokens["accent_text"]))
            today_format.setBackground(QColor(tokens["accent"]))
            today_format.setFontWeight(QFont.Weight.Bold)
            calendar.setDateTextFormat(today, today_format)


def configure_calendar_theme(date_edit: QDateEdit) -> None:
    """Sincroniza los formatos de calendario con el tema para un QDateEdit."""
    date_edit.setProperty("themedCalendarPopup", True)
    if date_edit.findChild(_CalendarThemeBinder) is None:
        _CalendarThemeBinder(date_edit)
    date_edit.style().unpolish(date_edit)
    date_edit.style().polish(date_edit)
    date_edit.update()


__all__ = ["configure_calendar_theme"]

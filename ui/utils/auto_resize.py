"""Auto-resize utilities for consistent UI sizing across widgets."""

from PyQt6.QtWidgets import QTableWidget, QHeaderView, QPushButton, QSizePolicy
from typing import Dict, List, Optional


class TableAutoResize:
    """Helper class for intelligent table auto-resizing."""
    
    @staticmethod
    def configure(table: QTableWidget,
                 fixed_columns: Optional[Dict[int, int]] = None,
                 content_fit_columns: Optional[List[int]] = None,
                 stretch_columns: Optional[List[int]] = None,
                 interactive_columns: Optional[List[int]] = None,
                 use_legacy_mode: bool = False):
        """
        Configure intelligent auto-resizing for table columns.
        
        Args:
            table: The QTableWidget to configure
            fixed_columns: Dict of {column_index: width_in_pixels} for fixed-width columns
            content_fit_columns: List of column indices that should auto-fit to content
            stretch_columns: List of column indices that should stretch to fill space
            interactive_columns: List of column indices that user can manually resize
            use_legacy_mode: If True, use old behavior (all interactive + resize to contents)
        """
        header = table.horizontalHeader()
        
        # Legacy mode for compatibility
        if use_legacy_mode:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
            header.setStretchLastSection(False)
            return
        
        # Disable stretch last section by default for more control
        header.setStretchLastSection(False)
        
        # Fixed width columns (e.g., ID, short codes)
        if fixed_columns:
            for col_idx, width in fixed_columns.items():
                header.setSectionResizeMode(col_idx, QHeaderView.ResizeMode.Fixed)
                table.setColumnWidth(col_idx, width)
        
        # Auto-fit to content columns (e.g., severity, status)
        if content_fit_columns:
            for col_idx in content_fit_columns:
                header.setSectionResizeMode(col_idx, QHeaderView.ResizeMode.ResizeToContents)
        
        # Stretch columns (e.g., descriptions, long text)
        if stretch_columns:
            for col_idx in stretch_columns:
                header.setSectionResizeMode(col_idx, QHeaderView.ResizeMode.Stretch)
        
        # Interactive columns (user can resize)
        if interactive_columns:
            for col_idx in interactive_columns:
                header.setSectionResizeMode(col_idx, QHeaderView.ResizeMode.Interactive)
    
    @staticmethod
    def use_legacy_interactive(table: QTableWidget):
        """
        Use legacy behavior: all columns interactive, call resizeColumnsToContents() after populating.
        This is the old behavior before auto-resize was implemented.
        """
        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(False)
    
    @staticmethod
    def use_stretch_last(table: QTableWidget):
        """
        Simple mode: all interactive except last column stretches.
        Good middle ground between legacy and new behavior.
        """
        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(True)


class ButtonSizePolicy:
    """Helper class for consistent button sizing."""
    
    @staticmethod
    def apply_responsive(button: QPushButton, 
                        horizontal: str = "expanding",
                        vertical: str = "fixed",
                        min_width: Optional[int] = None,
                        max_width: Optional[int] = None,
                        min_height: Optional[int] = None,
                        max_height: Optional[int] = None):
        """
        Apply responsive sizing policy to a button.
        
        Args:
            button: The QPushButton to configure
            horizontal: Horizontal policy - "expanding", "minimum", "fixed", "preferred"
            vertical: Vertical policy - "expanding", "minimum", "fixed", "preferred"
            min_width: Optional minimum width in pixels
            max_width: Optional maximum width in pixels
            min_height: Optional minimum height in pixels
            max_height: Optional maximum height in pixels
        """
        # Map string policies to Qt enums
        policy_map = {
            "expanding": QSizePolicy.Policy.Expanding,
            "minimum": QSizePolicy.Policy.Minimum,
            "fixed": QSizePolicy.Policy.Fixed,
            "preferred": QSizePolicy.Policy.Preferred,
            "maximum": QSizePolicy.Policy.Maximum,
        }
        
        h_policy = policy_map.get(horizontal.lower(), QSizePolicy.Policy.Expanding)
        v_policy = policy_map.get(vertical.lower(), QSizePolicy.Policy.Fixed)
        
        button.setSizePolicy(h_policy, v_policy)
        
        # Set size constraints if provided
        if min_width is not None:
            button.setMinimumWidth(min_width)
        if max_width is not None:
            button.setMaximumWidth(max_width)
        if min_height is not None:
            button.setMinimumHeight(min_height)
        if max_height is not None:
            button.setMaximumHeight(max_height)
    
    @staticmethod
    def make_compact(button: QPushButton, min_width: int = 60, max_height: int = 24):
        """
        Make a button compact with minimum size constraints.
        Common for toolbar buttons and action buttons.
        """
        ButtonSizePolicy.apply_responsive(
            button,
            horizontal="minimum",
            vertical="fixed",
            min_width=min_width,
            max_height=max_height
        )
    
    @staticmethod
    def make_flexible(button: QPushButton, min_width: int = 80):
        """
        Make a button flexible to expand with layout.
        Common for dialog buttons and primary actions.
        """
        ButtonSizePolicy.apply_responsive(
            button,
            horizontal="expanding",
            vertical="fixed",
            min_width=min_width
        )
    
    @staticmethod
    def make_fixed(button: QPushButton, width: int, height: int = 24):
        """
        Make a button fixed size.
        Common for icon buttons or specific-sized controls.
        """
        button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        button.setFixedSize(width, height)
    
    @staticmethod
    def use_legacy(button: QPushButton, min_width: Optional[int] = None, max_height: Optional[int] = None):
        """
        Use legacy button sizing (just set min/max without size policy).
        This mimics the old behavior before ButtonSizePolicy was implemented.
        """
        if min_width is not None:
            button.setMinimumWidth(min_width)
        if max_height is not None:
            button.setMaximumHeight(max_height)


# Convenience functions for common patterns
def setup_finding_table(table: QTableWidget):
    """Setup auto-resize for findings table."""
    TableAutoResize.configure(
        table,
        content_fit_columns=[0, 2, 3],  # ID, Severity, Data Source
        stretch_columns=[6],  # MITRE Techniques (stretches to fill)
        interactive_columns=[1, 4, 5]  # Timestamp, Anomaly Score, Cluster
    )


def setup_search_results_table(table: QTableWidget):
    """Setup auto-resize for search results table."""
    TableAutoResize.configure(
        table,
        content_fit_columns=[1, 2, 3],  # Type, Severity, Source
        stretch_columns=[4],  # Description (stretches to fill)
        interactive_columns=[0]  # Timestamp
    )


def setup_entity_table(table: QTableWidget):
    """Setup auto-resize for entity table."""
    TableAutoResize.configure(
        table,
        content_fit_columns=[0, 1],  # Type, Entity
        stretch_columns=[3],  # Related Findings (stretches to fill)
        interactive_columns=[2]  # Risk Score
    )

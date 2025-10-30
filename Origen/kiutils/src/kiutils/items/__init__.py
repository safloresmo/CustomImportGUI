"""Items package for kiutils

This package contains all item classes for different KiCad file types including
boards, schematics, footprints, symbols, and worksheets. Each module contains
dataclass-based representations of KiCad file elements.

The items are organized by file type:
- common: Items used across multiple file types
- brditems: Board-specific items (.kicad_pcb files)
- fpitems: Footprint-specific items (.kicad_mod files)
- schitems: Schematic-specific items (.kicad_sch files)
- syitems: Symbol-specific items (.kicad_sym files)
- gritems: Graphics items used in various contexts
- zones: Zone and fill-related items
- dimensions: Dimension and measurement items
"""

# Common items - used across multiple file types
from .common import (
    Position, Coordinate, ColorRGBA, Stroke, Font, Justify, 
    Effects, Net, Group, PageSettings, TitleBlock, Property,
    RenderCache, RenderCachePolygon, Fill, Image, ProjectInstance
)

# Board-specific items (.kicad_pcb files)
from .brditems import (
    GeneralSettings, LayerToken, StackupLayer, StackupSubLayer, 
    Stackup, PlotSettings, SetupData, Segment, Via, Arc, Target
)

# Footprint-specific items (.kicad_mod files)
from .fpitems import (
    FpText, FpLine, FpRect, FpTextBox, FpCircle, 
    FpArc, FpPoly, FpCurve
)

# Schematic-specific items (.kicad_sch files)
from .schitems import (
    Junction, NoConnect, BusEntry, BusAlias, Connection, PolyLine,
    Text, TextBox, LocalLabel, GlobalLabel, HierarchicalLabel,
    SchematicSymbol, HierarchicalSheet, HierarchicalPin,
    HierarchicalSheetInstance, SymbolInstance,
    Rectangle, Arc, Circle, NetclassFlag
)

# Symbol-specific items (.kicad_sym files)
from .syitems import (
    SyArc, SyCircle, SyCurve, SyPolyLine, 
    SyRect, SyText, SyTextBox
)

# Graphics items (used in multiple contexts)
from .gritems import (
    GrText, GrTextBox, GrLine, GrRect, 
    GrCircle, GrArc, GrPoly, GrCurve
)

# Zone and fill items
from .zones import (
    Zone, KeepoutSettings, FillSettings, 
    ZonePolygon, FilledPolygon, FillSegments, Hatch
)

# Dimension and measurement items
from .dimensions import (
    Dimension, DimensionFormat, DimensionStyle
)

# Export list for controlled imports
__all__ = [
    # Common items
    'Position', 'Coordinate', 'ColorRGBA', 'Stroke', 'Font', 'Justify',
    'Effects', 'Net', 'Group', 'PageSettings', 'TitleBlock', 'Property',
    'RenderCache', 'RenderCachePolygon', 'Fill', 'Image', 'ProjectInstance',
    
    # Board items
    'GeneralSettings', 'LayerToken', 'StackupLayer', 'StackupSubLayer',
    'Stackup', 'PlotSettings', 'SetupData', 'Segment', 'Via', 'Arc', 'Target',
    
    # Footprint items
    'FpText', 'FpLine', 'FpRect', 'FpTextBox', 'FpCircle',
    'FpArc', 'FpPoly', 'FpCurve',
    
    # Schematic items
    'Junction', 'NoConnect', 'BusEntry', 'BusAlias', 'Connection', 'PolyLine',
    'Text', 'TextBox', 'LocalLabel', 'GlobalLabel', 'HierarchicalLabel',
    'SchematicSymbol', 'HierarchicalSheet', 'HierarchicalPin',
    'HierarchicalSheetInstance', 'SymbolInstance',
    'Rectangle', 'Circle', 'NetclassFlag',
    
    # Symbol items
    'SyArc', 'SyCircle', 'SyCurve', 'SyPolyLine',
    'SyRect', 'SyText', 'SyTextBox',
    
    # Graphics items
    'GrText', 'GrTextBox', 'GrLine', 'GrRect',
    'GrCircle', 'GrArc', 'GrPoly', 'GrCurve',
    
    # Zone items  
    'Zone', 'KeepoutSettings', 'FillSettings',
    'ZonePolygon', 'FilledPolygon', 'FillSegments', 'Hatch',
    
    # Dimension items
    'Dimension', 'DimensionFormat', 'DimensionStyle',
]
import QtQuick
import QtQuick.Controls

QtObject {
    id: theme

    // Valid values: "Normal", "Dark", "System"
    property string mode: settingsController.theme
    
    // Check system dark mode
    property bool systemDark: settingsController.systemDarkMode

    readonly property bool isDark: {
        if (mode === "System") return systemDark
        return mode === "Dark"
    }

    // Colors
    readonly property color backgroundColor: isDark ? "#2d2d30" : "#d0d0d5" // Slightly darker/warmer for desktop feel
    readonly property color textColor: isDark ? "#ffffff" : "#000000"
    readonly property color headerColor: isDark ? "#383838" : "#e0e0e0"

    // Gradients & 3D Elements
    readonly property color headerGradientStart: isDark ? "#454545" : "#f5f5f5"
    readonly property color headerGradientEnd: isDark ? "#2d2d2d" : "#cfcfcf"
    
    readonly property color buttonGradientStart: isDark ? "#4e4e4e" : "#fdfdfd"
    readonly property color buttonGradientEnd: isDark ? "#333333" : "#dadada"
    readonly property color buttonPressedStart: isDark ? "#2a2a2a" : "#c4c4c4"
    readonly property color buttonPressedEnd: isDark ? "#3a3a3a" : "#e0e0e0"

    readonly property color bevelLight: isDark ? "#606060" : "#ffffff"
    readonly property color bevelDark: isDark ? "#1a1a1a" : "#a0a0a0"
    readonly property color shadowColor: "#40000000"

    readonly property color buttonColor: isDark ? "#333333" : "#ffffff" // Fallback
    readonly property color highlightColor: "#0078d7" // Standard Windows Blue
    readonly property color secondaryHighlightColor: isDark ? "#1d4874" : "#86C1FC"
    readonly property color secondaryTextColor: isDark ? "#b0b0b0" : "#666666"
    readonly property color borderColor: isDark ? "#1e1e1e" : "#888888" // Sharper borders
    readonly property color textFieldColor: isDark ? "#202020" : "#ffffff"
}

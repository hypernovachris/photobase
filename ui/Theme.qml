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
    readonly property color backgroundColor: isDark ? "#121212" : "#e0e0e0"
    readonly property color textColor: isDark ? "#ffffff" : "#000000"
    readonly property color headerColor: isDark ? "#1e1e1e" : "#f0f0f0"
    readonly property color buttonColor: isDark ? "#333333" : "#ffffff"
    readonly property color highlightColor: "#0077EE"
    readonly property color secondaryHighlightColor: isDark ? "#1d4874" : "#86C1FC"
    readonly property color secondaryTextColor: isDark ? "#b0b0b0" : "#666666"
    readonly property color borderColor: isDark ? "#444444" : "#bbbbbb"
    readonly property color textFieldColor: isDark ? "#000000" : "#ffffff"
}

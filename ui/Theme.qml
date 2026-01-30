import QtQuick
import QtQuick.Controls

QtObject {
    id: theme

    // Colors
    readonly property color backgroundColor: "#f0f0f0"
    readonly property color textColor: "#000000"
    readonly property color highlightColor: "#0078d7"
    readonly property color secondaryHighlightColor: "#cce5ff"
    readonly property color secondaryTextColor: "#666666"
    readonly property color borderColor: "#777777"
    readonly property color secondaryBackgroundColor: "#ffffff"
    readonly property color buttonColor: "#777777"



    // Font Sizes
    readonly property int fontSizeTitle: 32
    readonly property int fontSizeHeader: 24
    readonly property int fontSizeSubheader: 20
    readonly property int fontSizeBody: 14
    readonly property int fontSizeSmall: 12

    // Spacing & Layout
    readonly property int spacingSmall: 5
    readonly property int spacingMedium: 10
    readonly property int spacingLarge: 20
    readonly property int paddingMedium: 20
    
    // Component Sizes
    readonly property int headerHeight: 50
}

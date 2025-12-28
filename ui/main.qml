import QtQuick
import QtQuick.Controls
import QtQuick.Layouts



ApplicationWindow {
    visible: true
    width: 1000
    height: 700
    title: "Photobase"
    color: theme.backgroundColor

    Connections {
        target: galleryModel
        function onFilterChanged(tagName) {
            if (tagName !== "") {
                bar.currentIndex = 0
            }
        }
    }

    header: TabBar {
        id: bar
        width: parent.width
        
        background: Rectangle {
            color: theme.headerColor
        }

        contentItem: ListView {
            model: bar.contentModel
            currentIndex: bar.currentIndex
            spacing: bar.spacing
            orientation: ListView.Horizontal
            boundsBehavior: Flickable.StopAtBounds
            flickableDirection: Flickable.AutoFlickIfNeeded
        }

        StyledTabButton {
            text: "Gallery"
        }
        StyledTabButton {
            text: "Tags"
        }
        StyledTabButton {
            text: "People"
        }
        StyledTabButton {
            text: "Places"
        }
        StyledTabButton {
            text: "Search"
        }
        StyledTabButton {
            text: "Settings"
        }
    }

    StackLayout {
        anchors.fill: parent
        currentIndex: bar.currentIndex

        Gallery {
        }
        Tags {
        }
        People {
        }
        Places {
        }
        Search {
        }
        Settings {
        }
    }
    

    footer: ToolBar {
        height: 30
        background: Rectangle {
            color: theme.headerColor
        }
        
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 10
            anchors.rightMargin: 10
            
            Text {
                text: faceScanner.unscanned_count > 0 ? "Scanning faces: " + faceScanner.unscanned_count + " remaining..." : "All photos scanned."
                color: theme.textColor
                font.pixelSize: 12
            }
            
            Item { Layout.fillWidth: true }
        }
    }
}

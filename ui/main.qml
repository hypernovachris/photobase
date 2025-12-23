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
}

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    visible: true
    width: 1000
    height: 700
    title: "Photobase"
    color: theme.backgroundColor

    Theme {
        id: theme
    }


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

        TabButton {
            text: "Gallery"
            palette.buttonText: theme.textColor
        }
        TabButton {
            text: "Tags"
            palette.buttonText: theme.textColor
        }
        TabButton {
            text: "People"
            palette.buttonText: theme.textColor
        }
        TabButton {
            text: "Places"
            palette.buttonText: theme.textColor
        }
        TabButton {
            text: "Search"
            palette.buttonText: theme.textColor
        }
        TabButton {
            text: "Settings"
            palette.buttonText: theme.textColor
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

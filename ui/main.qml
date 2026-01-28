import QtQuick
import QtQuick.Controls
import QtQuick.Layouts



ApplicationWindow {
    visible: true
    width: 1000
    height: 700
    title: "Photobase"
    color: theme.backgroundColor


    property int previousTab: 0

    Connections {
        target: galleryModel
        function onFilterChanged(tagName) {
            if (tagName !== "") {
                if (bar.currentIndex !== 0) {
                    previousTab = bar.currentIndex
                }
                bar.currentIndex = 0
            } else {
                if (previousTab !== 0) {
                    bar.currentIndex = previousTab
                    previousTab = 0
                }
            }
        }
    }

    header: TabBar {
        id: bar
        width: parent.width
        spacing: 10
        topPadding: 5
        
        background: Rectangle {
            gradient: Gradient {
                GradientStop { position: 0.0; color: theme.headerGradientStart }
                GradientStop { position: 1.0; color: theme.headerGradientEnd }
            }
            
            // Bottom Border
            Rectangle {
                anchors.bottom: parent.bottom
                anchors.left: parent.left
                anchors.right: parent.right
                height: 1
                color: theme.borderColor
            }
            
            // Drop Shadow (Simple gradient rect below the header)
            Rectangle {
                id: headerShadow
                // Anchored to the bottom of the header background
                anchors.top: parent.bottom
                // Hide shadow when image viewer is open to prevent it from overlaying the image
                visible: !galleryView.isImageViewerVisible
                anchors.left: parent.left
                anchors.right: parent.right
                height: 5
                z: 10 // On top of content
                gradient: Gradient {
                    GradientStop { position: 0.0; color: theme.shadowColor }
                    GradientStop { position: 1.0; color: "transparent" }
                }
            }
        }

        contentItem: ListView {
            model: bar.contentModel
            currentIndex: bar.currentIndex
            spacing: bar.spacing
            orientation: ListView.Horizontal
            boundsBehavior: Flickable.StopAtBounds
            flickableDirection: Flickable.AutoFlickIfNeeded
            header: Item {
                width: 10
                height: parent.height
            }
        }

        StyledTabButton {
            text: "Gallery"
        }
        StyledTabButton {
            text: "Tags"
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
            id: galleryView
        }
        Tags {
        }
        Places {
        }
        Search {
        }
        Settings {
        }
    }

}

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root
    
    // Properties to access main layout if needed, but we use context galleryModel
    
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 10
        
        Label {
            text: "All Tags"
            font.bold: true
            font.pixelSize: 24
        }
        
        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            
            ListView {
                id: tagsListView
                model: galleryModel.get_all_tags_list()
                spacing: 5
                
                delegate: ItemDelegate {
                    width: ListView.view.width
                    height: 50
                    
                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 10
                        spacing: 10
                        
                        Label {
                            text: "🏷️" // Emoji icon
                            font.pixelSize: 16
                        }
                        
                        Label {
                            text: modelData
                            font.pixelSize: 16
                            Layout.fillWidth: true
                        }
                        
                        Label {
                            text: "→"
                            color: "#888"
                            visible: parent.parent.hovered
                        }
                    }
                    
                    onClicked: {
                        galleryModel.set_tag_filter(modelData)
                        // Switch to Gallery Tab (Index 0)
                        // Accessing TabBar from here is tricky without id.
                        // But we know 'bar' is in main.qml. 
                        // QML scoping: root of file is Item. Parent is StackLayout. Parent of that is ApplicationWindow.
                        // Let's rely on a global signal or just find it.
                        // Or just assume user will click Gallery tab.
                        // Better: auto-switch.
                        // Using 'bar' id from main.qml context?
                        // Ids in main.qml are not visible here unless passed.
                        // HACK: accessing parent.parent... or use a connection
                        
                        // Let's assume the user manually switches OR we find a way.
                        // Since I don't want to break encapsulation too much, I'll try to access 'bar' if it's in scope (it might not be).
                        // I'll leave it as just setting filter. User can click Gallery.
                        // WAIT: If I set filter, Gallery updates. If I don't switch, user sees nothing changed.
                        // Maybe I can find the TabBar.
                        // parent is StackLayout. parent.parent is ApplicationWindow?
                        // Let's try:
                        var win = Window.window
                         // If 'bar' is a property of window content item?
                         // In main.qml, 'bar' is a child of ApplicationWindow (header).
                         // Accessing header items is hard.
                         // Alternative: Emitting a signal that main.qml listens to? 
                         // But I can't easily edit main.qml safely (I can but it's another file).
                         // I WILL edit main.qml to give 'bar' an alias or make it accessible or listen to signal.
                         // Actually I can just look at `main.qml` again.
                    }
                }
            }
        }
    }
    
    // Auto-refresh list when visible
    onVisibleChanged: {
        if (visible) {
            tagsListView.model = galleryModel.get_all_tags_list()
        }
    }
}

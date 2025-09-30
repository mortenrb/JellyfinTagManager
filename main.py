import sys
import configparser
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QLabel,
                             QHeaderView, QAbstractItemView, QCheckBox, QMessageBox)
from PyQt6.QtCore import Qt
from jellyfin_apiclient_python.client import JellyfinClient


class JellyfinTagManager(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Jellyfin Tag Manager')
        self.setGeometry(100, 100, 1000, 600)
        self.client = None
        self.items = []  # Cache to hold all fetched items

        self.init_ui()
        self.load_config()
        self.connect_and_fetch()

    def init_ui(self):
        main_layout = QHBoxLayout()

        # Left Panel (Content Table and Filters)
        left_layout = QVBoxLayout()

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            ['Select', 'Movie Name', 'Library', 'Tags'])
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers)

        filter_layout = QHBoxLayout()
        self.filter_inputs = []
        for i in range(4):
            filter_input = QLineEdit()
            filter_input.setPlaceholderText(
                self.table.horizontalHeaderItem(i).text())
            filter_input.textChanged.connect(self.filter_table)
            filter_layout.addWidget(filter_input)
            self.filter_inputs.append(filter_input)

        left_layout.addLayout(filter_layout)
        left_layout.addWidget(self.table)
        main_layout.addLayout(left_layout, 3)

        # Right Panel (Controls)
        right_layout = QVBoxLayout()

        right_layout.addWidget(QLabel('Jellyfin Server URL:'))
        self.url_input = QLineEdit()
        right_layout.addWidget(self.url_input)

        right_layout.addWidget(QLabel('API Key:'))
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        right_layout.addWidget(self.api_key_input)

        right_layout.addWidget(QLabel('User Id:'))
        self.user_id_input = QLineEdit()
        right_layout.addWidget(self.user_id_input)

        connect_button = QPushButton('Connect and Fetch Content')
        connect_button.clicked.connect(self.connect_and_fetch)
        right_layout.addWidget(connect_button)
        right_layout.addStretch()

        check_uncheck_button = QPushButton('Check/Uncheck All')
        check_uncheck_button.clicked.connect(self.toggle_all_selection)
        right_layout.addWidget(check_uncheck_button)

        clear_tags_button = QPushButton('Clear Tags on Selected')
        clear_tags_button.clicked.connect(self.clear_tags)
        right_layout.addWidget(clear_tags_button)

        right_layout.addWidget(QLabel('Tags to Append (comma-separated):'))
        self.tags_input = QLineEdit()
        right_layout.addWidget(self.tags_input)

        append_tags_button = QPushButton('Append Tags to Selected')
        append_tags_button.clicked.connect(self.append_tags)
        right_layout.addWidget(append_tags_button)
        right_layout.addStretch()

        main_layout.addLayout(right_layout, 1)
        self.setLayout(main_layout)

    def load_config(self):
        config = configparser.ConfigParser()
        if config.read('config.ini'):
            self.url_input.setText(config['Jellyfin']['url'])
            self.api_key_input.setText(config['Jellyfin']['api_key'])
            self.user_id_input.setText(config['Jellyfin']['user_id'])

    def connect_and_fetch(self):
        url = self.url_input.text().strip()
        api_key = self.api_key_input.text().strip()
        user_id = self.user_id_input.text().strip()

        if not url or not api_key:
            QMessageBox.warning(
                self, "Error", "Please enter a valid URL and API Key.")
            return

        self.client = JellyfinClient()

        try:
            self.client.config.data["app.name"] = 'Tag Editor'
            self.client.config.data["app.version"] = '0.0.1'
            self.client.config.data["auth.ssl"] = False
            self.client.config.data["auth.user_id"] = user_id
            self.client.authenticate(
                {"Servers": [{"AccessToken": api_key, "address": url}]}, discover=False)
            self.fetch_content()
        except Exception as e:
            QMessageBox.critical(self, "Connection Error",
                                 f"Failed to connect to Jellyfin: {e}")
            self.client = None

    def fetch_content(self):
        if not self.client:
            QMessageBox.warning(self, "Error", "Not connected to Jellyfin.")
            return

        self.table.setRowCount(0)
        self.items = []

        try:
            # libraries = self.client.system.get_virtual_folders_list()['Items']
            libraries = self.client.jellyfin.virtual_folders()
            for lib in libraries:
                library_id = lib['ItemId']
                library_name = lib['Name']
                # Use client.items.get_items for fetching content
                params = {
                    'recursive': True,
                    'parentId': library_id,
                    'fields': 'Tags',
                }
                library_items = self.client.jellyfin.items(
                    params=params)["Items"]

                for item in library_items:
                    row_count = self.table.rowCount()
                    self.table.insertRow(row_count)
                    self.items.append(item)

                    checkbox = QCheckBox()
                    h_layout = QHBoxLayout()
                    h_layout.addWidget(checkbox)
                    h_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    cell_widget = QWidget()
                    cell_widget.setLayout(h_layout)
                    self.table.setCellWidget(row_count, 0, cell_widget)

                    name_item = QTableWidgetItem(item.get('Name', ''))
                    self.table.setItem(row_count, 1, name_item)

                    library_item = QTableWidgetItem(library_name)
                    self.table.setItem(row_count, 2, library_item)

                    tags = ', '.join(item.get('Tags', []))
                    tags_item = QTableWidgetItem(tags)
                    self.table.setItem(row_count, 3, tags_item)

        except Exception as e:
            QMessageBox.critical(self, "Fetch Error",
                                 f"Error fetching content: {e}")

    def filter_table(self):
        for row in range(self.table.rowCount()):
            match = True
            for col in range(self.table.columnCount()):
                filter_text = self.filter_inputs[col].text().lower()
                if filter_text:
                    if col == 0:
                        continue
                    item = self.table.item(row, col)
                    if item and filter_text not in item.text().lower():
                        match = False
                        break
            self.table.setRowHidden(row, not match)

    def get_selected_items(self):
        selected_indices = []
        for row in range(self.table.rowCount()):
            if not self.table.isRowHidden(row):
                widget = self.table.cellWidget(row, 0)
                if isinstance(widget, QWidget):
                    checkbox = widget.findChild(QCheckBox)
                    if checkbox and checkbox.isChecked():
                        selected_indices.append(row)
        return selected_indices

    def update_tags_in_gui(self, row, new_tags):
        tags_item = QTableWidgetItem(', '.join(new_tags))
        self.table.setItem(row, 3, tags_item)

    def clear_tags(self):
        selected_rows = self.get_selected_items()
        if not selected_rows:
            return

        if not self.client:
            QMessageBox.warning(self, "Error", "Not connected to Jellyfin.")
            return

        headers = {'X-Emby-Token': self.api_key_input.text().strip(),
                   'Content-Type': 'application/json'}
        for row in selected_rows:
            item = self.items[row]
            item_id = item['Id']

            try:
                updated_tags = []
                # Update the item with the new tags
                item_data = self.client.jellyfin.get_item(item_id)
                item_data["Tags"] = updated_tags
                # print(item_data)
                handler = '/' + item_id
                self.client.jellyfin.items(handler=handler,
                                           action="POST", json=item_data, headers=headers)
                self.items[row]['Tags'] = updated_tags
                self.update_tags_in_gui(row, updated_tags)

            except Exception as e:
                print(f"Error appending tags for item {item_id}: {e}")

    def append_tags(self):
        new_tags = [tag.strip()
                    for tag in self.tags_input.text().split(',') if tag.strip()]
        if not new_tags:
            return

        selected_rows = self.get_selected_items()
        if not selected_rows:
            return

        if not self.client:
            QMessageBox.warning(self, "Error", "Not connected to Jellyfin.")
            return

        headers = {'X-Emby-Token': self.api_key_input.text().strip(),
                   'Content-Type': 'application/json'}
        for row in selected_rows:
            item = self.items[row]
            item_id = item['Id']

            try:
                existing_tags = set(item.get('Tags', []))
                updated_tags = sorted(list(existing_tags.union(set(new_tags))))
                # Update the item with the new tags
                item_data = self.client.jellyfin.get_item(item_id)
                item_data["Tags"] = updated_tags
                # print(item_data)
                handler = '/' + item_id
                self.client.jellyfin.items(handler=handler,
                                           action="POST", json=item_data, headers=headers)
                self.items[row]['Tags'] = updated_tags
                self.update_tags_in_gui(row, updated_tags)

            except Exception as e:
                print(f"Error appending tags for item {item_id}: {e}")

    def toggle_all_selection(self):
        first_checkbox = None
        for row in range(self.table.rowCount()):
            if not self.table.isRowHidden(row):
                widget = self.table.cellWidget(row, 0)
                if widget:
                    first_checkbox = widget.findChild(QCheckBox)
                    if first_checkbox:
                        break

        if not first_checkbox:
            return

        select_all = not first_checkbox.isChecked()

        for row in range(self.table.rowCount()):
            if not self.table.isRowHidden(row):
                widget = self.table.cellWidget(row, 0)
                if widget:
                    checkbox = widget.findChild(QCheckBox)
                    if checkbox:
                        checkbox.setChecked(select_all)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = JellyfinTagManager()
    window.show()
    sys.exit(app.exec())

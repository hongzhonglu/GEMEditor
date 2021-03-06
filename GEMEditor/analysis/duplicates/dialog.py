from GEMEditor.analysis.duplicates.functions import merge_reactions, merge_metabolites
from GEMEditor.analysis.duplicates.ui.TreeViewDialog import Ui_Duplicates
from GEMEditor.base import Settings, restore_state
from GEMEditor.base.dialogs import CustomStandardDialog
from GEMEditor.model.display.tables import ReactionBaseTable, MetaboliteTable
from PyQt5 import QtGui, QtCore
from PyQt5.QtWidgets import QInputDialog, QMenu, QAction


class DuplicateDialog(CustomStandardDialog, Ui_Duplicates):
    """ Display duplicated model items

    This dialog is used for the display of potential duplicated
    model items in groups. The user is able to select a group
    and merge the corresponding items by click.

    Parameters
    ----------
    groups: list or dict,
        Containing the groups of duplicated items
    merge_function: func,
        The function called in order to merge a group of functions
    row_factory: func,
        The function called for retrieving a row to add to the table
    headers: list,
        The headers used in the table
    item_type: str,
        Type of the items being displayed
    """

    def __init__(self, groups, merge_function, row_factory, headers, item_type):
        super(DuplicateDialog, self).__init__()
        self.setupUi(self)

        # Make sure to use either dict or lists
        if isinstance(groups, list):
            self.items = groups
        elif isinstance(groups, dict):
            self.items = groups.values()
        self.merge_function = merge_function
        self.row_factory = row_factory
        self.dialog_type = item_type

        # Setup dialog
        self.dataModel = QtGui.QStandardItemModel(self)
        self.dataModel.setHorizontalHeaderLabels(headers)
        self.treeView.setModel(self.dataModel)
        self.populate_tree()

        # Connect signals
        self.finished.connect(self.save_dialog_geometry)
        self.treeView.customContextMenuRequested.connect(self.showContextMenu)

        # Restore dialog state
        self.restore_dialog_geometry()

    def populate_tree(self):
        """ Populate the tree view with duplicates """

        # Clear existing items
        self.dataModel.setRowCount(0)

        # Load new items
        root_item = self.dataModel.invisibleRootItem()
        if self.items:
            n = 1
            for item_list in self.items:
                if len(item_list) > 1:
                    group_item = QtGui.QStandardItem("Group {}".format(str(n)))
                    for item in item_list:
                        group_item.appendRow(self.row_factory(item))
                    n += 1
                    root_item.setChild(n-2, group_item)
            self.treeView.expandAll()

    @QtCore.pyqtSlot(QtCore.QPoint)
    def showContextMenu(self, pos):
        menu = QMenu()
        index = self.treeView.indexAt(pos)
        if index.isValid():
            item = self.dataModel.itemFromIndex(index)
            if item.parent() is None:
                action_merge_items = QAction(self.tr("Merge"), menu)
                action_merge_items.triggered.connect(self.merge_items)
                menu.addAction(action_merge_items)
                menu.exec_(self.treeView.viewport().mapToGlobal(pos))

    @QtCore.pyqtSlot()
    def merge_items(self):
        """ Merge the selected items """

        indices = self.treeView.selectedIndexes()
        first_index = sorted(indices, key=lambda x: x.column())[0]

        item = self.dataModel.itemFromIndex(first_index)
        child_items = [item.child(n, 0).link for n in range(item.rowCount())]
        item_ids = [model_item.id for model_item in child_items]
        selected_id, status = QInputDialog.getItem(self, "Select item", "Select item to keep:",
                                                   item_ids, 0, False)
        if status:
            self.merge_function(child_items, child_items.pop(item_ids.index(selected_id)))
            self.dataModel.removeRow(first_index.row())

    def restore_dialog_geometry(self):
        """ Restore the geometry of the table from the settings """

        super(DuplicateDialog, self).restore_dialog_geometry()
        header_state = Settings().value(self.__class__.__name__ + "TableHeader"+str(self.dialog_type))
        restore_state(self.treeView.header(), header_state)

    def save_dialog_geometry(self):
        """ Save the geometry of the table in settings """

        super(DuplicateDialog, self).save_dialog_geometry()
        Settings().setValue(self.__class__.__name__ + "TableHeader"+str(self.dialog_type),
                                    self.treeView.header().saveState())


def factory_duplicate_dialog(input_type, duplicates):
    """ Factory for duplicate dialogs

    Parameters
    ----------
    input_type: str
    duplicates: list

    Returns
    -------

    """

    if input_type.lower() == "metabolite":
        row_factory = MetaboliteTable.row_from_item
        dialog = DuplicateDialog(duplicates, merge_metabolites, row_factory, MetaboliteTable.header, input_type)
        dialog.setWindowTitle("Duplicate metabolites")
        return dialog
    elif input_type.lower() == "reaction":
        row_factory = ReactionBaseTable.row_from_item
        dialog = DuplicateDialog(duplicates, merge_reactions, row_factory, ReactionBaseTable.header, input_type)
        dialog.setWindowTitle("Duplicate reactions")
        return dialog
    else:
        raise NotImplementedError

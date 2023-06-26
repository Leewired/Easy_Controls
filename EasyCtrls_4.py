import pymel.core as pm
from PySide2 import QtWidgets, QtCore, QtGui
from maya import OpenMayaUI as omui
import os
from functools import partial
from shiboken2 import wrapInstance

USERAPPDIR = pm.internalVar(userAppDir=True)
DIRECTORY = os.path.join(USERAPPDIR, '2023/prefs/icons')
DEFAULTCOL = (0.9, 0.65, 0)


def _getMayaMainWindow():
    # this is to set up parenting the UI to mayas main window
    # get main window of maya (memory address)
    win = omui.MQtUtil_mainWindow()
    # pointer to wrapped instance
    ptr = wrapInstance(int(win), QtWidgets.QMainWindow)
    return ptr


class CtrlsUI(QtWidgets.QWidget):

    def __init__(self):
        """
        Initialize class. Set up default values and empty lists for later usage (and reset them when re-initialized).
        Delete previous window if there is one.
        Create parent QDialog and parent it to Mayas main window. Set size, name and layout.
        Initialize QDialog.
        Build the UI using _buildUI()
        Show the QDialog.
        """

        self.ctrls = []
        self.constructors = []
        self.groups = []
        self.offsetSpins = []
        self.normalSpins = []
        self.connectors = {'conT': ['Connect translate', False],
                           'conR': ['Connect rotation', False],
                           'conS': ['Connect scale', False],
                           'point': ['Point constraint', True],
                           'orient': ['Orient constraint', True],
                           'scale': ['Scale constraint', True],
                           'parent': ['Parent constraint', True]}
        self.connectorButtons = {}
        self.offsetButtons = {}
        self.ctrlColor = DEFAULTCOL
        # self.cvOrigPos = [] for saving cvs original positions

        try:
            pm.deleteUI('easyCtrls')
        except RuntimeError:
            print('No previous UI exists')

        parent = QtWidgets.QDialog(parent=_getMayaMainWindow())
        parent.setObjectName('easyCtrls')
        parent.setWindowTitle("Easy Ctrls")
        parent.setFixedSize(220, 395)
        layout = QtWidgets.QVBoxLayout(parent)

        super(CtrlsUI, self).__init__(parent=parent)
        self._buildUI()
        self.parent().layout().addWidget(self)
        parent.show()

    def closeEvent(self, event):
        self._finish()

    def _buildUI(self):
        """
        This function builds the UI inside the window. Updating this, you should set parent windows size accordingly,
         or remove fixed size.
        """
        # Use grid layout.
        layout = QtWidgets.QGridLayout(self)

        # Create multiple push-buttons with named icons easily.
        # Add name to shapes-list. Searches for icon in DIRECTORY. (=.../2023/prefs/icons)
        shapes = ['square', 'circle']   # , 'boomerang'
        row = 0
        column = 0
        for s in shapes:
            image = os.path.join(DIRECTORY, '%s.png' % s)
            icon = QtGui.QIcon(image)

            CtrlBtn = QtWidgets.QPushButton()
            CtrlBtn.setIcon(icon)
            CtrlBtn.setIconSize(QtCore.QSize(32, 32))
            CtrlBtn.clicked.connect(partial(self._createCtrls, ctrltype=s))
            layout.addWidget(CtrlBtn, row, column)
            column += 1

        # Delete button. Size fixed, click connected to self._deleteCtrls, 1st row, Cth column, depending on shape buttons.
        deleteBtn = QtWidgets.QPushButton('DEL')
        deleteBtn.setFixedSize(QtCore.QSize(54, 42))
        deleteBtn.clicked.connect(self._deleteCtrls)
        layout.addWidget(deleteBtn, row, column)
        row += 1

        # Radius-slider. Sends out value divided by ten (so min = .1 and max = 10). Connected to self._changeRadius.
        radius = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        radius.setMinimum(1)
        radius.setMaximum(100)
        radius.setValue(10)
        radius.valueChanged.connect(lambda val: self._changeRadius(ctrlRadius=val/10))
        self.radiusSlider = radius
        layout.addWidget(radius, row, 0, 1, 3)
        row += 1
        column = 0

        # Spin boxes for setting normals for control objects. X ,Y and Z. Each connected to self._changeNormalX , Y or Z.
        while column < 3:
            normal = QtWidgets.QSpinBox()
            normal.setMinimum(-10)
            normal.setMaximum(10)
            normal.setValue(0)
            layout.addWidget(normal, row, column, 1, 1)
            self.normalSpins.append(normal)
            column += 1
        self.normalSpins[0].valueChanged.connect(lambda val: self._changeNormalX(ctrlNormalX=val))
        self.normalSpins[1].valueChanged.connect(lambda val: self._changeNormalY(ctrlNormalY=val))
        self.normalSpins[2].valueChanged.connect(lambda val: self._changeNormalZ(ctrlNormalZ=val))
        row += 1
        column = 0

        # Double spin boxes for setting offsets for control objects. X ,Y and Z. Each connected to self._changeOffsetX , Y or Z.
        while column < 3:
            offset = QtWidgets.QDoubleSpinBox()
            offset.setMinimum(-10)
            offset.setMaximum(10)
            offset.setSingleStep(0.5)
            offset.setValue(0)
            layout.addWidget(offset, row, column, 1, 1)
            self.offsetSpins.append(offset)
            column += 1
        self.offsetSpins[0].valueChanged.connect(lambda val: self._changeOffsetX(ctrlOffsetX=val))
        self.offsetSpins[1].valueChanged.connect(lambda val: self._changeOffsetY(ctrlOffsetY=val))
        self.offsetSpins[2].valueChanged.connect(lambda val: self._changeOffsetZ(ctrlOffsetZ=val))
        row += 1
        # column = 0

        # Push button for color. Button color set to represent control objects color with self._setButtonColor().
        # Connected to self._setColor.
        self.colorBtn = QtWidgets.QPushButton()
        self._setButtonColor()
        self.colorBtn.clicked.connect(self._setColor)
        layout.addWidget(self.colorBtn, row, 0, 1, 3)
        row += 1

        # Multiple checkboxes for making connections and constraints. Make boxes from self.connectors -dictionary, uses
        # key for naming the button and the first value for setting the text. If second value is True, creates an offset
        # button with matching name and row.
        # self.connectors is a dictionary, where connector = key. Self.connectors[connector] gives values.
        for connector in self.connectors:
            self.connectorButtons[connector] = QtWidgets.QCheckBox(self.connectors[connector][0])
            layout.addWidget(self.connectorButtons[connector], row, 0, 1, 3)
            if self.connectors[connector][1]:
                self.offsetButtons[connector] = QtWidgets.QCheckBox('Offset')
                layout.addWidget(self.offsetButtons[connector], row, 2, 1, 1)
            row += 1
        # have to make connections manually with lambda. Otherwise, signals get overwritten.
        self.connectorButtons['conT'].toggled.connect(lambda val: self._connectTranslate(connect=val))
        self.connectorButtons['conR'].toggled.connect(lambda val: self._connectRotate(connect=val))
        self.connectorButtons['conS'].toggled.connect(lambda val: self._connectScale(connect=val))
        self.connectorButtons['point'].toggled.connect(lambda val: self._connectPointCon(connect=val))
        self.connectorButtons['orient'].toggled.connect(lambda val: self._connectOrientCon(connect=val))
        self.connectorButtons['scale'].toggled.connect(lambda val: self._connectScaleCon(connect=val))
        self.connectorButtons['parent'].toggled.connect(lambda val: self._connectParentCon(connect=val))

        # Push button for resetting all elements in the UI, which also resets control objects to default positions.
        # Connected to self._resetValues.
        self.resetValBtn = QtWidgets.QPushButton('Reset Values')
        self.resetValBtn.clicked.connect(self._resetValues)
        layout.addWidget(self.resetValBtn, row, 0, 1, 3)
        row += 1

        # Push button for finishing and deleting history.
        self.doneBtn = QtWidgets.QPushButton('Done')
        self.doneBtn.clicked.connect(self.parent().close)
        layout.addWidget(self.doneBtn, row, 0, 1, 3)
        row +=1

    def _setButtonColor(self, color=None):
        """
        Sets color for the self.colorBtn.
        Args:
            color: Tuple or list of three float values (0-1). If none given uses values from self.ctrlColor.
        """
        if not color:
            color = self.ctrlColor

        assert len(color) == 3, "You must provide a list of three values"

        r, g, b = [c * 255 for c in color]

        self.colorBtn.setStyleSheet('background-color: rgba({0}, {1}, {2}, 1.0)'.format(r, g, b))

    def _connectTranslate(self, connect=False):
        if connect:
            self.connectorButtons['point'].setChecked(False)
            self.connectorButtons['parent'].setChecked(False)
            self._connectTrans()
        else:
            self._disconnectTrans()

    def _connectRotate(self, connect=False):
        if connect:
            self.connectorButtons['orient'].setChecked(False)
            self.connectorButtons['parent'].setChecked(False)
            self._connectRot()
        else:
            self._disconnectRot()

    def _connectScale(self, connect=False):
        if connect:
            self.connectorButtons['scale'].setChecked(False)
            self._connectScl()
        else:
            self._disconnectScl()

    def _connectPointCon(self, connect=False):
        if connect:
            self.connectorButtons['conT'].setChecked(False)
            self.connectorButtons['parent'].setChecked(False)
            self._pointConstrain()
        else:
            self._delPointConstraints()

    def _connectOrientCon(self, connect=False):
        if connect:
            self.connectorButtons['conR'].setChecked(False)
            self.connectorButtons['parent'].setChecked(False)
            self._orientConstrain()
        else:
            self._delOrientConstraints()

    def _connectScaleCon(self, connect=False):
        if connect:
            self.connectorButtons['conS'].setChecked(False)
            self._scaleConstrain()
        else:
            self._delScaleConstraints()

    def _connectParentCon(self, connect=False):
        if connect:
            self.connectorButtons['conT'].setChecked(False)
            self.connectorButtons['conR'].setChecked(False)
            self.connectorButtons['point'].setChecked(False)
            self.connectorButtons['orient'].setChecked(False)
            self._parentConstrain()
        else:
            self._delParentConstraints()

    def _resetValues(self):
        """
        Resets the values of UI elements, which resets the controls to original settings as well.
        Severs all connections and deletes all constraints.
        """
        self.radiusSlider.setValue(10)
        self.normalSpins[0].setValue(0)
        self.normalSpins[1].setValue(0)
        self.normalSpins[2].setValue(0)
        self.offsetSpins[0].setValue(0)
        self.offsetSpins[1].setValue(0)
        self.offsetSpins[2].setValue(0)
        self.ctrlColor = DEFAULTCOL
        self._setButtonColor()
        for c in self.ctrls:
            pm.setAttr(c.overrideColorRGB, self.ctrlColor[0], self.ctrlColor[1], self.ctrlColor[2])
        for button in self.connectorButtons:
            self.connectorButtons[button].setChecked(False)
        for button in self.offsetButtons:
            self.offsetButtons[button].setChecked(False)

    def _createCtrls(self, ctrltype=None):
        """
        Creates control objects of given type for selected objects, if nothing selected notifies and errors out.
        Control objects have groups which are matched to original objects position and rotation --> Zero transformations.
        Checks if values in UI have changed and adjusts controls accordingly.
        ---
        Saves original transform values for selected objects in dictionaries. (self.selOrigTrans, self.selOrigRot, self.selOrigScale)
        Key is selected object name, values a list.
        Save controls to self.controls.
        Save constructors to self.constructors.
        Save groups to self.groups.
        Initialize lists for constraints. (self.ctrlPointCon, self.ctrlOrientCon, self.ctrlScaleCon, self.ctrlParentCon)
        Args:
            ctrltype: String. Set in _buildUI() -function. For now if 'circle': circle, else square.
        """
        self.sel = pm.ls(sl=True)

        if len(self.sel) == 0:
            pm.confirmDialog(title="Error", message="Select something")
            raise IOError('Nothing selected')

        # flush lists aka forget about previously created controls
        self.ctrls.clear()
        self.constructors.clear()
        self.groups.clear()

        # setting original trans back is not optimal, what if translate is locked?
        self.selOrigTrans = {}
        self.selOrigRot = {}
        self.selOrigScale = {}
        self.ctrlPointCon = []
        self.ctrlOrientCon = []
        self.ctrlScaleCon = []
        self.ctrlParentCon = []

        for i, item in enumerate(self.sel):
            # add original transform values to dictionaries for later access.
            self.selOrigTrans.update({item: pm.getAttr(item.translate)})
            self.selOrigRot.update({item: pm.getAttr(item.rotate)})
            self.selOrigScale.update({item: pm.getAttr(item.scale)})

            # create a group for controls
            ctrlGrp = pm.group(n=(item + "_ctrl_grp"), em=True)
            # check given control type and make matching controls
            if ctrltype == 'circle':
                ctrl, constructor = pm.circle(name=(item + "_ctrl"), c=(0, 0, 0), nr=(0, 0, 0), sw=360, r=0.5, d=3,
                                              ut=0, tol=0.01, s=8, ch=1)
            else:
                ctrl, constructor = pm.circle(name=(item + "_ctrl"), c=(0, 0, 0), nr=(0, 0, 0), sw=360, r=0.5, d=1,
                                              ut=0, tol=0.01, s=4, ch=1)
            '''
            This is for constructing 'boomerang':
            else:
                ctrl, constructor = pm.circle(name=(item + "_ctrl"), c=(0, 0, 0), nr=(0, 0, 0), sw=360, r=0.5,
                                                d=3, ut=0, tol=0.01, s=8, ch=1)
                pm.move(0, 0.2, 0, ctrl + ".cv[1]", r=True)
                pm.move(0, 0.45, 0, ctrl + ".cv[4:6]", r=True)
                pm.move(0, 0.5, 0, ctrl + ".cv[5]", r=True)
            '''
            # set control color to default
            pm.setAttr(ctrl.overrideEnabled, 1)
            pm.setAttr(ctrl.overrideRGBColors, 1)
            pm.setAttr(ctrl.overrideColorRGB, self.ctrlColor[0], self.ctrlColor[1], self.ctrlColor[2])
            '''
            For saving every cvs original position:
            cvs = ctrl.cv[0:]
            a = 0
            for _ in cvs:
                self.cvOrigPos.append(ctrl.cv[a].getPosition())
                print(self.cvOrigPos)
                print("orig pos for cv%s saved: %s" % ([a], self.cvOrigPos[a]))
                a += 1
            '''
            pm.matchTransform(ctrlGrp, item)
            pm.pointConstraint(ctrlGrp, ctrl)
            pm.orientConstraint(ctrlGrp, ctrl)
            # delete constraints
            pm.delete(ctrl, cn=True)
            pm.parent(ctrl, ctrlGrp)
            # add to lists
            self.ctrls.append(ctrl)
            self.groups.append(ctrlGrp)
            self.constructors.append(constructor)

        for ctrl in self.ctrls:
            # somehow ctrl is not scaled exactly 1, 1, 1 when created. So must do this manually.
            pm.setAttr(ctrl.scale, 1, 1, 1)
        # set controls to match UI values
        self._changeRadius(self.radiusSlider.value() / 10)
        self._changeOffsetX(self.offsetSpins[0].value())
        self._changeOffsetY(self.offsetSpins[1].value())
        self._changeOffsetZ(self.offsetSpins[2].value())
        self._changeNormalX(self.normalSpins[0].value())
        self._changeNormalY(self.normalSpins[1].value())
        self._changeNormalZ(self.normalSpins[2].value())
        pm.select(cl=True)
        # check if connector buttons have been checked
        if self.connectorButtons['conT'].isChecked():
            self._connectTrans()
        if self.connectorButtons['conR'].isChecked():
            self._connectRot()
        if self.connectorButtons['conS'].isChecked():
            self._connectScl()
        if self.connectorButtons['point'].isChecked():
            self._pointConstrain()
        if self.connectorButtons['orient'].isChecked():
            self._orientConstrain()
        if self.connectorButtons['scale'].isChecked():
            self._scaleConstrain()
        if self.connectorButtons['parent'].isChecked():
            self._parentConstrain()

    def _changeRadius(self, ctrlRadius=1):
        """
        Sets radius for each control, using its constructor node.
        Args:
            ctrlRadius: Float. Given by self.radiusSlider -slider.
        """
        for con in self.constructors:
            pm.setAttr(con.radius, ctrlRadius)
        '''
        Reset cvs position to original values. Works for all types, but is heavy.
        scaleVal = [ctrlRadius, ctrlRadius, ctrlRadius]
        for c in self.ctrls:
            cvs = c.cv[0:]
            i = 0
            for _ in cvs:
                c.cv[i].setPosition(self.cvOrigPos[i])
                i += 1

            cwrld = pm.xform(c, sp=True, q=True, ws=True)
            pm.scale(c.cv[0:], scaleVal, r=True, p=cwrld)
        '''

    def _changeOffsetX(self, ctrlOffsetX=0):
        """
        Sets X value for every control vertex of each made control object.
        Args:
            ctrlOffsetX: Float. Given by self.offsetSpins[0] -doubleSpinBox.
        """
        for c in self.ctrls:
            for i, cp in enumerate(c.cv[0:]):
                pm.setAttr(c.controlPoints[i].xValue, ctrlOffsetX)

    def _changeOffsetY(self, ctrlOffsetY=0):
        for c in self.ctrls:
            for i, cp in enumerate(c.cv[0:]):
                pm.setAttr(c.controlPoints[i].yValue, ctrlOffsetY)

    def _changeOffsetZ(self, ctrlOffsetZ=0):
        for c in self.ctrls:
            for i, cp in enumerate(c.cv[0:]):
                pm.setAttr(c.controlPoints[i].zValue, ctrlOffsetZ)

    def _changeNormalX(self, ctrlNormalX=0):
        """
        Sets control-objects normal X value, using constructor-node.
        Args:
            ctrlNormalX: Integer. Given by self.normalSpins[0] -spinbox.
        """
        for con in self.constructors:
            pm.setAttr(con.normalX, ctrlNormalX)

    def _changeNormalY(self, ctrlNormalY=0):
        for con in self.constructors:
            pm.setAttr(con.normalY, ctrlNormalY)

    def _changeNormalZ(self, ctrlNormalZ=0):
        for con in self.constructors:
            pm.setAttr(con.normalZ, ctrlNormalZ)

    def _setColor(self):
        """
        Opens color editor, then splits gotten rgba-floats and assigns them into color (=r, g, b).
        Overrides ctrl color with these values then calls _setButtonColor to set button color.
        """
        color = pm.colorEditor(rgbValue=self.ctrlColor)
        r, g, b, a = [float(c) for c in color.split()]
        color = (r, g, b)
        for c in self.ctrls:
            pm.setAttr(c.overrideColorRGB, r, g, b)
        self.ctrlColor = color
        self._setButtonColor(color)

    def _flushCtrls(self):

        # flush lists and dictionaries
        self.constructors.clear()
        self.ctrls.clear()
        self.sel.clear()
        self.selOrigTrans.clear()
        self.selOrigRot.clear()
        self.selOrigScale.clear()
        self.ctrlPointCon.clear()
        self.ctrlOrientCon.clear()
        self.ctrlScaleCon.clear()
        self.ctrlParentCon.clear()

        # flush groups list
        self.groups.clear()

    def _deleteCtrls(self):
        """
        Clears connector checkbox buttons, which severs connections and deletes constraints.
        Flush lists and dictionaries used by UI elements, so they don't control values to non-existing controls.
        Delete parent groups.
        """
        if not self.groups:
            pm.confirmDialog(title="Error", message="No ctrls constructed")
            raise IOError('No control groups to delete')

        # set check buttons off, which deletes constraints
        for button in self.connectorButtons:
            self.connectorButtons[button].setChecked(False)
        for button in self.offsetButtons:
            self.offsetButtons[button].setChecked(False)

        # flush lists and dictionaries
        self.constructors.clear()
        self.ctrls.clear()
        self.sel.clear()
        self.selOrigTrans.clear()
        self.selOrigRot.clear()
        self.selOrigScale.clear()
        self.ctrlPointCon.clear()
        self.ctrlOrientCon.clear()
        self.ctrlScaleCon.clear()
        self.ctrlParentCon.clear()

        # delete parent groups (and the children with them)
        for g in self.groups:
            pm.delete(g)

        # flush groups list
        self.groups.clear()

    def _connectTrans(self):
        for i, ctrl in enumerate(self.ctrls):
            selTrans = self.sel[i].translate
            ctrlTrans = ctrl.translate

            if pm.getAttr(selTrans) == pm.getAttr(ctrlTrans):
                pm.connectAttr(ctrlTrans, selTrans, f=True)
            else:
                pm.confirmDialog(title="Error", message="Translations do not match on: \"%s\" and \"%s\"\n\nMake"
                                                        " sure selected items translate = 0, 0, 0" %
                                                        (self.sel[i], ctrl))
                self.connectorButtons['conT'].setChecked(False)
                break

    def _disconnectTrans(self):
        for i, ctrl in enumerate(self.ctrls):
            selTrans = self.sel[i].translate
            ctrlTrans = ctrl.translate

            try:
                pm.disconnectAttr(ctrlTrans, selTrans)
            except RuntimeError as r:
                print(r)

            pm.setAttr(selTrans, self.selOrigTrans[self.sel[i]])
            pm.setAttr(ctrlTrans, 0, 0, 0)

    def _connectRot(self):
        for i, ctrl in enumerate(self.ctrls):
            selRot = self.sel[i].rotate
            ctrlRot = ctrl.rotate

            if pm.getAttr(selRot) == pm.getAttr(ctrlRot):
                pm.connectAttr(ctrlRot, selRot, f=True)
            else:
                pm.confirmDialog(title="Error", message="Rotations do not match on: \"%s\" and \"%s\"\n\nMake"
                                                        " sure selected items rotation = 0, 0, 0" %
                                                        (self.sel[i], ctrl))
                self.connectorButtons['conR'].setChecked(False)
                break

    def _disconnectRot(self):
        for i, ctrl in enumerate(self.ctrls):
            selRot = self.sel[i].rotate
            ctrlRot = ctrl.rotate

            try:
                pm.disconnectAttr(ctrlRot, selRot)
            except RuntimeError as r:
                print(r)

            pm.setAttr(selRot, self.selOrigRot[self.sel[i]])
            pm.setAttr(ctrlRot, 0, 0, 0)

    def _connectScl(self):
        for i, ctrl in enumerate(self.ctrls):
            selScale = self.sel[i].scale
            ctrlScale = ctrl.scale

            if pm.getAttr(selScale) == pm.getAttr(ctrlScale):
                pm.connectAttr(ctrlScale, selScale, f=True)
            else:
                pm.confirmDialog(title="Error", message="Scale does not match on: \"%s\" and \"%s\"\n\nMake"
                                                        " sure selected items scale = 1, 1, 1" %
                                                        (self.sel[i], ctrl))
                self.connectorButtons['conS'].setChecked(False)
                break

    def _disconnectScl(self):
        for i, ctrl in enumerate(self.ctrls):
            selScale = self.sel[i].scale
            ctrlScale = ctrl.scale

            try:
                pm.disconnectAttr(ctrlScale, selScale)
            except RuntimeError as r:
                print(r)

            pm.setAttr(selScale, self.selOrigScale[self.sel[i]])
            pm.setAttr(ctrlScale, 1, 1, 1)

    def _pointConstrain(self):
        selection = []
        for i, ctrl in enumerate(self.ctrls):

            if self.offsetButtons['point'].isChecked():
                self.ctrlPointCon.append(pm.pointConstraint(ctrl, self.sel[i], maintainOffset=True))
            elif not self.offsetButtons['point'].isChecked() and pm.getAttr(self.sel[i].translate) ==\
                    pm.getAttr(ctrl.translate):
                self.ctrlPointCon.append(pm.pointConstraint(ctrl, self.sel[i], maintainOffset=False))
            else:
                selection.append(self.sel[i])
                self.ctrlPointCon.append(pm.pointConstraint(ctrl, self.sel[i], maintainOffset=True))
        self._notifyNoMatch(selection)

    def _delPointConstraints(self):
        try:
            pm.delete(self.ctrlPointCon[0:])
            self.ctrlPointCon.clear()
        except AttributeError as a:
            print(a)

        for i, ctrl in enumerate(self.ctrls):
            pm.setAttr(self.sel[i].translate, self.selOrigTrans[self.sel[i]])
            pm.setAttr(ctrl.translate, 0, 0, 0)

    def _orientConstrain(self):
        selection = []
        for i, ctrl in enumerate(self.ctrls):
            if self.offsetButtons['orient'].isChecked():
                self.ctrlOrientCon.append(pm.orientConstraint(ctrl, self.sel[i], maintainOffset=True))
            elif not self.offsetButtons['orient'].isChecked() and pm.getAttr(self.sel[i].rotate) ==\
                    pm.getAttr(ctrl.rotate):
                self.ctrlOrientCon.append(pm.orientConstraint(ctrl, self.sel[i], maintainOffset=False))
            else:
                selection.append(self.sel[i])
                self.ctrlOrientCon.append(pm.orientConstraint(ctrl, self.sel[i], maintainOffset=True))
        self._notifyNoMatch(selection)

    def _delOrientConstraints(self):
        try:
            pm.delete(self.ctrlOrientCon[0:])
            self.ctrlOrientCon.clear()
        except AttributeError as a:
            print(a)

        for i, ctrl in enumerate(self.ctrls):
            pm.setAttr(self.sel[i].rotate, self.selOrigRot[self.sel[i]])
            pm.setAttr(ctrl.rotate, 0, 0, 0)

    def _scaleConstrain(self):
        selection = []
        for i, ctrl in enumerate(self.ctrls):
            if self.offsetButtons['scale'].isChecked():
                self.ctrlScaleCon.append(pm.scaleConstraint(ctrl, self.sel[i], maintainOffset=True))
            elif not self.offsetButtons['scale'].isChecked() and pm.getAttr(self.sel[i].scale) ==\
                    pm.getAttr(ctrl.scale):
                self.ctrlScaleCon.append(pm.scaleConstraint(ctrl, self.sel[i], maintainOffset=False))
            else:
                selection.append(self.sel[i])
                self.ctrlScaleCon.append(pm.scaleConstraint(ctrl, self.sel[i], maintainOffset=True))
        self._notifyNoMatch(selection)

    def _delScaleConstraints(self):
        try:
            pm.delete(self.ctrlScaleCon[0:])
            self.ctrlScaleCon.clear()
        except AttributeError as a:
            print(a)

        for i, ctrl in enumerate(self.ctrls):
            pm.setAttr(self.sel[i].scale, self.selOrigScale[self.sel[i]])
            pm.setAttr(ctrl.scale, 1, 1, 1)

    def _parentConstrain(self):
        selection = []
        for i, ctrl in enumerate(self.ctrls):
            if self.offsetButtons['parent'].isChecked():
                self.ctrlParentCon.append(pm.parentConstraint(ctrl, self.sel[i], maintainOffset=True))
            elif not self.offsetButtons['parent'].isChecked() \
                    and pm.getAttr(self.sel[i].translate) == pm.getAttr(ctrl.translate) \
                    and pm.getAttr(self.sel[i].rotate) == pm.getAttr(ctrl.rotate):
                self.ctrlParentCon.append(pm.parentConstraint(ctrl, self.sel[i], maintainOffset=False))
            else:
                selection.append(self.sel[i])
                self.ctrlParentCon.append(pm.parentConstraint(ctrl, self.sel[i], maintainOffset=True))
        self._notifyNoMatch(selection)

    def _delParentConstraints(self):
        try:
            pm.delete(self.ctrlParentCon[0:])
            self.ctrlParentCon.clear()
        except AttributeError as a:
            print(a)
        for i, ctrl in enumerate(self.ctrls):
            pm.setAttr(self.sel[i].translate, self.selOrigTrans[self.sel[i]])
            pm.setAttr(self.sel[i].rotate, self.selOrigRot[self.sel[i]])
            pm.setAttr(ctrl.translate, 0, 0, 0)
            pm.setAttr(ctrl.rotate, 0, 0, 0)

    def _notifyNoMatch(self, selection):
        msg = "Some attributes do not match on: \n"
        for i in selection:
            msg += str(i) + "\n"
        msg += "Constrained them WITH offset"
        pm.confirmDialog(title="Attributes don't match.", message=msg)

    def _finish(self):
        for ctrl in self.ctrls:
            pm.delete(ctrl, ch=True)
        self._flushCtrls()


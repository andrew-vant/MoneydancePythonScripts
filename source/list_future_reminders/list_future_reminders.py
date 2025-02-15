#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# list_future_reminders.py (build: 1018)

###############################################################################
# MIT License
#
# Copyright (c) 2021-2022 Stuart Beesley - StuWareSoftSystems
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
###############################################################################

# Build: 1000 - Initial release - cribbed from extract_reminders_csv (for @CanSaver)
# Build: 1001 - Enhancement to prevent duplicate extension running.....
# Build: 1002 - Tweak to block old MD versions...
# Build: 1003 - tweak to common code for launch detection
# Build: 1004 - tweak to common code (minor, non-functional change)
# Build: 1005 - Switch to SwingUtilities.invokeLater() rather than Thread(); other small internal tweaks; fix toolbar location on older versions
# build: 1005 - Build 3051 of Moneydance... fix references to moneydance_* variables;
# build: 1006 - Build 3056 'deal' with the Python loader changes..
# build: 1007 - Build 3056 Utilise .unload() method...
# build: 1008 - Common code tweaks
# build: 1009 - Small cosmetic tweaks to confirm to IK design standards
# build: 1010 - Fixed pickle.dump/load common code to work properly cross-platform (e.g. Windows to Mac) by (stripping \r when needed)
# build: 1010 - Common code tweaks
# build: 1011 - Added printing support
# build: 1012 - Common code tweaks; Tweaked colors for Dark themes and to be more MD 'compatible'
# build: 1013 - Common code tweaks; Flat Dark Theme
# build: 1014 - Common code tweaks
# build: 1015 - Common code tweaks; Fix JMenu()s - remove <html> tags (affects colors on older Macs); newer MyJFrame.dispose()
# build: 1015 - Tweaked date format to use MD Preferences set by user
# build: 1016 - Added <PREVIEW> title to main JFrame if preview build detected...
# Build: 1016 - Added <html> tags to JMenu() titles to stop becoming invisible when mouse hovers
# build: 1016 - Eliminated common code globals :->
# build: 1016 - Added QuickSearch box/filter; also pop up record next reminder windows when double-clicked. Right-click edit reminder
# build: 1016 - Chucked in the kitchen sink too. Added Account Name.. Added Reminder Listeners, dumped the 'old' stuff...
# build: 1016 - Chucked in the kitchen sink too. Added Account Name.. Added Reminder Listeners, dumped the 'old' stuff...
# build: 1016 - lAllowEscapeExitApp_SWSS to allow/block escape from exiting the app; Tweaked the JMenuBar() to say "MENU"
# build: 1016 - pushing .setEscapeKeyCancels(True) to the popup dialogs....
# build: 1016 - added showRawItemDetails() to popup right-click menu....
# build: 1017 - Fixed calls to .setEscapeKeyCancels() on older MD versions
# build: 1018 - Added right-click popup to allow deletion of Reminder...; Search field grabs focus too..
# build: 1018 - FileDialog() (refer: java.desktop/sun/lwawt/macosx/CFileDialog.java) seems to no longer use "com.apple.macos.use-file-dialog-packages" in favor of "apple.awt.use-file-dialog-packages" since Monterrey...
# build: 1018 - Common code
# build: 1018 - Common code update - remove Decimal Grouping Character - not necessary to collect and crashes on newer Java versions (> byte)

# Displays Moneydance future reminders

# todo - Add the fields from extract_data:extract_reminders, with options future on/off, hide / select columns etc

# CUSTOMIZE AND COPY THIS ##############################################################################################
# CUSTOMIZE AND COPY THIS ##############################################################################################
# CUSTOMIZE AND COPY THIS ##############################################################################################

# SET THESE LINES
myModuleID = u"list_future_reminders"
version_build = "1018"
MIN_BUILD_REQD = 1904                                               # Check for builds less than 1904 / version < 2019.4
_I_CAN_RUN_AS_MONEYBOT_SCRIPT = True

if u"debug" in globals():
    global debug
else:
    debug = False
global list_future_reminders_frame_
# SET LINES ABOVE ^^^^

# COPY >> START
global moneydance, moneydance_ui, moneydance_extension_loader, moneydance_extension_parameter
MD_REF = moneydance             # Make my own copy of reference as MD removes it once main thread ends.. Don't use/hold on to _data variable
MD_REF_UI = moneydance_ui       # Necessary as calls to .getUI() will try to load UI if None - we don't want this....
if MD_REF is None: raise Exception("CRITICAL ERROR - moneydance object/variable is None?")
if u"moneydance_extension_loader" in globals():
    MD_EXTENSION_LOADER = moneydance_extension_loader
else:
    MD_EXTENSION_LOADER = None

from java.lang import System, Runnable
from javax.swing import JFrame, SwingUtilities, SwingWorker
from java.awt.event import WindowEvent

class QuickAbortThisScriptException(Exception): pass

class MyJFrame(JFrame):

    def __init__(self, frameTitle=None):
        super(JFrame, self).__init__(frameTitle)
        self.disposing = False
        self.myJFrameVersion = 3
        self.isActiveInMoneydance = False
        self.isRunTimeExtension = False
        self.MoneydanceAppListener = None
        self.HomePageViewObj = None

    def dispose(self):
        # This removes all content as VAqua retains the JFrame reference in memory...
        if self.disposing: return
        try:
            self.disposing = True
            self.removeAll()
            if self.getJMenuBar() is not None: self.setJMenuBar(None)
            super(self.__class__, self).dispose()
        except:
            _msg = "%s: ERROR DISPOSING OF FRAME: %s\n" %(myModuleID, self)
            print(_msg); System.err.write(_msg)
        finally:
            self.disposing = False

class GenericWindowClosingRunnable(Runnable):

    def __init__(self, theFrame):
        self.theFrame = theFrame

    def run(self):
        self.theFrame.setVisible(False)
        self.theFrame.dispatchEvent(WindowEvent(self.theFrame, WindowEvent.WINDOW_CLOSING))

class GenericDisposeRunnable(Runnable):
    def __init__(self, theFrame):
        self.theFrame = theFrame

    def run(self):
        self.theFrame.setVisible(False)
        self.theFrame.dispose()

class GenericVisibleRunnable(Runnable):
    def __init__(self, theFrame, lVisible=True, lToFront=False):
        self.theFrame = theFrame
        self.lVisible = lVisible
        self.lToFront = lToFront

    def run(self):
        self.theFrame.setVisible(self.lVisible)
        if self.lVisible and self.lToFront:
            if self.theFrame.getExtendedState() == JFrame.ICONIFIED:
                self.theFrame.setExtendedState(JFrame.NORMAL)
            self.theFrame.toFront()

def getMyJFrame(moduleName):
    try:
        frames = JFrame.getFrames()
        for fr in frames:
            if (fr.getName().lower().startswith(u"%s_main" %moduleName)
                    and (type(fr).__name__ == MyJFrame.__name__ or type(fr).__name__ == u"MyCOAWindow")  # isinstance() won't work across namespaces
                    and fr.isActiveInMoneydance):
                _msg = "%s: Found live frame: %s (MyJFrame() version: %s)\n" %(myModuleID,fr.getName(),fr.myJFrameVersion)
                print(_msg); System.err.write(_msg)
                if fr.isRunTimeExtension:
                    _msg = "%s: ... and this is a run-time self-installed extension too...\n" %(myModuleID)
                    print(_msg); System.err.write(_msg)
                return fr
    except:
        _msg = "%s: Critical error in getMyJFrame(); caught and ignoring...!\n" %(myModuleID)
        print(_msg); System.err.write(_msg)
    return None


frameToResurrect = None
try:
    # So we check own namespace first for same frame variable...
    if (u"%s_frame_"%myModuleID in globals()
            and (isinstance(list_future_reminders_frame_, MyJFrame)                 # EDIT THIS
                 or type(list_future_reminders_frame_).__name__ == u"MyCOAWindow")  # EDIT THIS
            and list_future_reminders_frame_.isActiveInMoneydance):                 # EDIT THIS
        frameToResurrect = list_future_reminders_frame_                             # EDIT THIS
    else:
        # Now check all frames in the JVM...
        getFr = getMyJFrame( myModuleID )
        if getFr is not None:
            frameToResurrect = getFr
        del getFr
except:
    msg = "%s: Critical error checking frameToResurrect(1); caught and ignoring...!\n" %(myModuleID)
    print(msg); System.err.write(msg)

# ############################
# Trap startup conditions here.... The 'if's pass through to oblivion (and thus a clean exit)... The final 'else' actually runs the script
if int(MD_REF.getBuild()) < MIN_BUILD_REQD:     # Check for builds less than 1904 (version 2019.4) or build 3056 accordingly
    msg = "SORRY YOUR MONEYDANCE VERSION IS TOO OLD FOR THIS SCRIPT/EXTENSION (min build %s required)" %(MIN_BUILD_REQD)
    print(msg); System.err.write(msg)
    try:    MD_REF_UI.showInfoMessage(msg)
    except: raise Exception(msg)

elif frameToResurrect and frameToResurrect.isRunTimeExtension:
    msg = "%s: Sorry - runtime extension already running. Please uninstall/reinstall properly. Must be on build: %s onwards. Now exiting script!\n" %(myModuleID, MIN_BUILD_REQD)
    print(msg); System.err.write(msg)
    try: MD_REF_UI.showInfoMessage(msg)
    except: raise Exception(msg)

elif not _I_CAN_RUN_AS_MONEYBOT_SCRIPT and u"__file__" in globals():
    msg = "%s: Sorry - this script cannot be run in Moneybot console. Please install mxt and run extension properly. Must be on build: %s onwards. Now exiting script!\n" %(myModuleID, MIN_BUILD_REQD)
    print(msg); System.err.write(msg)
    try: MD_REF_UI.showInfoMessage(msg)
    except: raise Exception(msg)

elif not _I_CAN_RUN_AS_MONEYBOT_SCRIPT and u"moneydance_extension_loader" not in globals():
    msg = "%s: Error - moneydance_extension_loader seems to be missing? Must be on build: %s onwards. Now exiting script!\n" %(myModuleID, MIN_BUILD_REQD)
    print(msg); System.err.write(msg)
    try: MD_REF_UI.showInfoMessage(msg)
    except: raise Exception(msg)

elif frameToResurrect:  # and it's active too...
    try:
        msg = "%s: Detected that %s is already running..... Attempting to resurrect..\n" %(myModuleID, myModuleID)
        print(msg); System.err.write(msg)
        SwingUtilities.invokeLater(GenericVisibleRunnable(frameToResurrect, True, True))
    except:
        msg  = "%s: Failed to resurrect main Frame.. This duplicate Script/extension is now terminating.....\n" %(myModuleID)
        print(msg); System.err.write(msg)
        raise Exception(msg)

else:
    del frameToResurrect
    msg = "%s: Startup conditions passed (and no other instances of this program detected). Now executing....\n" %(myModuleID)
    print(msg); System.err.write(msg)

    # COMMON IMPORTS #######################################################################################################
    # COMMON IMPORTS #######################################################################################################
    # COMMON IMPORTS #######################################################################################################

    # NOTE: As of MD2022(4040) python.getSystemState().setdefaultencoding("utf8") is called on the python interpreter at launch...
    import sys
    reload(sys)  # Dirty hack to eliminate UTF-8 coding errors
    sys.setdefaultencoding('utf8')  # Dirty hack to eliminate UTF-8 coding errors. Without this str() fails on unicode strings...

    import os
    import os.path
    import codecs
    import inspect
    import pickle
    import platform
    import csv
    import datetime
    import traceback
    import subprocess

    from org.python.core.util import FileUtil

    from com.moneydance.util import Platform
    from com.moneydance.awt import JTextPanel, GridC, JDateField
    from com.moneydance.apps.md.view.gui import MDImages

    from com.infinitekind.util import DateUtil, CustomDateFormat, StringUtils

    from com.infinitekind.moneydance.model import *
    from com.infinitekind.moneydance.model import AccountUtil, AcctFilter, CurrencyType, CurrencyUtil
    from com.infinitekind.moneydance.model import Account, Reminder, ParentTxn, SplitTxn, TxnSearch, InvestUtil, TxnUtil

    from com.moneydance.apps.md.controller import AccountBookWrapper
    from com.infinitekind.moneydance.model import AccountBook

    from javax.swing import JButton, JScrollPane, WindowConstants, JLabel, JPanel, JComponent, KeyStroke, JDialog, JComboBox
    from javax.swing import JOptionPane, JTextArea, JMenuBar, JMenu, JMenuItem, AbstractAction, JCheckBoxMenuItem, JFileChooser
    from javax.swing import JTextField, JPasswordField, Box, UIManager, JTable, JCheckBox, JRadioButton, ButtonGroup
    from javax.swing.text import PlainDocument
    from javax.swing.border import EmptyBorder
    from javax.swing.filechooser import FileFilter

    exec("from javax.print import attribute")       # IntelliJ doesnt like the use of 'print' (as it's a keyword). Messy, but hey!
    exec("from java.awt.print import PrinterJob")   # IntelliJ doesnt like the use of 'print' (as it's a keyword). Messy, but hey!
    global attribute, PrinterJob

    from java.awt.datatransfer import StringSelection
    from javax.swing.text import DefaultHighlighter
    from javax.swing.event import AncestorListener

    from java.awt import Color, Dimension, FileDialog, FlowLayout, Toolkit, Font, GridBagLayout, GridLayout
    from java.awt import BorderLayout, Dialog, Insets, Point
    from java.awt.event import KeyEvent, WindowAdapter, InputEvent
    from java.util import Date, Locale

    from java.text import DecimalFormat, SimpleDateFormat, MessageFormat
    from java.util import Calendar, ArrayList
    from java.lang import Thread, IllegalArgumentException, String, Integer, Long
    from java.lang import Double, Math, Character, NoSuchFieldException, NoSuchMethodException, Boolean
    from java.lang.reflect import Modifier
    from java.io import FileNotFoundException, FilenameFilter, File, FileInputStream, FileOutputStream, IOException, StringReader
    from java.io import BufferedReader, InputStreamReader
    from java.nio.charset import Charset
    if isinstance(None, (JDateField,CurrencyUtil,Reminder,ParentTxn,SplitTxn,TxnSearch, JComboBox, JCheckBox,
                         AccountBook, AccountBookWrapper, Long, Integer, Boolean,
                         JTextArea, JMenuBar, JMenu, JMenuItem, JCheckBoxMenuItem, JFileChooser, JDialog,
                         JButton, FlowLayout, InputEvent, ArrayList, File, IOException, StringReader, BufferedReader,
                         InputStreamReader, Dialog, JTable, BorderLayout, Double, InvestUtil, JRadioButton, ButtonGroup,
                         AccountUtil, AcctFilter, CurrencyType, Account, TxnUtil, JScrollPane, WindowConstants, JFrame,
                         JComponent, KeyStroke, AbstractAction, UIManager, Color, Dimension, Toolkit, KeyEvent, GridLayout,
                         WindowAdapter, CustomDateFormat, SimpleDateFormat, Insets, FileDialog, Thread, SwingWorker)): pass
    if codecs.BOM_UTF8 is not None: pass
    if csv.QUOTE_ALL is not None: pass
    if datetime.MINYEAR is not None: pass
    if Math.max(1,1): pass
    # END COMMON IMPORTS ###################################################################################################

    # COMMON GLOBALS #######################################################################################################
    # All common globals have now been eliminated :->
    # END COMMON GLOBALS ###################################################################################################
    # COPY >> END

    # SET THESE VARIABLES FOR ALL SCRIPTS ##################################################################################
    if "GlobalVars" in globals():   # Prevent wiping if 'buddy' extension - like Toolbox - is running too...
        global GlobalVars
    else:
        class GlobalVars:        # Started using this method for storing global variables from August 2021
            CONTEXT = MD_REF
            defaultPrintService = None
            defaultPrinterAttributes = None
            defaultPrintFontSize = None
            defaultPrintLandscape = None
            defaultDPI = 72     # NOTE: 72dpi is Java2D default for everything; just go with it. No easy way to change
            STATUS_LABEL = None
            DARK_GREEN = Color(0, 192, 0)
            resetPickleParameters = False
            decimalCharSep = "."
            lGlobalErrorDetected = False
            MYPYTHON_DOWNLOAD_URL = "https://yogi1967.github.io/MoneydancePythonScripts/"
            i_am_an_extension_so_run_headless = None
            parametersLoadedFromFile = {}
            thisScriptName = None
            MD_MDPLUS_BUILD = 4040
            MD_ALERTCONTROLLER_BUILD = 4077
            def __init__(self): pass    # Leave empty

            class Strings:
                def __init__(self): pass    # Leave empty

    GlobalVars.thisScriptName = u"%s.py(Extension)" %(myModuleID)

    # END SET THESE VARIABLES FOR ALL SCRIPTS ##############################################################################

    # >>> THIS SCRIPT'S IMPORTS ############################################################################################
    import threading
    from java.awt.event import MouseAdapter
    from java.util import Comparator
    from javax.swing import SortOrder, ListSelectionModel, JPopupMenu
    from javax.swing.table import DefaultTableCellRenderer, DefaultTableModel, TableRowSorter
    from javax.swing.border import CompoundBorder, MatteBorder
    from javax.swing.event import TableColumnModelListener, ListSelectionListener, DocumentListener
    from java.lang import Number
    from com.infinitekind.util import StringUtils
    from com.moneydance.apps.md.controller import AppEventListener
    from com.moneydance.awt import QuickSearchField
    from java.awt.event import FocusAdapter
    from javax.swing import RowFilter

    # from com.moneydance.apps.md.view.gui import EditRemindersWindow
    from com.moneydance.apps.md.view.gui import LoanTxnReminderNotificationWindow
    from com.moneydance.apps.md.view.gui import TxnReminderNotificationWindow
    from com.moneydance.apps.md.view.gui import BasicReminderNotificationWindow

    from com.moneydance.apps.md.view.gui import LoanTxnReminderInfoWindow
    from com.moneydance.apps.md.view.gui import TxnReminderInfoWindow
    from com.moneydance.apps.md.view.gui import BasicReminderInfoWindow
    from com.infinitekind.moneydance.model import ReminderListener
    # from com.moneydance.apps.md.view.gui import MoneydanceGUI

    exec("from java.awt.print import Book")     # IntelliJ doesnt like the use of 'print' (as it's a keyword). Messy, but hey!
    global Book     # Keep this here for above import
    # >>> END THIS SCRIPT'S IMPORTS ########################################################################################

    # >>> THIS SCRIPT'S GLOBALS ############################################################################################

    # Saved to parameters file - common
    global lAllowEscapeExitApp_SWSS

    # Saved to parameters file
    global __list_future_reminders, _column_widths_LFR, daysToLookForward_LFR

    # Other used by this program
    GlobalVars.saveStatusLabel = None
    GlobalVars.md_dateFormat = None

    # >>> END THIS SCRIPT'S GLOBALS ############################################################################################

    # Set programmatic defaults/parameters for filters HERE.... Saved Parameters will override these now
    # NOTE: You  can override in the pop-up screen
    _column_widths_LFR = []                                                                                          	# noqa
    daysToLookForward_LFR = 365                                                                                         # noqa
    lAllowEscapeExitApp_SWSS = True                                                                                     # noqa
    # >>> END THIS SCRIPT'S GLOBALS ############################################################################################

    # COPY >> START
    # COMMON CODE ######################################################################################################
    # COMMON CODE ################# VERSION 108 ########################################################################
    # COMMON CODE ######################################################################################################
    GlobalVars.i_am_an_extension_so_run_headless = False
    try:
        GlobalVars.thisScriptName = os.path.basename(__file__)
    except:
        GlobalVars.i_am_an_extension_so_run_headless = True

    scriptExit = """
----------------------------------------------------------------------------------------------------------------------
Thank you for using %s!
The author has other useful Extensions / Moneybot Python scripts available...:

Extension (.mxt) format only:
Toolbox:                                View Moneydance settings, diagnostics, fix issues, change settings and much more
                                        + Extension Menus: Total selected transactions & Move Investment Transactions
Custom Balances (net_account_balances): Summary Page (HomePage) widget. Display the total of selected Account Balances

Extension (.mxt) and Script (.py) Versions available:
Extract Data:                           Extract various data to screen and/or csv.. Consolidation of:
- stockglance2020                       View summary of Securities/Stocks on screen, total by Security, export to csv 
- extract_reminders_csv                 View reminders on screen, edit if required, extract all to csv
- extract_currency_history_csv          Extract currency history to csv
- extract_investment_transactions_csv   Extract investment transactions to csv
- extract_account_registers_csv         Extract Account Register(s) to csv along with any attachments

List Future Reminders:                  View future reminders on screen. Allows you to set the days to look forward
Accounts Categories Mega Search Window: Combines MD Menu> Tools>Accounts/Categories and adds Quick Search box/capability
Security Performance Graph:             Graphs selected securities, calculating relative price performance as percentage

A collection of useful ad-hoc scripts (zip file)
useful_scripts:                         Just unzip and select the script you want for the task at hand...

Visit: %s (Author's site)
----------------------------------------------------------------------------------------------------------------------
""" %(GlobalVars.thisScriptName, GlobalVars.MYPYTHON_DOWNLOAD_URL)

    def cleanup_references():
        global MD_REF, MD_REF_UI, MD_EXTENSION_LOADER
        # myPrint("DB","About to delete reference to MD_REF, MD_REF_UI and MD_EXTENSION_LOADER....!")
        # del MD_REF, MD_REF_UI, MD_EXTENSION_LOADER

    def load_text_from_stream_file(theStream):
        myPrint("DB", "In ", inspect.currentframe().f_code.co_name, "()")

        cs = Charset.forName("UTF-8")

        istream = theStream

        if not istream:
            myPrint("B","... Error - the input stream is None")
            return "<NONE>"

        fileContents = ""
        istr = bufr = None
        try:
            istr = InputStreamReader(istream, cs)
            bufr = BufferedReader(istr)
            while True:
                line = bufr.readLine()
                if line is not None:
                    line += "\n"                   # not very efficient - should convert this to "\n".join() to contents
                    fileContents+=line
                    continue
                break
            fileContents+="\n<END>"
        except:
            myPrint("B", "ERROR reading from input stream... ")
            dump_sys_error_to_md_console_and_errorlog()

        try: bufr.close()
        except: pass

        try: istr.close()
        except: pass

        try: istream.close()
        except: pass

        myPrint("DB", "Exiting ", inspect.currentframe().f_code.co_name, "()")

        return fileContents

    # P=Display on Python Console, J=Display on MD (Java) Console Error Log, B=Both, D=If Debug Only print, DB=print both
    def myPrint(where, *args):
        if where[0] == "D" and not debug: return

        try:
            printString = ""
            for what in args:
                printString += "%s " %what
            printString = printString.strip()

            if where == "P" or where == "B" or where[0] == "D":
                if not GlobalVars.i_am_an_extension_so_run_headless:
                    try:
                        print(printString)
                    except:
                        print("Error writing to screen...")
                        dump_sys_error_to_md_console_and_errorlog()

            if where == "J" or where == "B" or where == "DB":
                dt = datetime.datetime.now().strftime("%Y/%m/%d-%H:%M:%S")
                try:
                    System.err.write(GlobalVars.thisScriptName + ":" + dt + ": ")
                    System.err.write(printString)
                    System.err.write("\n")
                except:
                    System.err.write(GlobalVars.thisScriptName + ":" + dt + ": "+"Error writing to console")
                    dump_sys_error_to_md_console_and_errorlog()

        except IllegalArgumentException:
            myPrint("B","ERROR - Probably on a multi-byte character..... Will ignore as code should just continue (PLEASE REPORT TO DEVELOPER).....")
            dump_sys_error_to_md_console_and_errorlog()

        return

    def dump_sys_error_to_md_console_and_errorlog(lReturnText=False):

        tb = traceback.format_exc()
        trace = traceback.format_stack()
        theText =  ".\n" \
                   "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\n" \
                   "@@@@@ Unexpected error caught!\n".upper()
        theText += tb
        for trace_line in trace: theText += trace_line
        theText += "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\n"
        myPrint("B", theText)
        if lReturnText: return theText
        return

    def safeStr(_theText): return ("%s" %(_theText))

    def pad(theText, theLength, padChar=u" "):
        if not isinstance(theText, (unicode, str)): theText = safeStr(theText)
        theText = theText[:theLength].ljust(theLength, padChar)
        return theText

    def rpad(theText, theLength, padChar=u" "):
        if not isinstance(theText, (unicode, str)): theText = safeStr(theText)
        theText = theText[:theLength].rjust(theLength, padChar)
        return theText

    def cpad(theText, theLength, padChar=u" "):
        if not isinstance(theText, (unicode, str)): theText = safeStr(theText)
        if len(theText) >= theLength: return theText[:theLength]
        padLength = int((theLength - len(theText)) / 2)
        theText = theText[:theLength]
        theText = ((padChar * padLength)+theText+(padChar * padLength))[:theLength]
        return theText

    myPrint("B", GlobalVars.thisScriptName, ": Python Script Initialising.......", "Build:", version_build)

    def getMonoFont():
        try:
            theFont = MD_REF.getUI().getFonts().code
            # if debug: myPrint("B","Success setting Font set to Moneydance code: %s" %theFont)
        except:
            theFont = Font("monospaced", Font.PLAIN, 15)
            if debug: myPrint("B","Failed to Font set to Moneydance code - So using: %s" %theFont)

        return theFont

    def isOSXVersionAtLeast(compareVersion):
        # type: (basestring) -> bool
        """Pass a string in the format 'x.x.x'. Will check that this MacOSX version is at least that version. The 3rd micro number is optional"""

        try:
            if not Platform.isOSX(): return False

            def convertVersion(convertString):
                _os_major = _os_minor = _os_micro = 0
                _versionNumbers = []

                for versionPart in StringUtils.splitIntoList(convertString, '.'):
                    strippedPart = StringUtils.stripNonNumbers(versionPart, '.')
                    if (StringUtils.isInteger(strippedPart)):
                        _versionNumbers.append(Integer.valueOf(Integer.parseInt(strippedPart)))
                    else:
                        _versionNumbers.append(0)

                if len(_versionNumbers) >= 1: _os_major = max(0, _versionNumbers[0])
                if len(_versionNumbers) >= 2: _os_minor = max(0, _versionNumbers[1])
                if len(_versionNumbers) >= 3: _os_micro = max(0, _versionNumbers[2])

                return _os_major, _os_minor, _os_micro


            os_major, os_minor, os_micro = convertVersion(System.getProperty("os.version", "0.0.0"))
            myPrint("DB", "MacOS Version number(s): %s.%s.%s" %(os_major, os_minor, os_micro))

            if not isinstance(compareVersion, basestring) or len(compareVersion) < 1:
                myPrint("B", "ERROR: Invalid compareVersion of '%s' passed - returning False" %(compareVersion))
                return False

            chk_os_major, chk_os_minor, chk_os_micro = convertVersion(compareVersion)
            myPrint("DB", "Comparing against Version(s): %s.%s.%s" %(chk_os_major, chk_os_minor, chk_os_micro))


            if os_major < chk_os_major: return False
            if os_major > chk_os_major: return True

            if os_minor < chk_os_minor: return False
            if os_minor > chk_os_minor: return True

            if os_micro < chk_os_micro: return False
            return True

        except:
            myPrint("B", "ERROR: isOSXVersionAtLeast() failed - returning False")
            dump_sys_error_to_md_console_and_errorlog()
            return False

    def isOSXVersionCheetahOrLater():       return isOSXVersionAtLeast("10.0")
    def isOSXVersionPumaOrLater():          return isOSXVersionAtLeast("10.1")
    def isOSXVersionJaguarOrLater():        return isOSXVersionAtLeast("10.2")
    def isOSXVersionPantherOrLater():       return isOSXVersionAtLeast("10.3")
    def isOSXVersionTigerOrLater():         return isOSXVersionAtLeast("10.4")
    def isOSXVersionLeopardOrLater():       return isOSXVersionAtLeast("10.5")
    def isOSXVersionSnowLeopardOrLater():   return isOSXVersionAtLeast("10.6")
    def isOSXVersionLionOrLater():          return isOSXVersionAtLeast("10.7")
    def isOSXVersionMountainLionOrLater():  return isOSXVersionAtLeast("10.8")
    def isOSXVersionMavericksOrLater():     return isOSXVersionAtLeast("10.9")
    def isOSXVersionYosemiteOrLater():      return isOSXVersionAtLeast("10.10")
    def isOSXVersionElCapitanOrLater():     return isOSXVersionAtLeast("10.11")
    def isOSXVersionSierraOrLater():        return isOSXVersionAtLeast("10.12")
    def isOSXVersionHighSierraOrLater():    return isOSXVersionAtLeast("10.13")
    def isOSXVersionMojaveOrLater():        return isOSXVersionAtLeast("10.14")
    def isOSXVersionCatalinaOrLater():      return isOSXVersionAtLeast("10.15")
    def isOSXVersionBigSurOrLater():        return isOSXVersionAtLeast("10.16")  # BigSur is officially 11.0, but started at 10.16
    def isOSXVersionMontereyOrLater():      return isOSXVersionAtLeast("12.0")
    def isOSXVersionVenturaOrLater():       return isOSXVersionAtLeast("13.0")

    def get_home_dir():
        homeDir = None

        # noinspection PyBroadException
        try:
            if Platform.isOSX():
                homeDir = System.getProperty(u"UserHome")  # On a Mac in a Java VM, the homedir is hidden
            else:
                # homeDir = System.getProperty("user.home")
                homeDir = os.path.expanduser(u"~")  # Should work on Unix and Windows
                if homeDir is None or homeDir == u"":
                    homeDir = System.getProperty(u"user.home")
                if homeDir is None or homeDir == u"":
                    homeDir = os.environ.get(u"HOMEPATH")
        except:
            pass

        if homeDir is None or homeDir == u"":
            homeDir = MD_REF.getCurrentAccountBook().getRootFolder().getParent()  # Better than nothing!

        if homeDir is None or homeDir == u"":
            homeDir = u""

        myPrint("DB", "Home Directory detected...:", homeDir)
        return homeDir

    def getDecimalPoint():
        decimalFormat = DecimalFormat.getInstance()
        # noinspection PyUnresolvedReferences
        decimalSymbols = decimalFormat.getDecimalFormatSymbols()

        try:
            _decimalCharSep = decimalSymbols.getDecimalSeparator()
            myPrint(u"D",u"Decimal Point Character: %s" %(_decimalCharSep))
            return _decimalCharSep
        except:
            myPrint(u"B",u"Error in getDecimalPoint() routine....?")
            dump_sys_error_to_md_console_and_errorlog()
        return u"error"


    GlobalVars.decimalCharSep = getDecimalPoint()


    def isMacDarkModeDetected():
        darkResponse = "LIGHT"
        if Platform.isOSX():
            try:
                darkResponse = subprocess.check_output("defaults read -g AppleInterfaceStyle", shell=True)
                darkResponse = darkResponse.strip().lower()
            except: pass
        return ("dark" in darkResponse)

    def isMDThemeDark():
        try:
            currentTheme = MD_REF.getUI().getCurrentTheme()
            try:
                if currentTheme.isSystemDark(): return True     # NOTE: Only VAQua has isSystemDark()
            except: pass
            if "dark" in currentTheme.getThemeID().lower(): return True
            if isMDThemeFlatDark(): return True
            if isMDThemeDarcula(): return True
        except: pass
        return False

    def isMDThemeDarcula():
        try:
            currentTheme = MD_REF.getUI().getCurrentTheme()
            if isMDThemeFlatDark(): return False                    # Flat Dark pretends to be Darcula!
            if "darcula" in currentTheme.getThemeID(): return True
        except: pass
        return False

    def isMDThemeCustomizable():
        try:
            currentTheme = MD_REF.getUI().getCurrentTheme()
            if currentTheme.isCustomizable(): return True
        except: pass
        return False

    def isMDThemeHighContrast():
        try:
            currentTheme = MD_REF.getUI().getCurrentTheme()
            if "high_contrast" in currentTheme.getThemeID(): return True
        except: pass
        return False

    def isMDThemeDefault():
        try:
            currentTheme = MD_REF.getUI().getCurrentTheme()
            if "default" in currentTheme.getThemeID(): return True
        except: pass
        return False

    def isMDThemeClassic():
        try:
            currentTheme = MD_REF.getUI().getCurrentTheme()
            if "classic" in currentTheme.getThemeID(): return True
        except: pass
        return False

    def isMDThemeSolarizedLight():
        try:
            currentTheme = MD_REF.getUI().getCurrentTheme()
            if "solarized_light" in currentTheme.getThemeID(): return True
        except: pass
        return False

    def isMDThemeSolarizedDark():
        try:
            currentTheme = MD_REF.getUI().getCurrentTheme()
            if "solarized_dark" in currentTheme.getThemeID(): return True
        except: pass
        return False

    def isMDThemeFlatDark():
        try:
            currentTheme = MD_REF.getUI().getCurrentTheme()
            if "flat dark" in currentTheme.toString().lower(): return True
        except: pass
        return False

    def isMDThemeVAQua():
        if Platform.isOSX():
            try:
                currentTheme = MD_REF.getUI().getCurrentTheme()
                if ".vaqua" in safeStr(currentTheme.getClass()).lower(): return True
            except: pass
        return False

    def isIntelX86_32bit():
        """Detect Intel x86 32bit system"""
        return String(System.getProperty("os.arch", "null").strip()).toLowerCase(Locale.ROOT) == "x86"

    def getMDIcon(startingIcon=None, lAlwaysGetIcon=False):
        if lAlwaysGetIcon or isIntelX86_32bit():
            return MD_REF.getUI().getIcon("/com/moneydance/apps/md/view/gui/glyphs/appicon_64.png")
        return startingIcon

    # JOptionPane.DEFAULT_OPTION, JOptionPane.YES_NO_OPTION, JOptionPane.YES_NO_CANCEL_OPTION, JOptionPane.OK_CANCEL_OPTION
    # JOptionPane.ERROR_MESSAGE, JOptionPane.INFORMATION_MESSAGE, JOptionPane.WARNING_MESSAGE, JOptionPane.QUESTION_MESSAGE, JOptionPane.PLAIN_MESSAGE

    # Copies MD_REF.getUI().showInfoMessage (but a newer version now exists in MD internal code)
    def myPopupInformationBox(theParent=None, theMessage="What no message?!", theTitle="Info", theMessageType=JOptionPane.INFORMATION_MESSAGE):

        if theParent is None and (theMessageType == JOptionPane.PLAIN_MESSAGE or theMessageType == JOptionPane.INFORMATION_MESSAGE):
            icon = getMDIcon(lAlwaysGetIcon=True)
        else:
            icon = getMDIcon(None)
        JOptionPane.showMessageDialog(theParent, JTextPanel(theMessage), theTitle, theMessageType, icon)

    def wrapLines(message, numChars=40):
        charCount = 0
        result=""
        for ch in message:
            if ch == '\n' or ch == '\r':
                charCount = 0
            elif charCount > numChars and not Character.isWhitespace(ch):
                result+="\n"
                charCount = 0
            else:
                charCount+=1
            result+=ch
        return result

    def doesUserAcceptDisclaimer(theParent, theTitle, disclaimerQuestion):
        disclaimer = myPopupAskForInput(theParent,
                                        theTitle,
                                        "DISCLAIMER:",
                                        "%s Type 'IAGREE' to continue.." %(disclaimerQuestion),
                                        "NO",
                                        False,
                                        JOptionPane.ERROR_MESSAGE)
        agreed = (disclaimer == "IAGREE")
        if agreed:
            myPrint("B", "%s: User AGREED to disclaimer question: '%s'" %(theTitle, disclaimerQuestion))
        else:
            myPrint("B", "%s: User DECLINED disclaimer question: '%s' - no action/changes made" %(theTitle, disclaimerQuestion))
        return agreed

    def myPopupAskBackup(theParent=None, theMessage="What no message?!", lReturnTheTruth=False):

        _options=["STOP", "PROCEED WITHOUT BACKUP", "DO BACKUP NOW"]
        response = JOptionPane.showOptionDialog(theParent,
                                                theMessage,
                                                "PERFORM BACKUP BEFORE UPDATE?",
                                                0,
                                                JOptionPane.WARNING_MESSAGE,
                                                getMDIcon(),
                                                _options,
                                                _options[0])

        if response == 2:
            myPrint("B", "User requested to create a backup before update/fix - calling moneydance 'Export Backup' routine...")
            MD_REF.getUI().setStatus("%s is creating a backup...." %(GlobalVars.thisScriptName),-1.0)
            MD_REF.getUI().saveToBackup(None)
            MD_REF.getUI().setStatus("%s create (export) backup process completed...." %(GlobalVars.thisScriptName),0)
            return True

        elif response == 1:
            myPrint("B", "User DECLINED to create a backup before update/fix...!")
            if not lReturnTheTruth:
                return True

        return False

    def confirm_backup_confirm_disclaimer(theFrame, theTitleToDisplay, theAction):

        if not myPopupAskQuestion(theFrame,
                                  theTitle=theTitleToDisplay,
                                  theQuestion=theAction,
                                  theOptionType=JOptionPane.YES_NO_OPTION,
                                  theMessageType=JOptionPane.ERROR_MESSAGE):

            txt = "'%s' User did not say yes to '%s' - no changes made" %(theTitleToDisplay, theAction)
            setDisplayStatus(txt, "R")
            myPrint("B", txt)
            myPopupInformationBox(theFrame,"User did not agree to proceed - no changes made...","NO UPDATE",JOptionPane.ERROR_MESSAGE)
            return False

        if not myPopupAskBackup(theFrame, "Would you like to perform a backup before %s" %(theTitleToDisplay)):
            txt = "'%s' - User chose to exit without the fix/update...."%(theTitleToDisplay)
            setDisplayStatus(txt, "R")
            myPrint("B","'%s' User aborted at the backup prompt to '%s' - no changes made" %(theTitleToDisplay, theAction))
            myPopupInformationBox(theFrame,"User aborted at the backup prompt - no changes made...","DISCLAIMER",JOptionPane.ERROR_MESSAGE)
            return False

        if not doesUserAcceptDisclaimer(theFrame, theTitleToDisplay, theAction):
            setDisplayStatus("'%s' - User declined the disclaimer - no changes made...." %(theTitleToDisplay), "R")
            myPrint("B","'%s' User did not say accept Disclaimer to '%s' - no changes made" %(theTitleToDisplay, theAction))
            myPopupInformationBox(theFrame,"User did not accept Disclaimer - no changes made...","DISCLAIMER",JOptionPane.ERROR_MESSAGE)
            return False

        myPrint("B","'%s' - User has been offered opportunity to create a backup and they accepted the DISCLAIMER on Action: %s - PROCEEDING" %(theTitleToDisplay, theAction))
        return True

    # Copied MD_REF.getUI().askQuestion
    def myPopupAskQuestion(theParent=None,
                           theTitle="Question",
                           theQuestion="What?",
                           theOptionType=JOptionPane.YES_NO_OPTION,
                           theMessageType=JOptionPane.QUESTION_MESSAGE):

        if theParent is None and (theMessageType == JOptionPane.PLAIN_MESSAGE or theMessageType == JOptionPane.INFORMATION_MESSAGE):
            icon = getMDIcon(lAlwaysGetIcon=True)
        else:
            icon = getMDIcon(None)

        # question = wrapLines(theQuestion)
        question = theQuestion
        result = JOptionPane.showConfirmDialog(theParent,
                                               question,
                                               theTitle,
                                               theOptionType,
                                               theMessageType,
                                               icon)
        return result == 0

    # Copies Moneydance .askForQuestion
    def myPopupAskForInput(theParent,
                           theTitle,
                           theFieldLabel,
                           theFieldDescription="",
                           defaultValue=None,
                           isPassword=False,
                           theMessageType=JOptionPane.INFORMATION_MESSAGE):

        if theParent is None and (theMessageType == JOptionPane.PLAIN_MESSAGE or theMessageType == JOptionPane.INFORMATION_MESSAGE):
            icon = getMDIcon(lAlwaysGetIcon=True)
        else:
            icon = getMDIcon(None)

        p = JPanel(GridBagLayout())
        defaultText = None
        if defaultValue: defaultText = defaultValue
        if isPassword:
            field = JPasswordField(defaultText)
        else:
            field = JTextField(defaultText)
        field.addAncestorListener(RequestFocusListener())

        _x = 0
        if theFieldLabel:
            p.add(JLabel(theFieldLabel), GridC.getc(_x, 0).east())
            _x+=1

        p.add(field, GridC.getc(_x, 0).field())
        p.add(Box.createHorizontalStrut(244), GridC.getc(_x, 0))
        if theFieldDescription:
            p.add(JTextPanel(theFieldDescription), GridC.getc(_x, 1).field().colspan(_x + 1))
        if (JOptionPane.showConfirmDialog(theParent,
                                          p,
                                          theTitle,
                                          JOptionPane.OK_CANCEL_OPTION,
                                          theMessageType,
                                          icon) == 0):
            return field.getText()
        return None

    # APPLICATION_MODAL, DOCUMENT_MODAL, MODELESS, TOOLKIT_MODAL
    class MyPopUpDialogBox():

        def __init__(self,
                     theParent=None,
                     theStatus="",
                     theMessage="",
                     maxSize=Dimension(0,0),
                     theTitle="Info",
                     lModal=True,
                     lCancelButton=False,
                     OKButtonText="OK",
                     lAlertLevel=0):

            self.theParent = theParent
            self.theStatus = theStatus
            self.theMessage = theMessage
            self.maxSize = maxSize
            self.theTitle = theTitle
            self.lModal = lModal
            self.lCancelButton = lCancelButton
            self.OKButtonText = OKButtonText
            self.lAlertLevel = lAlertLevel
            self.fakeJFrame = None
            self._popup_d = None
            self.lResult = [None]
            self.statusLabel = None
            self.messageJText = None
            if not self.theMessage.endswith("\n"): self.theMessage+="\n"
            if self.OKButtonText == "": self.OKButtonText="OK"
            # if Platform.isOSX() and int(float(MD_REF.getBuild())) >= 3039: self.lAlertLevel = 0    # Colors don't work on Mac since VAQua
            if isMDThemeDark() or isMacDarkModeDetected(): self.lAlertLevel = 0

        def updateMessages(self, newTitle=None, newStatus=None, newMessage=None, lPack=True):
            if not newTitle and not newStatus and not newMessage: return
            if newTitle:
                self.theTitle = newTitle
                self._popup_d.setTitle(self.theTitle)
            if newStatus:
                self.theStatus = newStatus
                self.statusLabel.setText(self.theStatus)
            if newMessage:
                self.theMessage = newMessage
                self.messageJText.setText(self.theMessage)
            if lPack: self._popup_d.pack()

        class WindowListener(WindowAdapter):

            def __init__(self, theDialog, theFakeFrame, lResult):
                self.theDialog = theDialog
                self.theFakeFrame = theFakeFrame
                self.lResult = lResult

            def windowClosing(self, WindowEvent):                                                                       # noqa
                myPrint("DB", "In ", inspect.currentframe().f_code.co_name, "()", "Event: ", WindowEvent)
                myPrint("DB", "SwingUtilities.isEventDispatchThread() = %s" %(SwingUtilities.isEventDispatchThread()))

                myPrint("DB", "JDialog Frame shutting down....")

                self.lResult[0] = False

                # Note - listeners are already on the EDT
                if self.theFakeFrame is not None:
                    self.theDialog.dispose()
                    self.theFakeFrame.dispose()
                else:
                    self.theDialog.dispose()

                myPrint("D", "Exiting ", inspect.currentframe().f_code.co_name, "()")
                return

        class OKButtonAction(AbstractAction):

            def __init__(self, theDialog, theFakeFrame, lResult):
                self.theDialog = theDialog
                self.theFakeFrame = theFakeFrame
                self.lResult = lResult

            def actionPerformed(self, event):
                myPrint("DB", "In ", inspect.currentframe().f_code.co_name, "()", "Event: ", event)
                myPrint("DB", "SwingUtilities.isEventDispatchThread() = %s" %(SwingUtilities.isEventDispatchThread()))

                self.lResult[0] = True

                # Note - listeners are already on the EDT
                if self.theFakeFrame is not None:
                    self.theDialog.dispose()
                    self.theFakeFrame.dispose()
                else:
                    self.theDialog.dispose()

                myPrint("D", "Exiting ", inspect.currentframe().f_code.co_name, "()")
                return

        class CancelButtonAction(AbstractAction):

            def __init__(self, theDialog, theFakeFrame, lResult):
                self.theDialog = theDialog
                self.theFakeFrame = theFakeFrame
                self.lResult = lResult

            def actionPerformed(self, event):
                myPrint("DB", "In ", inspect.currentframe().f_code.co_name, "()", "Event: ", event)
                myPrint("DB", "SwingUtilities.isEventDispatchThread() = %s" %(SwingUtilities.isEventDispatchThread()))

                self.lResult[0] = False

                # Note - listeners are already on the EDT
                if self.theFakeFrame is not None:
                    self.theDialog.dispose()
                    self.theFakeFrame.dispose()
                else:
                    self.theDialog.dispose()

                myPrint("D", "Exiting ", inspect.currentframe().f_code.co_name, "()")
                return

        def kill(self):
            myPrint("DB", "In ", inspect.currentframe().f_code.co_name, "()")
            myPrint("DB", "SwingUtilities.isEventDispatchThread() = %s" %(SwingUtilities.isEventDispatchThread()))

            if not SwingUtilities.isEventDispatchThread():
                SwingUtilities.invokeLater(GenericVisibleRunnable(self._popup_d, False))
                if self.fakeJFrame is not None:
                    SwingUtilities.invokeLater(GenericDisposeRunnable(self._popup_d))
                    SwingUtilities.invokeLater(GenericDisposeRunnable(self.fakeJFrame))
                else:
                    SwingUtilities.invokeLater(GenericDisposeRunnable(self._popup_d))
            else:
                self._popup_d.setVisible(False)
                if self.fakeJFrame is not None:
                    self._popup_d.dispose()
                    self.fakeJFrame.dispose()
                else:
                    self._popup_d.dispose()

            myPrint("D", "Exiting ", inspect.currentframe().f_code.co_name, "()")
            return

        def result(self):
            return self.lResult[0]

        def go(self):
            myPrint("DB", "In ", inspect.currentframe().f_code.co_name, "()")
            myPrint("DB", "SwingUtilities.isEventDispatchThread() = %s" %(SwingUtilities.isEventDispatchThread()))

            class MyPopUpDialogBoxRunnable(Runnable):
                def __init__(self, callingClass):
                    self.callingClass = callingClass

                def run(self):                                                                                                      # noqa

                    myPrint("DB", "In ", inspect.currentframe().f_code.co_name, "()")
                    myPrint("DB", "SwingUtilities.isEventDispatchThread() = %s" %(SwingUtilities.isEventDispatchThread()))

                    # Create a fake JFrame so we can set the Icons...
                    if self.callingClass.theParent is None:
                        self.callingClass.fakeJFrame = MyJFrame()
                        self.callingClass.fakeJFrame.setName(u"%s_fake_dialog" %(myModuleID))
                        self.callingClass.fakeJFrame.setDefaultCloseOperation(WindowConstants.DO_NOTHING_ON_CLOSE)
                        self.callingClass.fakeJFrame.setUndecorated(True)
                        self.callingClass.fakeJFrame.setVisible(False)
                        if not Platform.isOSX():
                            self.callingClass.fakeJFrame.setIconImage(MDImages.getImage(MD_REF.getSourceInformation().getIconResource()))

                    class MyJDialog(JDialog):
                        def __init__(self, maxSize, *args):
                            self.maxSize = maxSize                                                                      # type: Dimension
                            super(self.__class__, self).__init__(*args)

                        # On Windows, the height was exceeding the screen height when default size of Dimension (0,0), so set the max....
                        def getPreferredSize(self):
                            calcPrefSize = super(self.__class__, self).getPreferredSize()
                            newPrefSize = Dimension(min(calcPrefSize.width, self.maxSize.width), min(calcPrefSize.height, self.maxSize.height))
                            return newPrefSize

                    screenSize = Toolkit.getDefaultToolkit().getScreenSize()

                    if isinstance(self.callingClass.maxSize, Dimension)\
                            and self.callingClass.maxSize.height and self.callingClass.maxSize.width:
                        maxDialogWidth = min(screenSize.width-20, self.callingClass.maxSize.width)
                        maxDialogHeight = min(screenSize.height-40, self.callingClass.maxSize.height)
                        maxDimension = Dimension(maxDialogWidth,maxDialogHeight)
                        # self.callingClass._popup_d.setPreferredSize(Dimension(maxDialogWidth,maxDialogHeight))
                    else:
                        maxDialogWidth = min(screenSize.width-20, max(GetFirstMainFrame.DEFAULT_MAX_WIDTH, int(round(GetFirstMainFrame.getSize().width *.9,0))))
                        maxDialogHeight = min(screenSize.height-40, max(GetFirstMainFrame.DEFAULT_MAX_WIDTH, int(round(GetFirstMainFrame.getSize().height *.9,0))))
                        maxDimension = Dimension(maxDialogWidth,maxDialogHeight)
                        # self.callingClass._popup_d.setPreferredSize(Dimension(maxDialogWidth,maxDialogHeight))

                    # noinspection PyUnresolvedReferences
                    self.callingClass._popup_d = MyJDialog(maxDimension,
                                                           self.callingClass.theParent, self.callingClass.theTitle,
                                                           Dialog.ModalityType.APPLICATION_MODAL if (self.callingClass.lModal) else Dialog.ModalityType.MODELESS)

                    self.callingClass._popup_d.getContentPane().setLayout(BorderLayout())
                    self.callingClass._popup_d.setDefaultCloseOperation(WindowConstants.DO_NOTHING_ON_CLOSE)

                    shortcut = Toolkit.getDefaultToolkit().getMenuShortcutKeyMaskEx()

                    # Add standard CMD-W keystrokes etc to close window
                    self.callingClass._popup_d.getRootPane().getInputMap(JComponent.WHEN_ANCESTOR_OF_FOCUSED_COMPONENT).put(KeyStroke.getKeyStroke(KeyEvent.VK_W, shortcut), "close-window")
                    self.callingClass._popup_d.getRootPane().getInputMap(JComponent.WHEN_ANCESTOR_OF_FOCUSED_COMPONENT).put(KeyStroke.getKeyStroke(KeyEvent.VK_F4, shortcut), "close-window")
                    self.callingClass._popup_d.getRootPane().getInputMap(JComponent.WHEN_IN_FOCUSED_WINDOW).put(KeyStroke.getKeyStroke(KeyEvent.VK_ESCAPE, 0), "close-window")
                    self.callingClass._popup_d.getRootPane().getActionMap().put("close-window", self.callingClass.CancelButtonAction(self.callingClass._popup_d, self.callingClass.fakeJFrame,self.callingClass.lResult))
                    self.callingClass._popup_d.addWindowListener(self.callingClass.WindowListener(self.callingClass._popup_d, self.callingClass.fakeJFrame,self.callingClass.lResult))

                    if (not Platform.isMac()):
                        # MD_REF.getUI().getImages()
                        self.callingClass._popup_d.setIconImage(MDImages.getImage(MD_REF.getSourceInformation().getIconResource()))

                    self.callingClass.messageJText = JTextArea(self.callingClass.theMessage)
                    self.callingClass.messageJText.setFont(getMonoFont())
                    self.callingClass.messageJText.setEditable(False)
                    self.callingClass.messageJText.setLineWrap(False)
                    self.callingClass.messageJText.setWrapStyleWord(False)

                    _popupPanel = JPanel(BorderLayout())
                    _popupPanel.setBorder(EmptyBorder(8, 8, 8, 8))

                    if self.callingClass.theStatus:
                        _statusPnl = JPanel(BorderLayout())
                        self.callingClass.statusLabel = JLabel(self.callingClass.theStatus)
                        self.callingClass.statusLabel.setForeground(getColorBlue())
                        self.callingClass.statusLabel.setBorder(EmptyBorder(8, 0, 8, 0))
                        _popupPanel.add(self.callingClass.statusLabel, BorderLayout.NORTH)

                    myScrollPane = JScrollPane(self.callingClass.messageJText, JScrollPane.VERTICAL_SCROLLBAR_AS_NEEDED,JScrollPane.HORIZONTAL_SCROLLBAR_AS_NEEDED)
                    myScrollPane.setWheelScrollingEnabled(True)
                    _popupPanel.add(myScrollPane, BorderLayout.CENTER)

                    buttonPanel = JPanel()
                    if self.callingClass.lModal or self.callingClass.lCancelButton:
                        buttonPanel.setLayout(FlowLayout(FlowLayout.CENTER))

                        if self.callingClass.lCancelButton:
                            cancel_button = JButton("CANCEL")
                            cancel_button.setPreferredSize(Dimension(100,40))
                            cancel_button.setBackground(Color.LIGHT_GRAY)
                            cancel_button.setBorderPainted(False)
                            cancel_button.setOpaque(True)
                            cancel_button.setBorder(EmptyBorder(8, 8, 8, 8))

                            cancel_button.addActionListener(self.callingClass.CancelButtonAction(self.callingClass._popup_d, self.callingClass.fakeJFrame,self.callingClass.lResult) )
                            buttonPanel.add(cancel_button)

                        if self.callingClass.lModal:
                            ok_button = JButton(self.callingClass.OKButtonText)
                            if len(self.callingClass.OKButtonText) <= 2:
                                ok_button.setPreferredSize(Dimension(100,40))
                            else:
                                ok_button.setPreferredSize(Dimension(200,40))

                            ok_button.setBackground(Color.LIGHT_GRAY)
                            ok_button.setBorderPainted(False)
                            ok_button.setOpaque(True)
                            ok_button.setBorder(EmptyBorder(8, 8, 8, 8))
                            ok_button.addActionListener( self.callingClass.OKButtonAction(self.callingClass._popup_d, self.callingClass.fakeJFrame, self.callingClass.lResult) )
                            buttonPanel.add(ok_button)

                        _popupPanel.add(buttonPanel, BorderLayout.SOUTH)

                    if self.callingClass.lAlertLevel >= 2:
                        # internalScrollPane.setBackground(Color.RED)
                        self.callingClass.messageJText.setBackground(Color.RED)
                        self.callingClass.messageJText.setForeground(Color.BLACK)
                        self.callingClass.messageJText.setOpaque(True)
                        _popupPanel.setBackground(Color.RED)
                        _popupPanel.setForeground(Color.BLACK)
                        _popupPanel.setOpaque(True)
                        buttonPanel.setBackground(Color.RED)
                        buttonPanel.setOpaque(True)

                    elif self.callingClass.lAlertLevel >= 1:
                        # internalScrollPane.setBackground(Color.YELLOW)
                        self.callingClass.messageJText.setBackground(Color.YELLOW)
                        self.callingClass.messageJText.setForeground(Color.BLACK)
                        self.callingClass.messageJText.setOpaque(True)
                        _popupPanel.setBackground(Color.YELLOW)
                        _popupPanel.setForeground(Color.BLACK)
                        _popupPanel.setOpaque(True)
                        buttonPanel.setBackground(Color.YELLOW)
                        buttonPanel.setOpaque(True)

                    self.callingClass._popup_d.add(_popupPanel, BorderLayout.CENTER)
                    self.callingClass._popup_d.pack()
                    self.callingClass._popup_d.setLocationRelativeTo(self.callingClass.theParent)
                    self.callingClass._popup_d.setVisible(True)

            if not SwingUtilities.isEventDispatchThread():
                myPrint("DB",".. Not running within the EDT so calling via MyPopUpDialogBoxRunnable()...")
                SwingUtilities.invokeAndWait(MyPopUpDialogBoxRunnable(self))
            else:
                myPrint("DB",".. Already within the EDT so calling naked...")
                MyPopUpDialogBoxRunnable(self).run()

            myPrint("D", "Exiting ", inspect.currentframe().f_code.co_name, "()")

            return self.lResult[0]

    def play_the_money_sound():

        # Seems to cause a crash on Virtual Machine with no Audio - so just in case....
        try:
            if MD_REF.getPreferences().getSetting("beep_on_transaction_change", "y") == "y":
                MD_REF.getUI().getSounds().playSound("cash_register.wav")
        except:
            pass

        return

    def get_filename_addition():

        cal = Calendar.getInstance()
        hhmm = str(10000 + cal.get(11) * 100 + cal.get(12))[1:]
        nameAddition = "-" + str(DateUtil.getStrippedDateInt()) + "-"+hhmm

        return nameAddition

    def check_file_writable(fnm):
        myPrint("D", "In ", inspect.currentframe().f_code.co_name, "()" )
        myPrint("DB","Checking path: ", fnm)

        if os.path.exists(fnm):
            myPrint("DB", "path exists..")
            # path exists
            if os.path.isfile(fnm):  # is it a file or a dir?
                myPrint("DB","path is a file..")
                # also works when file is a link and the target is writable
                return os.access(fnm, os.W_OK)
            else:
                myPrint("DB", "path is not a file..")
                return False  # path is a dir, so cannot write as a file
        # target does not exist, check perms on parent dir
        myPrint("DB","path does not exist...")
        pdir = os.path.dirname(fnm)
        if not pdir: pdir = '.'
        # target is creatable if parent dir is writable
        return os.access(pdir, os.W_OK)

    class ExtFilenameFilter(FilenameFilter):
        """File extension filter for FileDialog"""
        def __init__(self, ext): self.ext = "." + ext.upper()                                                           # noqa

        def accept(self, thedir, filename):                                                                             # noqa
            if filename is not None and filename.upper().endswith(self.ext): return True
            return False

    class ExtFileFilterJFC(FileFilter):
        """File extension filter for JFileChooser"""
        def __init__(self, ext): self.ext = "." + ext.upper()

        def getDescription(self): return "*"+self.ext                                                                   # noqa

        def accept(self, _theFile):                                                                                     # noqa
            if _theFile is None: return False
            return _theFile.getName().upper().endswith(self.ext)

    def MDDiag():
        myPrint("D", "Moneydance Build:", MD_REF.getVersion(), "Build:", MD_REF.getBuild())


    MDDiag()

    myPrint("DB","System file encoding is:", sys.getfilesystemencoding() )   # Not used, but interesting. Perhaps useful when switching between Windows/Macs and writing files...

    def checkVersions():
        lError = False
        plat_j = platform.system()
        plat_p = platform.python_implementation()
        python_maj = sys.version_info.major
        python_min = sys.version_info.minor

        myPrint("DB","Platform:", plat_p, plat_j, python_maj, ".", python_min)
        myPrint("DB", sys.version)

        if plat_p != "Jython":
            lError = True
            myPrint("DB", "Error: Script requires Jython")
        if plat_j != "Java":
            lError = True
            myPrint("DB", "Error: Script requires Java  base")
        if (python_maj != 2 or python_min != 7):
            lError = True
            myPrint("DB", "\n\nError: Script was  designed on version 2.7. By all means bypass this test and see what happens.....")

        if lError:
            myPrint("J", "Platform version issue - will terminate script!")
            myPrint("P", "\n@@@ TERMINATING PROGRAM @@@\n")
            raise(Exception("Platform version issue - will terminate script!"))

        return not lError


    checkVersions()

    def setDefaultFonts():
        """Grabs the MD defaultText font, reduces default size down to below 18, sets UIManager defaults (if runtime extension, will probably error, so I catch and skip)"""
        if MD_REF_UI is None: return

        # If a runtime extension, then this may fail, depending on timing... Just ignore and return...
        try:
            myFont = MD_REF.getUI().getFonts().defaultText
        except:
            myPrint("B","ERROR trying to call .getUI().getFonts().defaultText - skipping setDefaultFonts()")
            return

        if myFont is None:
            myPrint("B","WARNING: In setDefaultFonts(): calling .getUI().getFonts().defaultText has returned None (but moneydance_ui was set) - skipping setDefaultFonts()")
            return

        if myFont.getSize()>18:
            try:
                myFont = myFont.deriveFont(16.0)
                myPrint("B", "I have reduced the font size down to point-size 16 - Default Fonts are now set to: %s" %(myFont))
            except:
                myPrint("B","ERROR - failed to override font point size down to 16.... will ignore and continue. Font set to: %s" %(myFont))
        else:
            myPrint("DB", "Attempting to set default font to %s" %myFont)

        try:
            UIManager.getLookAndFeelDefaults().put("defaultFont", myFont )

            # https://thebadprogrammer.com/swing-uimanager-keys/
            UIManager.put("CheckBoxMenuItem.acceleratorFont", myFont)
            UIManager.put("Button.font", myFont)
            UIManager.put("ToggleButton.font", myFont)
            UIManager.put("RadioButton.font", myFont)
            UIManager.put("CheckBox.font", myFont)
            UIManager.put("ColorChooser.font", myFont)
            UIManager.put("ComboBox.font", myFont)
            UIManager.put("Label.font", myFont)
            UIManager.put("List.font", myFont)
            UIManager.put("MenuBar.font", myFont)
            UIManager.put("Menu.acceleratorFont", myFont)
            UIManager.put("RadioButtonMenuItem.acceleratorFont", myFont)
            UIManager.put("MenuItem.acceleratorFont", myFont)
            UIManager.put("MenuItem.font", myFont)
            UIManager.put("RadioButtonMenuItem.font", myFont)
            UIManager.put("CheckBoxMenuItem.font", myFont)
            UIManager.put("OptionPane.buttonFont", myFont)
            UIManager.put("OptionPane.messageFont", myFont)
            UIManager.put("Menu.font", myFont)
            UIManager.put("PopupMenu.font", myFont)
            UIManager.put("OptionPane.font", myFont)
            UIManager.put("Panel.font", myFont)
            UIManager.put("ProgressBar.font", myFont)
            UIManager.put("ScrollPane.font", myFont)
            UIManager.put("Viewport.font", myFont)
            UIManager.put("TabbedPane.font", myFont)
            UIManager.put("Slider.font", myFont)
            UIManager.put("Table.font", myFont)
            UIManager.put("TableHeader.font", myFont)
            UIManager.put("TextField.font", myFont)
            UIManager.put("Spinner.font", myFont)
            UIManager.put("PasswordField.font", myFont)
            UIManager.put("TextArea.font", myFont)
            UIManager.put("TextPane.font", myFont)
            UIManager.put("EditorPane.font", myFont)
            UIManager.put("TabbedPane.smallFont", myFont)
            UIManager.put("TitledBorder.font", myFont)
            UIManager.put("ToolBar.font", myFont)
            UIManager.put("ToolTip.font", myFont)
            UIManager.put("Tree.font", myFont)
            UIManager.put("FormattedTextField.font", myFont)
            UIManager.put("IconButton.font", myFont)
            UIManager.put("InternalFrame.optionDialogTitleFont", myFont)
            UIManager.put("InternalFrame.paletteTitleFont", myFont)
            UIManager.put("InternalFrame.titleFont", myFont)
        except:
            myPrint("B","Failed to set Swing default fonts to use Moneydance defaults... sorry")

        myPrint("DB",".setDefaultFonts() successfully executed...")
        return

    setDefaultFonts()

    def who_am_i():
        try: username = System.getProperty("user.name")
        except: username = "???"
        return username

    def getHomeDir():
        # Yup - this can be all over the place...
        myPrint("D", 'System.getProperty("user.dir")', System.getProperty("user.dir"))
        myPrint("D", 'System.getProperty("UserHome")', System.getProperty("UserHome"))
        myPrint("D", 'System.getProperty("user.home")', System.getProperty("user.home"))
        myPrint("D", 'os.path.expanduser("~")', os.path.expanduser("~"))
        myPrint("D", 'os.environ.get("HOMEPATH")', os.environ.get("HOMEPATH"))
        return

    myPrint("D", "I am user:", who_am_i())
    if debug: getHomeDir()

    # noinspection PyArgumentList
    class JTextFieldLimitYN(PlainDocument):

        limit = 10  # Default
        toUpper = False
        what = ""

        def __init__(self, limit, toUpper, what):

            super(PlainDocument, self).__init__()
            self.limit = limit
            self.toUpper = toUpper
            self.what = what

        def insertString(self, myOffset, myString, myAttr):

            if (myString is None): return
            if self.toUpper: myString = myString.upper()
            if (self.what == "YN" and (myString in "YN")) \
                    or (self.what == "DELIM" and (myString in ";|,")) \
                    or (self.what == "1234" and (myString in "1234")) \
                    or (self.what == "CURR"):
                if ((self.getLength() + len(myString)) <= self.limit):
                    super(JTextFieldLimitYN, self).insertString(myOffset, myString, myAttr)                             # noqa

    def fix_delimiter( theDelimiter ):

        try:
            if sys.version_info.major >= 3: return theDelimiter
            if sys.version_info.major <  2: return str(theDelimiter)

            if sys.version_info.minor >  7: return theDelimiter
            if sys.version_info.minor <  7: return str(theDelimiter)

            if sys.version_info.micro >= 2: return theDelimiter
        except:
            pass

        return str( theDelimiter )

    def get_StuWareSoftSystems_parameters_from_file(myFile="StuWareSoftSystems.dict"):
        global debug    # This global for debug must be here as we set it from loaded parameters

        myPrint("D", "In ", inspect.currentframe().f_code.co_name, "()" )

        if GlobalVars.resetPickleParameters:
            myPrint("B", "User has specified to reset parameters... keeping defaults and skipping pickle()")
            GlobalVars.parametersLoadedFromFile = {}
            return

        old_dict_filename = os.path.join("..", myFile)

        # Pickle was originally encrypted, no need, migrating to unencrypted
        migratedFilename = os.path.join(MD_REF.getCurrentAccountBook().getRootFolder().getAbsolutePath(),myFile)

        myPrint("DB", "Now checking for parameter file:", migratedFilename)

        if os.path.exists( migratedFilename ):

            myPrint("DB", "loading parameters from non-encrypted Pickle file:", migratedFilename)
            myPrint("DB", "Parameter file", migratedFilename, "exists..")
            # Open the file
            try:
                # Really we should open() the file in binary mode and read/write as binary, then we wouldn't get platform differences!
                istr = FileInputStream(migratedFilename)
                load_file = FileUtil.wrap(istr)
                if not Platform.isWindows():
                    load_string = load_file.read().replace('\r', '')    # This allows for files migrated from windows (strip the extra CR)
                else:
                    load_string = load_file.read()

                GlobalVars.parametersLoadedFromFile = pickle.loads(load_string)
                load_file.close()
            except FileNotFoundException:
                myPrint("B", "Error: failed to find parameter file...")
                GlobalVars.parametersLoadedFromFile = None
            except EOFError:
                myPrint("B", "Error: reached EOF on parameter file....")
                GlobalVars.parametersLoadedFromFile = None
            except:
                myPrint("B","Error opening Pickle File (will try encrypted version) - Unexpected error ", sys.exc_info()[0])
                myPrint("B","Error opening Pickle File (will try encrypted version) - Unexpected error ", sys.exc_info()[1])
                myPrint("B","Error opening Pickle File (will try encrypted version) - Line Number: ", sys.exc_info()[2].tb_lineno)

                # OK, so perhaps from older version - encrypted, try to read
                try:
                    local_storage = MD_REF.getCurrentAccountBook().getLocalStorage()
                    istr = local_storage.openFileForReading(old_dict_filename)
                    load_file = FileUtil.wrap(istr)
                    # noinspection PyTypeChecker
                    GlobalVars.parametersLoadedFromFile = pickle.load(load_file)
                    load_file.close()
                    myPrint("B","Success loading Encrypted Pickle file - will migrate to non encrypted")
                except:
                    myPrint("B","Opening Encrypted Pickle File - Unexpected error ", sys.exc_info()[0])
                    myPrint("B","Opening Encrypted Pickle File - Unexpected error ", sys.exc_info()[1])
                    myPrint("B","Error opening Pickle File - Line Number: ", sys.exc_info()[2].tb_lineno)
                    myPrint("B", "Error: Pickle.load() failed.... Is this a restored dataset? Will ignore saved parameters, and create a new file...")
                    GlobalVars.parametersLoadedFromFile = None

            if GlobalVars.parametersLoadedFromFile is None:
                GlobalVars.parametersLoadedFromFile = {}
                myPrint("DB","Parameters did not load, will keep defaults..")
            else:
                myPrint("DB","Parameters successfully loaded from file...")
        else:
            myPrint("J", "Parameter Pickle file does not exist - will use default and create new file..")
            myPrint("D", "Parameter Pickle file does not exist - will use default and create new file..")
            GlobalVars.parametersLoadedFromFile = {}

        if not GlobalVars.parametersLoadedFromFile: return

        myPrint("DB","GlobalVars.parametersLoadedFromFile read from file contains...:")
        for key in sorted(GlobalVars.parametersLoadedFromFile.keys()):
            myPrint("DB","...variable:", key, GlobalVars.parametersLoadedFromFile[key])

        if GlobalVars.parametersLoadedFromFile.get("debug") is not None: debug = GlobalVars.parametersLoadedFromFile.get("debug")
        if GlobalVars.parametersLoadedFromFile.get("lUseMacFileChooser") is not None:
            myPrint("B", "Detected old lUseMacFileChooser parameter/variable... Will delete it...")
            GlobalVars.parametersLoadedFromFile.pop("lUseMacFileChooser", None)  # Old variable - not used - delete from parameter file

        myPrint("DB","Parameter file loaded if present and GlobalVars.parametersLoadedFromFile{} dictionary set.....")

        # Now load into memory!
        load_StuWareSoftSystems_parameters_into_memory()

        return

    def save_StuWareSoftSystems_parameters_to_file(myFile="StuWareSoftSystems.dict"):
        myPrint("D", "In ", inspect.currentframe().f_code.co_name, "()" )

        if GlobalVars.parametersLoadedFromFile is None: GlobalVars.parametersLoadedFromFile = {}

        # Don't forget, any parameters loaded earlier will be preserved; just add changed variables....
        GlobalVars.parametersLoadedFromFile["__Author"] = "Stuart Beesley - (c) StuWareSoftSystems"
        GlobalVars.parametersLoadedFromFile["debug"] = debug

        dump_StuWareSoftSystems_parameters_from_memory()

        # Pickle was originally encrypted, no need, migrating to unencrypted
        migratedFilename = os.path.join(MD_REF.getCurrentAccountBook().getRootFolder().getAbsolutePath(),myFile)

        myPrint("DB","Will try to save parameter file:", migratedFilename)

        ostr = FileOutputStream(migratedFilename)

        myPrint("DB", "about to Pickle.dump and save parameters to unencrypted file:", migratedFilename)

        try:
            save_file = FileUtil.wrap(ostr)
            pickle.dump(GlobalVars.parametersLoadedFromFile, save_file, protocol=0)
            save_file.close()

            myPrint("DB","GlobalVars.parametersLoadedFromFile now contains...:")
            for key in sorted(GlobalVars.parametersLoadedFromFile.keys()):
                myPrint("DB","...variable:", key, GlobalVars.parametersLoadedFromFile[key])

        except:
            myPrint("B", "Error - failed to create/write parameter file.. Ignoring and continuing.....")
            dump_sys_error_to_md_console_and_errorlog()

            return

        myPrint("DB","Parameter file written and parameters saved to disk.....")

        return

    def get_time_stamp_as_nice_text(timeStamp, _format=None, lUseHHMMSS=True):

        if _format is None: _format = MD_REF.getPreferences().getShortDateFormat()

        humanReadableDate = ""
        try:
            c = Calendar.getInstance()
            c.setTime(Date(timeStamp))
            longHHMMSSText = " HH:mm:ss(.SSS) Z z zzzz" if (lUseHHMMSS) else ""
            dateFormatter = SimpleDateFormat("%s%s" %(_format, longHHMMSSText))
            humanReadableDate = dateFormatter.format(c.getTime())
        except: pass
        return humanReadableDate

    def currentDateTimeMarker():
        c = Calendar.getInstance()
        dateformat = SimpleDateFormat("_yyyyMMdd_HHmmss")
        _datetime = dateformat.format(c.getTime())
        return _datetime

    def destroyOldFrames(moduleName):
        myPrint("DB", "In ", inspect.currentframe().f_code.co_name, "()")
        myPrint("DB", "SwingUtilities.isEventDispatchThread() = %s" %(SwingUtilities.isEventDispatchThread()))
        frames = JFrame.getFrames()
        for fr in frames:
            if fr.getName().lower().startswith(moduleName+"_"):
                myPrint("DB","Found old frame %s and active status is: %s" %(fr.getName(),fr.isActiveInMoneydance))
                try:
                    fr.isActiveInMoneydance = False
                    if not SwingUtilities.isEventDispatchThread():
                        SwingUtilities.invokeLater(GenericVisibleRunnable(fr, False, False))
                        SwingUtilities.invokeLater(GenericDisposeRunnable(fr))  # This should call windowClosed() which should remove MD listeners.....
                    else:
                        fr.setVisible(False)
                        fr.dispose()            # This should call windowClosed() which should remove MD listeners.....
                    myPrint("DB","disposed of old frame: %s" %(fr.getName()))
                except:
                    myPrint("B","Failed to dispose old frame: %s" %(fr.getName()))
                    dump_sys_error_to_md_console_and_errorlog()

    def classPrinter(className, theObject):
        try:
            text = "Class: %s %s@{:x}".format(System.identityHashCode(theObject)) %(className, theObject.__class__)
        except:
            text = "Error in classPrinter(): %s: %s" %(className, theObject)
        return text

    def getColorBlue():
        if not isMDThemeDark() and not isMacDarkModeDetected(): return(Color.BLUE)
        return (MD_REF.getUI().getColors().defaultTextForeground)

    def getColorRed(): return (MD_REF.getUI().getColors().errorMessageForeground)

    def getColorDarkGreen(): return (MD_REF.getUI().getColors().budgetHealthyColor)

    def setDisplayStatus(_theStatus, _theColor=None):
        """Sets the Display / Status label on the main diagnostic display: G=Green, B=Blue, R=Red, DG=Dark Green"""

        if GlobalVars.STATUS_LABEL is None or not isinstance(GlobalVars.STATUS_LABEL, JLabel): return

        class SetDisplayStatusRunnable(Runnable):
            def __init__(self, _status, _color):
                self.status = _status; self.color = _color

            def run(self):
                GlobalVars.STATUS_LABEL.setText((_theStatus))
                if self.color is None or self.color == "": self.color = "X"
                self.color = self.color.upper()
                if self.color == "R":    GlobalVars.STATUS_LABEL.setForeground(getColorRed())
                elif self.color == "B":  GlobalVars.STATUS_LABEL.setForeground(getColorBlue())
                elif self.color == "DG": GlobalVars.STATUS_LABEL.setForeground(getColorDarkGreen())
                else:                    GlobalVars.STATUS_LABEL.setForeground(MD_REF.getUI().getColors().defaultTextForeground)

        if not SwingUtilities.isEventDispatchThread():
            SwingUtilities.invokeLater(SetDisplayStatusRunnable(_theStatus, _theColor))
        else:
            SetDisplayStatusRunnable(_theStatus, _theColor).run()

    def setJFileChooserParameters(_jf, lReportOnly=False, lDefaults=False, lPackagesT=None, lApplicationsT=None, lOptionsButton=None, lNewFolderButton=None):
        """sets up Client Properties for JFileChooser() to behave as required >> Mac only"""

        myPrint("D", "In ", inspect.currentframe().f_code.co_name, "()")

        if not Platform.isOSX(): return
        if not isinstance(_jf, JFileChooser): return

        _PKG = "JFileChooser.packageIsTraversable"
        _APP = "JFileChooser.appBundleIsTraversable"
        _OPTIONS = "JFileChooser.optionsPanelEnabled"
        _NEWFOLDER = "JFileChooser.canCreateDirectories"

        # JFileChooser defaults: https://violetlib.org/vaqua/filechooser.html
        # "JFileChooser.packageIsTraversable"   default False   >> set "true" to allow Packages to be traversed
        # "JFileChooser.appBundleIsTraversable" default False   >> set "true" to allow App Bundles to be traversed
        # "JFileChooser.optionsPanelEnabled"    default False   >> set "true" to allow Options button
        # "JFileChooser.canCreateDirectories"   default False   >> set "true" to allow New Folder button

        if debug or lReportOnly:
            myPrint("B", "Parameters set: ReportOnly: %s, Defaults:%s, PackagesT: %s, ApplicationsT:%s, OptionButton:%s, NewFolderButton: %s" %(lReportOnly, lDefaults, lPackagesT, lApplicationsT, lOptionsButton, lNewFolderButton))
            txt = ("Before setting" if not lReportOnly else "Reporting only")
            for setting in [_PKG, _APP, _OPTIONS, _NEWFOLDER]: myPrint("DB", "%s: '%s': '%s'" %(pad(txt,14), pad(setting,50), _jf.getClientProperty(setting)))
            if lReportOnly: return

        if lDefaults:
            _jf.putClientProperty(_PKG, None)
            _jf.putClientProperty(_APP, None)
            _jf.putClientProperty(_OPTIONS, None)
            _jf.putClientProperty(_NEWFOLDER, None)
        else:
            if lPackagesT       is not None: _jf.putClientProperty(_PKG, lPackagesT)
            if lApplicationsT   is not None: _jf.putClientProperty(_APP, lApplicationsT)
            if lOptionsButton   is not None: _jf.putClientProperty(_OPTIONS, lOptionsButton)
            if lNewFolderButton is not None: _jf.putClientProperty(_NEWFOLDER, lNewFolderButton)

        for setting in [_PKG, _APP, _OPTIONS, _NEWFOLDER]: myPrint("DB", "%s: '%s': '%s'" %(pad("After setting",14), pad(setting,50), _jf.getClientProperty(setting)))

        return

    def setFileDialogParameters(lReportOnly=False, lDefaults=False, lSelectDirectories=None, lPackagesT=None):
        """sets up System Properties for FileDialog() to behave as required >> Mac only"""

        myPrint("D", "In ", inspect.currentframe().f_code.co_name, "()")

        if not Platform.isOSX(): return

        _TRUE = "true"
        _FALSE = "false"

        _DIRS_FD = "apple.awt.fileDialogForDirectories"        # When True you can select a Folder (rather than a file)
        _PKGS_FD = "apple.awt.use-file-dialog-packages"        # When True allows you to select a 'bundle' as a file; False means navigate inside the bundle
        # "com.apple.macos.use-file-dialog-packages"           # DEPRECATED since Monterrey - discovered this about MD2022.5(4090) - refer: java.desktop/sun/lwawt/macosx/CFileDialog.java

        # FileDialog defaults
        # "apple.awt.fileDialogForDirectories"       default "false" >> set "true"  to allow Directories to be selected
        # "apple.awt.use-file-dialog-packages"       default "true"  >> set "false" to allow access to Mac 'packages'

        if debug or lReportOnly:
            myPrint("B", "Parameters set: ReportOnly: %s, Defaults:%s, SelectDirectories:%s, PackagesT:%s" % (lReportOnly, lDefaults, lSelectDirectories, lPackagesT))
            txt = ("Before setting" if not lReportOnly else "Reporting only")
            for setting in [_DIRS_FD, _PKGS_FD]: myPrint("DB", "%s: '%s': '%s'" %(pad(txt,14), pad(setting,50), System.getProperty(setting)))
            if lReportOnly: return

        if lDefaults:
            System.setProperty(_DIRS_FD,_FALSE)
            System.setProperty(_PKGS_FD,_TRUE)
        else:
            if lSelectDirectories is not None: System.setProperty(_DIRS_FD, (_TRUE if lSelectDirectories   else _FALSE))
            if lPackagesT         is not None: System.setProperty(_PKGS_FD, (_TRUE if lPackagesT           else _FALSE))

        for setting in [_DIRS_FD, _PKGS_FD]: myPrint("DB", "After setting:  '%s': '%s'" %(pad(setting,50), System.getProperty(setting)))

        return

    def getFileFromFileChooser(fileChooser_parent,                  # The Parent Frame, or None
                               fileChooser_starting_dir,            # The Starting Dir
                               fileChooser_filename,                # Default filename (or None)
                               fileChooser_title,                   # The Title (with FileDialog, only works on SAVE)
                               fileChooser_multiMode,               # Normally False (True has not been coded!)
                               fileChooser_open,                    # True for Open/Load, False for Save
                               fileChooser_selectFiles,             # True for files, False for Directories
                               fileChooser_OK_text,                 # Normally None, unless set - use text
                               fileChooser_fileFilterText=None,     # E.g. "txt" or "qif"
                               lForceJFC=False,
                               lForceFD=False,
                               lAllowTraversePackages=None,
                               lAllowTraverseApplications=None,     # JFileChooser only..
                               lAllowNewFolderButton=True,          # JFileChooser only..
                               lAllowOptionsButton=None):           # JFileChooser only..
        """Launches FileDialog on Mac, or JFileChooser on other platforms... NOTE: Do not use Filter on Macs!"""

        _THIS_METHOD_NAME = "Dynamic File Chooser"

        if fileChooser_multiMode:
            myPrint("B","@@ SORRY Multi File Selection Mode has not been coded! Exiting...")
            return None

        if fileChooser_starting_dir is None or fileChooser_starting_dir == "" or not os.path.exists(fileChooser_starting_dir):
            fileChooser_starting_dir = MD_REF.getPreferences().getSetting("gen.data_dir", None)

        if fileChooser_starting_dir is None or not os.path.exists(fileChooser_starting_dir):
            fileChooser_starting_dir = None
            myPrint("B","ERROR: Starting Path does not exist - will start with no starting path set..")

        else:
            myPrint("DB", "Preparing the Dynamic File Chooser with path: %s" %(fileChooser_starting_dir))
            if Platform.isOSX() and "/Library/Containers/" in fileChooser_starting_dir:
                myPrint("DB", "WARNING: Folder will be restricted by MacOSx...")
                if not lForceJFC:
                    txt = ("FileDialog: MacOSx restricts Java Access to 'special' locations like 'Library\n"
                          "Folder: %s\n"
                          "Please navigate to this location manually in the next popup. This grants permission"
                          %(fileChooser_starting_dir))
                else:
                    txt = ("JFileChooser: MacOSx restricts Java Access to 'special' locations like 'Library\n"
                          "Folder: %s\n"
                          "Your files will probably be hidden.. If so, switch to FileDialog()...(contact author)"
                          %(fileChooser_starting_dir))
                MyPopUpDialogBox(fileChooser_parent,
                                 "NOTE: Mac Security Restriction",
                                 txt,
                                 theTitle=_THIS_METHOD_NAME,
                                 lAlertLevel=1).go()

        if (Platform.isOSX() and not lForceJFC) or lForceFD:

            setFileDialogParameters(lPackagesT=lAllowTraversePackages, lSelectDirectories=(not fileChooser_selectFiles))

            myPrint("DB", "Preparing FileDialog() with path: %s" %(fileChooser_starting_dir))
            if fileChooser_filename is not None: myPrint("DB", "... and filename:                 %s" %(fileChooser_filename))

            fileDialog = FileDialog(fileChooser_parent, fileChooser_title)

            fileDialog.setTitle(fileChooser_title)

            if fileChooser_starting_dir is not None:    fileDialog.setDirectory(fileChooser_starting_dir)
            if fileChooser_filename is not None:        fileDialog.setFile(fileChooser_filename)

            fileDialog.setMultipleMode(fileChooser_multiMode)

            if fileChooser_open:
                fileDialog.setMode(FileDialog.LOAD)
            else:
                fileDialog.setMode(FileDialog.SAVE)

            # if fileChooser_fileFilterText is not None and (not Platform.isOSX() or not Platform.isOSXVersionAtLeast("10.13")):
            if fileChooser_fileFilterText is not None and (not Platform.isOSX() or isOSXVersionMontereyOrLater()):
                myPrint("DB",".. Adding file filter for: %s" %(fileChooser_fileFilterText))
                fileDialog.setFilenameFilter(ExtFilenameFilter(fileChooser_fileFilterText))

            fileDialog.setVisible(True)

            setFileDialogParameters(lDefaults=True)

            myPrint("DB", "FileDialog returned File:      %s" %(fileDialog.getFile()))
            myPrint("DB", "FileDialog returned Directory: %s" %(fileDialog.getDirectory()))

            if fileDialog.getFile() is None or fileDialog.getFile() == "": return None

            _theFile = os.path.join(fileDialog.getDirectory(), fileDialog.getFile())

        else:

            myPrint("DB", "Preparing JFileChooser() with path: %s" %(fileChooser_starting_dir))
            if fileChooser_filename is not None: myPrint("DB", "... and filename:                   %s" %(fileChooser_filename))

            if fileChooser_starting_dir is not None:
                jfc = JFileChooser(fileChooser_starting_dir)
            else:
                jfc = JFileChooser()

            if fileChooser_filename is not None: jfc.setSelectedFile(File(fileChooser_filename))
            setJFileChooserParameters(jfc,
                                      lPackagesT=lAllowTraversePackages,
                                      lApplicationsT=lAllowTraverseApplications,
                                      lNewFolderButton=lAllowNewFolderButton,
                                      lOptionsButton=lAllowOptionsButton)

            jfc.setDialogTitle(fileChooser_title)
            jfc.setMultiSelectionEnabled(fileChooser_multiMode)

            if fileChooser_selectFiles:
                jfc.setFileSelectionMode(JFileChooser.FILES_ONLY)         # FILES_ONLY, DIRECTORIES_ONLY, FILES_AND_DIRECTORIES
            else:
                jfc.setFileSelectionMode(JFileChooser.DIRECTORIES_ONLY)   # FILES_ONLY, DIRECTORIES_ONLY, FILES_AND_DIRECTORIES

            # if fileChooser_fileFilterText is not None and (not Platform.isOSX() or not Platform.isOSXVersionAtLeast("10.13")):
            if fileChooser_fileFilterText is not None and (not Platform.isOSX() or isOSXVersionMontereyOrLater()):
                myPrint("DB",".. Adding file filter for: %s" %(fileChooser_fileFilterText))
                jfc.setFileFilter(ExtFileFilterJFC(fileChooser_fileFilterText))

            if fileChooser_OK_text is not None:
                returnValue = jfc.showDialog(fileChooser_parent, fileChooser_OK_text)
            else:
                if fileChooser_open:
                    returnValue = jfc.showOpenDialog(fileChooser_parent)
                else:
                    returnValue = jfc.showSaveDialog(fileChooser_parent)

            if returnValue == JFileChooser.CANCEL_OPTION \
                    or (jfc.getSelectedFile() is None or jfc.getSelectedFile().getName()==""):
                myPrint("DB","JFileChooser was cancelled by user, or no file was selected...")
                return None

            _theFile = jfc.getSelectedFile().getAbsolutePath()
            myPrint("DB","JFileChooser returned File/path..: %s" %(_theFile))

        myPrint("DB","...File/path exists..: %s" %(os.path.exists(_theFile)))
        return _theFile

    class RequestFocusListener(AncestorListener):
        """Add this Listener to a JTextField by using .addAncestorListener(RequestFocusListener()) before calling JOptionPane.showOptionDialog()"""

        def __init__(self, removeListener=True):
            self.removeListener = removeListener

        def ancestorAdded(self, e):
            component = e.getComponent()
            component.requestFocusInWindow()
            component.selectAll()
            if (self.removeListener): component.removeAncestorListener(self)

        def ancestorMoved(self, e): pass
        def ancestorRemoved(self, e): pass

    class SearchAction(AbstractAction):

        def __init__(self, theFrame, searchJText):
            self.theFrame = theFrame
            self.searchJText = searchJText
            self.lastSearch = ""
            self.lastPosn = -1
            self.previousEndPosn = -1
            self.lastDirection = 0

        def actionPerformed(self, event):
            myPrint("D","in SearchAction(), Event: ", event)

            p = JPanel(FlowLayout())
            lbl = JLabel("Enter the search text:")
            tf = JTextField(self.lastSearch,20)
            p.add(lbl)
            p.add(tf)

            tf.addAncestorListener(RequestFocusListener())

            _search_options = [ "Next", "Previous", "Cancel" ]

            defaultDirection = _search_options[self.lastDirection]

            response = JOptionPane.showOptionDialog(self.theFrame,
                                                    p,
                                                    "Search for text",
                                                    JOptionPane.OK_CANCEL_OPTION,
                                                    JOptionPane.QUESTION_MESSAGE,
                                                    getMDIcon(None),
                                                    _search_options,
                                                    defaultDirection)

            lSwitch = False
            if (response == 0 or response == 1):
                if response != self.lastDirection: lSwitch = True
                self.lastDirection = response
                searchWhat = tf.getText()
            else:
                searchWhat = None

            del p, lbl, tf, _search_options

            if not searchWhat or searchWhat == "": return

            theText = self.searchJText.getText().lower()
            highlighter = self.searchJText.getHighlighter()
            highlighter.removeAllHighlights()

            startPos = 0

            if response == 0:
                direction = "[forwards]"
                if searchWhat == self.lastSearch:
                    startPos = self.lastPosn
                    if lSwitch: startPos=startPos+len(searchWhat)+1
                self.lastSearch = searchWhat

                # if startPos+len(searchWhat) >= len(theText):
                #     startPos = 0
                #
                pos = theText.find(searchWhat.lower(),startPos)     # noqa
                myPrint("DB", "Search %s Pos: %s, searchWhat: '%s', startPos: %s, endPos: %s" %(direction, pos, searchWhat,startPos, -1))

            else:
                direction = "[backwards]"
                endPos = len(theText)-1

                if searchWhat == self.lastSearch:
                    if self.previousEndPosn < 0: self.previousEndPosn = len(theText)-1
                    endPos = max(0,self.previousEndPosn)
                    if lSwitch: endPos = max(0,self.lastPosn-1)

                self.lastSearch = searchWhat

                pos = theText.rfind(searchWhat.lower(),startPos,endPos)     # noqa
                myPrint("DB", "Search %s Pos: %s, searchWhat: '%s', startPos: %s, endPos: %s" %(direction, pos, searchWhat,startPos,endPos))

            if pos >= 0:
                self.searchJText.setCaretPosition(pos)
                try:
                    highlighter.addHighlight(pos,min(pos+len(searchWhat),len(theText)),DefaultHighlighter.DefaultPainter)
                except: pass
                if response == 0:
                    self.lastPosn = pos+len(searchWhat)
                    self.previousEndPosn = len(theText)-1
                else:
                    self.lastPosn = pos-len(searchWhat)
                    self.previousEndPosn = pos-1
            else:
                self.lastPosn = 0
                self.previousEndPosn = len(theText)-1
                myPopupInformationBox(self.theFrame,"Searching %s text not found" %direction)

            return

    def saveOutputFile(_theFrame, _theTitle, _fileName, _theText):

        theTitle = "Select location to save the current displayed output... (CANCEL=ABORT)"
        copyToFile = getFileFromFileChooser(_theFrame,          # Parent frame or None
                                            get_home_dir(),     # Starting path
                                            _fileName,          # Default Filename
                                            theTitle,           # Title
                                            False,              # Multi-file selection mode
                                            False,              # True for Open/Load, False for Save
                                            True,               # True = Files, else Dirs
                                            None,               # Load/Save button text, None for defaults
                                            "txt",              # File filter (non Mac only). Example: "txt" or "qif"
                                            lAllowTraversePackages=False,
                                            lForceJFC=False,
                                            lForceFD=True,
                                            lAllowNewFolderButton=True,
                                            lAllowOptionsButton=True)

        if copyToFile is None or copyToFile == "":
            return
        elif not safeStr(copyToFile).endswith(".txt"):
            myPopupInformationBox(_theFrame, "Sorry - please use a .txt file extension when saving output txt")
            return
        elif ".moneydance" in os.path.dirname(copyToFile):
            myPopupInformationBox(_theFrame, "Sorry, please choose a location outside of the Moneydance location")
            return

        if not check_file_writable(copyToFile):
            myPopupInformationBox(_theFrame, "Sorry, that file/location does not appear allowed by the operating system!?")

        toFile = copyToFile
        try:
            with open(toFile, 'w') as f: f.write(_theText)
            myPrint("B", "%s: text output copied to: %s" %(_theTitle, toFile))

            if os.path.exists(toFile):
                play_the_money_sound()
                txt = "%s: Output text saved as requested to: %s" %(_theTitle, toFile)
                setDisplayStatus(txt, "B")
                myPopupInformationBox(_theFrame, txt)
            else:
                txt = "ERROR - failed to write output text to file: %s" %(toFile)
                myPrint("B", txt)
                myPopupInformationBox(_theFrame, txt)
        except:
            txt = "ERROR - failed to write output text to file: %s" %(toFile)
            dump_sys_error_to_md_console_and_errorlog()
            myPopupInformationBox(_theFrame, txt)

        return

    if MD_REF_UI is not None:       # Only action if the UI is loaded - e.g. scripts (not run time extensions)
        try: GlobalVars.defaultPrintFontSize = eval("MD_REF.getUI().getFonts().print.getSize()")   # Do this here as MD_REF disappears after script ends...
        except: GlobalVars.defaultPrintFontSize = 12
    else:
        GlobalVars.defaultPrintFontSize = 12

    ####################################################################################################################
    # PRINTING UTILITIES...: Points to MM, to Inches, to Resolution: Conversion routines etc
    _IN2MM = 25.4; _IN2CM = 2.54; _IN2PT = 72
    def pt2dpi(_pt,_resolution):    return _pt * _resolution / _IN2PT
    def mm2pt(_mm):                 return _mm * _IN2PT / _IN2MM
    def mm2mpt(_mm):                return _mm * 1000 * _IN2PT / _IN2MM
    def pt2mm(_pt):                 return round(_pt * _IN2MM / _IN2PT, 1)
    def mm2in(_mm):                 return _mm / _IN2MM
    def in2mm(_in):                 return _in * _IN2MM
    def in2mpt(_in):                return _in * _IN2PT * 1000
    def in2pt(_in):                 return _in * _IN2PT
    def mpt2in(_mpt):               return _mpt / _IN2PT / 1000
    def mm2px(_mm, _resolution):    return mm2in(_mm) * _resolution
    def mpt2px(_mpt, _resolution):  return mpt2in(_mpt) * _resolution

    def printDeducePrintableWidth(_thePageFormat, _pAttrs):

        _BUFFER_PCT = 0.95

        myPrint("DB", "PageFormat after user dialog: Portrait=%s Landscape=%s W: %sMM(%spts) H: %sMM(%spts) Paper: %s Paper W: %sMM(%spts) H: %sMM(%spts)"
                %(_thePageFormat.getOrientation()==_thePageFormat.PORTRAIT, _thePageFormat.getOrientation()==_thePageFormat.LANDSCAPE,
                  pt2mm(_thePageFormat.getWidth()),_thePageFormat.getWidth(), pt2mm(_thePageFormat.getHeight()),_thePageFormat.getHeight(),
                  _thePageFormat.getPaper(),
                  pt2mm(_thePageFormat.getPaper().getWidth()), _thePageFormat.getPaper().getWidth(), pt2mm(_thePageFormat.getPaper().getHeight()), _thePageFormat.getPaper().getHeight()))

        if _pAttrs.get(attribute.standard.MediaSizeName):
            myPrint("DB", "Requested Media: %s" %(_pAttrs.get(attribute.standard.MediaSizeName)))

        if not _pAttrs.get(attribute.standard.MediaPrintableArea):
            raise Exception("ERROR: MediaPrintableArea not present in pAttrs!?")

        mediaPA = _pAttrs.get(attribute.standard.MediaPrintableArea)
        myPrint("DB", "MediaPrintableArea settings from Printer Attributes..: w%sMM h%sMM MediaPrintableArea: %s, getPrintableArea: %s "
                % (mediaPA.getWidth(attribute.standard.MediaPrintableArea.MM),
                   mediaPA.getHeight(attribute.standard.MediaPrintableArea.MM),
                   mediaPA, mediaPA.getPrintableArea(attribute.standard.MediaPrintableArea.MM)))

        if (_thePageFormat.getOrientation()==_thePageFormat.PORTRAIT):
            deducedWidthMM = mediaPA.getWidth(attribute.standard.MediaPrintableArea.MM)
        elif (_thePageFormat.getOrientation()==_thePageFormat.LANDSCAPE):
            deducedWidthMM = mediaPA.getHeight(attribute.standard.MediaPrintableArea.MM)
        else:
            raise Exception("ERROR: thePageFormat.getOrientation() was not PORTRAIT or LANDSCAPE!?")

        myPrint("DB","Paper Orientation: %s" %("LANDSCAPE" if _thePageFormat.getOrientation()==_thePageFormat.LANDSCAPE else "PORTRAIT"))

        _maxPaperWidthPTS = mm2px(deducedWidthMM, GlobalVars.defaultDPI)
        _maxPaperWidthPTS_buff = _maxPaperWidthPTS * _BUFFER_PCT

        myPrint("DB", "MediaPrintableArea: deduced printable width: %sMM(%sPTS) (using factor of *%s = %sPTS)" %(round(deducedWidthMM,1), round(_maxPaperWidthPTS,1), _BUFFER_PCT, _maxPaperWidthPTS_buff))
        return deducedWidthMM, _maxPaperWidthPTS, _maxPaperWidthPTS_buff

    def loadDefaultPrinterAttributes(_pAttrs=None):

        if _pAttrs is None:
            _pAttrs = attribute.HashPrintRequestAttributeSet()
        else:
            _pAttrs.clear()

        # Refer: https://docs.oracle.com/javase/7/docs/api/javax/print/attribute/standard/package-summary.html
        _pAttrs.add(attribute.standard.DialogTypeSelection.NATIVE)
        if GlobalVars.defaultPrintLandscape:
            _pAttrs.add(attribute.standard.OrientationRequested.LANDSCAPE)
        else:
            _pAttrs.add(attribute.standard.OrientationRequested.PORTRAIT)
        _pAttrs.add(attribute.standard.Chromaticity.MONOCHROME)
        _pAttrs.add(attribute.standard.JobSheets.NONE)
        _pAttrs.add(attribute.standard.Copies(1))
        _pAttrs.add(attribute.standard.PrintQuality.NORMAL)

        return _pAttrs

    def printOutputFile(_callingClass=None, _theTitle=None, _theJText=None, _theString=None):

        # Possible future modification, leverage MDPrinter, and it's classes / methods to save/load preferences and create printers
        try:
            if _theJText is None and _theString is None: return
            if _theJText is not None and len(_theJText.getText()) < 1: return
            if _theString is not None and len(_theString) < 1: return

            # Make a new one for printing
            if _theJText is not None:
                printJTextArea = JTextArea(_theJText.getText())
            else:
                printJTextArea = JTextArea(_theString)

            printJTextArea.setEditable(False)
            printJTextArea.setLineWrap(True)    # As we are reducing the font size so that the width fits the page width, this forces any remainder to wrap
            # if _callingClass is not None: printJTextArea.setLineWrap(_callingClass.lWrapText)  # Mirror the word wrap set by user
            printJTextArea.setWrapStyleWord(False)
            printJTextArea.setOpaque(False); printJTextArea.setBackground(Color(0,0,0,0)); printJTextArea.setForeground(Color.BLACK)
            printJTextArea.setBorder(EmptyBorder(0, 0, 0, 0))

            # IntelliJ doesnt like the use of 'print' (as it's a keyword)
            try:
                if "MD_REF" in globals():
                    usePrintFontSize = eval("MD_REF.getUI().getFonts().print.getSize()")
                elif "moneydance" in globals():
                    usePrintFontSize = eval("moneydance.getUI().getFonts().print.getSize()")
                else:
                    usePrintFontSize = GlobalVars.defaultPrintFontSize  # Just in case cleanup_references() has tidied up once script ended
            except:
                usePrintFontSize = 12   # Font print did not exist before build 3036

            theFontToUse = getMonoFont()       # Need Monospaced font, but with the font set in MD preferences for print
            theFontToUse = theFontToUse.deriveFont(float(usePrintFontSize))
            printJTextArea.setFont(theFontToUse)

            def computeFontSize(_theComponent, _maxPaperWidth, _dpi):

                # Auto shrink font so that text fits on one line when printing
                # Note: Java seems to operate it's maths at 72DPI (so must factor that into the maths)
                try:
                    _DEFAULT_MIN_WIDTH = mm2px(100, _dpi)   # 100MM
                    _minFontSize = 5                        # Below 5 too small
                    theString = _theComponent.getText()
                    _startingComponentFont = _theComponent.getFont()

                    if not theString or len(theString) < 1: return -1

                    fm = _theComponent.getFontMetrics(_startingComponentFont)
                    _maxFontSize = curFontSize = _startingComponentFont.getSize()   # Max out at the MD default for print font size saved in preferences
                    myPrint("DB","Print - starting font:", _startingComponentFont)
                    myPrint("DB","... calculating.... The starting/max font size is:", curFontSize)

                    maxLineWidthInFile = _DEFAULT_MIN_WIDTH
                    longestLine = ""
                    for line in theString.split("\n"):              # Look for the widest line adjusted for font style
                        _w = pt2dpi(fm.stringWidth(line), _dpi)
                        # myPrint("DB", "Found line (len: %s):" %(len(line)), line)
                        # myPrint("DB", "...calculated length metrics: %s/%sPTS (%sMM)" %(fm.stringWidth(line), _w, pt2mm(_w)))
                        if _w > maxLineWidthInFile:
                            longestLine = line
                            maxLineWidthInFile = _w
                    myPrint("DB","longest line width %s chars; maxLineWidthInFile now: %sPTS (%sMM)" %(len(longestLine),maxLineWidthInFile, pt2mm(maxLineWidthInFile)))

                    # Now shrink the font size to fit.....
                    while (pt2dpi(fm.stringWidth(longestLine) + 5,_dpi) > _maxPaperWidth):
                        myPrint("DB","At font size: %s; (pt2dpi(fm.stringWidth(longestLine) + 5,_dpi):" %(curFontSize), (pt2dpi(fm.stringWidth(longestLine) + 5,_dpi)), pt2mm(pt2dpi(fm.stringWidth(longestLine) + 5,_dpi)), "MM", " >> max width:", _maxPaperWidth)
                        curFontSize -= 1
                        fm = _theComponent.getFontMetrics(Font(_startingComponentFont.getName(), _startingComponentFont.getStyle(), curFontSize))
                        myPrint("DB","... next will be: at font size: %s; (pt2dpi(fm.stringWidth(longestLine) + 5,_dpi):" %(curFontSize), (pt2dpi(fm.stringWidth(longestLine) + 5,_dpi)), pt2mm(pt2dpi(fm.stringWidth(longestLine) + 5,_dpi)), "MM")

                        myPrint("DB","... calculating.... length of line still too long... reducing font size to:", curFontSize)
                        if curFontSize < _minFontSize:
                            myPrint("DB","... calculating... Next font size is too small... exiting the reduction loop...")
                            break

                    if not Platform.isMac():
                        curFontSize -= 1   # For some reason, sometimes on Linux/Windows still too big....
                        myPrint("DB","..knocking 1 off font size for good luck...! Now: %s" %(curFontSize))

                    # Code to increase width....
                    # while (pt2dpi(fm.stringWidth(theString) + 5,_dpi) < _maxPaperWidth):
                    #     curSize += 1
                    #     fm = _theComponent.getFontMetrics(Font(_startingComponentFont.getName(), _startingComponentFont.getStyle(), curSize))

                    curFontSize = max(_minFontSize, curFontSize); curFontSize = min(_maxFontSize, curFontSize)
                    myPrint("DB","... calculating.... Adjusted final font size to:", curFontSize)

                except:
                    myPrint("B", "ERROR: computeFontSize() crashed?"); dump_sys_error_to_md_console_and_errorlog()
                    return -1
                return curFontSize

            myPrint("DB", "Creating new PrinterJob...")
            printer_job = PrinterJob.getPrinterJob()

            if GlobalVars.defaultPrintService is not None:
                printer_job.setPrintService(GlobalVars.defaultPrintService)
                myPrint("DB","Assigned remembered PrintService...: %s" %(printer_job.getPrintService()))

            if GlobalVars.defaultPrinterAttributes is not None:
                pAttrs = attribute.HashPrintRequestAttributeSet(GlobalVars.defaultPrinterAttributes)
            else:
                pAttrs = loadDefaultPrinterAttributes(None)

            pAttrs.remove(attribute.standard.JobName)
            pAttrs.add(attribute.standard.JobName("%s: %s" %(myModuleID.capitalize(), _theTitle), None))

            if GlobalVars.defaultDPI != 72:
                pAttrs.remove(attribute.standard.PrinterResolution)
                pAttrs.add(attribute.standard.PrinterResolution(GlobalVars.defaultDPI, GlobalVars.defaultDPI, attribute.standard.PrinterResolution.DPI))

            for atr in pAttrs.toArray(): myPrint("DB", "Printer attributes before user dialog: %s:%s" %(atr.getName(), atr))

            if not printer_job.printDialog(pAttrs):
                myPrint("DB","User aborted the Print Dialog setup screen, so exiting...")
                return

            selectedPrintService = printer_job.getPrintService()
            myPrint("DB", "User selected print service:", selectedPrintService)

            thePageFormat = printer_job.getPageFormat(pAttrs)

            # .setPrintable() seems to modify pAttrs & adds MediaPrintableArea. Do this before printDeducePrintableWidth()
            header = MessageFormat(_theTitle)
            footer = MessageFormat("- page {0} -")
            printer_job.setPrintable(printJTextArea.getPrintable(header, footer), thePageFormat)    # Yes - we do this twice

            for atr in pAttrs.toArray(): myPrint("DB", "Printer attributes **AFTER** user dialog (and setPrintable): %s:%s" %(atr.getName(), atr))

            deducedWidthMM, maxPaperWidthPTS, maxPaperWidthPTS_buff = printDeducePrintableWidth(thePageFormat, pAttrs)

            if _callingClass is None or not _callingClass.lWrapText:

                newFontSize = computeFontSize(printJTextArea, int(maxPaperWidthPTS), GlobalVars.defaultDPI)

                if newFontSize > 0:
                    theFontToUse = theFontToUse.deriveFont(float(newFontSize))
                    printJTextArea.setFont(theFontToUse)

            # avoiding Intellij errors
            # eval("printJTextArea.print(header, footer, False, selectedPrintService, pAttrs, True)")  # If you do this, then native features like print to PDF will get ignored - so print via PrinterJob

            # Yup - calling .setPrintable() twice - before and after .computeFontSize()
            printer_job.setPrintable(printJTextArea.getPrintable(header, footer), thePageFormat)
            eval("printer_job.print(pAttrs)")

            del printJTextArea

            myPrint("DB", "Saving current print service:", printer_job.getPrintService())
            GlobalVars.defaultPrinterAttributes = attribute.HashPrintRequestAttributeSet(pAttrs)
            GlobalVars.defaultPrintService = printer_job.getPrintService()

        except:
            myPrint("B", "ERROR in printing routines.....:"); dump_sys_error_to_md_console_and_errorlog()
        return

    def pageSetup():

        myPrint("DB","Printer Page setup routines..:")

        myPrint("DB", 'NOTE: A4        210mm x 297mm	8.3" x 11.7"	Points: w595 x h842')
        myPrint("DB", 'NOTE: Letter    216mm x 279mm	8.5" x 11.0"	Points: w612 x h791')

        pj = PrinterJob.getPrinterJob()

        # Note: PrintService is not used/remembered/set by .pageDialog

        if GlobalVars.defaultPrinterAttributes is not None:
            pAttrs = attribute.HashPrintRequestAttributeSet(GlobalVars.defaultPrinterAttributes)
        else:
            pAttrs = loadDefaultPrinterAttributes(None)

        for atr in pAttrs.toArray(): myPrint("DB", "Printer attributes before Page Setup: %s:%s" %(atr.getName(), atr))

        if not pj.pageDialog(pAttrs):
            myPrint("DB", "User cancelled Page Setup - exiting...")
            return

        for atr in pAttrs.toArray(): myPrint("DB", "Printer attributes **AFTER** Page Setup: %s:%s" %(atr.getName(), atr))

        if debug: printDeducePrintableWidth(pj.getPageFormat(pAttrs), pAttrs)

        myPrint("DB", "Printer selected: %s" %(pj.getPrintService()))

        GlobalVars.defaultPrinterAttributes = attribute.HashPrintRequestAttributeSet(pAttrs)
        myPrint("DB", "Printer Attributes saved....")

        return

    class SetupMDColors:

        OPAQUE = None
        FOREGROUND = None
        FOREGROUND_REVERSED = None
        BACKGROUND = None
        BACKGROUND_REVERSED = None

        def __init__(self): raise Exception("ERROR - Should not create instance of this class!")

        @staticmethod
        def updateUI():
            myPrint("DB", "In ", inspect.currentframe().f_code.co_name, "()")

            SetupMDColors.OPAQUE = False

            SetupMDColors.FOREGROUND = GlobalVars.CONTEXT.getUI().getColors().defaultTextForeground
            SetupMDColors.FOREGROUND_REVERSED = SetupMDColors.FOREGROUND

            SetupMDColors.BACKGROUND = GlobalVars.CONTEXT.getUI().getColors().defaultBackground
            SetupMDColors.BACKGROUND_REVERSED = SetupMDColors.BACKGROUND

            if ((not isMDThemeVAQua() and not isMDThemeDark() and isMacDarkModeDetected())
                    or (not isMacDarkModeDetected() and isMDThemeDarcula())):
                SetupMDColors.FOREGROUND_REVERSED = GlobalVars.CONTEXT.getUI().colors.defaultBackground
                SetupMDColors.BACKGROUND_REVERSED = GlobalVars.CONTEXT.getUI().colors.defaultTextForeground

    global ManuallyCloseAndReloadDataset            # Declare it for QuickJFrame/IDE, but not present in common code. Other code will ignore it

    class GetFirstMainFrame:

        DEFAULT_MAX_WIDTH = 1024
        DEFAULT_MAX_HEIGHT = 768

        def __init__(self): raise Exception("ERROR: DO NOT CREATE INSTANCE OF GetFirstMainFrame!")

        @staticmethod
        def getSize(defaultWidth=None, defaultHeight=None):
            if defaultWidth is None: defaultWidth = GetFirstMainFrame.DEFAULT_MAX_WIDTH
            if defaultHeight is None: defaultHeight = GetFirstMainFrame.DEFAULT_MAX_HEIGHT
            try:
                firstMainFrame = MD_REF.getUI().firstMainFrame
                return firstMainFrame.getSize()
            except: pass
            return Dimension(defaultWidth, defaultHeight)

        @staticmethod
        def getSelectedAccount():
            try:
                firstMainFrame = MD_REF.getUI().firstMainFrame
                return firstMainFrame.getSelectedAccount()
            except: pass
            return None

    class QuickJFrame():

        def __init__(self,
                     title,
                     output,
                     lAlertLevel=0,
                     copyToClipboard=False,
                     lJumpToEnd=False,
                     lWrapText=True,
                     lQuitMDAfterClose=False,
                     lRestartMDAfterClose=False,
                     screenLocation=None,
                     lAutoSize=False):
            self.title = title
            self.output = output
            self.lAlertLevel = lAlertLevel
            self.returnFrame = None
            self.copyToClipboard = copyToClipboard
            self.lJumpToEnd = lJumpToEnd
            self.lWrapText = lWrapText
            self.lQuitMDAfterClose = lQuitMDAfterClose
            self.lRestartMDAfterClose = lRestartMDAfterClose
            self.screenLocation = screenLocation
            self.lAutoSize = lAutoSize
            # if Platform.isOSX() and int(float(MD_REF.getBuild())) >= 3039: self.lAlertLevel = 0    # Colors don't work on Mac since VAQua
            if isMDThemeDark() or isMacDarkModeDetected(): self.lAlertLevel = 0

        class QJFWindowListener(WindowAdapter):

            def __init__(self, theFrame, lQuitMDAfterClose=False, lRestartMDAfterClose=False):
                self.theFrame = theFrame
                self.lQuitMDAfterClose = lQuitMDAfterClose
                self.lRestartMDAfterClose = lRestartMDAfterClose
                self.saveMD_REF = MD_REF

            def windowClosing(self, WindowEvent):                                                                       # noqa
                myPrint("DB", "In ", inspect.currentframe().f_code.co_name, "()", "Event: ", WindowEvent)
                myPrint("DB", "SwingUtilities.isEventDispatchThread() = %s" %(SwingUtilities.isEventDispatchThread()))

                myPrint("DB", "QuickJFrame() Frame shutting down.... Calling .dispose()")
                self.theFrame.dispose()

                myPrint("D", "Exiting ", inspect.currentframe().f_code.co_name, "()")

            def windowClosed(self, WindowEvent):                                                                       # noqa
                myPrint("DB","In ", inspect.currentframe().f_code.co_name, "()")
                myPrint("DB", "... SwingUtilities.isEventDispatchThread() returns: %s" %(SwingUtilities.isEventDispatchThread()))

                if self.lQuitMDAfterClose or self.lRestartMDAfterClose:
                    if "ManuallyCloseAndReloadDataset" not in globals():
                        myPrint("DB", "'ManuallyCloseAndReloadDataset' not in globals(), so just exiting MD the easy way...")
                        myPrint("B", "@@ EXITING MONEYDANCE @@")
                        MD_REF.getUI().exit()
                    else:
                        if self.lQuitMDAfterClose:
                            myPrint("B", "Quit MD after Close triggered... Now quitting MD")
                            ManuallyCloseAndReloadDataset.moneydanceExitOrRestart(lRestart=False)
                        elif self.lRestartMDAfterClose:
                            myPrint("B", "Restart MD after Close triggered... Now restarting MD")
                            ManuallyCloseAndReloadDataset.moneydanceExitOrRestart(lRestart=True)
                else:
                    myPrint("DB", "FYI No Quit MD after Close triggered... So doing nothing...")

        class CloseAction(AbstractAction):

            def __init__(self, theFrame):
                self.theFrame = theFrame

            def actionPerformed(self, event):
                myPrint("D","in CloseAction(), Event: ", event)
                myPrint("DB", "QuickJFrame() Frame shutting down....")

                try:
                    if not SwingUtilities.isEventDispatchThread():
                        SwingUtilities.invokeLater(GenericDisposeRunnable(self.theFrame))
                    else:
                        self.theFrame.dispose()
                except:
                    myPrint("B","Error. QuickJFrame dispose failed....?")
                    dump_sys_error_to_md_console_and_errorlog()


        class ToggleWrap(AbstractAction):

            def __init__(self, theCallingClass, theJText):
                self.theCallingClass = theCallingClass
                self.theJText = theJText

            def actionPerformed(self, event):
                myPrint("D", "In ", inspect.currentframe().f_code.co_name, "()", "Event: ", event )

                self.theCallingClass.lWrapText = not self.theCallingClass.lWrapText
                self.theJText.setLineWrap(self.theCallingClass.lWrapText)

        class QuickJFrameNavigate(AbstractAction):

            def __init__(self, theJText, lTop=False, lBottom=False):
                self.theJText = theJText
                self.lTop = lTop
                self.lBottom = lBottom

            def actionPerformed(self, event):
                myPrint("D", "In ", inspect.currentframe().f_code.co_name, "()", "Event: ", event )

                if self.lBottom: self.theJText.setCaretPosition(self.theJText.getDocument().getLength())
                if self.lTop:    self.theJText.setCaretPosition(0)

        class QuickJFramePrint(AbstractAction):

            def __init__(self, theCallingClass, theJText, theTitle=""):
                self.theCallingClass = theCallingClass
                self.theJText = theJText
                self.theTitle = theTitle

            def actionPerformed(self, event):
                myPrint("D", "In ", inspect.currentframe().f_code.co_name, "()", "Event: ", event )
                printOutputFile(_callingClass=self.theCallingClass, _theTitle=self.theTitle, _theJText=self.theJText)

        class QuickJFramePageSetup(AbstractAction):

            def __init__(self): pass

            def actionPerformed(self, event):
                myPrint("D", "In ", inspect.currentframe().f_code.co_name, "()", "Event: ", event )
                pageSetup()

        class QuickJFrameSaveTextToFile(AbstractAction):

            def __init__(self, theText, callingFrame):
                self.theText = theText
                self.callingFrame = callingFrame

            def actionPerformed(self, event):
                myPrint("D", "In ", inspect.currentframe().f_code.co_name, "()", "Event: ", event )
                saveOutputFile(self.callingFrame, "QUICKJFRAME", "%s_output.txt" %(myModuleID), self.theText)

        def show_the_frame(self):

            class MyQuickJFrameRunnable(Runnable):

                def __init__(self, callingClass):
                    self.callingClass = callingClass

                def run(self):                                                                                          # noqa
                    screenSize = Toolkit.getDefaultToolkit().getScreenSize()
                    frame_width = min(screenSize.width-20, max(GetFirstMainFrame.DEFAULT_MAX_WIDTH, int(round(GetFirstMainFrame.getSize().width *.9,0))))
                    frame_height = min(screenSize.height-20, max(GetFirstMainFrame.DEFAULT_MAX_HEIGHT, int(round(GetFirstMainFrame.getSize().height *.9,0))))

                    # JFrame.setDefaultLookAndFeelDecorated(True)   # Note: Darcula Theme doesn't like this and seems to be OK without this statement...
                    if self.callingClass.lQuitMDAfterClose:
                        extraText =  ">> MD WILL QUIT AFTER VIEWING THIS <<"
                    elif self.callingClass.lRestartMDAfterClose:
                        extraText =  ">> MD WILL RESTART AFTER VIEWING THIS <<"
                    else:
                        extraText = ""

                    jInternalFrame = MyJFrame(self.callingClass.title + " (%s+F to find/search for text)%s" %(MD_REF.getUI().ACCELERATOR_MASK_STR, extraText))
                    jInternalFrame.setName(u"%s_quickjframe" %myModuleID)

                    if not Platform.isOSX(): jInternalFrame.setIconImage(MDImages.getImage(MD_REF.getSourceInformation().getIconResource()))

                    jInternalFrame.setDefaultCloseOperation(WindowConstants.DO_NOTHING_ON_CLOSE)
                    jInternalFrame.setResizable(True)

                    shortcut = Toolkit.getDefaultToolkit().getMenuShortcutKeyMaskEx()
                    jInternalFrame.getRootPane().getInputMap(JComponent.WHEN_ANCESTOR_OF_FOCUSED_COMPONENT).put(KeyStroke.getKeyStroke(KeyEvent.VK_W,  shortcut), "close-window")
                    jInternalFrame.getRootPane().getInputMap(JComponent.WHEN_ANCESTOR_OF_FOCUSED_COMPONENT).put(KeyStroke.getKeyStroke(KeyEvent.VK_F4, shortcut), "close-window")
                    jInternalFrame.getRootPane().getInputMap(JComponent.WHEN_ANCESTOR_OF_FOCUSED_COMPONENT).put(KeyStroke.getKeyStroke(KeyEvent.VK_F,  shortcut), "search-window")
                    jInternalFrame.getRootPane().getInputMap(JComponent.WHEN_ANCESTOR_OF_FOCUSED_COMPONENT).put(KeyStroke.getKeyStroke(KeyEvent.VK_P, shortcut),  "print-me")
                    jInternalFrame.getRootPane().getInputMap(JComponent.WHEN_IN_FOCUSED_WINDOW).put(KeyStroke.getKeyStroke(KeyEvent.VK_ESCAPE, 0), "close-window")

                    theJText = JTextArea(self.callingClass.output)
                    theJText.setEditable(False)
                    theJText.setLineWrap(self.callingClass.lWrapText)
                    theJText.setWrapStyleWord(False)
                    theJText.setFont( getMonoFont() )

                    jInternalFrame.getRootPane().getActionMap().put("close-window", self.callingClass.CloseAction(jInternalFrame))
                    jInternalFrame.getRootPane().getActionMap().put("search-window", SearchAction(jInternalFrame,theJText))
                    jInternalFrame.getRootPane().getActionMap().put("print-me", self.callingClass.QuickJFramePrint(self.callingClass, theJText, self.callingClass.title))
                    jInternalFrame.addWindowListener(self.callingClass.QJFWindowListener(jInternalFrame, self.callingClass.lQuitMDAfterClose, self.callingClass.lRestartMDAfterClose))

                    internalScrollPane = JScrollPane(theJText, JScrollPane.VERTICAL_SCROLLBAR_AS_NEEDED,JScrollPane.HORIZONTAL_SCROLLBAR_AS_NEEDED)

                    if self.callingClass.lAlertLevel>=2:
                        # internalScrollPane.setBackground(Color.RED)
                        theJText.setBackground(Color.RED)
                        theJText.setForeground(Color.BLACK)
                        theJText.setOpaque(True)
                    elif self.callingClass.lAlertLevel>=1:
                        # internalScrollPane.setBackground(Color.YELLOW)
                        theJText.setBackground(Color.YELLOW)
                        theJText.setForeground(Color.BLACK)
                        theJText.setOpaque(True)

                    if not self.callingClass.lAutoSize:
                        jInternalFrame.setPreferredSize(Dimension(frame_width, frame_height))

                    SetupMDColors.updateUI()

                    printButton = JButton("Print")
                    printButton.setToolTipText("Prints the output displayed in this window to your printer")
                    printButton.setOpaque(SetupMDColors.OPAQUE)
                    printButton.setBackground(SetupMDColors.BACKGROUND); printButton.setForeground(SetupMDColors.FOREGROUND)
                    printButton.addActionListener(self.callingClass.QuickJFramePrint(self.callingClass, theJText, self.callingClass.title))

                    if GlobalVars.defaultPrinterAttributes is None:
                        printPageSetup = JButton("Page Setup")
                        printPageSetup.setToolTipText("Printer Page Setup")
                        printPageSetup.setOpaque(SetupMDColors.OPAQUE)
                        printPageSetup.setBackground(SetupMDColors.BACKGROUND); printPageSetup.setForeground(SetupMDColors.FOREGROUND)
                        printPageSetup.addActionListener(self.callingClass.QuickJFramePageSetup())

                    saveButton = JButton("Save to file")
                    saveButton.setToolTipText("Saves the output displayed in this window to a file")
                    saveButton.setOpaque(SetupMDColors.OPAQUE)
                    saveButton.setBackground(SetupMDColors.BACKGROUND); saveButton.setForeground(SetupMDColors.FOREGROUND)
                    saveButton.addActionListener(self.callingClass.QuickJFrameSaveTextToFile(self.callingClass.output, jInternalFrame))

                    wrapOption = JCheckBox("Wrap Contents (Screen & Print)", self.callingClass.lWrapText)
                    wrapOption.addActionListener(self.callingClass.ToggleWrap(self.callingClass, theJText))
                    wrapOption.setForeground(SetupMDColors.FOREGROUND_REVERSED); wrapOption.setBackground(SetupMDColors.BACKGROUND_REVERSED)

                    topButton = JButton("Top")
                    topButton.setOpaque(SetupMDColors.OPAQUE)
                    topButton.setBackground(SetupMDColors.BACKGROUND); topButton.setForeground(SetupMDColors.FOREGROUND)
                    topButton.addActionListener(self.callingClass.QuickJFrameNavigate(theJText, lTop=True))

                    botButton = JButton("Bottom")
                    botButton.setOpaque(SetupMDColors.OPAQUE)
                    botButton.setBackground(SetupMDColors.BACKGROUND); botButton.setForeground(SetupMDColors.FOREGROUND)
                    botButton.addActionListener(self.callingClass.QuickJFrameNavigate(theJText, lBottom=True))

                    closeButton = JButton("Close")
                    closeButton.setOpaque(SetupMDColors.OPAQUE)
                    closeButton.setBackground(SetupMDColors.BACKGROUND); closeButton.setForeground(SetupMDColors.FOREGROUND)
                    closeButton.addActionListener(self.callingClass.CloseAction(jInternalFrame))

                    if Platform.isOSX():
                        save_useScreenMenuBar= System.getProperty("apple.laf.useScreenMenuBar")
                        if save_useScreenMenuBar is None or save_useScreenMenuBar == "":
                            save_useScreenMenuBar= System.getProperty("com.apple.macos.useScreenMenuBar")
                        System.setProperty("apple.laf.useScreenMenuBar", "false")
                        System.setProperty("com.apple.macos.useScreenMenuBar", "false")
                    else:
                        save_useScreenMenuBar = "true"

                    mb = JMenuBar()
                    mb.setBorder(EmptyBorder(0, 0, 0, 0))
                    mb.add(Box.createRigidArea(Dimension(10, 0)))
                    mb.add(topButton)
                    mb.add(Box.createRigidArea(Dimension(10, 0)))
                    mb.add(botButton)
                    mb.add(Box.createHorizontalGlue())
                    mb.add(wrapOption)

                    if GlobalVars.defaultPrinterAttributes is None:
                        mb.add(Box.createRigidArea(Dimension(10, 0)))
                        mb.add(printPageSetup)                                                                          # noqa

                    mb.add(Box.createHorizontalGlue())
                    mb.add(printButton)
                    mb.add(Box.createRigidArea(Dimension(10, 0)))
                    mb.add(saveButton)
                    mb.add(Box.createRigidArea(Dimension(10, 0)))
                    mb.add(closeButton)
                    mb.add(Box.createRigidArea(Dimension(30, 0)))

                    jInternalFrame.setJMenuBar(mb)

                    jInternalFrame.add(internalScrollPane)

                    jInternalFrame.pack()
                    if self.callingClass.screenLocation and isinstance(self.callingClass.screenLocation, Point):
                        jInternalFrame.setLocation(self.callingClass.screenLocation)
                    else:
                        jInternalFrame.setLocationRelativeTo(None)

                    jInternalFrame.setVisible(True)

                    if Platform.isOSX():
                        System.setProperty("apple.laf.useScreenMenuBar", save_useScreenMenuBar)
                        System.setProperty("com.apple.macos.useScreenMenuBar", save_useScreenMenuBar)

                    if "errlog.txt" in self.callingClass.title or self.callingClass.lJumpToEnd:
                        theJText.setCaretPosition(theJText.getDocument().getLength())

                    try:
                        if self.callingClass.copyToClipboard:
                            Toolkit.getDefaultToolkit().getSystemClipboard().setContents(StringSelection(self.callingClass.output), None)
                    except:
                        myPrint("J","Error copying contents to Clipboard")
                        dump_sys_error_to_md_console_and_errorlog()

                    self.callingClass.returnFrame = jInternalFrame

            if not SwingUtilities.isEventDispatchThread():
                myPrint("DB",".. Not running within the EDT so calling via MyQuickJFrameRunnable()...")
                SwingUtilities.invokeAndWait(MyQuickJFrameRunnable(self))
            else:
                myPrint("DB",".. Already within the EDT so calling naked...")
                MyQuickJFrameRunnable(self).run()

            return (self.returnFrame)

    class AboutThisScript(AbstractAction, Runnable):

        def __init__(self, theFrame):
            self.theFrame = theFrame
            self.aboutDialog = None

        def actionPerformed(self, event):
            myPrint("DB", "In ", inspect.currentframe().f_code.co_name, "()", "Event:", event)
            self.aboutDialog.dispose()  # Listener is already on the Swing EDT...

        def go(self):
            myPrint("DB", "In ", inspect.currentframe().f_code.co_name, "()")

            if not SwingUtilities.isEventDispatchThread():
                myPrint("DB",".. Not running within the EDT so calling via MyAboutRunnable()...")
                SwingUtilities.invokeAndWait(self)
            else:
                myPrint("DB",".. Already within the EDT so calling naked...")
                self.run()

        def run(self):                                                                                                  # noqa
            myPrint("DB", "In ", inspect.currentframe().f_code.co_name, "()")
            myPrint("DB", "SwingUtilities.isEventDispatchThread() = %s" %(SwingUtilities.isEventDispatchThread()))

            # noinspection PyUnresolvedReferences
            self.aboutDialog = JDialog(self.theFrame, "About", Dialog.ModalityType.MODELESS)

            shortcut = Toolkit.getDefaultToolkit().getMenuShortcutKeyMaskEx()
            self.aboutDialog.getRootPane().getInputMap(JComponent.WHEN_ANCESTOR_OF_FOCUSED_COMPONENT).put(KeyStroke.getKeyStroke(KeyEvent.VK_W, shortcut), "close-window")
            self.aboutDialog.getRootPane().getInputMap(JComponent.WHEN_ANCESTOR_OF_FOCUSED_COMPONENT).put(KeyStroke.getKeyStroke(KeyEvent.VK_F4, shortcut), "close-window")
            self.aboutDialog.getRootPane().getInputMap(JComponent.WHEN_IN_FOCUSED_WINDOW).put(KeyStroke.getKeyStroke(KeyEvent.VK_ESCAPE, 0), "close-window")

            self.aboutDialog.getRootPane().getActionMap().put("close-window", self)
            self.aboutDialog.setDefaultCloseOperation(WindowConstants.DISPOSE_ON_CLOSE)

            if (not Platform.isMac()):
                # MD_REF.getUI().getImages()
                self.aboutDialog.setIconImage(MDImages.getImage(MD_REF.getSourceInformation().getIconResource()))

            aboutPanel = JPanel()
            aboutPanel.setLayout(FlowLayout(FlowLayout.LEFT))
            aboutPanel.setPreferredSize(Dimension(1120, 550))

            _label1 = JLabel(pad("Author: Stuart Beesley", 800))
            _label1.setForeground(getColorBlue())
            aboutPanel.add(_label1)

            _label2 = JLabel(pad("StuWareSoftSystems (2020-2022)", 800))
            _label2.setForeground(getColorBlue())
            aboutPanel.add(_label2)

            _label3 = JLabel(pad("Script/Extension: %s (build: %s)" %(GlobalVars.thisScriptName, version_build), 800))
            _label3.setForeground(getColorBlue())
            aboutPanel.add(_label3)

            displayString=scriptExit
            displayJText = JTextArea(displayString)
            displayJText.setFont( getMonoFont() )
            displayJText.setEditable(False)
            displayJText.setLineWrap(False)
            displayJText.setWrapStyleWord(False)
            displayJText.setMargin(Insets(8, 8, 8, 8))

            aboutPanel.add(displayJText)

            self.aboutDialog.add(aboutPanel)

            self.aboutDialog.pack()
            self.aboutDialog.setLocationRelativeTo(None)
            self.aboutDialog.setVisible(True)

            myPrint("D", "Exiting ", inspect.currentframe().f_code.co_name, "()")

    def isGoodRate(theRate):

        if Double.isNaN(theRate) or Double.isInfinite(theRate) or theRate == 0:
            return False
        return True

    def safeInvertRate(theRate):

        if not isGoodRate(theRate):
            return theRate
        return (1.0 / theRate)

    def convertBytesGBs(_size): return round((_size/(1000.0*1000.0*1000)),1)

    def convertBytesMBs(_size): return round((_size/(1000.0*1000.0)),1)

    def convertBytesKBs(_size): return round((_size/(1000.0)),1)

    def convertMDShortDateFormat_strftimeFormat(lIncludeTime=False, lForceYYMMDDHMS=False):
        """Returns a Python strftime format string in accordance with MD Preferences for Date Format"""
        # https://strftime.org

        _MDFormat = MD_REF.getPreferences().getShortDateFormat()

        rtnFormat = "%Y-%m-%d"

        if lForceYYMMDDHMS:
            lIncludeTime = True
        else:
            if _MDFormat == "MM/dd/yyyy":
                rtnFormat = "%m/%d/%Y"
            elif _MDFormat == "MM.dd.yyyy":
                rtnFormat = "%m.%d.%Y"
            elif _MDFormat == "yyyy/MM/dd":
                rtnFormat = "%Y/%m/%d"
            elif _MDFormat == "yyyy.MM.dd":
                rtnFormat = "%Y.%m.%d"
            elif _MDFormat == "dd/MM/yyyy":
                rtnFormat = "%d/%m/%Y"
            elif _MDFormat == "dd.MM.yyyy":
                rtnFormat = "%d.%m.%Y"

        if lIncludeTime: rtnFormat += " %H:%M:%S"
        return rtnFormat

    def getHumanReadableDateTimeFromTimeStamp(_theTimeStamp, lIncludeTime=False, lForceYYMMDDHMS=False):
        return datetime.datetime.fromtimestamp(_theTimeStamp).strftime(convertMDShortDateFormat_strftimeFormat(lIncludeTime=lIncludeTime, lForceYYMMDDHMS=lForceYYMMDDHMS))

    def getHumanReadableModifiedDateTimeFromFile(_theFile, lIncludeTime=True, lForceYYMMDDHMS=True):
        return getHumanReadableDateTimeFromTimeStamp(os.path.getmtime(_theFile), lIncludeTime=lIncludeTime, lForceYYMMDDHMS=lForceYYMMDDHMS)

    def convertStrippedIntDateFormattedText(strippedDateInt, _format=None):

        # if _format is None: _format = "yyyy/MM/dd"
        if _format is None: _format = MD_REF.getPreferences().getShortDateFormat()

        if strippedDateInt is None or strippedDateInt == 0:
            return "<not set>"

        try:
            c = Calendar.getInstance()
            dateFromInt = DateUtil.convertIntDateToLong(strippedDateInt)
            c.setTime(dateFromInt)
            dateFormatter = SimpleDateFormat(_format)
            convertedDate = dateFormatter.format(c.getTime())
        except:
            return "<error>"

        return convertedDate

    def selectHomeScreen():

        try:
            currentViewAccount = MD_REF.getUI().firstMainFrame.getSelectedAccount()
            if currentViewAccount != MD_REF.getRootAccount():
                myPrint("DB","Switched to Home Page Summary Page (from: %s)" %(currentViewAccount))
                MD_REF.getUI().firstMainFrame.selectAccount(MD_REF.getRootAccount())
        except:
            myPrint("B","@@ Error switching to Summary Page (Home Page)")

    def fireMDPreferencesUpdated():
        """This triggers MD to firePreferencesUpdated().... Hopefully refreshing Home Screen Views too"""
        myPrint("DB", "In ", inspect.currentframe().f_code.co_name, "()" )

        class FPSRunnable(Runnable):
            def __init__(self): pass

            def run(self):
                myPrint("DB",".. Inside FPSRunnable() - calling firePreferencesUpdated()...")
                myPrint("B","Triggering an update to the Summary/Home Page View")
                MD_REF.getPreferences().firePreferencesUpdated()

        if not SwingUtilities.isEventDispatchThread():
            myPrint("DB",".. Not running within the EDT so calling via FPSRunnable()...")
            SwingUtilities.invokeLater(FPSRunnable())
        else:
            myPrint("DB",".. Already running within the EDT so calling FPSRunnable() naked...")
            FPSRunnable().run()
        return

    def decodeCommand(passedEvent):
        param = ""
        uri = passedEvent
        command = uri
        theIdx = uri.find('?')
        if(theIdx>=0):
            command = uri[:theIdx]
            param = uri[theIdx+1:]
        else:
            theIdx = uri.find(':')
            if(theIdx>=0):
                command = uri[:theIdx]
                param = uri[theIdx+1:]
        return command, param

    def getFieldByReflection(theObj, fieldName, isInt=False):
        try: theClass = theObj.getClass()
        except TypeError: theClass = theObj     # This catches where the object is already the Class
        reflectField = None
        while theClass is not None:
            try:
                reflectField = theClass.getDeclaredField(fieldName)
                break
            except NoSuchFieldException:
                theClass = theClass.getSuperclass()
        if reflectField is None: raise Exception("ERROR: could not find field: %s in class hierarchy" %(fieldName))
        if Modifier.isPrivate(reflectField.getModifiers()): reflectField.setAccessible(True)
        elif Modifier.isProtected(reflectField.getModifiers()): reflectField.setAccessible(True)
        isStatic = Modifier.isStatic(reflectField.getModifiers())
        if isInt: return reflectField.getInt(theObj if not isStatic else None)
        return reflectField.get(theObj if not isStatic else None)

    def invokeMethodByReflection(theObj, methodName, params, *args):
        try: theClass = theObj.getClass()
        except TypeError: theClass = theObj     # This catches where the object is already the Class
        reflectMethod = None
        while theClass is not None:
            try:
                if params is None:
                    reflectMethod = theClass.getDeclaredMethod(methodName)
                    break
                else:
                    reflectMethod = theClass.getDeclaredMethod(methodName, params)
                    break
            except NoSuchMethodException:
                theClass = theClass.getSuperclass()
        if reflectMethod is None: raise Exception("ERROR: could not find method: %s in class hierarchy" %(methodName))
        reflectMethod.setAccessible(True)
        return reflectMethod.invoke(theObj, *args)

    def setFieldByReflection(theObj, fieldName, newValue):
        try: theClass = theObj.getClass()
        except TypeError: theClass = theObj     # This catches where the object is already the Class
        reflectField = None
        while theClass is not None:
            try:
                reflectField = theClass.getDeclaredField(fieldName)
                break
            except NoSuchFieldException:
                theClass = theClass.getSuperclass()
        if reflectField is None: raise Exception("ERROR: could not find field: %s in class hierarchy" %(fieldName))
        if Modifier.isPrivate(reflectField.getModifiers()): reflectField.setAccessible(True)
        elif Modifier.isProtected(reflectField.getModifiers()): reflectField.setAccessible(True)
        isStatic = Modifier.isStatic(reflectField.getModifiers())
        return reflectField.set(theObj if not isStatic else None, newValue)

    def find_feature_module(theModule):
        # type: (str) -> bool
        """Searches Moneydance for a specific extension loaded"""
        fms = MD_REF.getLoadedModules()
        for fm in fms:
            if fm.getIDStr().lower() == theModule:
                myPrint("DB", "Found extension: %s" %(theModule))
                return fm
        return None

    def isMDPlusEnabledBuild(): return (float(MD_REF.getBuild()) >= GlobalVars.MD_MDPLUS_BUILD)

    def isAlertControllerEnabledBuild(): return (float(MD_REF.getBuild()) >= GlobalVars.MD_ALERTCONTROLLER_BUILD)

    def shutdownMDPlusPoller():
        if isMDPlusEnabledBuild():
            myPrint("DB", "Shutting down the MD+ poller")
            plusPoller = MD_REF.getUI().getPlusController()
            if plusPoller is not None:
                invokeMethodByReflection(plusPoller, "shutdown", None)
                setFieldByReflection(MD_REF.getUI(), "plusPoller", None)
            # NOTE: MDPlus.licenseCache should be reset too, but it's a 'private static final' field....
            #       hence restart MD if changing (importing/zapping) the license object
            myPrint("DB", "... MD+ poller shutdown...")

    def shutdownMDAlertController():
        if isAlertControllerEnabledBuild():
            myPrint("DB", "Shutting down the Alert Controller")
            alertController = MD_REF.getUI().getAlertController()
            if alertController is not None:
                invokeMethodByReflection(alertController, "shutdown", None)
                setFieldByReflection(MD_REF.getUI(), "alertController", None)

    # END COMMON DEFINITIONS ###############################################################################################
    # END COMMON DEFINITIONS ###############################################################################################
    # END COMMON DEFINITIONS ###############################################################################################
    # COPY >> END

    # >>> CUSTOMISE & DO THIS FOR EACH SCRIPT
    # >>> CUSTOMISE & DO THIS FOR EACH SCRIPT
    # >>> CUSTOMISE & DO THIS FOR EACH SCRIPT
    def load_StuWareSoftSystems_parameters_into_memory():

        # >>> THESE ARE THIS SCRIPT's PARAMETERS TO LOAD - Common variables
        global lAllowEscapeExitApp_SWSS

        # >>> THESE ARE THIS SCRIPT's PARAMETERS TO LOAD
        global __list_future_reminders, _column_widths_LFR, daysToLookForward_LFR

        myPrint("D", "In ", inspect.currentframe().f_code.co_name, "()" )
        myPrint("DB", "Loading variables into memory...")

        if GlobalVars.parametersLoadedFromFile is None: GlobalVars.parametersLoadedFromFile = {}

        if GlobalVars.parametersLoadedFromFile.get("__list_future_reminders") is not None: __list_future_reminders = GlobalVars.parametersLoadedFromFile.get("__list_future_reminders")

        if GlobalVars.parametersLoadedFromFile.get("lAllowEscapeExitApp_SWSS") is not None: lAllowEscapeExitApp_SWSS = GlobalVars.parametersLoadedFromFile.get("lAllowEscapeExitApp_SWSS")

        if GlobalVars.parametersLoadedFromFile.get("_column_widths_LFR") is not None: _column_widths_LFR = GlobalVars.parametersLoadedFromFile.get("_column_widths_LFR")
        if GlobalVars.parametersLoadedFromFile.get("daysToLookForward_LFR") is not None: daysToLookForward_LFR = GlobalVars.parametersLoadedFromFile.get("daysToLookForward_LFR")

        myPrint("DB","parametersLoadedFromFile{} set into memory (as variables).....")

        return

    # >>> CUSTOMISE & DO THIS FOR EACH SCRIPT
    def dump_StuWareSoftSystems_parameters_from_memory():

        myPrint("D", "In ", inspect.currentframe().f_code.co_name, "()" )

        # NOTE: Parameters were loaded earlier on... Preserve existing, and update any used ones...
        # (i.e. other StuWareSoftSystems programs might be sharing the same file)

        if GlobalVars.parametersLoadedFromFile is None: GlobalVars.parametersLoadedFromFile = {}

        GlobalVars.parametersLoadedFromFile["__list_future_reminders"] = version_build
        GlobalVars.parametersLoadedFromFile["lAllowEscapeExitApp_SWSS"] = lAllowEscapeExitApp_SWSS
        GlobalVars.parametersLoadedFromFile["_column_widths_LFR"] = _column_widths_LFR
        GlobalVars.parametersLoadedFromFile["daysToLookForward_LFR"] = daysToLookForward_LFR

        myPrint("DB","variables dumped from memory back into parametersLoadedFromFile{}.....")

        return

    get_StuWareSoftSystems_parameters_from_file()

    # clear up any old left-overs....
    destroyOldFrames(myModuleID)

    myPrint("DB", "DEBUG IS ON..")

    if SwingUtilities.isEventDispatchThread():
        myPrint("DB", "FYI - This script/extension is currently running within the Swing Event Dispatch Thread (EDT)")
    else:
        myPrint("DB", "FYI - This script/extension is NOT currently running within the Swing Event Dispatch Thread (EDT)")

    def cleanup_actions(theFrame=None):
        myPrint("DB", "In", inspect.currentframe().f_code.co_name, "()")
        myPrint("DB", "SwingUtilities.isEventDispatchThread() = %s" %(SwingUtilities.isEventDispatchThread()))

        if theFrame is not None and not theFrame.isActiveInMoneydance:
            destroyOldFrames(myModuleID)

        try:
            MD_REF.getUI().setStatus(">> StuWareSoftSystems - thanks for using >> %s......." %(GlobalVars.thisScriptName),0)
        except:
            pass  # If this fails, then MD is probably shutting down.......

        if not GlobalVars.i_am_an_extension_so_run_headless: print(scriptExit)

        cleanup_references()

    # .moneydance_invoke_called() is used via the _invoke.py script as defined in script_info.dict. Not used for runtime extensions
    def moneydance_invoke_called(theCommand):
        # ... modify as required to handle .showURL() events sent to this extension/script...
        myPrint("B","INVOKE - Received extension command: '%s'" %(theCommand))

    GlobalVars.defaultPrintLandscape = False
    # END ALL CODE COPY HERE ###############################################################################################
    # END ALL CODE COPY HERE ###############################################################################################
    # END ALL CODE COPY HERE ###############################################################################################

    MD_REF.getUI().setStatus(">> StuWareSoftSystems - %s launching......." %(GlobalVars.thisScriptName),0)

    GlobalVars.md_dateFormat = MD_REF.getPreferences().getShortDateFormat()

    class MainAppRunnable(Runnable):
        def __init__(self):
            pass

        def run(self):                                                                                                  # noqa
            global list_future_reminders_frame_     # global as defined here

            myPrint("DB", "In MainAppRunnable()", inspect.currentframe().f_code.co_name, "()")
            myPrint("DB", "SwingUtilities.isEventDispatchThread() = %s" %(SwingUtilities.isEventDispatchThread()))

            # Create Application JFrame() so that all popups have correct Moneydance Icons etc
            # JFrame.setDefaultLookAndFeelDecorated(True)   # Note: Darcula Theme doesn't like this and seems to be OK without this statement...
            list_future_reminders_frame_ = MyJFrame()
            list_future_reminders_frame_.setName(u"%s_main" %(myModuleID))
            if (not Platform.isMac()):
                MD_REF.getUI().getImages()
                list_future_reminders_frame_.setIconImage(MDImages.getImage(MD_REF.getSourceInformation().getIconResource()))
            list_future_reminders_frame_.setVisible(False)
            list_future_reminders_frame_.setDefaultCloseOperation(WindowConstants.DISPOSE_ON_CLOSE)

            myPrint("DB","Main JFrame %s for application created.." %(list_future_reminders_frame_.getName()))

    if not SwingUtilities.isEventDispatchThread():
        myPrint("DB",".. Main App Not running within the EDT so calling via MainAppRunnable()...")
        SwingUtilities.invokeAndWait(MainAppRunnable())
    else:
        myPrint("DB",".. Main App Already within the EDT so calling naked...")
        MainAppRunnable().run()

    def isPreviewBuild():
        if MD_EXTENSION_LOADER is not None:
            try:
                stream = MD_EXTENSION_LOADER.getResourceAsStream("/_PREVIEW_BUILD_")
                if stream is not None:
                    myPrint("B", "@@ PREVIEW BUILD (%s) DETECTED @@" %(version_build))
                    stream.close()
                    return True
            except: pass
        return False

    def ShowEditForm():
        myPrint("D", "In ", inspect.currentframe().f_code.co_name, "()")
        myPrint("D", "Calling MD EditRemindersWindow() function...")

        GlobalVars.saveSelectedRowIndex = GlobalVars.saveJTable.getSelectedRow()
        GlobalVars.saveLastReminderObj = GlobalVars.saveJTable.getValueAt(GlobalVars.saveSelectedRowIndex, 0)

        # EditRemindersWindow.editReminder(None, MD_REF.getUI(), GlobalVars.saveLastReminderObj)

        r = GlobalVars.saveLastReminderObj
        book = MD_REF.getCurrentAccountBook()
        reminderSet = MD_REF.getUI().getCurrentBook().getReminders()
        # noinspection PyUnresolvedReferences
        if r.getReminderType() == Reminder.Type.TRANSACTION:
            if r.isLoanReminder():
                win = LoanTxnReminderInfoWindow(MD_REF.getUI(), list_future_reminders_frame_, r, book, r.getTransaction().getSplit(0).getAccount())
            else:
                win = TxnReminderInfoWindow(MD_REF.getUI(), list_future_reminders_frame_, r, reminderSet.getAccountBook())
        # noinspection PyUnresolvedReferences
        elif r.getReminderType() == Reminder.Type.NOTE:
            win = BasicReminderInfoWindow(MD_REF.getUI(), r, reminderSet, list_future_reminders_frame_)
        else: raise Exception("Unknown reminder class: " + r.getClass())

        try: win.setEscapeKeyCancels(True)
        except: pass

        win.setVisible(True)

        myPrint("D", "Exiting ", inspect.currentframe().f_code.co_name, "()")

    def deleteReminder():
        myPrint("D", "In ", inspect.currentframe().f_code.co_name, "()")
        myPrint("D", "Calling MD EditRemindersWindow() function...")

        GlobalVars.saveSelectedRowIndex = GlobalVars.saveJTable.getSelectedRow()
        GlobalVars.saveLastReminderObj = GlobalVars.saveJTable.getValueAt(GlobalVars.saveSelectedRowIndex, 0)

        # EditRemindersWindow.editReminder(None, MD_REF.getUI(), GlobalVars.saveLastReminderObj)

        r = GlobalVars.saveLastReminderObj
        if myPopupAskQuestion(list_future_reminders_frame_, "DELETE REMINDER", "Delete reminder (along with all other future versions displayed too)?", theMessageType=JOptionPane.WARNING_MESSAGE):
            r.deleteItem()

        myPrint("D", "Exiting ", inspect.currentframe().f_code.co_name, "()")

    def recordNextReminderOccurrence():
        myPrint("D", "In ", inspect.currentframe().f_code.co_name, "()")
        myPrint("D", "Calling MD EditRemindersWindow() function...")

        GlobalVars.saveSelectedRowIndex = GlobalVars.saveJTable.getSelectedRow()
        GlobalVars.saveLastReminderObj = GlobalVars.saveJTable.getValueAt(GlobalVars.saveSelectedRowIndex, 0)

        book = MD_REF.getCurrentAccountBook()
        rdate = GlobalVars.saveLastReminderObj.getNextOccurance(DateUtil.incrementDate(DateUtil.getStrippedDateInt(), 0, 0, daysToLookForward_LFR))
        if rdate <= 0:
            myPopupInformationBox(list_future_reminders_frame_,"The next occurrence of reminder is non-existent or too far into the future (more than 5 years")
        else:
            # noinspection PyUnresolvedReferences
            if GlobalVars.saveLastReminderObj.getReminderType() == Reminder.Type.TRANSACTION:
                if GlobalVars.saveLastReminderObj.isLoanReminder():
                    win = LoanTxnReminderNotificationWindow(MD_REF.getUI(), list_future_reminders_frame_, book, GlobalVars.saveLastReminderObj, rdate, True)
                else:
                    win = TxnReminderNotificationWindow(MD_REF.getUI(), list_future_reminders_frame_, book, GlobalVars.saveLastReminderObj, rdate, True)
            # noinspection PyUnresolvedReferences
            elif GlobalVars.saveLastReminderObj.getReminderType() == Reminder.Type.NOTE:
                win = BasicReminderNotificationWindow(MD_REF.getUI(), book, GlobalVars.saveLastReminderObj, rdate, True, list_future_reminders_frame_)
            else: raise Exception("ERROR: Unknown Reminder type")

            try: win.setEscapeKeyCancels(True)
            except: pass

            win.setVisible(True)

    class DoTheMenu(AbstractAction):

        def __init__(self): pass

        def actionPerformed(self, event):																				# noqa
            global debug                                                                # global as set here
            global lAllowEscapeExitApp_SWSS                                             # global as set here
            global _column_widths_LFR, daysToLookForward_LFR                            # global as set here

            myPrint("D", "In ", inspect.currentframe().f_code.co_name, "()", "Event: ", event )

            # ##########################################################################################################
            if event.getActionCommand().lower().startswith("show reminder"):
                MD_REF.getUI().showRawItemDetails(GlobalVars.saveJTable.getValueAt(GlobalVars.saveSelectedRowIndex, 0), list_future_reminders_frame_)

            # ##########################################################################################################
            if event.getActionCommand().lower().startswith("edit reminder"):
                ShowEditForm()

            # ##########################################################################################################
            if event.getActionCommand().lower().startswith("delete reminder"):
                deleteReminder()

            # ##########################################################################################################
            if event.getActionCommand().lower().startswith("page setup"):
                pageSetup()

            # ##########################################################################################################
            if event.getActionCommand().lower().startswith("change look"):
                days = myPopupAskForInput(list_future_reminders_frame_,
                                          "LOOK FORWARD",
                                          "DAYS:",
                                          "Enter the number of days to look forward",
                                          defaultValue=str(daysToLookForward_LFR))

                if StringUtils.isEmpty(days): days = "0"

                if StringUtils.isInteger(days) and int(days) > 0 and int(days) <= 365:
                    daysToLookForward_LFR = int(days)
                    myPrint("B","Days to look forward changed to %s" %(daysToLookForward_LFR))

                    formatDate = DateUtil.incrementDate(DateUtil.getStrippedDateInt(),0,0,daysToLookForward_LFR)
                    GlobalVars.saveStatusLabel.setText(">>: %s" %(convertStrippedIntDateFormattedText(formatDate)))

                    RefreshMenuAction().refresh()
                elif StringUtils.isInteger(days) and int(days) > 365:
                    myPopupInformationBox(list_future_reminders_frame_,"ERROR - Days must be between 1-365 - no changes made....",theMessageType=JOptionPane.WARNING_MESSAGE)
                else:
                    myPrint("DB","Invalid days entered.... doing nothing...")

            # ##########################################################################################################
            if event.getActionCommand().lower().startswith("debug"):
                debug = not debug
                myPrint("B","DEBUG is now set to: %s" %(debug))

            # ##########################################################################################################
            if event.getActionCommand().lower().startswith("allow escape"):
                lAllowEscapeExitApp_SWSS = not lAllowEscapeExitApp_SWSS
                if lAllowEscapeExitApp_SWSS:
                    list_future_reminders_frame_.getRootPane().getInputMap(JComponent.WHEN_IN_FOCUSED_WINDOW).put(KeyStroke.getKeyStroke(KeyEvent.VK_ESCAPE, 0), "close-window")
                else:
                    list_future_reminders_frame_.getRootPane().getInputMap(JComponent.WHEN_IN_FOCUSED_WINDOW).remove(KeyStroke.getKeyStroke(KeyEvent.VK_ESCAPE, 0))

                myPrint("B","Escape key can exit the app's main screen: %s" %(lAllowEscapeExitApp_SWSS))

            # ##########################################################################################################
            if event.getActionCommand().lower().startswith("reset"):
                _column_widths_LFR = []
                RefreshMenuAction().refresh()

            # ##########################################################################################################
            if event.getActionCommand().lower().startswith("refresh"):
                RefreshMenuAction().refresh()

            # ##########################################################################################################
            if event.getActionCommand() == "About":
                AboutThisScript(list_future_reminders_frame_).go()

            if event.getActionCommand().lower().startswith("close"): terminate_script()

            # Save parameters now...
            if (event.getActionCommand().lower().startswith("change look")
                    or event.getActionCommand().lower().startswith("debug")
                    or event.getActionCommand().lower().startswith("allow escape")
                    or event.getActionCommand().lower().startswith("reset")):
                try:
                    save_StuWareSoftSystems_parameters_to_file()
                except:
                    myPrint("B", "Error - failed to save parameters to pickle file...!")
                    dump_sys_error_to_md_console_and_errorlog()

            myPrint("D", "Exiting ", inspect.currentframe().f_code.co_name, "()")
            return

    def terminate_script():
        myPrint("DB", "In ", inspect.currentframe().f_code.co_name, "()")
        myPrint("DB", "... SwingUtilities.isEventDispatchThread() returns: %s" %(SwingUtilities.isEventDispatchThread()))

        # also do this here to save column widths (set during JFrame display)
        try:
            save_StuWareSoftSystems_parameters_to_file()
        except:
            myPrint("B", "Error - failed to save parameters to pickle file...!")
            dump_sys_error_to_md_console_and_errorlog()

        try:

            # NOTE - .dispose() - The windowClosed event should set .isActiveInMoneydance False and .removeAppEventListener()
            if not SwingUtilities.isEventDispatchThread():
                SwingUtilities.invokeLater(GenericDisposeRunnable(list_future_reminders_frame_))
            else:
                list_future_reminders_frame_.dispose()
        except:
            myPrint("B","Error. Final dispose failed....?")
            dump_sys_error_to_md_console_and_errorlog()

    try:

        # Mirror code in extract_data.py (keep identical)
        def printJTable(_theFrame, _theJTable, _theTitle, _secondJTable=None):

            # Possible future modification, leverage MDPrinter, and it's classes / methods to save/load preferences and create printers
            try:
                if _theJTable is None or _theFrame is None: return

                myPrint("DB", "Creating new PrinterJob...")
                printer_job = PrinterJob.getPrinterJob()

                if GlobalVars.defaultPrintService is not None:
                    printer_job.setPrintService(GlobalVars.defaultPrintService)
                    myPrint("DB","Assigned remembered PrintService...: %s" %(printer_job.getPrintService()))

                if GlobalVars.defaultPrinterAttributes is not None:
                    pAttrs = attribute.HashPrintRequestAttributeSet(GlobalVars.defaultPrinterAttributes)
                else:
                    pAttrs = loadDefaultPrinterAttributes(None)

                pAttrs.remove(attribute.standard.JobName)
                pAttrs.add(attribute.standard.JobName("%s: %s" %(myModuleID.capitalize(), _theTitle), None))

                if GlobalVars.defaultDPI != 72:
                    pAttrs.remove(attribute.standard.PrinterResolution)
                    pAttrs.add(attribute.standard.PrinterResolution(GlobalVars.defaultDPI, GlobalVars.defaultDPI, attribute.standard.PrinterResolution.DPI))

                if not printer_job.printDialog(pAttrs):
                    myPrint("DB","User aborted the Print Dialog setup screen, so exiting...")
                    return

                selectedPrintService = printer_job.getPrintService()
                myPrint("DB", "User selected print service:", selectedPrintService)

                thePageFormat = printer_job.getPageFormat(pAttrs)

                header = MessageFormat(_theTitle)
                footer = MessageFormat("- page {0} -")

                # NOTE: _ there is a bug in VAqua... The JTable.print() method doesn't work!!
                vaqua_laf = "com.apple.laf.AquaLookAndFeel"                                                             # noqa
                metal_laf = "javax.swing.plaf.metal.MetalLookAndFeel"

                the_laf = None
                using_vaqua = False
                if Platform.isOSX():
                    the_laf = UIManager.getLookAndFeel()
                    if "vaqua" in the_laf.getName().lower():                                                            # noqa
                        using_vaqua = True
                        myPrint("B", "VAqua LAF Detected... Must switch the LAF for print to work (due to a Java Bug)....")

                        # Without this the JMenuBar gets messed up
                        save_useScreenMenuBar= System.getProperty("apple.laf.useScreenMenuBar")
                        if save_useScreenMenuBar is None or save_useScreenMenuBar == "": save_useScreenMenuBar= System.getProperty("com.apple.macos.useScreenMenuBar")
                        System.setProperty("apple.laf.useScreenMenuBar", "false")
                        System.setProperty("com.apple.macos.useScreenMenuBar", "false")

                        UIManager.setLookAndFeel(metal_laf)     # Really don't like doing this....!

                try:
                    if using_vaqua:
                        myPrint("DB", "... Updating the JFrame()'s component tree to the temporary LAF....")
                        SwingUtilities.updateComponentTreeUI(_theFrame)


                    if _secondJTable is None:
                        printer_job.setPrintable(_theJTable.getPrintable(JTable.PrintMode.FIT_WIDTH, header, footer), thePageFormat)    # noqa
                        eval("printer_job.print(pAttrs)")
                    else:
                        # java.awt.print.Book() won't work as it passes the book page number instead of the Printable's page number...
                        footer = MessageFormat("<the total/summary table is printed on the next page>")
                        printer_job.setPrintable(_theJTable.getPrintable(JTable.PrintMode.FIT_WIDTH, header, footer), thePageFormat)    # noqa
                        eval("printer_job.print(pAttrs)")

                        header = MessageFormat(_theTitle+" (Total/Summary Table)")
                        footer = MessageFormat("<END>")

                        printer_job.setPrintable(_secondJTable.getPrintable(JTable.PrintMode.FIT_WIDTH, header, footer), thePageFormat)    # noqa
                        eval("printer_job.print(pAttrs)")

                except:
                    myPrint("B", "ERROR: Printing routines failed?")
                    dump_sys_error_to_md_console_and_errorlog()
                    raise

                finally:
                    if using_vaqua:
                        UIManager.setLookAndFeel(the_laf)     # Switch back quick
                        myPrint("B", "...quick switch of LAF to print complete. LAF restored to:", UIManager.getLookAndFeel())

                        myPrint("DB", "... Switching the JFrame()'s component tree back to VAqua....")
                        SwingUtilities.updateComponentTreeUI(_theFrame)

                        # Without this the JMenuBar gets screwed up
                        System.setProperty("apple.laf.useScreenMenuBar", save_useScreenMenuBar)                             # noqa
                        System.setProperty("com.apple.macos.useScreenMenuBar", save_useScreenMenuBar)                       # noqa

                myPrint("DB", "Saving current print service:", printer_job.getPrintService())
                GlobalVars.defaultPrinterAttributes = attribute.HashPrintRequestAttributeSet(pAttrs)
                GlobalVars.defaultPrintService = printer_job.getPrintService()

            except:
                myPrint("B", "ERROR in printing routines.....:"); dump_sys_error_to_md_console_and_errorlog()
            return

        myPrint("DB", "Locale Decimal point:", GlobalVars.decimalCharSep)

        lExit = False
        if lExit:
            cleanup_actions(list_future_reminders_frame_)

        else:

            myPrint("DB", "DEBUG turned on")

            # save here instead of at the end.
            save_StuWareSoftSystems_parameters_to_file()

            # Moneydance dates  are int yyyymmddd - convert to locale date string for CSV format
            def dateoutput(dateinput, theformat):

                if dateinput == "EXPIRED": _dateoutput = dateinput
                elif dateinput == "": _dateoutput = ""
                elif dateinput == 0: _dateoutput = ""
                elif dateinput == "0": _dateoutput = ""
                else:
                    dateasdate = datetime.datetime.strptime(str(dateinput), "%Y%m%d")  # Convert to Date field
                    _dateoutput = dateasdate.strftime(theformat)

                return _dateoutput

            def myGetNextOccurance(theRem, startDate, maximumDate):
                cal = Calendar.getInstance()
                ackPlusOne = theRem.getDateAcknowledgedInt()
                if ackPlusOne > 0:
                    ackPlusOne = DateUtil.incrementDate(ackPlusOne, 0, 0, 1)
                DateUtil.setCalendarDate(cal, Math.max(startDate, ackPlusOne))
                while True:
                    intDate = DateUtil.convertCalToInt(cal)
                    if (intDate > maximumDate or (theRem.getLastDateInt() > 0 and intDate > theRem.getLastDateInt())):	# noqa
                        return 0
                    if (theRem.occursOnDate(cal)):
                        return DateUtil.convertCalToInt(cal)
                    cal.add(Calendar.DAY_OF_MONTH, 1)

            def build_the_data_file(ind):
                myPrint("D", "In ", inspect.currentframe().f_code.co_name, "()", " - ind:", ind)

                # ind == 1 means that this is a repeat call, so the table should be refreshed

                rems = MD_REF.getCurrentAccountBook().getReminders().getAllReminders()

                if rems.size() < 1:
                    return False

                myPrint("DB", 'Success: read ', rems.size(), 'reminders')
                print
                GlobalVars.tableHeaderRowList = [
                    "THE_REMINDER_OBJECT",
                    "Next Due",
                    "Account Name",
                    "Reminder Description",
                    "Net Amount"
                ]

                GlobalVars.tableHeaderRowFormats = [
                    [Number,JLabel.CENTER],
                    [String,JLabel.CENTER],
                    [String,JLabel.LEFT],
                    [String,JLabel.LEFT],
                    [Number,JLabel.RIGHT]
                ]

                # Read each reminder and create a csv line for each in the GlobalVars.reminderDataList array
                GlobalVars.reminderDataList = []  # Set up an empty array

                for index in range(0, int(rems.size())):
                    rem = rems[index]  # Get the reminder

                    remtype = rem.getReminderType()  # NOTE or TRANSACTION
                    desc = rem.getDescription().replace(",", " ")  # remove commas to keep csv format happy
                    # memo = str(rem.getMemo()).replace(",", " ").strip()  # remove commas to keep csv format happy
                    # memo = str(memo).replace("\n", "*").strip()  # remove newlines to keep csv format happy

                    myPrint("P", "Reminder: ", index + 1, rem.getDescription())  # Name of Reminder

                    # determine the frequency of the transaction
                    daily = rem.getRepeatDaily()
                    weekly = rem.getRepeatWeeklyModifier()
                    monthly = rem.getRepeatMonthlyModifier()
                    yearly = rem.getRepeatYearly()
                    countfreqs = 0

                    remfreq = ''

                    if daily > 0:
                        remfreq += 'DAILY'
                        remfreq += '(every ' + str(daily) + ' days)'
                        countfreqs += 1

                    if len(rem.getRepeatWeeklyDays()) > 0 and rem.getRepeatWeeklyDays()[0] > 0:
                        for freq in range(0, len(rem.getRepeatWeeklyDays())):
                            if len(remfreq) > 0: remfreq += " & "
                            if weekly == Reminder.WEEKLY_EVERY:                remfreq += 'WEEKLY_EVERY'
                            if weekly == Reminder.WEEKLY_EVERY_FIFTH:            remfreq += 'WEEKLY_EVERY_FIFTH'
                            if weekly == Reminder.WEEKLY_EVERY_FIRST:            remfreq += 'WEEKLY_EVERY_FIRST'
                            if weekly == Reminder.WEEKLY_EVERY_FOURTH:            remfreq += 'WEEKLY_EVERY_FOURTH'
                            if weekly == Reminder.WEEKLY_EVERY_LAST:            remfreq += 'WEEKLY_EVERY_LAST'
                            if weekly == Reminder.WEEKLY_EVERY_SECOND:            remfreq += 'WEEKLY_EVERY_SECOND'
                            if weekly == Reminder.WEEKLY_EVERY_THIRD:            remfreq += 'WEEKLY_EVERY_THIRD'

                            if rem.getRepeatWeeklyDays()[freq] == 1: remfreq += '(on Sunday)'
                            if rem.getRepeatWeeklyDays()[freq] == 2: remfreq += '(on Monday)'
                            if rem.getRepeatWeeklyDays()[freq] == 3: remfreq += '(on Tuesday)'
                            if rem.getRepeatWeeklyDays()[freq] == 4: remfreq += '(on Wednesday)'
                            if rem.getRepeatWeeklyDays()[freq] == 5: remfreq += '(on Thursday)'
                            if rem.getRepeatWeeklyDays()[freq] == 6: remfreq += '(on Friday)'
                            if rem.getRepeatWeeklyDays()[freq] == 7: remfreq += '(on Saturday)'
                            if rem.getRepeatWeeklyDays()[freq] < 1 or rem.getRepeatWeeklyDays()[
                                freq] > 7: remfreq += '(*ERROR*)'
                            countfreqs += 1

                    if len(rem.getRepeatMonthly()) > 0 and rem.getRepeatMonthly()[0] > 0:
                        for freq in range(0, len(rem.getRepeatMonthly())):
                            if len(remfreq) > 0: remfreq += " & "
                            if monthly == Reminder.MONTHLY_EVERY:                 remfreq += 'MONTHLY_EVERY'
                            if monthly == Reminder.MONTHLY_EVERY_FOURTH:         remfreq += 'MONTHLY_EVERY_FOURTH'
                            if monthly == Reminder.MONTHLY_EVERY_OTHER:         remfreq += 'MONTHLY_EVERY_OTHER'
                            if monthly == Reminder.MONTHLY_EVERY_SIXTH:         remfreq += 'MONTHLY_EVERY_SIXTH'
                            if monthly == Reminder.MONTHLY_EVERY_THIRD:         remfreq += 'MONTHLY_EVERY_THIRD'

                            theday = rem.getRepeatMonthly()[freq]
                            if theday == Reminder.LAST_DAY_OF_MONTH:
                                remfreq += '(on LAST_DAY_OF_MONTH)'
                            else:
                                if 4 <= theday <= 20 or 24 <= theday <= 30: suffix = "th"
                                else:                                        suffix = ["st", "nd", "rd"][theday % 10 - 1]

                                remfreq += '(on ' + str(theday) + suffix + ')'

                            countfreqs += 1

                    if yearly:
                        if len(remfreq) > 0: remfreq += " & "
                        remfreq += 'YEARLY'
                        countfreqs += 1

                    if len(remfreq) < 1 or countfreqs == 0:         remfreq = '!ERROR! NO ACTUAL FREQUENCY OPTIONS SET PROPERLY ' + remfreq
                    if countfreqs > 1: remfreq = "**MULTI** " + remfreq													# noqa

                    todayInt = DateUtil.getStrippedDateInt()
                    lastdate = rem.getLastDateInt()

                    if lastdate < 1:  # Detect if an enddate is set
                        stopDate = min(DateUtil.incrementDate(todayInt, 0, 0, daysToLookForward_LFR),20991231)
                        nextDate = rem.getNextOccurance(stopDate)  # Use cutoff  far into the future

                    else:
                        stopDate = min(DateUtil.incrementDate(todayInt, 0, 0, daysToLookForward_LFR),lastdate)
                        nextDate = rem.getNextOccurance(stopDate)  # Stop at enddate

                    if nextDate < 1:
                        continue

                    # nextDate = DateUtil.incrementDate(nextDate, 0, 0, -1)

                    loopDetector=0

                    while True:

                        loopDetector+=1
                        if loopDetector > 10000:
                            myPrint("B","Loop detected..? Breaking out.... Reminder %s" %(rem))
                            myPopupInformationBox(list_future_reminders_frame_,"ERROR - Loop detected..?! Will exit (review console log)",theMessageType=JOptionPane.ERROR_MESSAGE)
                            raise Exception("Loop detected..? Aborting.... Reminder %s" %(rem))

                        calcNext = myGetNextOccurance(rem,nextDate, stopDate)

                        if calcNext < 1:
                            break

                        remdate = calcNext

                        # nextDate = DateUtil.incrementDate(calcNext, 0, 0, 1)
                        nextDate = DateUtil.incrementDate(calcNext, 0, 0, 1)

                        lastack = rem.getDateAcknowledgedInt()
                        if lastack == 0 or lastack == 19700101: lastack = ''											# noqa

                        auto = rem.getAutoCommitDays()
                        if auto >= 0:    auto = 'YES: (' + str(auto) + ' days before scheduled)'						# noqa
                        else:            auto = 'NO'																	# noqa

                        if str(remtype) == 'NOTE':
                            csvline = []

                            # csvline.append(index + 1)
                            csvline.append(rem)

                            csvline.append(remdate)
                            csvline.append('')
                            csvline.append(desc)
                            csvline.append('')  # NetAmount
                            GlobalVars.reminderDataList.append(csvline)

                        elif str(remtype) == 'TRANSACTION':
                            txnparent = rem.getTransaction()
                            amount = GlobalVars.baseCurrency.getDoubleValue(txnparent.getValue())

                            for index2 in [0]:
                                if index2 > 0: amount = ''  # Don't repeat the new amount on subsequent split lines (so you can total column). The split amount will be correct

                                csvline = []

                                csvline.append(rem)

                                csvline.append(remdate)
                                csvline.append(rem.getTransaction().getAccount().getAccountName())
                                csvline.append(desc)
                                csvline.append((amount))
                                GlobalVars.reminderDataList.append(csvline)

                    index += 1

                # if len(GlobalVars.reminderDataList) < 1:
                # 	return False
                #
                ReminderTable(GlobalVars.reminderDataList, ind)

                myPrint("D", "Exiting ", inspect.currentframe().f_code.co_name)

                return True

            # ENDDEF

            # Synchronises column widths of both JTables
            class ColumnChangeListener(TableColumnModelListener):
                sourceTable = None
                targetTable = None

                def __init__(self, source):
                    self.sourceTable = source

                def columnAdded(self, e): pass

                def columnSelectionChanged(self, e): pass

                def columnRemoved(self, e): pass

                def columnMoved(self, e): pass

                # noinspection PyUnusedLocal
                def columnMarginChanged(self, e):
                    global _column_widths_LFR       # global as set here

                    sourceModel = self.sourceTable.getColumnModel()

                    for _i in range(0, sourceModel.getColumnCount()):
                        # Saving for later... Yummy!!
                        _column_widths_LFR[_i] = sourceModel.getColumn(_i).getWidth()
                        myPrint("D","Saving column %s as width %s for later..." %(_i,_column_widths_LFR[_i]))


            # The javax.swing package and its subpackages provide a fairly comprehensive set of default renderer implementations, suitable for customization via inheritance. A notable omission is the lack #of a default renderer for a JTableHeader in the public API. The renderer used by default is a Sun proprietary class, sun.swing.table.DefaultTableCellHeaderRenderer, which cannot be extended.
            # DefaultTableHeaderCellRenderer seeks to fill this void, by providing a rendering designed to be identical with that of the proprietary class, with one difference: the vertical alignment of #the header text has been set to BOTTOM, to provide a better match between DefaultTableHeaderCellRenderer and other custom renderers.
            # The name of the class has been chosen considering this to be a default renderer for the cells of a table header, and not the table cells of a header as implied by the proprietary class name


            class DefaultTableHeaderCellRenderer(DefaultTableCellRenderer):

                # /**
                # * Constructs a <code>DefaultTableHeaderCellRenderer</code>.
                # * <P>
                # * The horizontal alignment and text position are set as appropriate to a
                # * table header cell, and the opaque property is set to false.
                # */

                def __init__(self):
                    # super(DefaultTableHeaderCellRenderer, self).__init__()
                    self.setHorizontalAlignment(JLabel.CENTER)  # This one changes the text alignment
                    self.setHorizontalTextPosition(JLabel.RIGHT)  # This positions the  text to the  left/right of  the sort icon
                    self.setVerticalAlignment(JLabel.BOTTOM)
                    self.setOpaque(True)  # if this is false then it hides the background colour

                # enddef

                # /**
                # * returns the default table header cell renderer.
                # * <P>
                # * If the column is sorted, the appropriate icon is retrieved from the
                # * current Look and Feel, and a border appropriate to a table header cell
                # * is applied.
                # * <P>
                # * Subclasses may overide this method to provide custom content or
                # * formatting.
                # *
                # * @param table the <code>JTable</code>.
                # * @param value the value to assign to the header cell
                # * @param isSelected This parameter is ignored.
                # * @param hasFocus This parameter is ignored.
                # * @param row This parameter is ignored.
                # * @param column the column of the header cell to render
                # * @return the default table header cell renderer
                # */

                def getTableCellRendererComponent(self, table, value, isSelected, hasFocus, row, column):				# noqa
                    # noinspection PyUnresolvedReferences
                    super(DefaultTableHeaderCellRenderer, self).getTableCellRendererComponent(table, value, isSelected,hasFocus, row, column)
                    # tableHeader = table.getTableHeader()
                    # if (tableHeader is not None): self.setForeground(tableHeader.getForeground())
                    align = table.getCellRenderer(0, column).getHorizontalAlignment()
                    self.setHorizontalAlignment(align)
                    if align == JLabel.RIGHT:
                        self.setHorizontalTextPosition(JLabel.RIGHT)
                    elif align == JLabel.LEFT:
                        self.setHorizontalTextPosition(JLabel.LEFT)
                    elif align == JLabel.CENTER:
                        self.setHorizontalTextPosition(JLabel.LEFT)

                    self.setIcon(self._getIcon(table, column))
                    self.setBorder(UIManager.getBorder("TableHeader.cellBorder"))

                    self.setForeground(MD_REF.getUI().getColors().headerFG)
                    self.setBackground(MD_REF.getUI().getColors().headerBG1)

                    # self.setHorizontalAlignment(JLabel.CENTER)

                    return self

                # enddef

                # /**
                # * Overloaded to return an icon suitable to the primary sorted column, or null if
                # * the column is not the primary sort key.
                # *
                # * @param table the <code>JTable</code>.
                # * @param column the column index.
                # * @return the sort icon, or null if the column is unsorted.
                # */
                def _getIcon(self, table, column):																		# noqa
                    sortKey = self.getSortKey(table, column)
                    if (sortKey is not None and table.convertColumnIndexToView(sortKey.getColumn()) == column):
                        x = (sortKey.getSortOrder())
                        if x == SortOrder.ASCENDING: return UIManager.getIcon("Table.ascendingSortIcon")
                        elif x == SortOrder.DESCENDING: return UIManager.getIcon("Table.descendingSortIcon")
                        elif x == SortOrder.UNSORTED: return UIManager.getIcon("Table.naturalSortIcon")
                    return None

                # enddef

                # /**
                # * returns the current sort key, or null if the column is unsorted.
                # *
                # * @param table the table
                # * @param column the column index
                # * @return the SortKey, or null if the column is unsorted
                # */
                # noinspection PyMethodMayBeStatic
                # noinspection PyUnusedLocal
                def getSortKey(self, table, column):																	# noqa
                    rowSorter = table.getRowSorter()
                    if (rowSorter is None): return None
                    sortedColumns = rowSorter.getSortKeys()
                    if (sortedColumns.size() > 0): return sortedColumns.get(0)
                    return None


            GlobalVars.baseCurrency = MD_REF.getCurrentAccount().getBook().getCurrencies().getBaseType()

            GlobalVars.saveLastReminderObj = None
            GlobalVars.saveSelectedRowIndex = 0
            GlobalVars.saveJTable = None

            GlobalVars.tableHeaderRowList = None
            GlobalVars.tableHeaderRowFormats = None

            GlobalVars.reminderListener = None

            GlobalVars.REMINDER_REFRESH_RUNNING_LOCK = threading.Lock()

            class MyMoneydanceEventListener(AppEventListener):

                def __init__(self, theFrame):
                    self.alreadyClosed = False
                    self.theFrame = theFrame
                    self.myModuleID = myModuleID

                def getMyself(self):
                    myPrint("D", "In ", inspect.currentframe().f_code.co_name, "()")
                    fm = MD_REF.getModuleForID(self.myModuleID)
                    if fm is None: return None, None
                    try:
                        pyObject = getFieldByReflection(fm, "extensionObject")
                    except:
                        myPrint("DB","Error retrieving my own Python extension object..?")
                        dump_sys_error_to_md_console_and_errorlog()
                        return None, None

                    return fm, pyObject

                # noinspection PyMethodMayBeStatic
                def handleEvent(self, appEvent):
                    myPrint("DB", "In ", inspect.currentframe().f_code.co_name, "()")
                    myPrint("DB", "... SwingUtilities.isEventDispatchThread() returns: %s" %(SwingUtilities.isEventDispatchThread()))
                    myPrint("DB", "I am .handleEvent() within %s" %(classPrinter("MoneydanceAppListener", self.theFrame.MoneydanceAppListener)))
                    myPrint("DB","Extension .handleEvent() received command: %s" %(appEvent))

                    if self.alreadyClosed:
                        myPrint("DB","....I'm actually still here (MD EVENT %s CALLED).. - Ignoring and returning back to MD...." %(appEvent))
                        return

                    # MD doesn't call .unload() or .cleanup(), so if uninstalled I need to close myself
                    fm, pyObject = self.getMyself()
                    myPrint("DB", "Checking myself: %s : %s" %(fm, pyObject))
                    # if (fm is None or pyObject is None) and appEvent != "md:app:exiting":
                    if (fm is None or (self.theFrame.isRunTimeExtension and pyObject is None)) and appEvent != "md:app:exiting":
                        myPrint("B", "@@ ALERT - I've detected that I'm no longer installed as an extension - I will deactivate.. (switching event code to :close)")
                        appEvent = "%s:customevent:close" %self.myModuleID

                    # I am only closing Toolbox when a new Dataset is opened.. I was calling it on MD Close/Exit, but it seemed to cause an Exception...
                    if (appEvent == "md:file:closing"
                            or appEvent == "md:file:closed"
                            or appEvent == "md:file:opening"
                            or appEvent == "md:app:exiting"):
                        myPrint("DB","@@ Ignoring MD handleEvent: %s" %(appEvent))

                    elif (appEvent == "md:file:opened" or appEvent == "%s:customevent:close" %self.myModuleID):
                        if debug:
                            myPrint("DB","MD event %s triggered.... Will call GenericWindowClosingRunnable (via the Swing EDT) to push a WINDOW_CLOSING Event to %s to close itself (while I exit back to MD quickly) ...." %(appEvent, self.myModuleID))
                        else:
                            myPrint("B","Moneydance triggered event %s triggered - So I am closing %s now...." %(appEvent, self.myModuleID))
                        self.alreadyClosed = True
                        try:
                            # t = Thread(GenericWindowClosingRunnable(self.theFrame))
                            # t.start()
                            SwingUtilities.invokeLater(GenericWindowClosingRunnable(self.theFrame))
                            myPrint("DB","Back from calling GenericWindowClosingRunnable to push a WINDOW_CLOSING Event (via the Swing EDT) to %s.... ;-> ** I'm getting out quick! **" %(self.myModuleID))
                        except:
                            dump_sys_error_to_md_console_and_errorlog()
                            myPrint("B","@@ ERROR calling GenericWindowClosingRunnable to push  a WINDOW_CLOSING Event (via the Swing EDT) to %s.... :-< ** I'm getting out quick! **" %(self.myModuleID))
                        if not debug: myPrint("DB","Returning back to Moneydance after calling for %s to close...." %self.myModuleID)

            # md:file:closing	The Moneydance file is being closed
            # md:file:closed	The Moneydance file has closed
            # md:file:opening	The Moneydance file is being opened
            # md:file:opened	The Moneydance file has opened
            # md:file:presave	The Moneydance file is about to be saved
            # md:file:postsave	The Moneydance file has been saved
            # md:app:exiting	Moneydance is shutting down
            # md:account:select	An account has been selected by the user
            # md:account:root	The root account has been selected
            # md:graphreport	An embedded graph or report has been selected
            # md:viewbudget	One of the budgets has been selected
            # md:viewreminders	One of the reminders has been selected
            # md:licenseupdated	The user has updated the license

            class MyReminderListener(ReminderListener):
                def reminderRemoved(self, paramReminder):
                    myPrint("DB", "In ", inspect.currentframe().f_code.co_name, "()", "Rem: ", paramReminder)
                    self.doReminderTableRefresh()

                def reminderAdded(self, paramReminder):
                    myPrint("DB", "In ", inspect.currentframe().f_code.co_name, "()", "Rem: ", paramReminder)
                    self.doReminderTableRefresh()

                def reminderModified(self, paramReminder):
                    myPrint("DB", "In ", inspect.currentframe().f_code.co_name, "()", "Rem: ", paramReminder)
                    self.doReminderTableRefresh()

                def doReminderTableRefresh(self):
                    myPrint("DB", "build_the_data_file(1)")

                    with GlobalVars.REMINDER_REFRESH_RUNNING_LOCK:
                        myPrint("DB","...REMINDER_REFRESH_RUNNING_LOCK threading lock gained....")
                        build_the_data_file(1)  # Re-extract data when window focus gained - assume something changed
                        myPrint("DB", "back from build_the_data_file(1), row: ", GlobalVars.saveSelectedRowIndex)
                        try:
                            lFoundObj = False
                            if GlobalVars.saveJTable.getRowCount() > 0 and GlobalVars.saveLastReminderObj is not None:
                                myPrint("DB","... Hunting for the reminder...")
                                for _i in range(0, GlobalVars.saveJTable.getRowCount()):
                                    cell = GlobalVars.saveJTable.getModel().getValueAt(GlobalVars.saveJTable.convertRowIndexToModel(_i), 0)
                                    if cell == GlobalVars.saveLastReminderObj:
                                        lFoundObj = True
                                        GlobalVars.saveSelectedRowIndex = _i
                                        GlobalVars.saveJTable.setRowSelectionInterval(_i, _i)
                                        cellRect = GlobalVars.saveJTable.getCellRect(GlobalVars.saveSelectedRowIndex, 0, True)
                                        GlobalVars.saveJTable.scrollRectToVisible(cellRect)  # force the scrollpane to make the row visible
                                        myPrint("DB","...... found at row index: %s" %(_i), cell)
                                        break
                            if not lFoundObj:
                                myPrint("DB","...... Oh - not found?")
                                GlobalVars.saveSelectedRowIndex = 0
                                GlobalVars.saveLastReminderObj = None
                        except:
                            myPrint("B","Caught error in .doReminderTableRefresh() - row variable = %s ... Ignoring...." %(GlobalVars.saveSelectedRowIndex))
                            dump_sys_error_to_md_console_and_errorlog()

            GlobalVars.reminderListener = MyReminderListener()


            class MyListSelectionListener(ListSelectionListener):
                def __init__(self):
                    pass

                def valueChanged(self, e):
                    try:
                        myPrint("DB", "In %s.%s()" %(self, inspect.currentframe().f_code.co_name))
                        myPrint("DB", "In MyListSelectionListener().valueChanged(): %s" %(e))

                        if e.getValueIsAdjusting():
                            myPrint("DB", ".. getValueIsAdjusting() is True.... Ignoring.....")
                            return
                        try:
                            if GlobalVars.saveJTable.getSelectedRow() > 0:
                                GlobalVars.saveSelectedRowIndex = GlobalVars.saveJTable.getSelectedRow()
                                GlobalVars.saveLastReminderObj = GlobalVars.saveJTable.getValueAt(GlobalVars.saveSelectedRowIndex, 0)
                                myPrint("DB","Reminder Obj saved:", GlobalVars.saveLastReminderObj)
                            else:
                                GlobalVars.saveSelectedRowIndex = 0
                                GlobalVars.saveLastReminderObj = None
                                myPrint("DB","Reminder Obj UNSAVED:")
                        except:
                            myPrint("B","@@ Error managing internal selected objects list")
                            dump_sys_error_to_md_console_and_errorlog()
                            raise

                    except:
                        myPrint("B","@@ ERROR in .valueChanged() routine")
                        dump_sys_error_to_md_console_and_errorlog()
                        raise

            class WindowListener(WindowAdapter):

                def __init__(self, theFrame, _reminderListener):
                    self.theFrame = theFrame                                                                            # type: MyJFrame
                    self.reminderListener = _reminderListener

                def windowClosing(self, WindowEvent):                         									        # noqa
                    myPrint("DB", "In ", inspect.currentframe().f_code.co_name, "()")

                    terminate_script()

                def windowClosed(self, WindowEvent):                                                                    # noqa

                    myPrint("DB","In ", inspect.currentframe().f_code.co_name, "()")
                    myPrint("DB", "... SwingUtilities.isEventDispatchThread() returns: %s" %(SwingUtilities.isEventDispatchThread()))

                    self.theFrame.isActiveInMoneydance = False

                    myPrint("DB","applistener is %s" %(classPrinter("MoneydanceAppListener", self.theFrame.MoneydanceAppListener)))

                    if self.theFrame.MoneydanceAppListener is not None:
                        try:
                            MD_REF.removeAppEventListener(self.theFrame.MoneydanceAppListener)
                            myPrint("DB","\n@@@ Removed my MD App Listener... %s\n" %(classPrinter("MoneydanceAppListener", self.theFrame.MoneydanceAppListener)))
                            self.theFrame.MoneydanceAppListener = None
                        except:
                            myPrint("B","FAILED to remove my MD App Listener... %s" %(classPrinter("MoneydanceAppListener", self.theFrame.MoneydanceAppListener)))
                            dump_sys_error_to_md_console_and_errorlog()

                    if self.theFrame.HomePageViewObj is not None:
                        self.theFrame.HomePageViewObj.unload()
                        myPrint("DB","@@ Called HomePageView.unload() and Removed reference to HomePageView %s from MyJFrame()...@@\n" %(classPrinter("HomePageView", self.theFrame.HomePageViewObj)))
                        self.theFrame.HomePageViewObj = None

                    if self.reminderListener is not None:
                        myPrint("DB", "Removing Reminders listener:", self.reminderListener)
                        MD_REF.getCurrentAccountBook().getReminders().removeReminderListener(self.reminderListener)

                    cleanup_actions(self.theFrame)


            MyWindowListener = WindowListener(list_future_reminders_frame_, GlobalVars.reminderListener)


            class MouseListener(MouseAdapter):

                # noinspection PyMethodMayBeStatic
                def mouseClicked(self, event):
                    myPrint("D", "In ", inspect.currentframe().f_code.co_name, "()")

                    # Select the row when right-click initiated
                    point = event.getPoint()
                    GlobalVars.saveSelectedRowIndex = GlobalVars.saveJTable.rowAtPoint(point)
                    GlobalVars.saveLastReminderObj = GlobalVars.saveJTable.getValueAt(GlobalVars.saveSelectedRowIndex, 0)
                    GlobalVars.saveJTable.setRowSelectionInterval(GlobalVars.saveSelectedRowIndex, GlobalVars.saveSelectedRowIndex)


                # noinspection PyMethodMayBeStatic
                def mousePressed(self, event):
                    myPrint("D", "In ", inspect.currentframe().f_code.co_name, "()")

                    clicks = event.getClickCount()
                    if clicks == 2:
                        recordNextReminderOccurrence()
                    myPrint("D", "Exiting ", inspect.currentframe().f_code.co_name, "()")

            MyMouseListener = MouseListener()


            class EnterAction(AbstractAction):
                # noinspection PyMethodMayBeStatic
                # noinspection PyUnusedLocal
                def actionPerformed(self, event):
                    myPrint("D", "In ", inspect.currentframe().f_code.co_name, "()")
                    recordNextReminderOccurrence()
                    myPrint("D", "Exiting ", inspect.currentframe().f_code.co_name, "()")

            class CloseAction(AbstractAction):

                # noinspection PyMethodMayBeStatic
                # noinspection PyUnusedLocal
                def actionPerformed(self, event):
                    myPrint("D", "In ", inspect.currentframe().f_code.co_name, "()")
                    terminate_script()

            class PrintJTable(AbstractAction):
                def __init__(self, _frame, _table, _title):
                    self._frame = _frame
                    self._table = _table
                    self._title = _title

                def actionPerformed(self, event):                                                               # noqa
                    printJTable(_theFrame=self._frame, _theJTable=self._table, _theTitle=self._title)

            class ExtractMenuAction():
                def __init__(self):
                    pass

                # noinspection PyMethodMayBeStatic
                def extract_or_close(self):
                    myPrint("D", "In ", inspect.currentframe().f_code.co_name, "()")
                    myPrint("D", "inside ExtractMenuAction() ;->")

                    terminate_script()


            class RefreshMenuAction():
                def __init__(self):
                    pass

                # noinspection PyMethodMayBeStatic
                def refresh(self):
                    myPrint("D", "In ", inspect.currentframe().f_code.co_name, "()", "\npre-extract details(1), row: ", GlobalVars.saveSelectedRowIndex)

                    GlobalVars.saveSelectedRowIndex = 0  # reset to row 1 (index zero)
                    GlobalVars.saveLastReminderObj = None

                    build_the_data_file(1)  # Re-extract data
                    myPrint("D", "back from build_the_data_file(1), row: ", GlobalVars.saveSelectedRowIndex)

                    # if GlobalVars.saveJTable.getRowCount() > 0:
                    #     GlobalVars.saveJTable.setRowSelectionInterval(GlobalVars.saveSelectedRowIndex, GlobalVars.saveSelectedRowIndex)

                    GlobalVars.saveJTable.requestFocus()

                    myPrint("D", "Exiting ", inspect.currentframe().f_code.co_name, "()")

            class GrabFocusRunnable(Runnable):
                def __init__(self, swingObject): self.swingObject = swingObject
                def run(self): self.swingObject.requestFocus()

            class MyJTable(JTable):
                myPrint("D", "In ", inspect.currentframe().f_code.co_name, "()")

                def __init__(self, tableModel):
                    super(JTable, self).__init__(tableModel)
                    self.fixTheRowSorter()

                # noinspection PyMethodMayBeStatic
                # noinspection PyUnusedLocal
                def isCellEditable(self, row, column):																	# noqa
                    return False

                #  Rendering depends on row (i.e. security's currency) as well as column
                # noinspection PyUnusedLocal
                # noinspection PyMethodMayBeStatic
                def getCellRenderer(self, row, column):																	# noqa

                    if column == 0:
                        # renderer = MyPlainNumberRenderer()
                        renderer = DefaultTableCellRenderer()
                    elif column == 1:
                        renderer = MyDateRenderer()
                    elif GlobalVars.tableHeaderRowFormats[column][0] == Number:
                        renderer = MyNumberRenderer()
                    else:
                        renderer = DefaultTableCellRenderer()

                    renderer.setHorizontalAlignment(GlobalVars.tableHeaderRowFormats[column][1])

                    return renderer

                class MyTextNumberComparator(Comparator):
                    lSortNumber = False
                    lSortRealNumber = False

                    def __init__(self, sortType):
                        if sortType == "N":
                            self.lSortNumber = True
                        elif sortType == "%":
                            self.lSortRealNumber = True
                        else:
                            self.lSortNumber = False

                    def compare(self, str1, str2):
                        validString = "-0123456789" + GlobalVars.decimalCharSep  # Yes this will strip % sign too, but that still works

                        # if debug: print str1, str2, self.lSortNumber, self.lSortRealNumber, type(str1), type(str2)

                        if isinstance(str1, (float,int)) or isinstance(str2,(float,int)):
                            if str1 is None or str1 == "": str1 = 0
                            if str2 is None or str2 == "": str2 = 0
                            if (str1) > (str2):
                                return 1
                            elif str1 == str2:
                                return 0
                            else:
                                return -1

                        if self.lSortNumber:
                            # strip non numerics from string so can convert back to float - yes, a bit of a reverse hack
                            conv_string1 = ""
                            if str1 is None or str1 == "": str1 = "0"
                            if str2 is None or str2 == "": str2 = "0"
                            for char in str1:
                                if char in validString:
                                    conv_string1 = conv_string1 + char

                            conv_string2 = ""
                            for char in str2:
                                if char in validString:
                                    conv_string2 = conv_string2 + char
                            str1 = float(conv_string1)
                            str2 = float(conv_string2)

                            if str1 > str2:
                                return 1
                            elif str1 == str2:
                                return 0
                            else:
                                return -1
                        elif self.lSortRealNumber:
                            if float(str1) > float(str2):
                                return 1
                            elif str1 == str2:
                                return 0
                            else:
                                return -1
                        else:
                            if str1.upper() > str2.upper():
                                return 1
                            elif str1.upper() == str2.upper():
                                return 0
                            else:
                                return -1

                # enddef

                def fixTheRowSorter(self):  # by default everything gets converted to strings. We need to fix this and code for my string number formats

                    sorter = TableRowSorter()
                    self.setRowSorter(sorter)
                    sorter.setModel(self.getModel())
                    for _i in range(0, self.getColumnCount()):
                        if _i == 0:
                            sorter.setComparator(_i, self.MyTextNumberComparator("%"))
                        if _i == 4 or _i == 4:
                            sorter.setComparator(_i, self.MyTextNumberComparator("N"))
                        else:
                            sorter.setComparator(_i, self.MyTextNumberComparator("T"))
                    self.getRowSorter().toggleSortOrder(1)

                    sorter.setRowFilter(GlobalVars.currentJTableSearchFilter)

                # make Banded rows
                def prepareRenderer(self, renderer, _row, column):

                    # noinspection PyUnresolvedReferences
                    component = super(MyJTable, self).prepareRenderer(renderer, _row, column)
                    if not self.isRowSelected(_row):
                        component.setBackground(MD_REF.getUI().getColors().registerBG1 if _row % 2 == 0 else MD_REF.getUI().getColors().registerBG2)

                    return component

            # This copies the standard class and just changes the colour to RED if it detects a negative - leaves field intact
            # noinspection PyArgumentList
            class MyNumberRenderer(DefaultTableCellRenderer):
                def __init__(self):
                    super(DefaultTableCellRenderer, self).__init__()

                def setValue(self, value):
                    if isinstance(value, (float,int)):
                        if value < 0.0:
                            self.setForeground(MD_REF.getUI().getColors().budgetAlertColor)
                        else:
                            self.setForeground(MD_REF.getUI().getColors().budgetHealthyColor)
                        self.setText(GlobalVars.baseCurrency.formatFancy(int(value*100), GlobalVars.decimalCharSep, True))
                    else:
                        self.setText(str(value))

                    return

            # noinspection PyArgumentList
            class MyDateRenderer(DefaultTableCellRenderer):
                def __init__(self):
                    super(DefaultTableCellRenderer, self).__init__()

                def setValue(self, value):
                    self.setText(convertStrippedIntDateFormattedText(value, GlobalVars.md_dateFormat))

            # noinspection PyArgumentList
            class MyPlainNumberRenderer(DefaultTableCellRenderer):
                def __init__(self):
                    super(DefaultTableCellRenderer, self).__init__()

                def setValue(self, value):
                    self.setText(str(value))

            # noinspection PyUnusedLocal
            class MyDocListener(DocumentListener):
                def __init__(self, _theSearchField):
                    self._theSearchField = _theSearchField
                def changedUpdate(self, evt):   self.searchFiltersUpdated()
                def removeUpdate(self, evt):    self.searchFiltersUpdated()
                def insertUpdate(self, evt):    self.searchFiltersUpdated()
                def searchFiltersUpdated(self):
                    myPrint("DB", "within searchFiltersUpdated()")
                    _searchFilter = self._theSearchField.getText().strip()
                    if len(_searchFilter) < 1:
                        GlobalVars.currentJTableSearchFilter = None
                    else:
                        GlobalVars.currentJTableSearchFilter = RowFilter.regexFilter("(?i)" + _searchFilter)            # noqa
                    sorter = GlobalVars.saveJTable.getRowSorter()
                    sorter.setRowFilter(GlobalVars.currentJTableSearchFilter)                                           # noqa


            # noinspection PyUnusedLocal
            class MyFocusAdapter(FocusAdapter):
                def __init__(self, _searchField, _document):
                    self._searchField = _searchField
                    self._document = _document
                def focusGained(self, e): self._searchField.setCaretPosition(self._document.getLength())

            GlobalVars.currentJTableSearchFilter = None

            GlobalVars.mySearchField = QuickSearchField()
            GlobalVars.mySearchField.setPlaceholderText("Search reminders...")
            document = GlobalVars.mySearchField.getDocument()                                                           # noqa
            document.addDocumentListener(MyDocListener(GlobalVars.mySearchField))
            GlobalVars.mySearchField.addFocusListener(MyFocusAdapter(GlobalVars.mySearchField,document))                # noqa

            GlobalVars.saveStatusLabel = JLabel("")
            GlobalVars.saveStatusLabel.setForeground(getColorRed())

            def ReminderTable(tabledata, ind):
                global list_future_reminders_frame_     # global as set here
                global _column_widths_LFR                                          # global as set here

                myPrint("D", "In ", inspect.currentframe().f_code.co_name, "()", " - ind:", ind)

                myDefaultWidths = [0,100,175,500,125]    # Rem Obj, Date, AcctName, Desc, Rem Amount

                validCount=0
                lInvalidate=True
                if _column_widths_LFR is not None and isinstance(_column_widths_LFR,(list)) and len(_column_widths_LFR) == len(myDefaultWidths):
                    # if sum(_column_widths_LFR)<1:
                    for width in _column_widths_LFR:
                        if width >= 0 and width <= 1000:																	# noqa
                            validCount += 1

                if validCount == len(myDefaultWidths): lInvalidate=False

                if lInvalidate:
                    myPrint("DB","Found invalid saved columns = resetting to defaults")
                    myPrint("DB","Found: %s" %_column_widths_LFR)
                    myPrint("DB","Resetting to: %s" %myDefaultWidths)
                    _column_widths_LFR = myDefaultWidths
                else:
                    myPrint("DB","Valid column widths loaded - Setting to: %s" %_column_widths_LFR)
                    myDefaultWidths = _column_widths_LFR

                # allcols = col0 + col1 + col2 + col3 + col4 + col5 + col6 + col7 + col8 + col9 + col10 + col11 + col12 + col13 + col14 + col15 + col16 + col17
                allcols = sum(myDefaultWidths)

                screenSize = Toolkit.getDefaultToolkit().getScreenSize()

                # button_width = 220
                # button_height = 40
                # frame_width = min(screenSize.width-20, allcols + 100)
                # frame_height = min(screenSize.height, 900)

                frame_width = min(screenSize.width-20, max(1024,int(round(GetFirstMainFrame.getSize().width *.95,0))))
                frame_height = min(screenSize.height-20, max(768, int(round(GetFirstMainFrame.getSize().height *.95,0))))

                frame_width = min( allcols+20, frame_width)

                # panel_width = frame_width - 50
                # button_panel_height = button_height + 5

                if ind == 1:    GlobalVars.saveScrollPane.getViewport().remove(GlobalVars.saveJTable)  # On repeat, just remove/refresh the table & rebuild the viewport

                colnames = GlobalVars.tableHeaderRowList

                GlobalVars.saveJTable = MyJTable(DefaultTableModel(tabledata, colnames))

                if ind == 0:  # Function can get called multiple times; only set main frames up once
                    # JFrame.setDefaultLookAndFeelDecorated(True)   # Note: Darcula Theme doesn't like this and seems to be OK without this statement...
                    titleExtraTxt = u"" if not isPreviewBuild() else u"<PREVIEW BUILD: %s>" %(version_build)
                    list_future_reminders_frame_.setTitle(u"List future reminders...   %s" %(titleExtraTxt))
                    list_future_reminders_frame_.setName(u"%s_main" %(myModuleID))

                    if (not Platform.isMac()):
                        MD_REF.getUI().getImages()
                        list_future_reminders_frame_.setIconImage(MDImages.getImage(MD_REF.getSourceInformation().getIconResource()))

                    list_future_reminders_frame_.setDefaultCloseOperation(WindowConstants.DO_NOTHING_ON_CLOSE)

                    shortcut = Toolkit.getDefaultToolkit().getMenuShortcutKeyMaskEx()

                    # Add standard CMD-W keystrokes etc to close window
                    list_future_reminders_frame_.getRootPane().getInputMap(JComponent.WHEN_ANCESTOR_OF_FOCUSED_COMPONENT).put(KeyStroke.getKeyStroke(KeyEvent.VK_W, shortcut), "close-window")
                    list_future_reminders_frame_.getRootPane().getInputMap(JComponent.WHEN_ANCESTOR_OF_FOCUSED_COMPONENT).put(KeyStroke.getKeyStroke(KeyEvent.VK_F4, shortcut), "close-window")
                    list_future_reminders_frame_.getRootPane().getInputMap(JComponent.WHEN_ANCESTOR_OF_FOCUSED_COMPONENT).put(KeyStroke.getKeyStroke(KeyEvent.VK_P, shortcut),  "print-me")

                    if lAllowEscapeExitApp_SWSS:
                        list_future_reminders_frame_.getRootPane().getInputMap(JComponent.WHEN_IN_FOCUSED_WINDOW).put(KeyStroke.getKeyStroke(KeyEvent.VK_ESCAPE, 0), "close-window")

                    list_future_reminders_frame_.getRootPane().getActionMap().put("close-window", CloseAction())


                    if Platform.isOSX():
                        save_useScreenMenuBar= System.getProperty("apple.laf.useScreenMenuBar")
                        if save_useScreenMenuBar is None or save_useScreenMenuBar == "":
                            save_useScreenMenuBar= System.getProperty("com.apple.macos.useScreenMenuBar")
                        System.setProperty("apple.laf.useScreenMenuBar", "false")
                        System.setProperty("com.apple.macos.useScreenMenuBar", "false")
                    else:
                        save_useScreenMenuBar = "true"

                    SetupMDColors.updateUI()

                    printButton = JButton("Print")
                    printButton.setToolTipText("Prints the output displayed in this window to your printer")
                    printButton.setOpaque(SetupMDColors.OPAQUE)
                    printButton.setBackground(SetupMDColors.BACKGROUND); printButton.setForeground(SetupMDColors.FOREGROUND)
                    printButton.addActionListener(PrintJTable(list_future_reminders_frame_, GlobalVars.saveJTable, "List Future Reminders"))

                    mb = JMenuBar()

                    menuO = JMenu("<html><B>MENU</b></html>")
                    # menuO = JMenu("OPTIONS")
                    menuO.setForeground(SetupMDColors.FOREGROUND_REVERSED); menuO.setBackground(SetupMDColors.BACKGROUND_REVERSED)

                    menuItemA = JMenuItem("About")
                    menuItemA.setToolTipText("About...")
                    menuItemA.addActionListener(DoTheMenu())
                    menuO.add(menuItemA)

                    menuItemR = JMenuItem("Refresh Data/Default Sort")
                    menuItemR.setToolTipText("Refresh (re-extract) the data, revert to default sort  order....")
                    menuItemR.addActionListener(DoTheMenu())
                    menuO.add(menuItemR)

                    menuItemL = JMenuItem("Change look forward days")
                    menuItemL.setToolTipText("Change the days to look forward")
                    menuItemL.addActionListener(DoTheMenu())
                    menuO.add(menuItemL)

                    menuItemEsc = JCheckBoxMenuItem("Allow Escape to Exit")
                    menuItemEsc.setToolTipText("When enabled, allows the Escape key to exit the main screen")
                    menuItemEsc.addActionListener(DoTheMenu())
                    menuItemEsc.setSelected(lAllowEscapeExitApp_SWSS)
                    menuO.add(menuItemEsc)

                    menuItemRC = JMenuItem("Reset default Column Widths")
                    menuItemRC.setToolTipText("Reset default Column Widths")
                    menuItemRC.addActionListener(DoTheMenu())
                    menuO.add(menuItemRC)

                    menuItemDEBUG = JCheckBoxMenuItem("Debug")
                    menuItemDEBUG.addActionListener(DoTheMenu())
                    menuItemDEBUG.setToolTipText("Enables script to output debug information (internal technical stuff)")
                    menuItemDEBUG.setSelected(debug)
                    menuO.add(menuItemDEBUG)

                    menuItemPS = JMenuItem("Page Setup")
                    menuItemPS.setToolTipText("Printer Page Setup....")
                    menuItemPS.addActionListener(DoTheMenu())
                    menuO.add(menuItemPS)

                    menuItemE = JMenuItem("Close Window")
                    menuItemE.setToolTipText("Exit and close the window")
                    menuItemE.addActionListener(DoTheMenu())
                    menuO.add(menuItemE)

                    mb.add(menuO)

                    mb.add(Box.createHorizontalGlue())
                    mb.add(printButton)
                    mb.add(Box.createRigidArea(Dimension(10, 0)))

                    list_future_reminders_frame_.setJMenuBar(mb)

                    if Platform.isOSX():
                        System.setProperty("apple.laf.useScreenMenuBar", save_useScreenMenuBar)
                        System.setProperty("com.apple.macos.useScreenMenuBar", save_useScreenMenuBar)

                # As the JTable is new each time, add this here....
                list_future_reminders_frame_.getRootPane().getActionMap().remove("print-me")
                list_future_reminders_frame_.getRootPane().getActionMap().put("print-me", PrintJTable(list_future_reminders_frame_, GlobalVars.saveJTable, "List Future Reminders"))

                GlobalVars.saveJTable.getTableHeader().setReorderingAllowed(True)
                GlobalVars.saveJTable.getTableHeader().setDefaultRenderer(DefaultTableHeaderCellRenderer())
                GlobalVars.saveJTable.selectionMode = ListSelectionModel.SINGLE_SELECTION

                fontSize = GlobalVars.saveJTable.getFont().getSize()+5
                GlobalVars.saveJTable.setRowHeight(fontSize)
                GlobalVars.saveJTable.setRowMargin(0)

                GlobalVars.saveJTable.getInputMap(JComponent.WHEN_ANCESTOR_OF_FOCUSED_COMPONENT).put(KeyStroke.getKeyStroke("ENTER"), "Enter")
                GlobalVars.saveJTable.getActionMap().put("Enter", EnterAction())

                for _i in range(0, GlobalVars.saveJTable.getColumnModel().getColumnCount()):
                    tcm = GlobalVars.saveJTable.getColumnModel().getColumn(_i)
                    tcm.setPreferredWidth(myDefaultWidths[_i])
                    if myDefaultWidths[_i] == 0:
                        tcm.setMinWidth(0)
                        tcm.setMaxWidth(0)
                        tcm.setWidth(0)

                cListener1 = ColumnChangeListener(GlobalVars.saveJTable)
                # Put the listener here - else it sets the defaults wrongly above....
                GlobalVars.saveJTable.getColumnModel().addColumnModelListener(cListener1)

                # GlobalVars.saveJTable.getTableHeader().setBackground(Color.LIGHT_GRAY)

                # GlobalVars.saveJTable.setAutoCreateRowSorter(True) # DON'T DO THIS - IT WILL OVERRIDE YOUR NICE CUSTOM SORT

                popupMenu = JPopupMenu()
                editReminder = JMenuItem("Edit Reminder")
                editReminder.addActionListener(DoTheMenu())
                popupMenu.add(editReminder)

                showDetails = JMenuItem("Show Reminder's raw details")
                showDetails.addActionListener(DoTheMenu())
                popupMenu.add(showDetails)

                _deleteReminder = JMenuItem("Delete Reminder")
                _deleteReminder.addActionListener(DoTheMenu())
                popupMenu.add(_deleteReminder)

                GlobalVars.saveJTable.addMouseListener(MyMouseListener)
                GlobalVars.saveJTable.setComponentPopupMenu(popupMenu)

                if ind == 0:
                    GlobalVars.saveScrollPane = JScrollPane(JScrollPane.VERTICAL_SCROLLBAR_ALWAYS, JScrollPane.HORIZONTAL_SCROLLBAR_ALWAYS)  # On first call, create the scrollpane
                    GlobalVars.saveScrollPane.setBorder(CompoundBorder(MatteBorder(1, 1, 1, 1, MD_REF.getUI().getColors().hudBorderColor), EmptyBorder(0, 0, 0, 0)))
                    GlobalVars.saveScrollPane.setBackground((MD_REF.getUI().getColors()).defaultBackground)
                # GlobalVars.saveScrollPane.setPreferredSize(Dimension(frame_width-20, frame_height-20	))

                GlobalVars.saveJTable.setPreferredScrollableViewportSize(Dimension(frame_width-20, frame_height-100))

                GlobalVars.saveJTable.setAutoResizeMode(JTable.AUTO_RESIZE_OFF)

                GlobalVars.saveScrollPane.setViewportView(GlobalVars.saveJTable)
                if ind == 0:

                    searchPanel = JPanel(GridBagLayout())
                    searchPanel.setBorder(EmptyBorder(2, 2, 2, 2))

                    searchPanel.add(GlobalVars.mySearchField,GridC.getc().xy(0,0).padx(50).fillx().wx(1.0).west().insets(0,2,0,2))

                    btnChangeLookForward = JButton("Change Look Forward Days")
                    btnChangeLookForward.setToolTipText("Changes the current 'Look forward [x] days' setting...")
                    btnChangeLookForward.addActionListener(DoTheMenu())
                    searchPanel.add(btnChangeLookForward, GridC.getc().xy(1,0).fillx().insets(0,2,0,2))

                    formatDate = DateUtil.incrementDate(DateUtil.getStrippedDateInt(),0,0,daysToLookForward_LFR)
                    GlobalVars.saveStatusLabel.setText(">>: %s" %(convertStrippedIntDateFormattedText(formatDate)))
                    searchPanel.add(GlobalVars.saveStatusLabel, GridC.getc().xy(2,0).fillx().east().insets(0,2,0,2))

                    p = JPanel(BorderLayout())
                    p.add(searchPanel, BorderLayout.NORTH)
                    p.add(GlobalVars.saveScrollPane, BorderLayout.CENTER)

                    list_future_reminders_frame_.getContentPane().setLayout(BorderLayout())
                    list_future_reminders_frame_.getContentPane().add(p, BorderLayout.CENTER)

                    list_future_reminders_frame_.pack()
                    list_future_reminders_frame_.setLocationRelativeTo(None)

                    try:
                        list_future_reminders_frame_.MoneydanceAppListener = MyMoneydanceEventListener(list_future_reminders_frame_)
                        MD_REF.addAppEventListener(list_future_reminders_frame_.MoneydanceAppListener)
                        myPrint("DB","@@ added AppEventListener() %s @@" %(classPrinter("MoneydanceAppListener", list_future_reminders_frame_.MoneydanceAppListener)))
                    except:
                        myPrint("B","FAILED to add MD App Listener...")
                        dump_sys_error_to_md_console_and_errorlog()

                    list_future_reminders_frame_.isActiveInMoneydance = True

                    if True or Platform.isOSX():
                        # list_future_reminders_frame_.setAlwaysOnTop(True)
                        list_future_reminders_frame_.toFront()

                myPrint("DB","Adding MyListSelectionListener() to JTable:")
                GlobalVars.saveJTable.getSelectionModel().addListSelectionListener(MyListSelectionListener())

                list_future_reminders_frame_.setVisible(True)
                list_future_reminders_frame_.toFront()

                if ind == 0:

                    list_future_reminders_frame_.addWindowFocusListener(MyWindowListener)
                    list_future_reminders_frame_.addWindowListener(MyWindowListener)

                    myPrint("DB","Adding reminder listener:", GlobalVars.reminderListener)
                    MD_REF.getCurrentAccountBook().getReminders().addReminderListener(GlobalVars.reminderListener)


                myPrint("D", "Exiting ", inspect.currentframe().f_code.co_name, "()")

                return

            def FormatAmount(oldamount):
                # Amount is held as an integer in pence
                # Remove - sign if present
                if oldamount < 0:
                    oldamount = oldamount * -1

                oldamount = str(oldamount)

                # Ensure at least 3 character
                if len(oldamount) < 3:
                    oldamount = "000" + oldamount
                    oldamount = (oldamount)[-3:]

                # Extract whole portion of amount
                whole = (oldamount)[0:-2]
                if len(whole) == 0:
                    whole = "0"

                # Extract decimal part of amount
                decimal = (oldamount)[-2:]
                declen = len(decimal)
                if declen == 0:
                    decimal = "00"
                    whole = "0"
                if declen == 1:
                    decimal = "0" + decimal
                    whole = "0"

                # Insert , commas in whole part
                wholelist = list(whole)
                listlen = len(wholelist)
                if wholelist[0] == "-":
                    listlen = listlen - 1
                listpos = 3
                while listpos < listlen:
                    wholelist.insert(-listpos, ",")
                    listpos = listpos + 4
                    listlen = listlen + 1

                newwhole = "".join(wholelist)
                newamount = newwhole + "." + decimal
                return newamount

            def FormatDate(olddate):
                # Date is held as an integer in format YYYYMMDD
                olddate = str(olddate)
                if len(olddate) < 8:
                    olddate = "00000000"
                year = olddate[0:4]
                month = olddate[4:6]
                day = olddate[6:8]

                newdate = day + "/" + month + "/" + year
                if newdate == "00/00/0000":
                    newdate = "Unavailable"

                return newdate

            if build_the_data_file(0):

                if isinstance(GlobalVars.saveJTable, JTable): pass

                # if GlobalVars.saveJTable.getRowCount() > 0:
                #     GlobalVars.saveJTable.setRowSelectionInterval(GlobalVars.saveSelectedRowIndex, GlobalVars.saveSelectedRowIndex)

                # GlobalVars.saveJTable.requestFocus()
                SwingUtilities.invokeLater(GrabFocusRunnable(GlobalVars.mySearchField))

            else:
                myPopupInformationBox(list_future_reminders_frame_, "You have no reminders to display!", GlobalVars.thisScriptName)
                cleanup_actions(list_future_reminders_frame_)
    except:
        crash_txt = "ERROR - List_Future_Reminders has crashed. Please review MD Menu>Help>Console Window for details".upper()
        myPrint("B",crash_txt)
        crash_output = dump_sys_error_to_md_console_and_errorlog(True)
        jif = QuickJFrame("ERROR - List_Future_Reminders:",crash_output).show_the_frame()
        myPopupInformationBox(jif,crash_txt,theMessageType=JOptionPane.ERROR_MESSAGE)
        raise

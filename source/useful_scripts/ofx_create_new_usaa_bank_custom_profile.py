#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# ofx_create_new_usaa_bank_custom_profile.py (build 19) - Author - Stuart Beesley - StuWareSoftSystems 2021

# READ THIS FIRST:
# https://github.com/yogi1967/MoneydancePythonScripts/raw/master/source/useful_scripts/ofx_create_new_usaa_bank_custom_profile.pdf

# Official Infinite Kind knowledgeable article:
# https://infinitekind.tenderapp.com/kb/online-banking-and-bill-pay/connecting-with-usaa

# This script builds a new USAA Bank Custom Profile from scratch to work with the new connection information
# It will DELETE your existing USAA profile(s) first!
# It will populate your UserID, Password, and allow you to change/update the Bank and Credit Card Number
# It will allow also allow you to prime a second account in case you have multiple logins
# This will create a custom profile to avoid any refresh issues....
# NOTE: ofx_create_new_usaa_bank_profile.py and ofx_fix_existing_usaa_bank_profile.py have both been deprecated

# DISCLAIMER >> PLEASE ALWAYS BACKUP YOUR DATA BEFORE MAKING CHANGES (Menu>Export Backup will achieve this)
#               You use this at your own risk. I take no responsibility for its usage..!
#               This should be considered a temporary fix only until Moneydance is fixed

# CREDITS:  @hleofxquotes for his technical input
#           @dtd for his extensive testing and the documentation

###############################################################################
# MIT License
#
# Copyright (c) 2021 Stuart Beesley - StuWareSoftSystems
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
# Use in Moneydance Menu Window->Show Moneybot Console >> Open Script >> RUN

# build: 1 - Initial preview release..... Based upon ofx_create_new_usaa_bank_profile.py (now deprecated)
# build: 1 - Released: 8th March 2021
# build: 2 - Put objects into editing mode by calling .setEditingMode() whilst editing until .syncItem() called
# build: 3 - Small internal tweak; allow 15 digit Amex numbers too
# build: 4 - Allow selection of Account Type
# build: 5 - Cosmetic tweaks - no change to core functionality; change "so_passwd_type_USAASignon" back to "FIXED"
# build: 6 - Internal common code tweaks - nothing to do with the core functionality
# build: 6 - URLEncoder.encode() the UserID and Password in the stored cached string
# build: 7 - Build 3051 of Moneydance... fix references to moneydance_* variables;
# build: 8 - Build 3056 of Moneydance...
# build: 9 - Change "date_avail_accts" to 2021-01-01
# build: 10 - Popup at end to show existing last txn download dates...
# build: 11 - Common code tweaks
# build: 12 - Common code tweaks
# build: 13 - Common code tweaks
# build: 14 - Disable script for 2022.0(4040) onwards - new mapping table
# build: 15 - Fixing to deal with 4040+... Adding custom "tik_fi_id" as "md:custom-1295"
# build: 16 - Updating common code - QuickJFrame()
# build: 17 - Update message on view last download dates window
# build: 18 - Common code tweaks
# build: 19 - Tweak to Authentication Cache routine.... Fixed a bug (that didn't matter too much)...

# CUSTOMIZE AND COPY THIS ##############################################################################################
# CUSTOMIZE AND COPY THIS ##############################################################################################
# CUSTOMIZE AND COPY THIS ##############################################################################################

# SET THESE LINES
myModuleID = u"ofx_create_new_usaa_bank_profile_custom"
version_build = "19"
MIN_BUILD_REQD = 1904                                               # Check for builds less than 1904 / version < 2019.4
_I_CAN_RUN_AS_MONEYBOT_SCRIPT = True

if u"debug" in globals():
    global debug
else:
    debug = False
global ofx_create_new_usaa_bank_profile_frame_
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

class MyJFrame(JFrame):

    def __init__(self, frameTitle=None):
        super(JFrame, self).__init__(frameTitle)
        self.myJFrameVersion = 2
        self.isActiveInMoneydance = False
        self.isRunTimeExtension = False
        self.MoneydanceAppListener = None
        self.HomePageViewObj = None

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

def getMyJFrame( moduleName ):
    try:
        frames = JFrame.getFrames()
        for fr in frames:
            if (fr.getName().lower().startswith(u"%s_main" %moduleName)
                    and type(fr).__name__ == MyJFrame.__name__                         # isinstance() won't work across namespaces
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
            and isinstance(ofx_create_new_usaa_bank_profile_frame_, MyJFrame)        # EDIT THIS
            and ofx_create_new_usaa_bank_profile_frame_.isActiveInMoneydance):       # EDIT THIS
        frameToResurrect = ofx_create_new_usaa_bank_profile_frame_                   # EDIT THIS
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

    from java.lang import Thread

    from com.moneydance.util import Platform
    from com.moneydance.awt import JTextPanel, GridC, JDateField
    from com.moneydance.apps.md.view.gui import MDImages

    from com.infinitekind.util import DateUtil, CustomDateFormat
    from com.infinitekind.moneydance.model import *
    from com.infinitekind.moneydance.model import AccountUtil, AcctFilter, CurrencyType, CurrencyUtil
    from com.infinitekind.moneydance.model import Account, Reminder, ParentTxn, SplitTxn, TxnSearch, InvestUtil, TxnUtil

    from javax.swing import JButton, JScrollPane, WindowConstants, JLabel, JPanel, JComponent, KeyStroke, JDialog, JComboBox
    from javax.swing import JOptionPane, JTextArea, JMenuBar, JMenu, JMenuItem, AbstractAction, JCheckBoxMenuItem, JFileChooser
    from javax.swing import JTextField, JPasswordField, Box, UIManager, JTable, JCheckBox, JRadioButton, ButtonGroup
    from javax.swing.text import PlainDocument
    from javax.swing.border import EmptyBorder
    from javax.swing.filechooser import FileFilter

    exec("from javax.print import attribute")   # IntelliJ doesnt like the use of 'print' (as it's a keyword). Messy, but hey!
    exec("from java.awt.print import PrinterJob")   # IntelliJ doesnt like the use of 'print' (as it's a keyword). Messy, but hey!
    global attribute, PrinterJob

    from java.awt.datatransfer import StringSelection
    from javax.swing.text import DefaultHighlighter

    from java.awt import Color, Dimension, FileDialog, FlowLayout, Toolkit, Font, GridBagLayout, GridLayout
    from java.awt import BorderLayout, Dialog, Insets
    from java.awt.event import KeyEvent, WindowAdapter, InputEvent
    from java.util import Date

    from java.text import DecimalFormat, SimpleDateFormat, MessageFormat
    from java.util import Calendar, ArrayList
    from java.lang import Double, Math, Character
    from java.io import FileNotFoundException, FilenameFilter, File, FileInputStream, FileOutputStream, IOException, StringReader
    from java.io import BufferedReader, InputStreamReader
    from java.nio.charset import Charset
    if isinstance(None, (JDateField,CurrencyUtil,Reminder,ParentTxn,SplitTxn,TxnSearch, JComboBox, JCheckBox,
                         JTextArea, JMenuBar, JMenu, JMenuItem, JCheckBoxMenuItem, JFileChooser, JDialog,
                         JButton, FlowLayout, InputEvent, ArrayList, File, IOException, StringReader, BufferedReader,
                         InputStreamReader, Dialog, JTable, BorderLayout, Double, InvestUtil, JRadioButton, ButtonGroup,
                         AccountUtil, AcctFilter, CurrencyType, Account, TxnUtil, JScrollPane, WindowConstants, JFrame,
                         JComponent, KeyStroke, AbstractAction, UIManager, Color, Dimension, Toolkit, KeyEvent,
                         WindowAdapter, CustomDateFormat, SimpleDateFormat, Insets, FileDialog, Thread, SwingWorker)): pass
    if codecs.BOM_UTF8 is not None: pass
    if csv.QUOTE_ALL is not None: pass
    if datetime.MINYEAR is not None: pass
    if Math.max(1,1): pass
    # END COMMON IMPORTS ###################################################################################################

    # COMMON GLOBALS #######################################################################################################
    global myParameters, myScriptName, _resetParameters, i_am_an_extension_so_run_headless, moneydanceIcon
    global lPickle_version_warning, decimalCharSep, groupingCharSep, lIamAMac, lGlobalErrorDetected
    global MYPYTHON_DOWNLOAD_URL
    # END COMMON GLOBALS ###################################################################################################
    # COPY >> END

    # SET THESE VARIABLES FOR ALL SCRIPTS ##################################################################################
    myScriptName = u"%s.py(Extension)" %myModuleID                                                                      # noqa
    myParameters = {}                                                                                                   # noqa
    _resetParameters = False                                                                                            # noqa
    lPickle_version_warning = False                                                                                     # noqa
    lIamAMac = False                                                                                                    # noqa
    lGlobalErrorDetected = False																						# noqa
    MYPYTHON_DOWNLOAD_URL = "https://yogi1967.github.io/MoneydancePythonScripts/"                                       # noqa

    class GlobalVars:        # Started using this method for storing global variables from August 2021
        defaultPrintService = None
        defaultPrinterAttributes = None
        defaultPrintFontSize = None
        defaultPrintLandscape = None
        defaultDPI = 72     # NOTE: 72dpi is Java2D default for everything; just go with it. No easy way to change
        STATUS_LABEL = None
        DARK_GREEN = Color(0, 192, 0)
        def __init__(self): pass    # Leave empty

    # END SET THESE VARIABLES FOR ALL SCRIPTS ##############################################################################

    # >>> THIS SCRIPT'S IMPORTS ############################################################################################
    from com.infinitekind.moneydance.model import OnlineService
    from com.moneydance.apps.md.view.gui import MDAccountProxy
    from com.infinitekind.tiksync import SyncRecord
    from com.infinitekind.util import StreamTable
    from java.net import URLEncoder
    from com.infinitekind.moneydance.model import OnlineTxnList
    from com.infinitekind.tiksync import SyncableItem

    # >>> THIS SCRIPT'S GLOBALS ########################################################################################
    MD_MDPLUS_BUILD = 4040
    # >>> END THIS SCRIPT'S GLOBALS ####################################################################################

    # COPY >> START
    # COMMON CODE ######################################################################################################
    # COMMON CODE ################# VERSION 103 ########################################################################
    # COMMON CODE ######################################################################################################
    i_am_an_extension_so_run_headless = False                                                                           # noqa
    try:
        myScriptName = os.path.basename(__file__)
    except:
        i_am_an_extension_so_run_headless = True                                                                        # noqa

    scriptExit = """
----------------------------------------------------------------------------------------------------------------------
Thank you for using %s!
The author has other useful Extensions / Moneybot Python scripts available...:

Extension (.mxt) format only:
toolbox                                 View Moneydance settings, diagnostics, fix issues, change settings and much more
net_account_balances:                   Homepage / summary screen widget. Display the total of selected Account Balances
total_selected_transactions:            One-click. Shows a popup total of the register txn amounts selected on screen

Extension (.mxt) and Script (.py) Versions available:
extract_data                            Extract various data to screen and/or csv.. Consolidation of:
- stockglance2020                       View summary of Securities/Stocks on screen, total by Security, export to csv 
- extract_reminders_csv                 View reminders on screen, edit if required, extract all to csv
- extract_currency_history_csv          Extract currency history to csv
- extract_investment_transactions_csv   Extract investment transactions to csv
- extract_account_registers_csv         Extract Account Register(s) to csv along with any attachments

list_future_reminders:                  View future reminders on screen. Allows you to set the days to look forward

A collection of useful ad-hoc scripts (zip file)
useful_scripts:                         Just unzip and select the script you want for the task at hand...

Visit: %s (Author's site)
----------------------------------------------------------------------------------------------------------------------
""" %(myScriptName, MYPYTHON_DOWNLOAD_URL)

    def cleanup_references():
        global MD_REF, MD_REF_UI, MD_EXTENSION_LOADER
        myPrint("DB","About to delete reference to MD_REF, MD_REF_UI and MD_EXTENSION_LOADER....!")
        del MD_REF, MD_REF_UI, MD_EXTENSION_LOADER

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
        global myScriptName, debug, i_am_an_extension_so_run_headless

        if where[0] == "D" and not debug: return

        printString = ""
        for what in args:
            printString += "%s " %what
        printString = printString.strip()

        if where == "P" or where == "B" or where[0] == "D":
            if not i_am_an_extension_so_run_headless:
                try:
                    print(printString)
                except:
                    print("Error writing to screen...")
                    dump_sys_error_to_md_console_and_errorlog()

        if where == "J" or where == "B" or where == "DB":
            dt = datetime.datetime.now().strftime("%Y/%m/%d-%H:%M:%S")
            try:
                System.err.write(myScriptName + ":" + dt + ": ")
                System.err.write(printString)
                System.err.write("\n")
            except:
                System.err.write(myScriptName + ":" + dt + ": "+"Error writing to console")
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

    def pad(theText, theLength):
        if not (isinstance(theText, unicode) or isinstance(theText, str)): theText = safeStr(theText)
        theText = theText[:theLength].ljust(theLength, u" ")
        return theText

    def rpad(theText, theLength):
        if not (isinstance(theText, unicode) or isinstance(theText, str)): theText = safeStr(theText)
        theText = theText[:theLength].rjust(theLength, u" ")
        return theText

    def cpad(theText, theLength):
        if not (isinstance(theText, unicode) or isinstance(theText, str)): theText = safeStr(theText)
        if len(theText)>=theLength: return theText[:theLength]
        padLength = int((theLength - len(theText)) / 2)
        theText = theText[:theLength]
        theText = ((" "*padLength)+theText+(" "*padLength))[:theLength]

        return theText

    myPrint("B", myScriptName, ": Python Script Initialising.......", "Build:", version_build)

    def getMonoFont():
        global debug

        try:
            theFont = MD_REF.getUI().getFonts().code
            # if debug: myPrint("B","Success setting Font set to Moneydance code: %s" %theFont)
        except:
            theFont = Font("monospaced", Font.PLAIN, 15)
            if debug: myPrint("B","Failed to Font set to Moneydance code - So using: %s" %theFont)

        return theFont

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

        if not homeDir: homeDir = u"?"
        return homeDir

    def getDecimalPoint(lGetPoint=False, lGetGrouping=False):
        global debug

        decimalFormat = DecimalFormat.getInstance()
        # noinspection PyUnresolvedReferences
        decimalSymbols = decimalFormat.getDecimalFormatSymbols()

        if not lGetGrouping: lGetPoint = True
        if lGetGrouping and lGetPoint: return u"error"

        try:
            if lGetPoint:
                _decimalCharSep = decimalSymbols.getDecimalSeparator()
                myPrint(u"D",u"Decimal Point Character: %s" %(_decimalCharSep))
                return _decimalCharSep

            if lGetGrouping:
                _groupingCharSep = decimalSymbols.getGroupingSeparator()
                if _groupingCharSep is None or _groupingCharSep == u"":
                    myPrint(u"B", u"Caught empty Grouping Separator")
                    return u""
                if ord(_groupingCharSep) >= 128:    # Probably a nbsp (160) = e.g. South Africa for example..!
                    myPrint(u"B", u"Caught special character in Grouping Separator. Ord(%s)" %(ord(_groupingCharSep)))
                    if ord(_groupingCharSep) == 160:
                        return u" (non breaking space character)"
                    return u" (non printable character)"
                myPrint(u"D",u"Grouping Separator Character:", _groupingCharSep)
                return _groupingCharSep
        except:
            myPrint(u"B",u"Error in getDecimalPoint() routine....?")
            dump_sys_error_to_md_console_and_errorlog()

        return u"error"


    decimalCharSep = getDecimalPoint(lGetPoint=True)
    groupingCharSep = getDecimalPoint(lGetGrouping=True)

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
                if currentTheme.isSystemDark(): return True
            except: pass
            if "dark" in currentTheme.getThemeID(): return True
            if "darcula" in currentTheme.getThemeID(): return True
        except: pass
        return False

    def isMDThemeDarcula():
        try:
            currentTheme = MD_REF.getUI().getCurrentTheme()
            if "darcula" in currentTheme.getThemeID(): return True
        except: pass
        return False

    def isMDThemeVAQua():
        if Platform.isOSX():
            try:
                currentTheme = MD_REF.getUI().getCurrentTheme()
                if ".vaqua" in safeStr(currentTheme.getClass()).lower(): return True
            except: pass
        return False

    # JOptionPane.DEFAULT_OPTION, JOptionPane.YES_NO_OPTION, JOptionPane.YES_NO_CANCEL_OPTION, JOptionPane.OK_CANCEL_OPTION
    # JOptionPane.ERROR_MESSAGE, JOptionPane.INFORMATION_MESSAGE, JOptionPane.WARNING_MESSAGE, JOptionPane.QUESTION_MESSAGE, JOptionPane.PLAIN_MESSAGE

    # Copies MD_REF.getUI().showInfoMessage
    def myPopupInformationBox(theParent=None, theMessage="What no message?!", theTitle="Info", theMessageType=JOptionPane.INFORMATION_MESSAGE):

        if theParent is None:
            if theMessageType == JOptionPane.PLAIN_MESSAGE or theMessageType == JOptionPane.INFORMATION_MESSAGE:
                icon_to_use=MD_REF.getUI().getIcon("/com/moneydance/apps/md/view/gui/glyphs/appicon_64.png")
                JOptionPane.showMessageDialog(theParent, JTextPanel(theMessage), theTitle, theMessageType, icon_to_use)
                return
        JOptionPane.showMessageDialog(theParent, JTextPanel(theMessage), theTitle, theMessageType)
        return

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

    def myPopupAskBackup(theParent=None, theMessage="What no message?!", lReturnTheTruth=False):

        _options=["STOP", "PROCEED WITHOUT BACKUP", "DO BACKUP NOW"]
        response = JOptionPane.showOptionDialog(theParent,
                                                theMessage,
                                                "PERFORM BACKUP BEFORE UPDATE?",
                                                0,
                                                JOptionPane.WARNING_MESSAGE,
                                                None,
                                                _options,
                                                _options[0])

        if response == 2:
            myPrint("B", "User requested to perform Export Backup before update/fix - calling moneydance export backup routine...")
            MD_REF.getUI().setStatus("%s performing an Export Backup...." %(myScriptName),-1.0)
            MD_REF.getUI().saveToBackup(None)
            MD_REF.getUI().setStatus("%s Export Backup completed...." %(myScriptName),0)
            return True

        elif response == 1:
            myPrint("B", "User DECLINED to perform Export Backup before update/fix...!")
            if not lReturnTheTruth:
                return True

        return False

    # Copied MD_REF.getUI().askQuestion
    def myPopupAskQuestion(theParent=None,
                           theTitle="Question",
                           theQuestion="What?",
                           theOptionType=JOptionPane.YES_NO_OPTION,
                           theMessageType=JOptionPane.QUESTION_MESSAGE):

        icon_to_use = None
        if theParent is None:
            if theMessageType == JOptionPane.PLAIN_MESSAGE or theMessageType == JOptionPane.INFORMATION_MESSAGE:
                icon_to_use=MD_REF.getUI().getIcon("/com/moneydance/apps/md/view/gui/glyphs/appicon_64.png")

        # question = wrapLines(theQuestion)
        question = theQuestion
        result = JOptionPane.showConfirmDialog(theParent,
                                               question,
                                               theTitle,
                                               theOptionType,
                                               theMessageType,
                                               icon_to_use)  # getIcon("/com/moneydance/apps/md/view/gui/glyphs/appicon_64.png"))

        return result == 0

    # Copies Moneydance .askForQuestion
    def myPopupAskForInput(theParent,
                           theTitle,
                           theFieldLabel,
                           theFieldDescription="",
                           defaultValue=None,
                           isPassword=False,
                           theMessageType=JOptionPane.INFORMATION_MESSAGE):

        icon_to_use = None
        if theParent is None:
            if theMessageType == JOptionPane.PLAIN_MESSAGE or theMessageType == JOptionPane.INFORMATION_MESSAGE:
                icon_to_use=MD_REF.getUI().getIcon("/com/moneydance/apps/md/view/gui/glyphs/appicon_64.png")

        p = JPanel(GridBagLayout())
        defaultText = None
        if defaultValue: defaultText = defaultValue
        if isPassword:
            field = JPasswordField(defaultText)
        else:
            field = JTextField(defaultText)

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
                                          icon_to_use) == 0):
            return field.getText()
        return None

    # APPLICATION_MODAL, DOCUMENT_MODAL, MODELESS, TOOLKIT_MODAL
    class MyPopUpDialogBox():

        def __init__(self, theParent=None, theStatus="", theMessage="", theWidth=200, theTitle="Info", lModal=True, lCancelButton=False, OKButtonText="OK", lAlertLevel=0):
            self.theParent = theParent
            self.theStatus = theStatus
            self.theMessage = theMessage
            self.theWidth = max(80,theWidth)
            self.theTitle = theTitle
            self.lModal = lModal
            self.lCancelButton = lCancelButton
            self.OKButtonText = OKButtonText
            self.lAlertLevel = lAlertLevel
            self.fakeJFrame = None
            self._popup_d = None
            self.lResult = [None]
            if not self.theMessage.endswith("\n"): self.theMessage+="\n"
            if self.OKButtonText == "": self.OKButtonText="OK"
            if Platform.isOSX() and int(float(MD_REF.getBuild())) >= 3039: self.lAlertLevel = 0    # Colors don't work on Mac since VAQua
            if isMDThemeDark() or isMacDarkModeDetected(): self.lAlertLevel = 0

        class WindowListener(WindowAdapter):

            def __init__(self, theDialog, theFakeFrame, lResult):
                self.theDialog = theDialog
                self.theFakeFrame = theFakeFrame
                self.lResult = lResult

            def windowClosing(self, WindowEvent):                                                                       # noqa
                global debug
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
                global debug
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
                global debug
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

            global debug
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
            global debug
            return self.lResult[0]

        def go(self):
            global debug

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
                        self.callingClass.fakeJFrame.setVisible( False )
                        if not Platform.isOSX():
                            self.callingClass.fakeJFrame.setIconImage(MDImages.getImage(MD_REF.getSourceInformation().getIconResource()))

                    if self.callingClass.lModal:
                        # noinspection PyUnresolvedReferences
                        self.callingClass._popup_d = JDialog(self.callingClass.theParent, self.callingClass.theTitle, Dialog.ModalityType.APPLICATION_MODAL)
                    else:
                        # noinspection PyUnresolvedReferences
                        self.callingClass._popup_d = JDialog(self.callingClass.theParent, self.callingClass.theTitle, Dialog.ModalityType.MODELESS)

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

                    displayJText = JTextArea(self.callingClass.theMessage)
                    displayJText.setFont( getMonoFont() )
                    displayJText.setEditable(False)
                    displayJText.setLineWrap(False)
                    displayJText.setWrapStyleWord(False)

                    _popupPanel=JPanel()

                    # maxHeight = 500
                    _popupPanel.setLayout(GridLayout(0,1))
                    _popupPanel.setBorder(EmptyBorder(8, 8, 8, 8))

                    if self.callingClass.theStatus:
                        _label1 = JLabel(pad(self.callingClass.theStatus,self.callingClass.theWidth-20))
                        if not isMDThemeDark() and not isMacDarkModeDetected():
                            _label1.setForeground(Color.BLUE)
                        _popupPanel.add(_label1)

                    myScrollPane = JScrollPane(displayJText, JScrollPane.VERTICAL_SCROLLBAR_AS_NEEDED,JScrollPane.HORIZONTAL_SCROLLBAR_AS_NEEDED)
                    if displayJText.getLineCount()>5:
                        myScrollPane.setWheelScrollingEnabled(True)
                        _popupPanel.add(myScrollPane)
                    else:
                        _popupPanel.add(displayJText)

                    buttonPanel = JPanel()
                    if self.callingClass.lModal or self.callingClass.lCancelButton:
                        buttonPanel.setLayout(FlowLayout(FlowLayout.CENTER))

                        if self.callingClass.lCancelButton:
                            cancel_button = JButton("CANCEL")
                            cancel_button.setPreferredSize(Dimension(100,40))
                            cancel_button.setBackground(Color.LIGHT_GRAY)
                            cancel_button.setBorderPainted(False)
                            cancel_button.setOpaque(True)
                            cancel_button.addActionListener( self.callingClass.CancelButtonAction(self.callingClass._popup_d, self.callingClass.fakeJFrame,self.callingClass.lResult) )
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
                            ok_button.addActionListener( self.callingClass.OKButtonAction(self.callingClass._popup_d, self.callingClass.fakeJFrame, self.callingClass.lResult) )
                            buttonPanel.add(ok_button)

                        _popupPanel.add(buttonPanel)

                    if self.callingClass.lAlertLevel>=2:
                        # internalScrollPane.setBackground(Color.RED)
                        # theJText.setBackground(Color.RED)
                        # theJText.setForeground(Color.BLACK)
                        displayJText.setBackground(Color.RED)
                        displayJText.setForeground(Color.BLACK)
                        _popupPanel.setBackground(Color.RED)
                        _popupPanel.setForeground(Color.BLACK)
                        buttonPanel.setBackground(Color.RED)
                        myScrollPane.setBackground(Color.RED)

                    elif self.callingClass.lAlertLevel>=1:
                        # internalScrollPane.setBackground(Color.YELLOW)
                        # theJText.setBackground(Color.YELLOW)
                        # theJText.setForeground(Color.BLACK)
                        displayJText.setBackground(Color.YELLOW)
                        displayJText.setForeground(Color.BLACK)
                        _popupPanel.setBackground(Color.YELLOW)
                        _popupPanel.setForeground(Color.BLACK)
                        buttonPanel.setBackground(Color.YELLOW)
                        myScrollPane.setBackground(Color.RED)

                    self.callingClass._popup_d.add(_popupPanel)
                    self.callingClass._popup_d.pack()
                    self.callingClass._popup_d.setLocationRelativeTo(None)
                    self.callingClass._popup_d.setVisible(True)  # Keeping this modal....

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

    try:
        moneydanceIcon = MDImages.getImage(MD_REF.getSourceInformation().getIconResource())
    except:
        moneydanceIcon = None

    def MDDiag():
        global debug
        myPrint("D", "Moneydance Build:", MD_REF.getVersion(), "Build:", MD_REF.getBuild())


    MDDiag()

    myPrint("DB","System file encoding is:", sys.getfilesystemencoding() )   # Not used, but interesting. Perhaps useful when switching between Windows/Macs and writing files...

    def checkVersions():
        global debug

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

        myFont = MD_REF.getUI().getFonts().defaultText

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

    if MD_REF_UI is not None:
        setDefaultFonts()

    def who_am_i():
        try:
            username = System.getProperty("user.name")
        except:
            username = "???"

        return username

    def getHomeDir():
        # Yup - this can be all over the place...
        myPrint("D", 'System.getProperty("user.dir")', System.getProperty("user.dir"))
        myPrint("D", 'System.getProperty("UserHome")', System.getProperty("UserHome"))
        myPrint("D", 'System.getProperty("user.home")', System.getProperty("user.home"))
        myPrint("D", 'os.path.expanduser("~")', os.path.expanduser("~"))
        myPrint("D", 'os.environ.get("HOMEPATH")', os.environ.get("HOMEPATH"))
        return

    def amIaMac():
        return Platform.isOSX()

    myPrint("D", "I am user:", who_am_i())
    if debug: getHomeDir()
    lIamAMac = amIaMac()

    def myDir():
        global lIamAMac
        homeDir = None

        try:
            if lIamAMac:
                homeDir = System.getProperty("UserHome")  # On a Mac in a Java VM, the homedir is hidden
            else:
                # homeDir = System.getProperty("user.home")
                homeDir = os.path.expanduser("~")  # Should work on Unix and Windows
                if homeDir is None or homeDir == "":
                    homeDir = System.getProperty("user.home")
                if homeDir is None or homeDir == "":
                    homeDir = os.environ.get("HOMEPATH")
        except:
            pass

        if homeDir is None or homeDir == "":
            homeDir = MD_REF.getCurrentAccountBook().getRootFolder().getParent()  # Better than nothing!

        myPrint("DB", "Home Directory selected...:", homeDir)
        if homeDir is None: return ""
        return homeDir

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
                    super(JTextFieldLimitYN, self).insertString(myOffset, myString, myAttr)                         # noqa

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
        global debug, myParameters, lPickle_version_warning, version_build, _resetParameters                            # noqa

        myPrint("D", "In ", inspect.currentframe().f_code.co_name, "()" )

        if _resetParameters:
            myPrint("B", "User has specified to reset parameters... keeping defaults and skipping pickle()")
            myParameters = {}
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

                myParameters = pickle.loads(load_string)
                load_file.close()
            except FileNotFoundException:
                myPrint("B", "Error: failed to find parameter file...")
                myParameters = None
            except EOFError:
                myPrint("B", "Error: reached EOF on parameter file....")
                myParameters = None
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
                    myParameters = pickle.load(load_file)
                    load_file.close()
                    myPrint("B","Success loading Encrypted Pickle file - will migrate to non encrypted")
                    lPickle_version_warning = True
                except:
                    myPrint("B","Opening Encrypted Pickle File - Unexpected error ", sys.exc_info()[0])
                    myPrint("B","Opening Encrypted Pickle File - Unexpected error ", sys.exc_info()[1])
                    myPrint("B","Error opening Pickle File - Line Number: ", sys.exc_info()[2].tb_lineno)
                    myPrint("B", "Error: Pickle.load() failed.... Is this a restored dataset? Will ignore saved parameters, and create a new file...")
                    myParameters = None

            if myParameters is None:
                myParameters = {}
                myPrint("DB","Parameters did not load, will keep defaults..")
            else:
                myPrint("DB","Parameters successfully loaded from file...")
        else:
            myPrint("J", "Parameter Pickle file does not exist - will use default and create new file..")
            myPrint("D", "Parameter Pickle file does not exist - will use default and create new file..")
            myParameters = {}

        if not myParameters: return

        myPrint("DB","myParameters read from file contains...:")
        for key in sorted(myParameters.keys()):
            myPrint("DB","...variable:", key, myParameters[key])

        if myParameters.get("debug") is not None: debug = myParameters.get("debug")
        if myParameters.get("lUseMacFileChooser") is not None:
            myPrint("B", "Detected old lUseMacFileChooser parameter/variable... Will delete it...")
            myParameters.pop("lUseMacFileChooser", None)  # Old variable - not used - delete from parameter file

        myPrint("DB","Parameter file loaded if present and myParameters{} dictionary set.....")

        # Now load into memory!
        load_StuWareSoftSystems_parameters_into_memory()

        return

    def save_StuWareSoftSystems_parameters_to_file(myFile="StuWareSoftSystems.dict"):
        global debug, myParameters, lPickle_version_warning, version_build

        myPrint("D", "In ", inspect.currentframe().f_code.co_name, "()" )

        if myParameters is None: myParameters = {}

        # Don't forget, any parameters loaded earlier will be preserved; just add changed variables....
        myParameters["__Author"] = "Stuart Beesley - (c) StuWareSoftSystems"
        myParameters["debug"] = debug

        dump_StuWareSoftSystems_parameters_from_memory()

        # Pickle was originally encrypted, no need, migrating to unencrypted
        migratedFilename = os.path.join(MD_REF.getCurrentAccountBook().getRootFolder().getAbsolutePath(),myFile)

        myPrint("DB","Will try to save parameter file:", migratedFilename)

        ostr = FileOutputStream(migratedFilename)

        myPrint("DB", "about to Pickle.dump and save parameters to unencrypted file:", migratedFilename)

        try:
            save_file = FileUtil.wrap(ostr)
            pickle.dump(myParameters, save_file, protocol=0)
            save_file.close()

            myPrint("DB","myParameters now contains...:")
            for key in sorted(myParameters.keys()):
                myPrint("DB","...variable:", key, myParameters[key])

        except:
            myPrint("B", "Error - failed to create/write parameter file.. Ignoring and continuing.....")
            dump_sys_error_to_md_console_and_errorlog()

            return

        myPrint("DB","Parameter file written and parameters saved to disk.....")

        return

    def get_time_stamp_as_nice_text( timeStamp ):

        prettyDate = ""
        try:
            c = Calendar.getInstance()
            c.setTime(Date(timeStamp))
            dateFormatter = SimpleDateFormat("yyyy/MM/dd HH:mm:ss(.SSS) Z z zzzz")
            prettyDate = dateFormatter.format(c.getTime())
        except:
            pass

        return prettyDate

    def currentDateTimeMarker():
        c = Calendar.getInstance()
        dateformat = SimpleDateFormat("_yyyyMMdd_HHmmss")
        _datetime = dateformat.format(c.getTime())
        return _datetime

    def destroyOldFrames(moduleName):
        myPrint("DB", "In ", inspect.currentframe().f_code.co_name, "()", "Event: ", WindowEvent)
        myPrint("DB", "SwingUtilities.isEventDispatchThread() = %s" %(SwingUtilities.isEventDispatchThread()))
        frames = JFrame.getFrames()
        for fr in frames:
            if fr.getName().lower().startswith(moduleName):
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

    def setDisplayStatus(_theStatus, _theColor="G"):
        """Sets the Display / Status label on the main diagnostic display: G=Green, B=Blue, R=Red, DG=Dark Green"""

        if GlobalVars.STATUS_LABEL is None or not isinstance(GlobalVars.STATUS_LABEL, JLabel): return

        GlobalVars.STATUS_LABEL.setText((_theStatus).ljust(800, " "))

        if _theColor is None or _theColor == "": _theColor = "G"
        _theColor = _theColor.upper()
        if _theColor == "R":    GlobalVars.STATUS_LABEL.setForeground(Color.RED)
        elif _theColor == "B":
            if not isMDThemeDark() and not isMacDarkModeDetected():
                GlobalVars.STATUS_LABEL.setForeground(Color.BLUE)
            else:
                GlobalVars.STATUS_LABEL.setForeground(MD_REF.getUI().getColors().defaultTextForeground)
        elif _theColor == "DG": GlobalVars.STATUS_LABEL.setForeground(GlobalVars.DARK_GREEN)
        else:                   GlobalVars.STATUS_LABEL.setForeground(Color.GREEN)
        return

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

        _DIRS_FD = "apple.awt.fileDialogForDirectories"        # Changes Behaviour. When True you can select a Folder (rather than a file)
        _PKGS_FD = "com.apple.macos.use-file-dialog-packages"

        # FileDialog defaults
        # "apple.awt.fileDialogForDirectories"       default "false" >> set "true"  to allow Directories to be selected
        # "com.apple.macos.use-file-dialog-packages" default "true"  >> set "false" to allow access to Mac 'packages'

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

            if fileChooser_fileFilterText is not None and (not Platform.isOSX() or not Platform.isOSXVersionAtLeast("10.13")):
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

            if fileChooser_fileFilterText is not None and (not Platform.isOSX() or not Platform.isOSXVersionAtLeast("10.13")):
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

            _search_options = [ "Next", "Previous", "Cancel" ]

            defaultDirection = _search_options[self.lastDirection]

            response = JOptionPane.showOptionDialog(self.theFrame,
                                                    p,
                                                    "Search for text",
                                                    JOptionPane.OK_CANCEL_OPTION,
                                                    JOptionPane.QUESTION_MESSAGE,
                                                    None,
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

    try: GlobalVars.defaultPrintFontSize = eval("MD_REF.getUI().getFonts().print.getSize()")   # Do this here as MD_REF disappears after script ends...
    except: GlobalVars.defaultPrintFontSize = 12

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

    class QuickJFrame():

        def __init__(self, title, output, lAlertLevel=0, copyToClipboard=False, lJumpToEnd=False, lWrapText=True, lQuitMDAfterClose=False):
            self.title = title
            self.output = output
            self.lAlertLevel = lAlertLevel
            self.returnFrame = None
            self.copyToClipboard = copyToClipboard
            self.lJumpToEnd = lJumpToEnd
            self.lWrapText = lWrapText
            self.lQuitMDAfterClose = lQuitMDAfterClose
            if Platform.isOSX() and int(float(MD_REF.getBuild())) >= 3039: self.lAlertLevel = 0    # Colors don't work on Mac since VAQua
            if isMDThemeDark() or isMacDarkModeDetected(): self.lAlertLevel = 0

        class QJFWindowListener(WindowAdapter):

            def __init__(self, theFrame, lQuitMDAfterClose=False):
                self.theFrame = theFrame
                self.lQuitMDAfterClose = lQuitMDAfterClose
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

                if self.lQuitMDAfterClose:
                    myPrint("B", "Quit MD after Close triggered... Now quitting MD")
                    self.saveMD_REF.getUI().exit()   # NOTE: This method should already detect whether MD is already shutting down.... (also, MD Shut down just kills extensions dead)
                else:
                    myPrint("DB", "FYI No Quit MD after Close triggered... So doing nothing")

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

                def run(self):                                                                                                      # noqa
                    screenSize = Toolkit.getDefaultToolkit().getScreenSize()
                    frame_width = min(screenSize.width-20, max(1024,int(round(MD_REF.getUI().firstMainFrame.getSize().width *.9,0))))
                    frame_height = min(screenSize.height-20, max(768, int(round(MD_REF.getUI().firstMainFrame.getSize().height *.9,0))))

                    JFrame.setDefaultLookAndFeelDecorated(True)
                    jInternalFrame = MyJFrame(self.callingClass.title + " (%s+F to find/search for text)%s"
                                              %( MD_REF.getUI().ACCELERATOR_MASK_STR,
                                                ("" if not self.callingClass.lQuitMDAfterClose else  " >> MD WILL QUIT AFTER VIEWING THIS <<")))

                    jInternalFrame.setName(u"%s_quickjframe" %myModuleID)

                    if not Platform.isOSX(): jInternalFrame.setIconImage(MDImages.getImage(MD_REF.getUI().getMain().getSourceInformation().getIconResource()))

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
                    jInternalFrame.addWindowListener(self.callingClass.QJFWindowListener(jInternalFrame, self.callingClass.lQuitMDAfterClose))

                    internalScrollPane = JScrollPane(theJText, JScrollPane.VERTICAL_SCROLLBAR_AS_NEEDED,JScrollPane.HORIZONTAL_SCROLLBAR_AS_NEEDED)

                    if self.callingClass.lAlertLevel>=2:
                        internalScrollPane.setBackground(Color.RED)
                        theJText.setBackground(Color.RED)
                        theJText.setForeground(Color.BLACK)
                    elif self.callingClass.lAlertLevel>=1:
                        internalScrollPane.setBackground(Color.YELLOW)
                        theJText.setBackground(Color.YELLOW)
                        theJText.setForeground(Color.BLACK)

                    jInternalFrame.setPreferredSize(Dimension(frame_width, frame_height))

                    mfgtc = fgc = MD_REF.getUI().getColors().defaultTextForeground
                    mbgtc = bgc = MD_REF.getUI().getColors().defaultBackground
                    if (not isMDThemeVAQua() and not isMDThemeDark() and isMacDarkModeDetected())\
                            or (not isMacDarkModeDetected() and isMDThemeDarcula()):
                        # Swap the colors round when text (not a button)
                        mfgtc = MD_REF.getUI().getColors().defaultBackground
                        mbgtc = MD_REF.getUI().getColors().defaultTextForeground
                    opq = False

                    printButton = JButton("Print")
                    printButton.setToolTipText("Prints the output displayed in this window to your printer")
                    printButton.setOpaque(opq)
                    printButton.setBackground(bgc); printButton.setForeground(fgc)
                    printButton.addActionListener(self.callingClass.QuickJFramePrint(self.callingClass, theJText, self.callingClass.title))

                    if GlobalVars.defaultPrinterAttributes is None:
                        printPageSetup = JButton("Page Setup")
                        printPageSetup.setToolTipText("Printer Page Setup")
                        printPageSetup.setOpaque(opq)
                        printPageSetup.setBackground(bgc); printPageSetup.setForeground(fgc)
                        printPageSetup.addActionListener(self.callingClass.QuickJFramePageSetup())

                    saveButton = JButton("Save to file")
                    saveButton.setToolTipText("Saves the output displayed in this window to a file")
                    saveButton.setOpaque(opq)
                    saveButton.setBackground(bgc); saveButton.setForeground(fgc)
                    saveButton.addActionListener(self.callingClass.QuickJFrameSaveTextToFile(self.callingClass.output, jInternalFrame))

                    wrapOption = JCheckBox("Wrap Contents (Screen & Print)", self.callingClass.lWrapText)
                    wrapOption.addActionListener(self.callingClass.ToggleWrap(self.callingClass, theJText))
                    wrapOption.setForeground(mfgtc); wrapOption.setBackground(mbgtc)

                    topButton = JButton("Top")
                    topButton.setOpaque(opq)
                    topButton.setBackground(bgc); topButton.setForeground(fgc)
                    topButton.addActionListener(self.callingClass.QuickJFrameNavigate(theJText, lTop=True))

                    botButton = JButton("Bottom")
                    botButton.setOpaque(opq)
                    botButton.setBackground(bgc); botButton.setForeground(fgc)
                    botButton.addActionListener(self.callingClass.QuickJFrameNavigate(theJText, lBottom=True))

                    closeButton = JButton("Close")
                    closeButton.setOpaque(opq)
                    closeButton.setBackground(bgc); closeButton.setForeground(fgc)
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

    class AboutThisScript():

        class CloseAboutAction(AbstractAction):

            def __init__(self, theFrame):
                self.theFrame = theFrame

            def actionPerformed(self, event):
                global debug
                myPrint("DB", "In ", inspect.currentframe().f_code.co_name, "()", "Event:", event)

                # Listener is already on the Swing EDT...
                self.theFrame.dispose()

        def __init__(self, theFrame):
            global debug, scriptExit
            self.theFrame = theFrame

        def go(self):
            myPrint("DB", "In ", inspect.currentframe().f_code.co_name, "()")

            class MyAboutRunnable(Runnable):
                def __init__(self, callingClass):
                    self.callingClass = callingClass

                def run(self):                                                                                                      # noqa

                    myPrint("DB", "In ", inspect.currentframe().f_code.co_name, "()")
                    myPrint("DB", "SwingUtilities.isEventDispatchThread() = %s" %(SwingUtilities.isEventDispatchThread()))

                    # noinspection PyUnresolvedReferences
                    about_d = JDialog(self.callingClass.theFrame, "About", Dialog.ModalityType.MODELESS)

                    shortcut = Toolkit.getDefaultToolkit().getMenuShortcutKeyMaskEx()
                    about_d.getRootPane().getInputMap(JComponent.WHEN_ANCESTOR_OF_FOCUSED_COMPONENT).put(KeyStroke.getKeyStroke(KeyEvent.VK_W, shortcut), "close-window")
                    about_d.getRootPane().getInputMap(JComponent.WHEN_ANCESTOR_OF_FOCUSED_COMPONENT).put(KeyStroke.getKeyStroke(KeyEvent.VK_F4, shortcut), "close-window")
                    about_d.getRootPane().getInputMap(JComponent.WHEN_IN_FOCUSED_WINDOW).put(KeyStroke.getKeyStroke(KeyEvent.VK_ESCAPE, 0), "close-window")

                    about_d.getRootPane().getActionMap().put("close-window", self.callingClass.CloseAboutAction(about_d))

                    about_d.setDefaultCloseOperation(WindowConstants.DISPOSE_ON_CLOSE)  # The CloseAction() and WindowListener() will handle dispose() - else change back to DISPOSE_ON_CLOSE

                    if (not Platform.isMac()):
                        # MD_REF.getUI().getImages()
                        about_d.setIconImage(MDImages.getImage(MD_REF.getUI().getMain().getSourceInformation().getIconResource()))

                    aboutPanel=JPanel()
                    aboutPanel.setLayout(FlowLayout(FlowLayout.LEFT))
                    aboutPanel.setPreferredSize(Dimension(1120, 525))

                    _label1 = JLabel(pad("Author: Stuart Beesley", 800))
                    if not isMDThemeDark() and not isMacDarkModeDetected(): _label1.setForeground(Color.BLUE)
                    aboutPanel.add(_label1)

                    _label2 = JLabel(pad("StuWareSoftSystems (2020-2021)", 800))
                    if not isMDThemeDark() and not isMacDarkModeDetected(): _label2.setForeground(Color.BLUE)
                    aboutPanel.add(_label2)

                    _label3 = JLabel(pad("Script/Extension: %s (build: %s)" %(myScriptName, version_build), 800))
                    if not isMDThemeDark() and not isMacDarkModeDetected(): _label3.setForeground(Color.BLUE)
                    aboutPanel.add(_label3)

                    displayString=scriptExit
                    displayJText = JTextArea(displayString)
                    displayJText.setFont( getMonoFont() )
                    displayJText.setEditable(False)
                    displayJText.setLineWrap(False)
                    displayJText.setWrapStyleWord(False)
                    displayJText.setMargin(Insets(8, 8, 8, 8))

                    aboutPanel.add(displayJText)

                    about_d.add(aboutPanel)

                    about_d.pack()
                    about_d.setLocationRelativeTo(None)
                    about_d.setVisible(True)

            if not SwingUtilities.isEventDispatchThread():
                myPrint("DB",".. Not running within the EDT so calling via MyAboutRunnable()...")
                SwingUtilities.invokeAndWait(MyAboutRunnable(self))
            else:
                myPrint("DB",".. Already within the EDT so calling naked...")
                MyAboutRunnable(self).run()

            myPrint("D", "Exiting ", inspect.currentframe().f_code.co_name, "()")

    def isGoodRate(theRate):

        if Double.isNaN(theRate) or Double.isInfinite(theRate) or theRate == 0:
            return False
        return True

    def safeInvertRate(theRate):

        if not isGoodRate(theRate):
            return theRate
        return (1.0 / theRate)

    def convertBytesMBs(_size): return round((_size/(1000.0*1000.0)),1)

    def convertBytesKBs(_size): return round((_size/(1000.0)),1)

    def getHumanReadableDateTimeFromTimeStamp(_theTimeStamp):
        return datetime.datetime.fromtimestamp(_theTimeStamp).strftime('%Y-%m-%d %H:%M:%S')

    def getHumanReadableModifiedDateTimeFromFile(_theFile):
        return getHumanReadableDateTimeFromTimeStamp(os.path.getmtime(_theFile))

    def convertStrippedIntDateFormattedText( strippedDateInt ):

        prettyDate = ""
        try:
            c = Calendar.getInstance()
            dateFromInt = DateUtil.convertIntDateToLong(strippedDateInt)
            c.setTime(dateFromInt)
            dateFormatter = SimpleDateFormat("yyyy/MM/dd")
            prettyDate = dateFormatter.format(c.getTime())
        except:
            pass

        return prettyDate

    def selectHomeScreen():

        try:
            currentViewAccount = MD_REF.getUI().firstMainFrame.getSelectedAccount()
            if currentViewAccount != MD_REF.getRootAccount():
                myPrint("DB","Switched to Home Page Summary Screen (from: %s)" %(currentViewAccount))
                MD_REF.getUI().firstMainFrame.selectAccount(MD_REF.getRootAccount())
        except:
            myPrint("B","Error switching to Home Page Summary Screen")

    # END COMMON DEFINITIONS ###############################################################################################
    # END COMMON DEFINITIONS ###############################################################################################
    # END COMMON DEFINITIONS ###############################################################################################
    # COPY >> END

    # >>> CUSTOMISE & DO THIS FOR EACH SCRIPT
    # >>> CUSTOMISE & DO THIS FOR EACH SCRIPT
    # >>> CUSTOMISE & DO THIS FOR EACH SCRIPT
    def load_StuWareSoftSystems_parameters_into_memory():
        pass
        return

    # >>> CUSTOMISE & DO THIS FOR EACH SCRIPT
    def dump_StuWareSoftSystems_parameters_from_memory():
        pass
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
            MD_REF.getUI().setStatus(">> StuWareSoftSystems - thanks for using >> %s......." %(myScriptName),0)
        except:
            pass  # If this fails, then MD is probably shutting down.......

        if not i_am_an_extension_so_run_headless: print(scriptExit)

        cleanup_references()

    GlobalVars.defaultPrintLandscape = True
    # END ALL CODE COPY HERE ###############################################################################################
    # END ALL CODE COPY HERE ###############################################################################################
    # END ALL CODE COPY HERE ###############################################################################################

    MD_REF.getUI().setStatus(">> StuWareSoftSystems - %s launching......." %(myScriptName),0)

    def isMDPlusEnabledBuild(): return (float(MD_REF.getBuild()) >= MD_MDPLUS_BUILD)

    PARAMETER_KEY = "ofx_create_new_usaa_bank_custom_profile"

    book = MD_REF.getCurrentAccountBook()

    mappingObject = None

    if isMDPlusEnabledBuild():
        myPrint("B", "MD2022+ build detected.. Enabling new features....")
        from com.infinitekind.moneydance.model import OnlineAccountMapping
        mappingObject = book.getItemForID("online_acct_mapping")
        if mappingObject is not None:
            myPrint("B", "Online Account Mapping object found and reference stored....")
        else:
            myPrint("B", "No Online Account mapping object found...")

    if not isMDPlusEnabledBuild() and book.getItemForID("online_acct_mapping") is not None:
        alert = "MD version older than MD2022 detected, but you have an Online Account mapping object.. Have you downgraded? SORRY >> CANNOT PROCEED!"
        myPopupInformationBox(None, alert, theMessageType=JOptionPane.ERROR_MESSAGE)
        raise Exception(alert)


    def isUserEncryptionPassphraseSet():

        try:
            keyFile = File(MD_REF.getCurrentAccount().getBook().getRootFolder(), "key")

            keyInfo = SyncRecord()
            fin = FileInputStream(keyFile)
            keyInfo.readSet(fin)
            fin.close()
            return keyInfo.getBoolean("userpass", False)
        except:
            pass
        return False

    def my_getAccountKey(acct):      # noqa
        acctNum = acct.getAccountNum()
        if (acctNum <= 0):
            return acct.getUUID()
        return str(acctNum)

    class MyAcctFilter(AcctFilter):

        def __init__(self, selectType=0):
            self.selectType = selectType

        def matches(self, acct):         # noqa
            if self.selectType == 0:
                # noinspection PyUnresolvedReferences
                if not (acct.getAccountType() == Account.AccountType.BANK):
                    return False

            if self.selectType == 1:
                # noinspection PyUnresolvedReferences
                if not (acct.getAccountType() == Account.AccountType.CREDIT_CARD):
                    return False

            if self.selectType == 2:
                # noinspection PyUnresolvedReferences
                if not (acct.getAccountType() == Account.AccountType.BANK or acct.getAccountType() == Account.AccountType.CREDIT_CARD):
                    return False
                else:
                    return True

            if self.selectType == 3:
                # noinspection PyUnresolvedReferences
                if not (acct.getAccountType() == Account.AccountType.BANK or acct.getAccountType() == Account.AccountType.CREDIT_CARD):
                    return False

            if (acct.getAccountOrParentIsInactive()): return False
            if (acct.getHideOnHomePage() and acct.getBalance() == 0): return False

            return True

    class StoreAccountList():
        def __init__(self, obj):
            if isinstance(obj,Account):
                self.obj = obj                          # type: Account
            else:
                self.obj = None

        def __str__(self):
            if self.obj is None:
                return "Invalid Acct Obj or None"
            return "%s : %s" %(self.obj.getAccountType(),self.obj.getFullAccountName())

        def __repr__(self):
            if self.obj is None:
                return "Invalid Acct Obj or None"
            return "%s : %s" %(self.obj.getAccountType(),self.obj.getFullAccountName())

    if not myPopupAskQuestion(None, "BACKUP", "CREATE A NEW (CUSTOM) USAA PROFILE >> HAVE YOU DONE A GOOD BACKUP FIRST?", theMessageType=JOptionPane.WARNING_MESSAGE):
        alert = "BACKUP FIRST! PLEASE USE FILE>EXPORT BACKUP then come back!! - No changes made."
        myPopupInformationBox(None, alert, theMessageType=JOptionPane.ERROR_MESSAGE)
        raise Exception(alert)

    if not myPopupAskQuestion(None, "DISCLAIMER", "DO YOU ACCEPT YOU RUN THIS AT YOUR OWN RISK?", theMessageType=JOptionPane.WARNING_MESSAGE):
        alert = "Disclaimer rejected - no changes made"
        myPopupInformationBox(None, alert, theMessageType=JOptionPane.ERROR_MESSAGE)
        raise Exception(alert)

    ask = MyPopUpDialogBox(None, "This script will delete your existing USAA bank profile(s) and CREATE A BRAND NEW CUSTOM USAA PROFILE:",
                           "Get the latest useful_scripts.zip package from: %s \n"
                           "Read the latest walk through guide: ofx_create_new_usaa_bank_custom_profile.pdf\n"
                           "Latest: https://github.com/yogi1967/MoneydancePythonScripts/raw/master/source/useful_scripts/ofx_create_new_usaa_bank_custom_profile.pdf\n\n"
                           "This script configure one bank account & up to one credit card [optional]. You can add more later using standard Moneydance online menu\n"
                           "It will also allow you to 'prime' a second additional set of credentials for setup later [optional]\n\n"
                           "> You login to USAA at https://www.usaa.com/accessid to get your 'Quicken user' credentials.\n"
                           "> This is also where you find your clientUid (UUID) hidden within the browser url (BEFORE you click approve Quicken access)\n\n"
                           "This script will ask you for many numbers. You must know them:\n"
                           "- Do you know your new Bank Supplied UUID (36 digits 8-4-4-4-12)?\n"
                           "- Do you know your Bank supplied UserID (min length 8)?\n"
                           "- Do you know your new Password (min length 6) - no longer a PIN?\n"
                           "- Do you know your Bank Account Number(s) (10-digits) and routing Number (9-digits - usually '314074269')?\n"
                           "- Do you know the DIFFERENT Credit Card number that the bank will accept? (This may not apply, just try your current one first)\n"
                           "- Do you know which Accounts in Moneydance to select and link to this new profile?\n"
                           "IF NOT, STOP AND GATHER ALL INFORMATION" %(MYPYTHON_DOWNLOAD_URL),
                           250,"KNOWLEDGE",
                           lCancelButton=True,OKButtonText="CONFIRMED", lAlertLevel=1)
    if not ask.go():
        alert = "Knowledge rejected - no changes made"
        myPopupInformationBox(None, alert, theMessageType=JOptionPane.ERROR_MESSAGE)
        raise Exception(alert)

    lCachePasswords = (isUserEncryptionPassphraseSet() and MD_REF.getUI().getCurrentAccounts().getBook().getLocalStorage().getBoolean("store_passwords", False))
    if not lCachePasswords:
        if not myPopupAskQuestion(None,"STORE PASSWORDS","Your system is not set up to save/store passwords. Do you want to continue?",theMessageType=JOptionPane.ERROR_MESSAGE):
            alert = "Please set up Master password and select store passwords first - then try again - no changes made"
            myPopupInformationBox(None, alert, theMessageType=JOptionPane.ERROR_MESSAGE)
            raise Exception(alert)
        myPrint("B", "Proceeding even though system is not set up for passwords")


    lOverrideRootUUID = False
    lMultiAccountSetup = False

    prime_options = ["NO (Skip this)", "YES - PRIME SECOND ACCOUNT"]
    theResult = JOptionPane.showOptionDialog(None,
                                          "Do you have multiple DIFFERENT credentials where you wish to 'prime' the default UUID into (Root's) profile?",
                                          "MULTI-ACCOUNTS",
                                             JOptionPane.YES_NO_OPTION,
                                             JOptionPane.QUESTION_MESSAGE,
                                             None,
                                             prime_options,
                                             prime_options[0])
    if theResult > 0:
        lMultiAccountSetup = True
        myPrint("B","Will setup multi-accounts too.... ")

        # prime_options = ["NO (Skip this)","YES - SET GLOBAL DEFAULT ROOT UUID"]
        # theResult = JOptionPane.showOptionDialog(None,
        #                                          "Do you also wish to override Root's (global) default UUID with the one you specify?",
        #                                          "OVERRIDE ROOT DEFAULT UUID",
        #                                          JOptionPane.YES_NO_OPTION,
        #                                          JOptionPane.QUESTION_MESSAGE,
        #                                          None,
        #                                          prime_options,
        #                                          prime_options[0])
        # if theResult > 0:
        #     lOverrideRootUUID = True
        #     myPrint("B","Will also override Root UUID too.... ")
        # else:
        #     myPrint("B","User declined NOT to prime the global Root Default UUID...")
    else:
        myPrint("B","User selected NOT to prime for multiple-accounts...")

    serviceList = MD_REF.getCurrentAccount().getBook().getOnlineInfo().getAllServices()  # type: [OnlineService]

    USAA_FI_ID = "67811"
    USAA_FI_ORG = "USAA Federal Savings Bank"
    USAA_PROFILE_NAME = "USAA Custom Profile (ofx_create_new_usaa_bank_profile_custom.py)"
    OLD_TIK_FI_ID = "md:1295"
    NEW_TIK_FI_ID = "md:custom-1295"

    authKeyPrefix = "ofx.client_uid"

    SECU_ACCOUNT_TYPES = ["CHECKING", "SAVINGS", "MONEYMRKT"]

    ####################################################################################################################
    deleteServices = []
    for svc in serviceList:
        if (svc.getTIKServiceID() == OLD_TIK_FI_ID or svc.getTIKServiceID() == NEW_TIK_FI_ID
                or svc.getServiceId() == ":%s:%s" %(USAA_FI_ORG, USAA_FI_ID)
                or "USAA" in svc.getFIOrg()
                or "USAA" in svc.getFIName()):
            myPrint("B", "Found USAA service - to delete: %s" %(svc))
            deleteServices.append(svc)

    root = MD_REF.getRootAccount()
    rootKeys = list(root.getParameterKeys())
    lRootNeedsSync = False

    mappingKeys = None
    if mappingObject is not None: mappingKeys = list(mappingObject.getParameterKeys())
    lMappingNeedsSync = False

    if len(deleteServices) < 1:
        myPrint("B", "No USAA services / profile found to delete...")
    else:
        if not myPopupAskQuestion(None, "DELETE OLD SERVICES", "OK TO DELETE %s OLD USAA SERVICES (I WILL DO THIS FIRST)?" % (len(deleteServices)), theMessageType=JOptionPane.ERROR_MESSAGE):
            alert = "ERROR - User declined to delete %s old USAA service profiles - no changes made" %(len(deleteServices))
            myPopupInformationBox(None, alert, theMessageType=JOptionPane.ERROR_MESSAGE)
            raise Exception(alert)
        else:
            accounts = AccountUtil.allMatchesForSearch(MD_REF.getCurrentAccount().getBook(), MyAcctFilter(2))
            for s in deleteServices:
                iCount = 0
                for a in accounts:
                    if a.getBankingFI() == s or a.getBillPayFI() == s:
                        iCount+=1
                        myPrint("B", "clearing service link flag from account %s (%s)" %(a,s))
                        a.setEditingMode()
                        a.setBankingFI(None)
                        if isMDPlusEnabledBuild(): a.setOnlineIDForServiceID(s.getTIKServiceID(), None)
                        a.setBillPayFI(None)
                        a.syncItem()
                myPrint("B", "Clearing authentication cache from %s" %s)
                s.clearAuthenticationCache()

                # Clean up root here - as with custom profiles the UUID sets stored instead of the TIK ID which can be identified later....
                if s.getTIKServiceID() != OLD_TIK_FI_ID and s.getTIKServiceID() != NEW_TIK_FI_ID:  # Thus we presume it's our own custom profile, older script using uuid...
                    for i in range(0,len(rootKeys)):
                        rk = rootKeys[i]
                        if rk.startswith(authKeyPrefix) and (s.getTIKServiceID() in rk):
                            myPrint("B", "Deleting old authKey associated with this profile (from Root) %s: %s" %(rk,root.getParameter(rk)))
                            if not lRootNeedsSync: root.setEditingMode()
                            root.setParameter(rk, None)
                            lRootNeedsSync = True
                        i+=1

                if mappingObject is not None:
                    myPrint("B", "Checking Online Account Mapping object for references to old profile...")
                    for i in range(0, len(mappingKeys)):
                        pk = mappingKeys[i]
                        if pk.startswith("map.") and (OLD_TIK_FI_ID in pk or NEW_TIK_FI_ID in pk):
                            myPrint("B", "Deleting old Account Mapping %s: %s" %(pk, mappingObject.getParameter(pk)))
                            if not lMappingNeedsSync: mappingObject.setEditingMode()
                            mappingObject.setParameter(pk, None)
                            lMappingNeedsSync = True
                        i+=1

                myPrint("B", "Deleting profile %s" %s)
                s.deleteItem()
                myPopupInformationBox(None,"I have deleted Bank logon profile / service: %s and forgotten associated credentials (%s accounts were de-linked)" %(s,iCount))
            del accounts

    if lRootNeedsSync: root.syncItem()
    if lMappingNeedsSync: mappingObject.syncItem()

    del serviceList, deleteServices, lRootNeedsSync, rootKeys, mappingObject


    ####################################################################################################################
    invalidBankingLinks = []
    invalidBillPayLinks = []
    myPrint("B","Searching for Account banking / Bill Pay links with no profile (just a general cleanup routine)....")
    accounts = AccountUtil.allMatchesForSearch(MD_REF.getCurrentAccount().getBook(), MyAcctFilter(2))
    for a in accounts:
        if a.getBankingFI() is None and a.getParameter("olbfi", "") != "":
            invalidBankingLinks.append(a)
            myPrint("B","... Found account '%s' with a banking link (to %s), but no service profile exists (thus dead)..." %(a,a.getParameter("olbfi", "")))

        if a.getBillPayFI() is None and a.getParameter("bpfi", "") != "":
            invalidBillPayLinks.append(a)
            myPrint("B","... Found account '%s' with a BillPay link (to %s), but no service profile exists (thus dead)..." %(a,a.getParameter("bpfi", "")))

    if len(invalidBankingLinks) or len(invalidBillPayLinks):
        if myPopupAskQuestion(None,
                              "ACCOUNT WITH DEAD SERVICE PROFILE LINKS",
                              "ALERT: I found %s Banking and %s BillPay links to 'dead' / missing Service / Connection profiles - Shall I remove these links?"
                              %(len(invalidBankingLinks),len(invalidBillPayLinks)),
                              theMessageType=JOptionPane.INFORMATION_MESSAGE):
            for a in invalidBankingLinks:
                a.setBankingFI(None)
                a.syncItem()
                myPrint("B","...removed the dead link Banking link on account %s" %(a))
            for a in invalidBillPayLinks:
                a.setBillPayFI(None)
                a.syncItem()
                myPrint("B","...removed the dead link BillPay link on account %s" %(a))

    del invalidBankingLinks, invalidBillPayLinks, accounts
    ####################################################################################################################

    selectedBankAccount = selectedCCAccount = None

    accounts = AccountUtil.allMatchesForSearch(MD_REF.getCurrentAccount().getBook(), MyAcctFilter(0))
    accounts = sorted(accounts, key=lambda sort_x: (sort_x.getAccountType(), sort_x.getFullAccountName().upper()))
    bankAccounts = []
    for acct in accounts:
        bankAccounts.append(StoreAccountList(acct))

    if len(bankAccounts):
        saveOK = UIManager.get("OptionPane.okButtonText")
        saveCancel = UIManager.get("OptionPane.cancelButtonText")
        UIManager.put("OptionPane.okButtonText", "SELECT & PROCEED")
        UIManager.put("OptionPane.cancelButtonText", "NO BANK ACCOUNT")

        selectedBankAccount = JOptionPane.showInputDialog(None,
                                                          "Select the Bank account to link",
                                                          "Select Bank account",
                                                          JOptionPane.WARNING_MESSAGE,
                                                          None,
                                                          bankAccounts,
                                                          None)     # type: StoreAccountList
        UIManager.put("OptionPane.okButtonText", saveOK)
        UIManager.put("OptionPane.cancelButtonText", saveCancel)
    else:
        selectedBankAccount = None

    if not selectedBankAccount:
        myPrint("B", "no bank account selected")
        accountTypeOFX = None
    else:
        selectedBankAccount = selectedBankAccount.obj                                                                   # noqa
        if selectedBankAccount.getAccountType() != Account.AccountType.BANK:                                            # noqa
            alert = "ERROR BANK ACCOUNT INVALID TYPE SELECTED"
            myPopupInformationBox(None, alert, theMessageType=JOptionPane.ERROR_MESSAGE)
            raise Exception(alert)
        myPrint("B", "selected bank account %s" %selectedBankAccount)


        defaultAccountType = selectedBankAccount.getOFXAccountType()                                                   # noqa
        if defaultAccountType is None or defaultAccountType == "" or defaultAccountType not in SECU_ACCOUNT_TYPES:
            myPrint("DB","Account: %s account type is currently %s - defaulting to %s"
                    % (selectedBankAccount, defaultAccountType, SECU_ACCOUNT_TYPES[0]))
            defaultAccountType = SECU_ACCOUNT_TYPES[0]

        accountTypeOFX = JOptionPane.showInputDialog(None,
                                                     "Carefully select the type for this account: %s" % (selectedBankAccount),
                                                     "ACCOUNT TYPE",
                                                     JOptionPane.INFORMATION_MESSAGE,
                                                     MD_REF.getUI().getIcon("/com/moneydance/apps/md/view/gui/glyphs/appicon_64.png"),
                                                     SECU_ACCOUNT_TYPES,
                                                     defaultAccountType)

        if not accountTypeOFX:
            alert = "ERROR - NO ACCOUNT TYPE SELECTED"
            myPopupInformationBox(None, alert, theMessageType=JOptionPane.ERROR_MESSAGE)
            raise Exception(alert)
        del defaultAccountType
        myPrint("B", "Account %s - selected type: %s" %(selectedBankAccount,accountTypeOFX))


    # CREDIT CARD
    accounts = AccountUtil.allMatchesForSearch(MD_REF.getCurrentAccount().getBook(), MyAcctFilter(1))
    accounts = sorted(accounts, key=lambda sort_x: (sort_x.getAccountType(), sort_x.getFullAccountName().upper()))
    ccAccounts = []
    for acct in accounts:
        ccAccounts.append(StoreAccountList(acct))

    if len(ccAccounts):
        saveOK = UIManager.get("OptionPane.okButtonText")
        saveCancel = UIManager.get("OptionPane.cancelButtonText")
        UIManager.put("OptionPane.okButtonText", "SELECT & PROCEED")
        UIManager.put("OptionPane.cancelButtonText", "NO CC ACCOUNT")

        selectedCCAccount = JOptionPane.showInputDialog(None,
                                                        "Select the CC account to link",
                                                        "Select CC account",
                                                        JOptionPane.WARNING_MESSAGE,
                                                        None,
                                                        ccAccounts,
                                                        None)     # type: StoreAccountList

        UIManager.put("OptionPane.okButtonText", saveOK)
        UIManager.put("OptionPane.cancelButtonText", saveCancel)
    else:
        selectedCCAccount = None

    if not selectedCCAccount:
        myPrint("B", "no CC account selected")
    else:
        selectedCCAccount = selectedCCAccount.obj            # noqa
        if selectedCCAccount.getAccountType() != Account.AccountType.CREDIT_CARD:                                       # noqa
            alert = "ERROR CC ACCOUNT INVALID TYPE SELECTED"
            myPopupInformationBox(None, alert, theMessageType=JOptionPane.ERROR_MESSAGE)
            raise Exception(alert)
        myPrint("B", "selected CC account %s" %selectedCCAccount)

    if not selectedBankAccount and not selectedCCAccount:
        alert = "ERROR - You must select Bank and or CC account(s)"
        myPopupInformationBox(None, alert, theMessageType=JOptionPane.ERROR_MESSAGE)
        raise Exception(alert)

    ####################################################################################################################

    dummy = "12345678-1111-1111-1111-123456789012"

    defaultEntry = "nnnnnnnn-nnnn-nnnn-nnnn-nnnnnnnnnnnn"
    while True:
        uuid = myPopupAskForInput(None, "UUID", "UUID", "Paste the Bank Supplied UUID 36 digits 8-4-4-4-12 very carefully", defaultEntry)
        myPrint("B", "UUID entered: %s" %uuid)
        if uuid is None:
            alert = "ERROR - No uuid entered! Aborting"
            myPopupInformationBox(None, alert, theMessageType=JOptionPane.ERROR_MESSAGE)
            raise Exception(alert)
        defaultEntry = uuid
        if (uuid is None or uuid == "" or len(uuid) != 36 or uuid == "nnnnnnnn-nnnn-nnnn-nnnn-nnnnnnnnnnnn" or
                (str(uuid)[8]+str(uuid)[13]+str(uuid)[18]+str(uuid)[23]) != "----"):
            myPrint("B", "\n ** ERROR - no valid uuid supplied - try again ** \n")
            continue
        break
    del defaultEntry

    defaultEntry = "UserID"
    while True:
        userID = myPopupAskForInput(None, "UserID", "UserID", "Type/Paste your UserID (min length 8) very carefully", defaultEntry)
        myPrint("B", "userID entered: %s" %userID)
        if userID is None:
            alert = "ERROR - no userID supplied! Aborting"
            myPopupInformationBox(None, alert, theMessageType=JOptionPane.ERROR_MESSAGE)
            raise Exception(alert)
        defaultEntry = userID
        if userID is None or userID == "" or userID == "UserID" or len(userID)<8:
            myPrint("B", "\n ** ERROR - no valid userID supplied - try again ** \n")
            continue
        break
    del defaultEntry

    defaultEntry = "*****"
    while True:
        password = myPopupAskForInput(None, "password", "password", "Type/Paste your Password (min length 6) very carefully", defaultEntry)
        myPrint("B", "password entered: %s" %password)
        if password is None:
            alert = "ERROR - no password supplied! Aborting"
            myPopupInformationBox(None, alert, theMessageType=JOptionPane.ERROR_MESSAGE)
            raise Exception(alert)
        defaultEntry = password
        if password is None or password == "" or password == "*****" or len(password) < 6:
            myPrint("B", "\n ** ERROR - no password supplied - try again ** \n")
            continue
        break
    del defaultEntry

    bankID = routID = None
    route = bankAccount = None

    if selectedBankAccount:
        bankAccount = selectedBankAccount.getBankAccountNumber()        # noqa
        bankID = myPopupAskForInput(None, "BankAccount", "BankAccount", "Type/Paste your Bank Account Number - very carefully", bankAccount)
        if bankID is None or bankID == "":
            alert = "ERROR - no bankID supplied - Aborting"
            myPopupInformationBox(None, alert, theMessageType=JOptionPane.ERROR_MESSAGE)
            raise Exception(alert)
        myPrint("B", "existing bank account:   %s" %bankAccount)
        myPrint("B", "bankID entered:          %s" %bankID)

        route = selectedBankAccount.getOFXBankID()                      # noqa
        if route == "" or len(route) != 9:
            route = "314074269"
        routID = myPopupAskForInput(None, "Routing", "Routing", "Type/Paste your Routing Number (9 digits - usually '314074269')- very carefully", route)
        if routID is None or routID == "" or len(routID) != 9:
            alert = "ERROR - invalid Routing supplied - Aborting"
            myPopupInformationBox(None, alert, theMessageType=JOptionPane.ERROR_MESSAGE)
            raise Exception(alert)
        myPrint("B", "existing routing number: %s" %route)
        myPrint("B", "routID entered:          %s" %routID)

    ccID = ccAccount = None

    if selectedCCAccount:
        while True:
            ccAccount = selectedCCAccount.getBankAccountNumber()        # noqa
            ccID = myPopupAskForInput(None, "CC_Account", "CC_Account", "Type/Paste the CC Number that the bank uses for connection (length 16) very carefully", ccAccount)
            myPrint("B", "existing CC number:      %s" %ccAccount)
            myPrint("B", "ccID entered:            %s" %ccID)
            if ccID is None:
                alert = "ERROR - no valid ccID supplied - aborting"
                myPopupInformationBox(None, alert, theMessageType=JOptionPane.ERROR_MESSAGE)
                raise Exception(alert)
            if ccID is None or ccID == "" or len(ccID) < 15 or len(ccID) > 16:
                myPrint("B", "\n ** ERROR - no valid ccID supplied! Please try again (Number should be 15 or 16 digits) ** \n")
                continue
            break

        if ccID == ccAccount:
            if not myPopupAskQuestion(None, "Keep CC Number", "Confirm you want use the same CC %s for connection?" % ccID, theMessageType=JOptionPane.WARNING_MESSAGE):
                alert = "ERROR - User aborted on keeping the CC the same"
                myPopupInformationBox(None, alert, theMessageType=JOptionPane.ERROR_MESSAGE)
                raise Exception(alert)
        else:
            if not myPopupAskQuestion(None, "Change CC number", "Confirm you want to set a new CC as %s for connection?" % ccID, theMessageType=JOptionPane.ERROR_MESSAGE):
                alert = "ERROR - User aborted on CC change"
                myPopupInformationBox(None, alert, theMessageType=JOptionPane.ERROR_MESSAGE)
                raise Exception(alert)

    del ccAccount, route, bankAccount

    ####################################################################################################################

    if lMultiAccountSetup:
        defaultEntry = uuid
        while True:
            uuid2 = myPopupAskForInput(None, "UUID 2", "UUID 2", "Paste your SECOND Bank Supplied UUID 36 digits 8-4-4-4-12 very carefully (or keep the same)", defaultEntry)
            myPrint("B", "UUID2 entered: %s" %uuid2)
            if uuid2 is None:
                alert = "ERROR - No uuid2 entered! Aborting"
                myPopupInformationBox(None, alert, theMessageType=JOptionPane.ERROR_MESSAGE)
                raise Exception(alert)
            defaultEntry = uuid2
            if (uuid2 is None or uuid2 == "" or len(uuid2) != 36 or uuid2 == "nnnnnnnn-nnnn-nnnn-nnnn-nnnnnnnnnnnn" or
                    (str(uuid2)[8]+str(uuid2)[13]+str(uuid2)[18]+str(uuid2)[23]) != "----"):
                myPrint("B", "\n ** ERROR - no valid uuid2 supplied - try again ** \n")
                continue
            break
        del defaultEntry

        defaultEntry = "UserID2"
        while True:
            userID2 = myPopupAskForInput(None, "UserID2", "UserID2", "Type/Paste your SECOND UserID (min length 8) very carefully", defaultEntry)
            myPrint("B", "userID2 entered: %s" %userID2)
            if userID2 is None:
                alert = "ERROR - no userID2 supplied! Aborting"
                myPopupInformationBox(None, alert, theMessageType=JOptionPane.ERROR_MESSAGE)
                raise Exception(alert)
            defaultEntry = userID2
            if userID2 is None or userID2 == "" or userID2 == "UserID2" or len(userID2)<8:
                myPrint("B", "\n ** ERROR - no valid userID2 supplied - try again ** \n")
                continue
            break
        del defaultEntry

    ####################################################################################################################

    myPrint("B", "Creating new Online Banking OFX Service Profile")
    manualFIInfo = StreamTable()     # type: StreamTable
    manualFIInfo.put("obj_type",                                 "olsvc")
    manualFIInfo.put("access_type",                              "OFX")
    manualFIInfo.put("tik_fi_id",                                NEW_TIK_FI_ID)
    manualFIInfo.put("app_id",                                   "QMOFX")
    manualFIInfo.put("app_ver",                                  "2300")
    manualFIInfo.put("bank_closing_avail",                       "0")
    manualFIInfo.put("bank_email_can_notify",                    "0")
    manualFIInfo.put("bank_email_enabled",                       "0")
    manualFIInfo.put("bootstrap_url",                            "https://df3cx-services.1fsapi.com/casm/usaa/access.ofx")
    manualFIInfo.put("cc_closing_avail",                         "1")
    manualFIInfo.put("date_avail_accts",                         "20210101120000")
    manualFIInfo.put("fi_addr1",                                 "10750 McDermott Freeway")
    manualFIInfo.put("fi_addr2",                                 "")
    manualFIInfo.put("fi_addr3",                                 "")
    manualFIInfo.put("fi_city",                                  "San Antonio")
    manualFIInfo.put("fi_country",                               "USA")
    manualFIInfo.put("fi_cust_svc_phone",                        "877-820-8320")
    manualFIInfo.put("fi_email",                                 "")
    manualFIInfo.put("fi_id",                                    USAA_FI_ID)
    manualFIInfo.put("fi_name",                                  USAA_PROFILE_NAME)
    manualFIInfo.put("fi_org",                                   USAA_FI_ORG)
    manualFIInfo.put("fi_state",                                 "TX")
    manualFIInfo.put("fi_tech_svc_phone",                        "877-820-8320")
    manualFIInfo.put("fi_url",                                   "www.usaa.com")
    manualFIInfo.put("fi_url_is_redirect",                       "1")
    manualFIInfo.put("fi_zip",                                   "78288")
    manualFIInfo.put("invst_dflt_broker_id",                     "")
    manualFIInfo.put("language_banking",                         "ENG")
    manualFIInfo.put("language_creditcard",                      "ENG")
    manualFIInfo.put("language_default",                         "ENG")
    manualFIInfo.put("language_fiprofile",                       "ENG")
    manualFIInfo.put("language_signup",                          "ENG")
    manualFIInfo.put("last_fi_refresh",                          "1613781515886")
    manualFIInfo.put("no_fi_refresh",                            "y")
    manualFIInfo.put("ofx_version",                              "103")
    manualFIInfo.put("ofxurl_banking",                           "https://df3cx-services.1fsapi.com/casm/usaa/access.ofx")
    manualFIInfo.put("ofxurl_creditcard",                        "https://df3cx-services.1fsapi.com/casm/usaa/access.ofx")
    manualFIInfo.put("ofxurl_default",                           "https://df3cx-services.1fsapi.com/casm/usaa/access.ofx")
    manualFIInfo.put("ofxurl_signup",                            "https://df3cx-services.1fsapi.com/casm/usaa/access.ofx")
    manualFIInfo.put("realm_banking",                            "USAASignon")
    manualFIInfo.put("realm_creditcard",                         "USAASignon")
    manualFIInfo.put("realm_default",                            "USAASignon")
    manualFIInfo.put("realm_fiprofile",                          "USAASignon")
    manualFIInfo.put("realm_signup",                             "USAASignon")
    manualFIInfo.put("rspnsfileerrors_banking",                  "1")
    manualFIInfo.put("rspnsfileerrors_creditcard",               "1")
    manualFIInfo.put("rspnsfileerrors_default",                  "1")
    manualFIInfo.put("rspnsfileerrors_fiprofile",                "1")
    manualFIInfo.put("rspnsfileerrors_signup",                   "1")
    manualFIInfo.put("securetransport_banking",                  "1")
    manualFIInfo.put("securetransport_creditcard",               "1")
    manualFIInfo.put("securetransport_default",                  "1")
    manualFIInfo.put("securetransport_fiprofile",                "1")
    manualFIInfo.put("securetransport_signup",                   "1")
    manualFIInfo.put("security_banking",                         "NONE")
    manualFIInfo.put("security_creditcard",                      "NONE")
    manualFIInfo.put("security_default",                         "NONE")
    manualFIInfo.put("security_fiprofile",                       "NONE")
    manualFIInfo.put("security_signup",                          "NONE")
    manualFIInfo.put("signup_accts_avail",                       "1")
    manualFIInfo.put("signup_can_activate_acct",                 "0")
    manualFIInfo.put("signup_can_chg_user_info",                 "0")
    manualFIInfo.put("signup_can_preauth",                       "0")
    manualFIInfo.put("signup_client_acct_num_req",               "1")
    manualFIInfo.put("signup_via_client",                        "0")
    manualFIInfo.put("signup_via_other",                         "1")
    manualFIInfo.put("signup_via_other_msg",                     "Please contact the financial institution for the enrollment process.")
    manualFIInfo.put("signup_via_web",                           "0")
    manualFIInfo.put("so_can_change_pin_USAASignon",             "1")
    manualFIInfo.put("so_client_uid_req_USAASignon",             "1")
    manualFIInfo.put("so_maxpasslen_USAASignon",                 "4")
    manualFIInfo.put("so_minpasslen_USAASignon",                 "4")
    manualFIInfo.put("so_must_chg_pin_first_USAASignon",         "0")
    manualFIInfo.put("so_passchartype_USAASignon",               "NUMERICONLY")
    manualFIInfo.put("so_passwd_case_sensitive_USAASignon",      "0")
    manualFIInfo.put("so_passwd_spaces_USAASignon",              "0")
    manualFIInfo.put("so_passwd_special_chars_USAASignon",       "0")
    manualFIInfo.put("so_passwd_type_USAASignon",                "FIXED")
    manualFIInfo.put("so_user_id_USAASignon",                    userID)
    if selectedBankAccount:
        manualFIInfo.put("so_user_id_USAASignon::%s" %(my_getAccountKey(selectedBankAccount)), userID)
    if selectedCCAccount:
        manualFIInfo.put("so_user_id_USAASignon::%s" %(my_getAccountKey(selectedCCAccount)),   userID)
    manualFIInfo.put("syncmode_banking",                         "LITE")
    manualFIInfo.put("syncmode_creditcard",                      "LITE")
    manualFIInfo.put("syncmode_default",                         "LITE")
    manualFIInfo.put("syncmode_fiprofile",                       "LITE")
    manualFIInfo.put("syncmode_signup",                          "LITE")
    manualFIInfo.put("user-agent",                               "InetClntApp/3.0")
    manualFIInfo.put("uses_fi_tag",                              "y")
    manualFIInfo.put("version_banking",                          "1")
    manualFIInfo.put("version_creditcard",                       "1")
    manualFIInfo.put("version_default",                          "1")
    manualFIInfo.put("version_fiprofile",                        "1")
    manualFIInfo.put("version_signup",                           "1")

    # manualFIInfo.put("always_send_date_range",                   "1")
    # manualFIInfo.put("id",                                       "4f085ab1-6f10-42d9-8048-4431b7919d61")
    # manualFIInfo.put("last_txn_id",                              "0-2f04b703_dd9df513-380")

    num = 0
    if selectedBankAccount:
        sNum = str(num)
        manualFIInfo.put("available_accts.%s.account_num" %(sNum),            str(bankID).zfill(10))
        manualFIInfo.put("available_accts.%s.account_type" %(sNum),           accountTypeOFX)
        manualFIInfo.put("available_accts.%s.branch_id" %(sNum),              "")
        manualFIInfo.put("available_accts.%s.desc" %(sNum),                   "USAA CLASSIC CHECKING")
        manualFIInfo.put("available_accts.%s.has_txn_dl" %(sNum),             "1")
        manualFIInfo.put("available_accts.%s.has_xfr_from" %(sNum),           "0")
        manualFIInfo.put("available_accts.%s.has_xfr_to" %(sNum),             "0")
        manualFIInfo.put("available_accts.%s.is_active" %(sNum),              "1")
        manualFIInfo.put("available_accts.%s.is_avail" %(sNum),               "0")
        manualFIInfo.put("available_accts.%s.is_bank_acct" %(sNum),           "1")
        manualFIInfo.put("available_accts.%s.is_pending" %(sNum),             "0")
        manualFIInfo.put("available_accts.%s.msg_type" %(sNum),               "4")
        manualFIInfo.put("available_accts.%s.phone" %(sNum),                  "")
        manualFIInfo.put("available_accts.%s.routing_num" %(sNum),            routID)
        num += 1

    if selectedCCAccount:
        sNum = str(num)
        manualFIInfo.put("available_accts.%s.account_num" %(sNum),            str(ccID))
        if len(ccID) == 15:
            manualFIInfo.put("available_accts.%s.desc" %(sNum),               "Signature AMEX")
        else:
            manualFIInfo.put("available_accts.%s.desc" %(sNum),               "Signature Visa")
        manualFIInfo.put("available_accts.%s.has_txn_dl" %(sNum),             "1")
        manualFIInfo.put("available_accts.%s.has_xfr_from" %(sNum),           "0")
        manualFIInfo.put("available_accts.%s.has_xfr_to" %(sNum),             "0")
        manualFIInfo.put("available_accts.%s.is_active" %(sNum),              "1")
        manualFIInfo.put("available_accts.%s.is_avail" %(sNum),               "0")
        manualFIInfo.put("available_accts.%s.is_cc_acct" %(sNum),             "1")
        manualFIInfo.put("available_accts.%s.is_pending" %(sNum),             "0")
        manualFIInfo.put("available_accts.%s.msg_type" %(sNum),               "5")
        manualFIInfo.put("available_accts.%s.phone" %(sNum),                  "")

    del sNum

    newService = OnlineService(book, manualFIInfo)
    newService.setParameter(PARAMETER_KEY, "python fix script")
    newService.syncItem()

    mappingObjectClass = None
    if isMDPlusEnabledBuild():
        myPrint("B", "Grabbing reference to OnlineAccountMapping() with new service profile...")
        mappingObjectClass =  OnlineAccountMapping(book, newService)

        if selectedBankAccount:
            myPrint("B", ".. setting bank account %s into map for: %s" %(bankID, selectedBankAccount))
            mappingObjectClass.setMapping(str(bankID).zfill(10), selectedBankAccount)

        if selectedCCAccount:
            myPrint("B", ".. setting cc account %s into map for: %s" %(ccID, selectedCCAccount))
            mappingObjectClass.setMapping(str(ccID), selectedCCAccount)

        mappingObjectClass.syncItem()

    del mappingObjectClass

    ####################################################################################################################

    service = newService

    if selectedBankAccount:
        myPrint("B", "Setting up account %s for OFX" %(selectedBankAccount))
        myPrint("B", ">> saving OFX bank account number: %s and OFX route: %s" %(bankID, routID))
        selectedBankAccount.setEditingMode()                            # noqa
        selectedBankAccount.setBankAccountNumber(bankID)                # noqa
        selectedBankAccount.setOFXBankID(routID)                        # noqa

        myPrint("B", ">> setting OFX Message type to '4'")
        selectedBankAccount.setOFXAccountMsgType(4)                     # noqa

        myPrint("B", ">> setting OFX Account Number to: %s" %(str(bankID).zfill(10)))
        selectedBankAccount.setOFXAccountNumber(str(bankID).zfill(10))  # noqa

        myPrint("B", ">> setting OFX Type to '%s'" %(accountTypeOFX))
        selectedBankAccount.setOFXAccountType(accountTypeOFX)           # noqa

        myPrint("B", ">> Setting up the Banking Acct %s link to new bank service / profile %s" %(selectedBankAccount, newService))
        selectedBankAccount.setBankingFI(newService)                    # noqa
        # MD2022 - can use setOnlineIDForServiceID() but for this, the old method should be OK...

        selectedBankAccount.syncItem()                                  # noqa
        selectedBankAccount.getDownloadedTxns()                         # noqa
        myPrint("B","")

    if selectedCCAccount:
        myPrint("B", "Setting up CC Account %s for OFX" %(selectedCCAccount))
        myPrint("B", ">> saving OFX CC account number %s" %(ccID))
        selectedCCAccount.setEditingMode()                              # noqa
        selectedCCAccount.setBankAccountNumber(str(ccID))               # noqa

        # myPrint("B", ">> setting OFX Type to 'CREDITCARD'")
        # selectedBankAccount.setOFXAccountType("CREDITCARD")           # noqa

        myPrint("B", ">> setting OFX Message type to '5'")
        selectedCCAccount.setOFXAccountMsgType(5)                       # noqa

        myPrint("B", ">> Settings up the CC Acct %s link to new profile %s" %(selectedCCAccount, newService))
        selectedCCAccount.setBankingFI(newService)                      # noqa
        # MD2022 - can use setOnlineIDForServiceID() but for this, the old method should be OK...

        selectedCCAccount.syncItem()                                    # noqa
        selectedCCAccount.getDownloadedTxns()                           # noqa
        print

    ####################################################################################################################

    myPrint("B", "Updating root with userID and uuid")
    root = MD_REF.getRootAccount()

    root.setEditingMode()

    if lOverrideRootUUID:
        myPrint("B","Overriding Root's default UUID. Was: %s >> changing to >> %s" %(root.getParameter(authKeyPrefix, ""),uuid))
        root.setParameter(authKeyPrefix, uuid)
        # root.setParameter(authKeyPrefix+"::" + service.getTIKServiceID() + "::" + "null",   uuid)         # noqa

    rootKeys = list(root.getParameterKeys())
    for i in range(0,len(rootKeys)):
        rk = rootKeys[i]
        if rk.startswith(authKeyPrefix) and (service.getTIKServiceID() in rk or OLD_TIK_FI_ID in rk or NEW_TIK_FI_ID in rk):
            myPrint("B", "Deleting old authKey %s: %s" %(rk,root.getParameter(rk)))
            root.setParameter(rk, None)
        i+=1

    root.setParameter(authKeyPrefix+"::" + service.getTIKServiceID() + "::" + userID,   uuid)                           # noqa
    root.setParameter(authKeyPrefix+"_default_user"+"::" + service.getTIKServiceID(), userID)                           # noqa
    myPrint("B", "Root UserID and uuid updated...")

    if lMultiAccountSetup:
        root.setParameter(authKeyPrefix+"::" + service.getTIKServiceID() + "::" + userID2,   uuid2)                     # noqa
        myPrint("B", "Root UserID TWO and uuid TWO primed - ready for Online Banking Setup...")

    root.syncItem()
    ####################################################################################################################

    myPrint("B", "accessing authentication keys")

    _ACCOUNT = 0
    _SERVICE = 1
    _ISBILLPAY = 2

    check = 0
    whichAccounts = []
    if selectedBankAccount:
        check += 1
        whichAccounts.append(selectedBankAccount)
    if selectedCCAccount:
        check += 1
        whichAccounts.append(selectedCCAccount)

    listAccountMDProxies=[]
    for acctObj in whichAccounts:
        acct = acctObj                                 # type: Account
        svcBank = acct.getBankingFI()                  # noqa
        svcBPay = acct.getBillPayFI()                  # noqa
        if svcBank is not None:
            myPrint("B", " - Found/Saved Banking Acct: %s" %acct)
            listAccountMDProxies.append([MDAccountProxy(acct, False),svcBank,False])
        if svcBPay is not None:
            myPrint("B", " - Found/Saved Bill Pay Acct: %s" %acct)
            listAccountMDProxies.append([MDAccountProxy(acct, True),svcBPay,True])

    if len(listAccountMDProxies) != check:
        alert = "LOGIC ERROR: listAccountMDProxies != %s - Some changes have been made - review log....." %check
        myPopupInformationBox(None, alert, theMessageType=JOptionPane.ERROR_MESSAGE)
        raise Exception(alert)

    myPrint("B", "\n>>REALMs configured:")
    realmsToCheck = service.getRealms()         # noqa
    if "DEFAULT" not in realmsToCheck:
        realmsToCheck.insert(0,"DEFAULT")       # noqa

    newAuthObj = "type=0&userid=%s&pass=%s&extra=" %(URLEncoder.encode(userID),URLEncoder.encode(password))

    for realm in realmsToCheck:

        myPrint("B", "Realm: %s current User ID: %s" %(realm, service.getUserId(realm, None)))

        authKey = "ofx:" + realm
        authObj = service.getCachedAuthentication(authKey)
        myPrint("B", "Realm: %s old Cached Authentication: %s" %(realm, authObj))
        myPrint("B", "   >> ** Setting new cached authentication from %s to: %s" %(authKey, newAuthObj))
        service.cacheAuthentication(authKey, newAuthObj)

        for olacct in listAccountMDProxies:

            authKey = "ofx:" + (realm + "::" + olacct[_ACCOUNT].getAccountKey())
            authObj = service.getCachedAuthentication(authKey)
            myPrint("B", "Realm: %s Account Key: %s old Cached Authentication: %s" %(realm, olacct[_ACCOUNT].getAccountKey(),authObj))
            myPrint("B", "   >>** Setting new cached authentication from %s to: %s" %(authKey, newAuthObj))
            service.cacheAuthentication(authKey, newAuthObj)

        myPrint("B", "Realm: %s now UserID: %s" %(realm, userID))
        myPrint("B", "-------------------------")

    ####################################################################################################################
    MD_REF.getCurrentAccount().getBook().getLocalStorage().save()  # Flush settings to disk before changes
    ####################################################################################################################

    myPrint("B","FINISHED UPDATES")
    myPrint("B","----------------")


    last_date_options = ["NO (FINISHED)", "YES - VIEW LAST TXN DOWNLOAD DATES"]
    theResult = JOptionPane.showOptionDialog(None,
                                             "SUCCESS! >> Now would you like to view your last txn download dates?",
                                             "LAST DOWNLOAD DATES",
                                             JOptionPane.YES_NO_OPTION,
                                             JOptionPane.QUESTION_MESSAGE,
                                             None,
                                             last_date_options,
                                             last_date_options[0])
    if theResult > 0:

        def MyGetDownloadedTxns(theAcct):       # Use my version to prevent creation of default record(s)

            myID = theAcct.getParameter("id", None)
            defaultTxnsListID = myID + ".oltxns"

            if myID is not None and myID != "":
                defaultTxnList = MD_REF.getCurrentAccount().getBook().getItemForID(defaultTxnsListID)   # type: SyncableItem
                if defaultTxnList is not None and isinstance(defaultTxnList, OnlineTxnList):
                    return defaultTxnList

            txnsListID = theAcct.getParameter("ol_txns_list_id", None)
            if txnsListID is None or txnsListID == "":
                if myID is not None and myID != "":
                    txnsListID = defaultTxnsListID

            if txnsListID is not None and txnsListID != "":
                txnsObj = MD_REF.getCurrentAccount().getBook().getItemForID(txnsListID)              # type: SyncableItem
                if (txnsObj is not None and isinstance(txnsObj, OnlineTxnList)):
                    return txnsObj

            return None

        accountsDL = AccountUtil.allMatchesForSearch(MD_REF.getCurrentAccount().getBook(), MyAcctFilter(3))
        accountsDL = sorted(accountsDL, key=lambda sort_x: (sort_x.getAccountType(), sort_x.getFullAccountName().upper()))

        outputDates = "\nBANK OFX: LAST DOWNLOADED TRANSACTION DATE(s)\n"\
                 "--------------------------------------------\n\n"\
                 "** Please check for recent dates. If your account is set to zero - you will likely get up to six months+ of data, maybe even more, or possibly problems (from too many transactions)!\n\n"

        for acct in accountsDL:
            theOnlineTxnRecord = MyGetDownloadedTxns(acct)     # Use my version to prevent creation of default record(s)
            if theOnlineTxnRecord is None:
                prettyLastTxnDate = "Never downloaded = 'Download all available dates'"
            else:
                theCurrentDate = theOnlineTxnRecord.getOFXLastTxnUpdate()
                if theCurrentDate > 0:
                    prettyLastTxnDate = get_time_stamp_as_nice_text(theCurrentDate)
                else:
                    prettyLastTxnDate = "IS SET TO ZERO = 'Download all available dates' (if on MD2022 onwards, MD will prompt you for a start date)"

            outputDates += "%s %s %s\n" %(pad(repr(acct.getAccountType()),12), pad(acct.getFullAccountName(),40), prettyLastTxnDate)

        outputDates += "\nIf you have Moneydance Version 2021.1(build 2012+) then you can use the Toolbox extension if you want to change any of these dates....\n" \
                       "... (Toolbox: Advanced Mode>Online Banking (OFX) Tools Menu>Update the Last Txn Update Date(Downloaded) field)\n" \
                       "\nIf you have a version older than 2021.1(build 2012) you will either have to accept/deal with the volume of downloaded Txns; or upgrade to use Toolbox...\n" \
                       "%s\n\n" \
                       "RESTART MONEYDANCE, THEN EDIT THE LAST TXN DOWNLOAD DATES BEFORE YOU DOWNLOAD ANYTHING\n" \
                       "\n\n** PLEASE CLOSE THIS WINDOW AND RESTART MONEYDANCE **\n\n" \
                       %(MYPYTHON_DOWNLOAD_URL)

        outputDates += "\n<END>"
        jif = QuickJFrame("LAST DOWNLOAD DATES", outputDates, lWrapText=False, copyToClipboard=True).show_the_frame()
        myPopupInformationBox(jif, "REVIEW OUTPUT. Use Toolbox first if you need to change any last download txn dates.....", theMessageType=JOptionPane.INFORMATION_MESSAGE)

    myPopupInformationBox(None, "SUCCESS. REVIEW OUTPUT - Then RESTART Moneydance.", theMessageType=JOptionPane.ERROR_MESSAGE)

    myPrint("B", "SUCCESS. Please RESTART Moneydance.")

    cleanup_actions()

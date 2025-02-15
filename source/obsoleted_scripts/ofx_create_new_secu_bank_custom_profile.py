#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# ofx_create_new_secu_bank_custom_profile.py (build 5) - Author - Stuart Beesley - StuWareSoftSystems 2021

# READ THIS FIRST:
# https://github.com/yogi1967/MoneydancePythonScripts/raw/master/source/useful_scripts/ofx_create_new_secu_bank_custom_profile.pdf

# This script builds a new NCSECU Bank Custom Profile from scratch to work with the new connection information
# It will DELETE your existing NCSECU profile(s) first!
# It will populate your UserID, Password, and allow you to change/update the Bank and Credit Card Number
# This will create a non MD profile to avoid any refresh issues....
# Based on the original 'magic' contained within ofx_create_new_usaa_bank_custom_profile.py

# DISCLAIMER >> PLEASE ALWAYS BACKUP YOUR DATA BEFORE MAKING CHANGES (Menu>Export Backup will achieve this)
#               You use this at your own risk. I take no responsibility for its usage..!
#               This should be considered a temporary fix only until Moneydance is fixed

# CREDITS:  hleofxquotes for his technical input and dtd for his extensive testing

###############################################################################
# MIT License
#
# Copyright (c) 2020 Stuart Beesley - StuWareSoftSystems
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

# build 1 - Initial preview release.....
# build 1 - Released: 13th March 2021 (thanks to @margopowell for volunteering her data to set this script up)
# build 2 - Internal tweaks - nothing to do with the core functionality
# build 3 - Cosmetic tweaks - nothing to do with the core functionality
# build 4 - Internal common code tweaks - nothing to do with the core functionality
# build 4 - URLEncoder.encode() the UserID and Password in the stored cached string
# build 5 - Build 3051 of Moneydance... fix references to moneydance_* variables;

# CUSTOMIZE AND COPY THIS ##############################################################################################
# CUSTOMIZE AND COPY THIS ##############################################################################################
# CUSTOMIZE AND COPY THIS ##############################################################################################

# SET THESE LINES
myModuleID = u"ofx_create_new_secu_bank_custom_profile"
version_build = "5"
if u"debug" in globals():
    global debug
else:
    debug = False
global ofx_create_new_secu_bank_custom_profile_frame_

# COPY >> START
global moneydance, moneydance_extension_loader
MD_REF = moneydance     # Make my own copy of reference as MD removes it once main thread ends.. Don't use/hold on to _ui / _data variables
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

    def run(self):                                                                                                      # noqa
        self.theFrame.setVisible(False)
        self.theFrame.dispatchEvent(WindowEvent(self.theFrame, WindowEvent.WINDOW_CLOSING))

class GenericDisposeRunnable(Runnable):
    def __init__(self, theFrame):
        self.theFrame = theFrame

    def run(self):                                                                                                      # noqa
        self.theFrame.dispose()

class GenericVisibleRunnable(Runnable):
    def __init__(self, theFrame, lVisible=True, lToFront=False):
        self.theFrame = theFrame
        self.lVisible = lVisible
        self.lToFront = lToFront

    def run(self):                                                                                                      # noqa
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
                print("%s: Found live frame: %s (MyJFrame() version: %s)" %(myModuleID,fr.getName(),fr.myJFrameVersion))
                System.err.write("%s: Found live frame: %s (MyJFrame() version: %s)\n" %(myModuleID, fr.getName(),fr.myJFrameVersion))
                if fr.isRunTimeExtension: print("%s: This extension is a run-time self-installed extension too..." %(myModuleID))
                if fr.isRunTimeExtension: System.err.write("%s: This extension is a run-time self-installed extension too...\n" %(myModuleID))
                return fr
    except:
        System.err.write("%s: Critical error in getMyJFrame(); caught and ignoring...!\n" %(myModuleID))
    return None


frameToResurrect = None
try:
    if (u"%s_frame_"%myModuleID in globals()
            and isinstance(ofx_create_new_secu_bank_custom_profile_frame_, MyJFrame)        # EDIT THIS
            and ofx_create_new_secu_bank_custom_profile_frame_.isActiveInMoneydance):       # EDIT THIS
        frameToResurrect = ofx_create_new_secu_bank_custom_profile_frame_                   # EDIT THIS
    else:
        getFr = getMyJFrame( myModuleID )
        if getFr is not None:
            frameToResurrect = getFr
        del getFr
except:
    System.err.write("%s: Critical error checking frameToResurrect(1); caught and ignoring...!\n" %(myModuleID))

lTerminatedExtension = False

try:
    if frameToResurrect:  # and it's still alive.....
        if frameToResurrect.isRunTimeExtension:     # this must be an install/reinstall. I need to deactivate and re-register extension...
            print("%s: Detected that runtime extension %s is already running..... Assuming a re-installation... Taking appropriate action..." %(myModuleID, myModuleID))
            System.err.write("%s: Detected that runtime extension %s is already running..... Assuming a re-installation... Taking appropriate action...\n" %(myModuleID, myModuleID))
            frameToResurrect.isActiveInMoneydance = False
            try:
                SwingUtilities.invokeLater(GenericWindowClosingRunnable(frameToResurrect))
                System.err.write("%s: Pushed a windowClosing event - via SwingUtilities.invokeLater() - to existing extension... Hopefully it will close to allow re-installation...\n" %(myModuleID))
            except:
                System.err.write("%s: ERROR pushing a windowClosing event to existing extension!\n" %(myModuleID))

            lTerminatedExtension = True
            frameToResurrect = None
        else:
            print("%s: Detected that %s is already running..... Attempting to resurrect.." %(myModuleID, myModuleID))
            System.err.write("%s: Detected that %s is already running..... Attempting to resurrect..\n" %(myModuleID, myModuleID))
except:
    System.err.write("%s: Critical error checking frameToResurrect(2); caught and ignoring...!\n" %(myModuleID))

if float(MD_REF.getBuild()) < 1904:     # Check for builds less than 1904 / version < 2019.4
    try:
        MD_REF.getUI().showInfoMessage("SORRY YOUR VERSION IS TOO OLD FOR THIS SCRIPT/EXTENSION")
    except:
        raise Exception("SORRY YOUR MONEYDANCE VERSION IS TOO OLD FOR THIS SCRIPT/EXTENSION")

elif frameToResurrect:
    try:
        SwingUtilities.invokeLater(GenericVisibleRunnable(frameToResurrect, True, True))
    except:
        print("%s: Failed to resurrect main Frame - via SwingUtilities.invokeLater() - This duplicate Script/extension is now terminating....." %(myModuleID))
        System.err.write("%s: Failed to resurrect main Frame.. This duplicate Script/extension is now terminating.....\n" %(myModuleID))
        raise Exception("SORRY - YOU CAN ONLY HAVE ONE INSTANCE OF %s RUNNING AT ONCE" %(myModuleID.upper()))

else:
    del frameToResurrect

    if not lTerminatedExtension:
        print("%s: No other 'live' instances of this program detected (or I terminated it) - running as normal" %(myModuleID))
        System.err.write("%s: No other instances of this program detected (or I terminated it) - running as normal\n" %(myModuleID))
    else:
        print("%s: I terminated extension in memory, running script to allow new installation..." %(myModuleID))
        System.err.write("%s: I terminated extension in memory, running script to allow new installation...\n" %(myModuleID))

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

    from java.awt.datatransfer import StringSelection
    from javax.swing.text import DefaultHighlighter

    from java.awt import Color, Dimension, FileDialog, FlowLayout, Toolkit, Font, GridBagLayout, GridLayout
    from java.awt import BorderLayout, Dialog, Insets
    from java.awt.event import KeyEvent, WindowAdapter, InputEvent
    from java.util import Date

    from java.text import DecimalFormat, SimpleDateFormat
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
    # END SET THESE VARIABLES FOR ALL SCRIPTS ##############################################################################

    # >>> THIS SCRIPT'S IMPORTS ############################################################################################
    from com.infinitekind.moneydance.model import OnlineService
    from com.moneydance.apps.md.view.gui import MDAccountProxy
    from com.infinitekind.tiksync import SyncRecord
    from com.infinitekind.util import StreamTable
    from java.util import UUID
    from com.infinitekind.util import StringUtils
    from java.net import URLEncoder

    # >>> THIS SCRIPT'S GLOBALS ############################################################################################
    # >>> END THIS SCRIPT'S GLOBALS ############################################################################################

    # COPY >> START
    # COMMON CODE ##########################################################################################################
    # COMMON CODE ##########################################################################################################
    # COMMON CODE ##########################################################################################################
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
        global MD_REF, MD_EXTENSION_LOADER
        myPrint("DB","About to delete reference to MD_REF and MD_EXTENSION_LOADER....!")
        del MD_REF, MD_EXTENSION_LOADER

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
                    line += "\n"
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

    def dump_sys_error_to_md_console_and_errorlog( lReturnText=False ):

        theText = ""
        myPrint("B","Unexpected error caught: %s" %(sys.exc_info()[0]))
        myPrint("B","Unexpected error caught: %s" %(sys.exc_info()[1]))
        myPrint("B","Error on Script Line Number: %s" %(sys.exc_info()[2].tb_lineno))

        if lReturnText:
            theText += "\n@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\n"
            theText += "Unexpected error caught: %s\n" %(sys.exc_info()[0])
            theText += "Unexpected error caught: %s\n" %(sys.exc_info()[1])
            theText += "Error on Script Line Number: %s\n" %(sys.exc_info()[2].tb_lineno)
            theText += "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\n"
            return theText

        return

    def pad(theText, theLength):
        theText = theText[:theLength].ljust(theLength, u" ")
        return theText

    def rpad(theText, theLength):
        if not (isinstance(theText, unicode) or isinstance(theText, str)):
            theText = str(theText)

        theText = theText[:theLength].rjust(theLength, u" ")
        return theText

    def cpad(theText, theLength):
        if not (isinstance(theText, unicode) or isinstance(theText, str)):
            theText = str(theText)

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

    def getTheSetting(what):
        x = MD_REF.getPreferences().getSetting(what, None)
        if not x or x == u"": return None
        return what + u": %s" %(x)

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

    def myPopupAskBackup(theParent=None, theMessage="What no message?!"):

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
            MD_REF.getUI().saveToBackup(None)
            return True

        elif response == 1:
            myPrint("B", "User DECLINED to perform Export Backup before update/fix...!")
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

        x = 0
        if theFieldLabel:
            p.add(JLabel(theFieldLabel), GridC.getc(x, 0).east())
            x+=1

        p.add(field, GridC.getc(x, 0).field())
        p.add(Box.createHorizontalStrut(244), GridC.getc(x, 0))
        if theFieldDescription:
            p.add(JTextPanel(theFieldDescription), GridC.getc(x, 1).field().colspan(x + 1))
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
            # noinspection PyMethodMayBeStatic

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
            # noinspection PyMethodMayBeStatic

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
        ext = ""

        def __init__(self, ext):
            self.ext = "." + ext.upper()

        def accept(self, thedir, filename):                                                                             # noqa
            if filename is not None and filename.upper().endswith(self.ext):
                return True
            return False

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

        return

    if MD_REF.getUI() is not None:
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
                istr = FileInputStream(migratedFilename)
                load_file = FileUtil.wrap(istr)
                # noinspection PyTypeChecker
                myParameters = pickle.load(load_file)
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
            # noinspection PyTypeChecker
            pickle.dump(myParameters, save_file)
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

    class QuickJFrame():

        def __init__(self, title, output, lAlertLevel=0, copyToClipboard=False):
            self.title = title
            self.output = output
            self.lAlertLevel = lAlertLevel
            self.returnFrame = None
            self.copyToClipboard = copyToClipboard

        class CloseAction(AbstractAction):

            def __init__(self, theFrame):
                self.theFrame = theFrame

            def actionPerformed(self, event):
                global debug
                myPrint("D","in CloseAction(), Event: ", event)
                myPrint("DB", "QuickJFrame() Frame shutting down....")

                # Already within the EDT
                self.theFrame.dispose()
                return

        def show_the_frame(self):
            global debug

            class MyQuickJFrameRunnable(Runnable):

                def __init__(self, callingClass):
                    self.callingClass = callingClass

                def run(self):                                                                                                      # noqa
                    screenSize = Toolkit.getDefaultToolkit().getScreenSize()

                    frame_width = min(screenSize.width-20, max(1024,int(round(MD_REF.getUI().firstMainFrame.getSize().width *.9,0))))
                    frame_height = min(screenSize.height-20, max(768, int(round(MD_REF.getUI().firstMainFrame.getSize().height *.9,0))))

                    JFrame.setDefaultLookAndFeelDecorated(True)

                    jInternalFrame = MyJFrame(self.callingClass.title + " (%s+F to find/search for text)" %(MD_REF.getUI().ACCELERATOR_MASK_STR))
                    jInternalFrame.setName(u"%s_quickjframe" %myModuleID)

                    if not Platform.isOSX():
                        jInternalFrame.setIconImage(MDImages.getImage(MD_REF.getUI().getMain().getSourceInformation().getIconResource()))

                    jInternalFrame.setDefaultCloseOperation(WindowConstants.DISPOSE_ON_CLOSE)
                    jInternalFrame.setResizable(True)

                    shortcut = Toolkit.getDefaultToolkit().getMenuShortcutKeyMaskEx()
                    jInternalFrame.getRootPane().getInputMap(JComponent.WHEN_ANCESTOR_OF_FOCUSED_COMPONENT).put(KeyStroke.getKeyStroke(KeyEvent.VK_W,  shortcut), "close-window")
                    jInternalFrame.getRootPane().getInputMap(JComponent.WHEN_ANCESTOR_OF_FOCUSED_COMPONENT).put(KeyStroke.getKeyStroke(KeyEvent.VK_F4, shortcut), "close-window")
                    jInternalFrame.getRootPane().getInputMap(JComponent.WHEN_ANCESTOR_OF_FOCUSED_COMPONENT).put(KeyStroke.getKeyStroke(KeyEvent.VK_F,  shortcut), "search-window")
                    jInternalFrame.getRootPane().getInputMap(JComponent.WHEN_IN_FOCUSED_WINDOW).put(KeyStroke.getKeyStroke(KeyEvent.VK_ESCAPE, 0), "close-window")

                    theJText = JTextArea(self.callingClass.output)
                    theJText.setEditable(False)
                    theJText.setLineWrap(True)
                    theJText.setWrapStyleWord(True)
                    theJText.setFont( getMonoFont() )

                    jInternalFrame.getRootPane().getActionMap().put("close-window", self.callingClass.CloseAction(jInternalFrame))
                    jInternalFrame.getRootPane().getActionMap().put("search-window", SearchAction(jInternalFrame,theJText))

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

                    jInternalFrame.add(internalScrollPane)

                    jInternalFrame.pack()
                    jInternalFrame.setLocationRelativeTo(None)
                    jInternalFrame.setVisible(True)

                    if "errlog.txt" in self.callingClass.title:
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
                    aboutPanel.setPreferredSize(Dimension(1120, 500))

                    _label1 = JLabel(pad("Author: Stuart Beesley", 800))
                    _label1.setForeground(Color.BLUE)
                    aboutPanel.add(_label1)

                    _label2 = JLabel(pad("StuWareSoftSystems (2020-2021)", 800))
                    _label2.setForeground(Color.BLUE)
                    aboutPanel.add(_label2)

                    displayString=scriptExit
                    displayJText = JTextArea(displayString)
                    displayJText.setFont( getMonoFont() )
                    displayJText.setEditable(False)
                    displayJText.setLineWrap(False)
                    displayJText.setWrapStyleWord(False)
                    displayJText.setMargin(Insets(8, 8, 8, 8))
                    # displayJText.setBackground((mdGUI.getColors()).defaultBackground)
                    # displayJText.setForeground((mdGUI.getColors()).defaultTextForeground)

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

    def cleanup_actions(theFrame=None):
        myPrint("DB", "In", inspect.currentframe().f_code.co_name, "()")
        myPrint("DB", "SwingUtilities.isEventDispatchThread() = %s" %(SwingUtilities.isEventDispatchThread()))

        if theFrame is not None and not theFrame.isActiveInMoneydance:
            destroyOldFrames(myModuleID)

        try:
            MD_REF.getUI().firstMainFrame.setStatus(">> StuWareSoftSystems - thanks for using >> %s......." %(myScriptName),0)
        except:
            pass  # If this fails, then MD is probably shutting down.......

        if not i_am_an_extension_so_run_headless: print(scriptExit)

        cleanup_references()

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

    # get_StuWareSoftSystems_parameters_from_file()

    # clear up any old left-overs....
    destroyOldFrames(myModuleID)

    myPrint("DB", "DEBUG IS ON..")

    if SwingUtilities.isEventDispatchThread():
        myPrint("DB", "FYI - This script/extension is currently running within the Swing Event Dispatch Thread (EDT)")
    else:
        myPrint("DB", "FYI - This script/extension is NOT currently running within the Swing Event Dispatch Thread (EDT)")

    # END ALL CODE COPY HERE ###############################################################################################
    # END ALL CODE COPY HERE ###############################################################################################
    # END ALL CODE COPY HERE ###############################################################################################

    MD_REF.getUI().firstMainFrame.setStatus(">> StuWareSoftSystems - %s launching......." %(myScriptName),0)

    def createNewClientUID():
        uid = UUID.randomUUID().toString()
        uid = StringUtils.replaceAll(uid, "-", "").trim()
        if (uid.length() > 32):
            uid = uid.substring(0, 32)
        return uid

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

    if not myPopupAskQuestion(None, "BACKUP", "CREATE A NEW (CUSTOM) NCSECU PROFILE >> HAVE YOU DONE A GOOD BACKUP FIRST?", theMessageType=JOptionPane.WARNING_MESSAGE):
        alert = "BACKUP FIRST! PLEASE USE FILE>EXPORT BACKUP then come back!! - No changes made."
        myPopupInformationBox(None, alert, theMessageType=JOptionPane.ERROR_MESSAGE)
        raise Exception(alert)

    if not myPopupAskQuestion(None, "DISCLAIMER", "DO YOU ACCEPT YOU RUN THIS AT YOUR OWN RISK?", theMessageType=JOptionPane.WARNING_MESSAGE):
        alert = "Disclaimer rejected - no changes made"
        myPopupInformationBox(None, alert, theMessageType=JOptionPane.ERROR_MESSAGE)
        raise Exception(alert)

    ask = MyPopUpDialogBox(None, "This script will delete your existing NCSECU bank profile(s) and CREATE A BRAND NEW CUSTOM NCSECU PROFILE:",
                           "Get the latest useful_scripts.zip package from: https://yogi1967.github.io/MoneydancePythonScripts/ \n"
                           "Read the latest walk through guide: ofx_create_new_secu_bank_custom_profile.pdf\n"
                           "Latest: https://github.com/yogi1967/MoneydancePythonScripts/raw/master/source/useful_scripts/ofx_create_new_secu_bank_custom_profile.pdf\n\n"
                           "This script configure one bank account & up to one credit card [optional]. You can add more later using standard Moneydance online menu\n"
                           "This script will ask you for many numbers. You must know them:\n"
                           "- Do you know your Bank supplied UserID (min length 7)?\n"
                           "- Do you know your Pin/Password (min length 4)?\n"
                           "- Do you know your Bank Account Number and routing Number (9-digits - usually '253177049')?\n"
                           "- Do you know your Credit Card number that the bank will accept? (This may not apply, just try your current one first)\n"
                           "- Do you know which Accounts in Moneydance to select and link to this new profile?\n"
                           "IF NOT, STOP AND GATHER ALL INFORMATION",
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

    # options = ["NO (Skip this)","YES - PRIME SECOND ACCOUNT"]
    # theResult = JOptionPane.showOptionDialog(None,
    #                                       "Do you have multiple DIFFERENT credentials where you wish to 'prime' the default UUID into (Root's) profile?",
    #                                       "MULTI-ACCOUNTS",
    #                                        JOptionPane.YES_NO_OPTION,
    #                                        JOptionPane.QUESTION_MESSAGE,
    #                                        None,
    #                                        options,
    #                                        options[0])
    # if theResult > 0:
    #     lMultiAccountSetup = True
    #     myPrint("B","Will setup multi-accounts too.... ")
    #
    #     # options = ["NO (Skip this)","YES - SET GLOBAL DEFAULT ROOT UUID"]
    #     # theResult = JOptionPane.showOptionDialog(None,
    #     #                                          "Do you also wish to override Root's (global) default UUID with the one you specify?",
    #     #                                          "OVERRIDE ROOT DEFAULT UUID",
    #     #                                          JOptionPane.YES_NO_OPTION,
    #     #                                          JOptionPane.QUESTION_MESSAGE,
    #     #                                          None,
    #     #                                          options,
    #     #                                          options[0])
    #     # if theResult > 0:
    #     #     lOverrideRootUUID = True
    #     #     myPrint("B","Will also override Root UUID too.... ")
    #     # else:
    #     #     myPrint("B","User declined NOT to prime the global Root Default UUID...")
    # else:
    #     myPrint("B","User selected NOT to prime for multiple-accounts...")
    #

    serviceList = MD_REF.getCurrentAccount().getBook().getOnlineInfo().getAllServices()  # type: [OnlineService]

    SECU_FI_ID = "1001"
    SECU_FI_ORG = "SECU"
    SECU_PROFILE_NAME = "NCSECU Custom Profile (ofx_create_new_secu_bank_profile_custom.py)"
    OLD_TIK_FI_ID = "md:1262"
    SECU_BOOTSTRAP = "https://onlineaccess.ncsecu.org/secuofx/secu.ofx"
    SECU_ACCT_LENGTH = 7

    authKeyPrefix = "ofx.client_uid"

    SECU_ACCOUNT_TYPES = ["CHECKING", "SAVINGS", "MONEYMRKT"]

    ####################################################################################################################
    deleteServices = []
    for svc in serviceList:
        if (svc.getTIKServiceID() == OLD_TIK_FI_ID
                or svc.getServiceId() == ":%s:%s" %(SECU_FI_ORG, SECU_FI_ID)
                or "SECU" in svc.getFIOrg()
                or "SECU" in svc.getFIName()):
            myPrint("B", "Found NCSECU service - to delete: %s" %(svc))
            deleteServices.append(svc)

    root = MD_REF.getRootAccount()
    rootKeys = list(root.getParameterKeys())
    lRootNeedsSync = False

    if len(deleteServices) < 1:
        myPrint("B", "No NCSECU services / profile found to delete...")
    else:
        if not myPopupAskQuestion(None, "DELETE OLD SERVICES", "OK TO DELETE %s OLD NCSECU SERVICES (I WILL DO THIS FIRST)?" % (len(deleteServices)), theMessageType=JOptionPane.ERROR_MESSAGE):
            alert = "ERROR - User declined to delete %s old NCSECU service profiles - no changes made" %(len(deleteServices))
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
                        a.setBillPayFI(None)
                        a.syncItem()

                myPrint("B", "Clearing authentication cache from %s" %s)
                s.clearAuthenticationCache()

                # # Clean up root here - as with custom profiles the UUID sets stored instead of the TIK ID which can be identified later....
                # if s.getTIKServiceID() != OLD_TIK_FI_ID:  # Thus we presume it's our own custom profile
                #     for i in range(0,len(rootKeys)):
                #         rk = rootKeys[i]
                #         if rk.startswith(authKeyPrefix) and (s.getTIKServiceID() in rk):
                #             myPrint("B", "Deleting old authKey associated with this profile (from Root) %s: %s" %(rk,root.getParameter(rk)))
                #
                #             if not lRootNeedsSync:
                #                 myPrint("B",".. triggering .setEditingMode() on root...")
                #                 root.setEditingMode()
                #
                #             root.setParameter(rk, None)
                #             lRootNeedsSync = True
                #         i+=1
                #
                myPrint("B", "Deleting profile %s" %s)
                s.deleteItem()
                myPopupInformationBox(None,"I have deleted Bank logon profile / service: %s and forgotten associated credentials (%s accounts were de-linked)" %(s,iCount))
            del accounts

    if lRootNeedsSync:
        root.syncItem()

    del serviceList, deleteServices, lRootNeedsSync, rootKeys


    ####################################################################################################################
    invalidBankingLinks = []
    invalidBillPayLinks = []
    myPrint("B","Searching for Account banking / Bill Pay links with no profile (just a general cleanup routine)....")
    accounts = AccountUtil.allMatchesForSearch(MD_REF.getCurrentAccount().getBook(), MyAcctFilter(2))
    for a in accounts:
        if a.getBankingFI() is None and a.getParameter("olbfi", "") != "":
            invalidBankingLinks.append(a)
            myPrint("B","... Found account %s with a banking link (to %s), but no service profile exists (thus dead)..." %(a,a.getParameter("olbfi", "")))

        if a.getBillPayFI() is None and a.getParameter("bpfi", "") != "":
            invalidBillPayLinks.append(a)
            myPrint("B","... Found account %s with a BillPay link (to %s), but no service profile exists (thus dead)..." %(a,a.getParameter("bpfi", "")))

    if len(invalidBankingLinks) or len(invalidBillPayLinks):
        if myPopupAskQuestion(None,
                              "ACCOUNT TO DEAD SERVICE PROFILE LINKS",
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

    # BANK ACCOUNT
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

    # dummy = "12345678-1111-1111-1111-123456789012"
    #
    # defaultEntry = "nnnnnnnn-nnnn-nnnn-nnnn-nnnnnnnnnnnn"
    # while True:
    #     uuid = myPopupAskForInput(None, "UUID", "UUID", "Paste the Bank Supplied UUID 36 digits 8-4-4-4-12 very carefully", defaultEntry)
    #     myPrint("B", "UUID entered: %s" %uuid)
    #     if uuid is None:
    #         alert = "ERROR - No uuid entered! Aborting"
    #         myPopupInformationBox(None, alert, theMessageType=JOptionPane.ERROR_MESSAGE)
    #         raise Exception(alert)
    #     defaultEntry = uuid
    #     if (uuid is None or uuid == "" or len(uuid) != 36 or uuid == "nnnnnnnn-nnnn-nnnn-nnnn-nnnnnnnnnnnn" or
    #             (str(uuid)[8]+str(uuid)[13]+str(uuid)[18]+str(uuid)[23]) != "----"):
    #         myPrint("B", "\n ** ERROR - no valid uuid supplied - try again ** \n")
    #         continue
    #     break
    # del defaultEntry
    #

    defaultEntry = "UserID"
    while True:
        userID = myPopupAskForInput(None, "UserID", "UserID", "Type/Paste your UserID (min length 7) very carefully", defaultEntry)
        myPrint("B", "userID entered: %s" %userID)
        if userID is None:
            alert = "ERROR - no userID supplied! Aborting"
            myPopupInformationBox(None, alert, theMessageType=JOptionPane.ERROR_MESSAGE)
            raise Exception(alert)
        defaultEntry = userID
        if userID is None or userID == "" or userID == "UserID" or len(userID)<7:
            myPrint("B", "\n ** ERROR - no valid userID supplied - try again ** \n")
            continue
        break
    del defaultEntry

    defaultEntry = "***"
    while True:
        password = myPopupAskForInput(None, "Pin/Password", "Pin/Password", "Type/Paste your Pin/Password (min length 4) very carefully", defaultEntry)
        myPrint("B", "Pin/Password entered: %s" %password)
        if password is None:
            alert = "ERROR - no Pin/Password supplied! Aborting"
            myPopupInformationBox(None, alert, theMessageType=JOptionPane.ERROR_MESSAGE)
            raise Exception(alert)
        defaultEntry = password
        if password is None or password == "" or password == "***" or len(password) < 4:
            myPrint("B", "\n ** ERROR - no Pin/Password supplied - try again ** \n")
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
            route = "253177049"
        routID = myPopupAskForInput(None, "Routing", "Routing", "Type/Paste your Routing Number (9 digits - usually '253177049')- very carefully", route)
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
            ccID = myPopupAskForInput(None, "CC_Account", "CC_Account", "Type/Paste the CC Number that the bank uses for connection (length 15/16) very carefully", ccAccount)
            myPrint("B", "existing CC number:      %s" %ccAccount)
            myPrint("B", "ccID entered:            %s" %ccID)
            if ccID is None:
                alert = "ERROR - no valid ccID supplied - aborting"
                myPopupInformationBox(None, alert, theMessageType=JOptionPane.ERROR_MESSAGE)
                raise Exception(alert)
            if ccID is None or ccID == "" or len(ccID) < 15 or len(ccID) > 16:
                myPrint("B", "\n ** ERROR - no valid ccID supplied! Please try again ** \n")
                continue
            break

        # if ccID == ccAccount:
        #     if not myPopupAskQuestion(None, "Keep CC Number", "Confirm you want use the same CC %s for connection?" % ccID, theMessageType=JOptionPane.WARNING_MESSAGE):
        #         alert = "ERROR - User aborted on keeping the CC the same"
        #         myPopupInformationBox(None, alert, theMessageType=JOptionPane.ERROR_MESSAGE)
        #         raise Exception(alert)
        # else:
        #     if not myPopupAskQuestion(None, "Change CC number", "Confirm you want to set a new CC as %s for connection?" % ccID, theMessageType=JOptionPane.ERROR_MESSAGE):
        #         alert = "ERROR - User aborted on CC change"
        #         myPopupInformationBox(None, alert, theMessageType=JOptionPane.ERROR_MESSAGE)
        #         raise Exception(alert)

    del ccAccount, route, bankAccount

    ####################################################################################################################

    # if lMultiAccountSetup:
    #     defaultEntry = uuid
    #     while True:
    #         uuid2 = myPopupAskForInput(None, "UUID 2", "UUID 2", "Paste your SECOND Bank Supplied UUID 36 digits 8-4-4-4-12 very carefully (or keep the same)", defaultEntry)
    #         myPrint("B", "UUID2 entered: %s" %uuid2)
    #         if uuid2 is None:
    #             alert = "ERROR - No uuid2 entered! Aborting"
    #             myPopupInformationBox(None, alert, theMessageType=JOptionPane.ERROR_MESSAGE)
    #             raise Exception(alert)
    #         defaultEntry = uuid2
    #         if (uuid2 is None or uuid2 == "" or len(uuid2) != 36 or uuid2 == "nnnnnnnn-nnnn-nnnn-nnnn-nnnnnnnnnnnn" or
    #                 (str(uuid2)[8]+str(uuid2)[13]+str(uuid2)[18]+str(uuid2)[23]) != "----"):
    #             myPrint("B", "\n ** ERROR - no valid uuid2 supplied - try again ** \n")
    #             continue
    #         break
    #     del defaultEntry
    #
    #     defaultEntry = "UserID2"
    #     while True:
    #         userID2 = myPopupAskForInput(None, "UserID2", "UserID2", "Type/Paste your SECOND UserID (min length 8) very carefully", defaultEntry)
    #         myPrint("B", "userID2 entered: %s" %userID2)
    #         if userID2 is None:
    #             alert = "ERROR - no userID2 supplied! Aborting"
    #             myPopupInformationBox(None, alert, theMessageType=JOptionPane.ERROR_MESSAGE)
    #             raise Exception(alert)
    #         defaultEntry = userID2
    #         if userID2 is None or userID2 == "" or userID2 == "UserID2" or len(userID2)<8:
    #             myPrint("B", "\n ** ERROR - no valid userID2 supplied - try again ** \n")
    #             continue
    #         break
    #     del defaultEntry

    ####################################################################################################################

    myPrint("B", "creating new service profile")
    book = MD_REF.getCurrentAccountBook()
    manualFIInfo = StreamTable()     # type: StreamTable

    manualFIInfo.put("obj_type",                                 "olsvc")

    manualFIInfo.put("access_type",                              "OFX")
    manualFIInfo.put("app_id",                                   "QWIN")
    manualFIInfo.put("app_ver",                                  "2700")
    manualFIInfo.put("bank_closing_avail",                       "0")
    manualFIInfo.put("bank_email_can_notify",                    "0")
    manualFIInfo.put("bank_email_enabled",                       "1")

    manualFIInfo.put("bank_xfr_can_mod_models",                  "0")
    manualFIInfo.put("bank_xfr_can_mod_xfrs",                    "0")
    manualFIInfo.put("bank_xfr_can_sched_recurring",             "0")
    manualFIInfo.put("bank_xfr_can_sched_xfrs",                  "0")
    manualFIInfo.put("bank_xfr_days_withdrawn",                  "0")
    manualFIInfo.put("bank_xfr_default_days_to_pay",             "0")
    manualFIInfo.put("bank_xfr_model_window",                    "0")
    manualFIInfo.put("bank_xfr_needs_tan",                       "0")
    manualFIInfo.put("bank_xfr_proc_end_time",                   "230000[0:GMT]")
    manualFIInfo.put("bank_xfr_supports_dt_avail",               "0")

    manualFIInfo.put("bootstrap_url",                            SECU_BOOTSTRAP)
    manualFIInfo.put("cc_closing_avail",                         "0")
    manualFIInfo.put("date_avail_accts",                         "20171128005611.653[0:GMT]")

    manualFIInfo.put("email_mail_supported",                     "1")
    manualFIInfo.put("email_supports_get_mime",                  "0")

    manualFIInfo.put("fi_addr1",                                 "900 Wade Avenue")
    manualFIInfo.put("fi_addr2",                                 "")
    manualFIInfo.put("fi_addr3",                                 "")
    manualFIInfo.put("fi_city",                                  "Raleigh")
    manualFIInfo.put("fi_country",                               "USA")
    manualFIInfo.put("fi_cust_svc_phone",                        "8887328562")
    manualFIInfo.put("fi_email",                                 "service@ncsecu.org")

    manualFIInfo.put("fi_id",                                    SECU_FI_ID)
    manualFIInfo.put("fi_name",                                  SECU_PROFILE_NAME)
    manualFIInfo.put("fi_org",                                   SECU_FI_ORG)
    manualFIInfo.put("fi_state",                                 "NC")

    manualFIInfo.put("fi_tech_svc_phone",                        "")
    manualFIInfo.put("fi_url",                                   "http://www.ncsecu.org")
    manualFIInfo.put("fi_url_is_redirect",                       "1")
    manualFIInfo.put("fi_zip",                                   "27603")

    manualFIInfo.put("invst_dflt_broker_id",                     "")

    manualFIInfo.put("language_banking",                         "ENG")
    manualFIInfo.put("language_creditcard",                      "ENG")
    manualFIInfo.put("language_default",                         "ENG")
    manualFIInfo.put("language_email",                           "ENG")
    manualFIInfo.put("language_fiprofile",                       "ENG")
    manualFIInfo.put("language_signup",                          "ENG")
    manualFIInfo.put("last_fi_refresh",                          "1612473805809")

    manualFIInfo.put("no_fi_refresh",                            "y")

    manualFIInfo.put("ofx_version",                              "102")
    manualFIInfo.put("ofxurl_banking",                           SECU_BOOTSTRAP)
    manualFIInfo.put("ofxurl_creditcard",                        SECU_BOOTSTRAP)
    manualFIInfo.put("ofxurl_default",                           SECU_BOOTSTRAP)
    manualFIInfo.put("ofxurl_email",                             SECU_BOOTSTRAP)
    manualFIInfo.put("ofxurl_signup",                            SECU_BOOTSTRAP)

    manualFIInfo.put("realm_banking",                            "Realm1")
    manualFIInfo.put("realm_creditcard",                         "Realm1")
    manualFIInfo.put("realm_default",                            "Realm1")
    manualFIInfo.put("realm_email",                              "Realm1")
    manualFIInfo.put("realm_fiprofile",                          "Realm1")
    manualFIInfo.put("realm_signup",                             "Realm1")

    manualFIInfo.put("rspnsfileerrors_banking",                  "1")
    manualFIInfo.put("rspnsfileerrors_creditcard",               "1")
    manualFIInfo.put("rspnsfileerrors_default",                  "1")
    manualFIInfo.put("rspnsfileerrors_email",                    "1")
    manualFIInfo.put("rspnsfileerrors_fiprofile",                "1")
    manualFIInfo.put("rspnsfileerrors_signup",                   "1")
    manualFIInfo.put("securetransport_banking",                  "1")
    manualFIInfo.put("securetransport_creditcard",               "1")
    manualFIInfo.put("securetransport_default",                  "1")
    manualFIInfo.put("securetransport_email",                    "1")
    manualFIInfo.put("securetransport_fiprofile",                "1")
    manualFIInfo.put("securetransport_signup",                   "1")
    manualFIInfo.put("security_banking",                         "NONE")
    manualFIInfo.put("security_creditcard",                      "NONE")
    manualFIInfo.put("security_default",                         "NONE")
    manualFIInfo.put("security_email",                           "NONE")
    manualFIInfo.put("security_fiprofile",                       "NONE")
    manualFIInfo.put("security_signup",                          "NONE")

    manualFIInfo.put("signup_accts_avail",                       "1")
    manualFIInfo.put("signup_can_activate_acct",                 "0")
    manualFIInfo.put("signup_can_chg_user_info",                 "0")
    manualFIInfo.put("signup_can_preauth",                       "0")
    manualFIInfo.put("signup_client_acct_num_req",               "0")
    manualFIInfo.put("signup_via_client",                        "1")
    manualFIInfo.put("signup_via_other",                         "0")
    manualFIInfo.put("signup_via_other_msg",                     "")
    manualFIInfo.put("signup_via_web",                           "0")

    manualFIInfo.put("so_can_change_pin_Realm1",                 "1")
    manualFIInfo.put("so_client_uid_req_Realm1",                 "0")   # THIS ONE IS THE CLIENT UUID!

    manualFIInfo.put("so_maxpasslen_Realm1",                     "32")
    manualFIInfo.put("so_minpasslen_Realm1",                     "6")
    manualFIInfo.put("so_must_chg_pin_first_Realm1",             "0")
    manualFIInfo.put("so_passchartype_Realm1",                   "ALPHAANDNUMERIC")
    manualFIInfo.put("so_passwd_case_sensitive_Realm1",          "1")
    manualFIInfo.put("so_passwd_spaces_Realm1",                  "0")
    manualFIInfo.put("so_passwd_special_chars_Realm1",           "1")
    manualFIInfo.put("so_passwd_type_Realm1",                    "FIXED")
    manualFIInfo.put("so_user_id_Realm1",                        userID)
    if selectedBankAccount:
        manualFIInfo.put("so_user_id_Realm1::%s" %(my_getAccountKey(selectedBankAccount)), userID)
    if selectedCCAccount:
        manualFIInfo.put("so_user_id_Realm1::%s" %(my_getAccountKey(selectedCCAccount)),   userID)
    manualFIInfo.put("syncmode_banking",                         "LITE")
    manualFIInfo.put("syncmode_creditcard",                      "FULL")
    manualFIInfo.put("syncmode_default",                         "FULL")
    manualFIInfo.put("syncmode_email",                           "FULL")
    manualFIInfo.put("syncmode_fiprofile",                       "FULL")
    manualFIInfo.put("syncmode_signup",                          "FULL")
    # manualFIInfo.put("tik_fi_id",                                OLD_TIK_FI_ID)

    manualFIInfo.put("user-agent",                               "InetClntApp/3.0")  # This is the magic!

    # manualFIInfo.put("use_ofx_certs",                            "y") # The original SECU profile had this - so not using...
    # manualFIInfo.put("uses_fi_tag",                              "y") # The original SECU profile had this - so not using...

    manualFIInfo.put("version_banking",                          "1")
    manualFIInfo.put("version_creditcard",                       "1")
    manualFIInfo.put("version_default",                          "1")
    manualFIInfo.put("version_email",                            "1")
    manualFIInfo.put("version_fiprofile",                        "1")
    manualFIInfo.put("version_signup",                           "1")

    # manualFIInfo.put("id",                                       "57554f9e-5728-4609-879a-f3dec0d213b8")
    # manualFIInfo.put("last_txn_id",                              "0-cce586a8_dcd941e0-63")

    num = 0
    if selectedBankAccount:
        sNum = str(num)
        manualFIInfo.put("available_accts.%s.account_num" %(sNum),            str(bankID).zfill(SECU_ACCT_LENGTH))
        manualFIInfo.put("available_accts.%s.account_type" %(sNum),           accountTypeOFX)
        manualFIInfo.put("available_accts.%s.branch_id" %(sNum),              "")
        manualFIInfo.put("available_accts.%s.desc" %(sNum),                   "")
        manualFIInfo.put("available_accts.%s.has_txn_dl" %(sNum),             "1")
        manualFIInfo.put("available_accts.%s.has_xfr_from" %(sNum),           "1")
        manualFIInfo.put("available_accts.%s.has_xfr_to" %(sNum),             "1")
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
        manualFIInfo.put("available_accts.%s.desc" %(sNum),                   "")
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
    newService.syncItem()

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

        myPrint("B", ">> setting OFX Account Number to: %s" %(str(bankID).zfill(SECU_ACCT_LENGTH)))
        selectedBankAccount.setOFXAccountNumber(str(bankID).zfill(SECU_ACCT_LENGTH))  # noqa

        myPrint("B", ">> setting OFX Type to '%s'" %(accountTypeOFX))
        selectedBankAccount.setOFXAccountType(accountTypeOFX)           # noqa

        myPrint("B", ">> Setting up the Banking Acct %s link to new bank service / profile %s" %(selectedBankAccount, newService))
        selectedBankAccount.setBankingFI(newService)                    # noqa

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

        selectedCCAccount.syncItem()                                    # noqa
        selectedCCAccount.getDownloadedTxns()                           # noqa
        print

    ####################################################################################################################

    # myPrint("B", "Updating root with userID and default global uuid")
    # root = MD_REF.getRootAccount()
    #
    # myPrint("B","... calling .setEditingMode() on root...")
    # root.setEditingMode()
    #
    # uuid = root.getParameter(authKeyPrefix, createNewClientUID())
    # # if lOverrideRootUUID:
    # #     myPrint("B","Overriding Root's default UUID. Was: %s >> changing to >> %s" %(root.getParameter(authKeyPrefix, ""),uuid))
    # #     root.setParameter(authKeyPrefix, uuid)
    # #     # root.setParameter(authKeyPrefix+"::" + service.getTIKServiceID() + "::" + "null",   uuid)         # noqa
    # #
    # rootKeys = list(root.getParameterKeys())
    # for i in range(0,len(rootKeys)):
    #     rk = rootKeys[i]
    #     if rk.startswith(authKeyPrefix) and (service.getTIKServiceID() in rk or OLD_TIK_FI_ID in rk):
    #         myPrint("B", "Deleting old authKey %s: %s" %(rk,root.getParameter(rk)))
    #         root.setParameter(rk, None)
    #     i+=1
    #
    # root.setParameter(authKeyPrefix+"::" + service.getTIKServiceID() + "::" + userID,   uuid)
    # root.setParameter(authKeyPrefix+"_default_user"+"::" + service.getTIKServiceID(), userID)
    # myPrint("B", "Root UserID and uuid updated...")

    # if lMultiAccountSetup:
    #     root.setParameter(authKeyPrefix+"::" + service.getTIKServiceID() + "::" + userID2,   uuid2)
    #     myPrint("B", "Root UserID TWO and uuid TWO primed - ready for Online Banking Setup...")
    #
    # root.syncItem()
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

    # if "DEFAULT" not in realmsToCheck:
    #     realmsToCheck.insert(0,"DEFAULT")       # noqa

    for realm in realmsToCheck:
        myPrint("B", "Realm: %s current User ID: %s" %(realm, service.getUserId(realm, None)))        # noqa

        for olacct in listAccountMDProxies:

            authKey = "ofx:" + realm
            authObj = service.getCachedAuthentication(authKey)                              # noqa
            myPrint("B", "Realm: %s Cached Authentication: %s" %(realm, authObj))

            newAuthObj = "type=0&userid=%s&pass=%s&extra=" %(URLEncoder.encode(userID),URLEncoder.encode(password))

            # myPrint("B", "** Setting new cached authentication from %s to: %s" %(authKey, newAuthObj))
            # service.cacheAuthentication(authKey, newAuthObj)        # noqa

            authKey = "ofx:" + (realm + "::" + olacct[_ACCOUNT].getAccountKey())
            authObj = service.getCachedAuthentication(authKey)        # noqa
            myPrint("B", "Realm: %s Account Key: %s Cached Authentication: %s" %(realm, olacct[_ACCOUNT].getAccountKey(),authObj))
            myPrint("B", "** Setting new cached authentication from %s to: %s" %(authKey, newAuthObj))
            service.cacheAuthentication(authKey, newAuthObj)        # noqa

            myPrint("B", "Realm: %s now UserID: %s" %(realm, userID))

    ####################################################################################################################

    myPrint("B", "SUCCESS. Please RESTART Moneydance.")

    myPopupInformationBox(None, "SUCCESS. REVIEW OUTPUT - Then RESTART Moneydance.", theMessageType=JOptionPane.ERROR_MESSAGE)

    cleanup_actions()

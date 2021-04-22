#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""Example script accessing moneydance data in 'headless' mode using jpype - uses: wrapper.loadDataModel()

DISCLAIMER: This is NOT a method 'supported' by Infinite Kind!
            Always BACKUP FIRST
            Do not use when Moneydance is open
            I would suggest you stay READONLY - do not update data
            USE AT YOUR OWN RISK!

More information on jpype here: https://jpype.readthedocs.io/en/latest/
note that project jar files are from MD Preview Version

###############################################################################
# MIT License
#
# Copyright (c) 2021 Stuart Beesley
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

Original concept & credits - Dale Furrow: https://github.com/dkfurrow/md_python_headless_demo

MODIFICATIONS: Stuart Beesley - StuWareSoftSystems 2021 - https://yogi1967.github.io/MoneydancePythonScripts/

Help and credits: hleofxquotes...

INSTRUCTIONS:
- Get Python working (outside of Moneydance)
- Read the JPype instructions at the website link provided: https://jpype.readthedocs.io/en/latest/
- Download / pip install the correct JPype for your platform
- extract the moneydance.jar and mdpython.jar files into a directory of your choosing

NOTE:
- This is a basic script to get access to your Moneydance data externally and allows you to open with a user set passphrase
- See Dale Furrow's scripts 1-5 for further examples of automation. Currently it's tricky to do these steps if you have a user
- passphrase set without extending Main and overriding .getUI(); and extending MoneydanceGUI() and overriding .getSecretKeyCallback(), .showErrorMessage(), .go()
- JPype cannot extend Java classes.. so see my own open_mdheadless_external_jython_with_passphrase2.py for example
- The IK developer (Sean) has indicated he's willing to set en environment variable to pass the passphrase (April 2021) - let's see....
"""

################### `set these variables ##########################################
lUsePassphrase = True
myEncryptionPassphrase = u"bob"
mdDataFolder = "/Users/stu/Library/Containers/com.infinitekind.MoneydanceOSX/Data/Documents/FAKE2.moneydance"
MD_PATH = "./MDJARS/"       # include moneydance.jar and mdpython.jar
################### `set these variables ##########################################


# from datetime import datetime, date
import os

# import jpype
import jpype.imports
from jpype.types import *
from jpype import JImplements, JOverride

# get oriented, print current working directory (script is based on working directory as project root)
print("Working Directory: {0}".format(os.getcwd()))

###################################################################
# Launch the JVM
join_jars = f'{str.join(":", [("%s" %(MD_PATH))+name for name in os.listdir("%s" %(MD_PATH))])}'
print("Starting JVM...")
jpype.startJVM(classpath=[join_jars])


print("Importing necessary Moneydance Classes...")
from com.moneydance.apps.md.controller import Main 
from com.moneydance.security import SecretKeyCallback

print("Importing useful Moneydance Classes...")
from com.moneydance.apps.md.controller import AccountBookWrapper
from com.infinitekind.moneydance.model import ParentTxn
from com.infinitekind.moneydance.model import CurrencyType
# from com.infinitekind.moneydance.model import AccountBook
# from com.infinitekind.moneydance.model import Account
# from com.infinitekind.moneydance.model import TxnSet
# from com.infinitekind.moneydance.model import AbstractTxn
# from com.infinitekind.moneydance.model import SplitTxn
# from com.infinitekind.moneydance.model import TxnUtil
# from com.infinitekind.moneydance.model import CurrencySnapshot
# from com.infinitekind.moneydance.model import CurrencyTable
# from com.infinitekind.moneydance.model import CurrencyUtil
# from com.infinitekind.moneydance.model import MoneydanceSyncableItem

print("Importing useful Java Classes...")
from java.io import File

print("prove moneydance data file exists, load it into java File object")
print("Moneydance Data File exists? {0}, in {1}".format(os.path.exists(mdDataFolder), mdDataFolder))
mdFileJava = File(mdDataFolder)
last_modded_long = mdFileJava.lastModified()  # type is java class 'JLong'
print("data folder last modified: %s" %(last_modded_long))


###################################################################
# The 'magic' that holds/returns the encryption key....
@JImplements(SecretKeyCallback)
class MySecret(object):
    def __init__(self, theKey):
        self.theKey = theKey

    @JOverride
    def getPassphrase(self, arg1, arg2=None):
        print("@getPassphrase(%s,%s) will return %s" %(arg1,arg2,self.theKey))
        return self.theKey


###################################################################
# Fire up Moneydance and initialize key stuff...
mdMain = Main()
mdMain.initializeApp()
#mdMain.startApplication()    

###################################################################
# Now get the 'wrapper' etc
print("@@@now get AccountBookWrapper, accountBook, and rootAccount")
wrapper = AccountBookWrapper.wrapperForFolder(mdFileJava)  # wrapper is of java type 'AccountBookWrapper'
accountBook = wrapper.getBook()

if lUsePassphrase:
    callback = MySecret(myEncryptionPassphrase)
else:
    callback = None

wrapper.loadLocalStorage(callback)
wrapper.loadDataModel(callback)


###################################################################
# Away we go, accessing the data...

root_account = accountBook.getRootAccount()

print("Verify by printing useful information about these elements...")
print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
print("The name of the rootAccount is {0}".format(root_account.getAccountName()))
print("The id of the rootAccount is {0}".format(root_account.getUUID()))
print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")

txnSet = accountBook.getTransactionSet()
transactionCount = int(txnSet.getTransactionCount())
print("There are {0:d} transactions in the AccountBook".format(transactionCount))

accountCount = int(root_account.getSubAccounts().size())
print("There are {0:d} sub-accounts in the rootAccount".format(accountCount))

print("printing details on last 10 parent transactions...")
parent_txns = [x for x in txnSet.iterableTxns() if isinstance(x, ParentTxn)]
ii=0
for txn in parent_txns:
    ii+=1
    if ii > 10: break
    print("transaction date {0:d} account {1} description: {2} for amount {3}"
          .format(int(txn.getDateInt()), txn.getAccount().getAccountName(), txn.getDescription(),
                  txn.getAccount().getCurrencyType().formatFancy(txn.getValue(), '.')))


print("Printing Information on Securities...")
currencies = accountBook.getCurrencies().getAllCurrencies()
# noinspection PyUnresolvedReferences
securities = [x for x in currencies if x.getCurrencyType() == CurrencyType.Type.SECURITY]

ii=0
for security in securities:
    try:
        ii+=1
        if ii > 10: break
        last_snapshot = [x for x in security.getSnapshots()][-1]
        price = 1 / float(last_snapshot.getRate())
        dateInt = last_snapshot.getDateInt()
        ticker = security.getTickerSymbol()
        print("Name: {0} Ticker:{1} last snapshot: {2:d} last price {3:.3f}"
              .format(security.getName(), ticker ,dateInt, price))
    except:
        pass
    
print("@@@@  END @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")

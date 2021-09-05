#!/bin/sh

# Co-Author Stuart Beesley - StuWareSoftSystems - Feb 2021 (last updated: 7th April 2021)
# Original Author, thanks & credits to hleofxquotes for the original base script and valuable input and knowledge.

# Shell script: launch-moneydance.sh
# Make sure you 'chmod +x launch-moneydance.sh' to make script executable

# NOTE:   You can also just run the 'code-signed app' by launching the following from Terminal (which is a simpler approach):
#         "/Applications/Moneydance.app/Contents/MacOS/Moneydance"                [-d] [-v] [... etc]
#         "/Applications/Moneydance 2021.2 (3089).app/Contents/MacOS/Moneydance"  [-d] [-v] [... etc]

# THIS IS WRITTEN FOR MacOS Terminal(zsh). Adjust accordingly...!

# The purpose of this shell script is to launch Moneydance from the Terminal command line, simulating the same
# 'experience' that you get when running Moneydance from the normal install icon (and the same folder locations).
# A real MacOs sandbox environment is not possible as you have to build an app installer for that, and this would
# defeat the point of using a script. However, this script sets up your environment to replicate everything, including
# folder paths. The real benefits of using this script are:
#   1. Ability to run without sandbox restrictions (access to all folders, not Gatekeeper messages with Python)
#   2. Ability to launch MD with parameters - e.g. -d for debug mode
#   3. Ability to swap in your own java libraries (assuming you are a developer)

# This has been setup for a Mac, and would need to be changed for Windows/Linux - especially the folder locations...

# Usage:
# Execute using './launch-moneydance.sh' you can add parameters that will be passed to Moneydance
# Parameter: '-d'                 is passed by default by this script and turns on MD DEBUG mode
# Parameter: '-v'                 prints the current version
# Parameter: datasetname          will open the specified dataset - specify the full path wrapped in "quotes"
# Parameter: pythonscriptname.py  adds script to a list of scripts to execute (but this seems to then be ignored)
# Parameter: importfilename       executes file import (mutually exclusive to datasetname option)
# Parameter: '-invoke_and_quit=x' will pass along a string that you can to invoke an 'fmodule' (extension) and quit (not showing UI)
#                                 executes Main.showURL(invokeAndQuitURI)
#                                 e.g. 'moneydance:fmodule:test:test:customevent:magic'
#                                 (e.g. my own extension with an id of test defines it's own command called 'test:customevent:magic'
#                                 (there are other variations of this parameter and with ? instead of ':' for parameters.....
# Parameter: '-invoke=x'          Same as -invoke_and_quit but does launch the UI first and doesn't quit...!

# MD2021.2(3088): Adds the capability to set the encryption passphrase into an environment variable to bypass the popup question
#                 Either: md_passphrase=  or  md_passphrase_[filename in lowercase format]

unset md_passphrase
unset md_passphrase
#export md_passphrase=XxX


# Download/install Java FX (allows Moneybot Console) to run: https://gluonhq.com/download/javafx-15-0-1-sdk-mac/
# Download/install OpenAdoptJDK (Hotspot) v15: https://adoptopenjdk.net/?variant=openjdk15&jvmVariant=hotspot

# Edit the necessary install locations for JDK and JavaFX below

# Edit the necessary settings and your folder locations below

clear
echo
echo
echo
echo
echo
echo
echo "############################################################################################"
echo "############################################################################################"
echo "#########                                                                               ####"
echo "#########  LAUNCHING MONEYDANCE (simulating click of icon)                              ####"
echo "#########                                                                               ####"
echo "############################################################################################"
echo "############################################################################################"
echo "############################################################################################"
echo

#CHECK_IF_RUNNING=$(ps axlww | grep -v grep | grep -i moneydance)
CHECK_IF_RUNNING=$(pgrep -i -l -f /moneydance)
if [ "${CHECK_IF_RUNNING}" != "" ]; then
    echo "@@ ERROR - it seems that Moneydance might already be running... So I will abort..."
    echo "pgrep returned: '${CHECK_IF_RUNNING}'"
    exit 99
fi

# Prevents Moneydance JFrames appearing in tabs... causes strange problems...
echo "current tabbing mode is set to..:"
defaults read -g AppleWindowTabbingMode

echo "changing tabbing mode to manual (=never)"
defaults write -g AppleWindowTabbingMode -string manual

my_user_path=~
echo "My user path: ${my_user_path}"

# Set your JAVA_HOME
# On Mac, output of '/usr/libexec/java_home --verbose' can help
export JAVA_HOME="${my_user_path}/Library/Java/JavaVirtualMachines/adopt-openjdk-15.0.2/Contents/Home"
export PATH="${JAVA_HOME}/bin:${PATH}"
java=java

# JavaFX directory
javafx="${my_user_path}/Documents/Moneydance/My Python Scripts/javafx-sdk-15.0.1/lib"
modules="javafx.swing,javafx.media,javafx.web,javafx.fxml"

# set to "" for standard app install name (I add the version and build to the app name when installing)
#md_version=""
md_version=" 2021.2 (3095)"

# Where are the MD jar files
md_jars="/Applications/Moneydance${md_version}.app/Contents/Java"
md_icon="/Applications/Moneydance${md_version}.app/Contents/Resources/desktop_icon.icns"

if ! test -d "${md_jars}"; then
  echo "ERROR - directory ${md_jars}/ does not exist!"
  exit 1
fi

# Other paths....
macos="/Applications/Moneydance${md_version}.app/Contents/MacOS"
machelper2="/Applications/Moneydance${md_version}.app/Contents/PlugIns/vm.jdk/Contents/Home/lib"

# Set to "" for no sandbox (however, with enabled=true is not really a sandbox)
#use_sandbox=""
use_sandbox="-DSandboxEnabled=true"

# NOTE: I set '-Dinstall4j.exeDir=x' to help my Toolbox extension - this is not needed

# Redirect output to the Moneydance console window...
mkdir -v -p "${my_user_path}/Library/Containers/com.infinitekind.MoneydanceOSX/Data/Library/Application Support/Moneydance"
console_file="${my_user_path}/Library/Containers/com.infinitekind.MoneydanceOSX/Data/Library/Application Support/Moneydance/errlog.txt"
${java} --version

# shellcheck disable=SC2086
# shellcheck disable=SC2048
${java} \
  -Xdock:icon="${md_icon}" \
  -cp "${md_jars}/*" \
  --module-path "${javafx}" \
  --add-modules ${modules} \
  -Djava.library.path="${macos}:${machelper2}" \
  -Dapple.laf.useScreenMenuBar=true \
  -Dcom.apple.macos.use-file-dialog-packages=true \
  -Dcom.apple.macos.useScreenMenuBar=true \
  -Dcom.apple.mrj.application.apple.menu.about.name=Moneydance \
  -Dapple.awt.application.name=Moneydance \
  -Dcom.apple.smallTabs=true \
  -Dapple.awt.application.appearance=system \
  -Dfile.encoding=UTF-8 \
  -DUserHome=${my_user_path} \
  ${use_sandbox} \
  -Dinstall4j.exeDir="${md_jars}" \
  -Duser.dir="${my_user_path}/Library/Containers/com.infinitekind.MoneydanceOSX/Data" \
  -Duser.home="${my_user_path}/Library/Containers/com.infinitekind.MoneydanceOSX/Data" \
  -DApplicationSupportDirectory="${my_user_path}/Library/Containers/com.infinitekind.MoneydanceOSX/Data/Library/Application Support" \
  -DLibraryDirectory="${my_user_path}/Library/Containers/com.infinitekind.MoneydanceOSX/Data/Library" \
  -DDownloadsDirectory="${my_user_path}/Library/Containers/com.infinitekind.MoneydanceOSX/Data/Downloads" \
  -DDesktopDirectory="${my_user_path}/Library/Containers/com.infinitekind.MoneydanceOSX/Data/Desktop" \
  -DPicturesDirectory="${my_user_path}/Library/Containers/com.infinitekind.MoneydanceOSX/Data/Pictures" \
  -DDocumentsDirectory="${my_user_path}/Library/Containers/com.infinitekind.MoneydanceOSX/Data/Documents" \
  -DCachesDirectory="${my_user_path}/Library/Containers/com.infinitekind.MoneydanceOSX/Data/Library/Caches" \
  -DSharedPublicDirectory="${my_user_path}/Library/Containers/com.infinitekind.MoneydanceOSX/Data/Public" \
  -DMoviesDirectory="${my_user_path}/Library/Containers/com.infinitekind.MoneydanceOSX/Data/Movies" \
  -DDownloadsDirectory="${my_user_path}/Library/Containers/com.infinitekind.MoneydanceOSX/Data/Downloads" \
  -DApplicationDirectory="${my_user_path}/Library/Containers/com.infinitekind.MoneydanceOSX/Data/Applications" \
  -DMusicDirectory="${my_user_path}/Library/Containers/com.infinitekind.MoneydanceOSX/Data/Music" \
  -DAutosavedInformationDirectory="${my_user_path}/Library/Containers/com.infinitekind.MoneydanceOSX/Data/Library/Autosave Information" \
  -Xmx2G \
  -Ddummyarg1=arg1 \
  -Ddummyarg2=arg2 \
  Moneydance -d $* &>"$console_file"

open "$console_file"

echo "changing tabbing mode to fullscreen"
defaults write -g AppleWindowTabbingMode -string fullscreen

exit 0


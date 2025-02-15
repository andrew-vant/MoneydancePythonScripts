#!/bin/sh

clear

EXTN_LIST=("toolbox" "extract_data" "useful_scripts" "list_future_reminders" "net_account_balances" "extension_tester" "accounts_categories_mega_search_window" "security_performance_graph")

if ! test -f "./build/extension-build.sh"; then
    echo "@@ PLEASE RUN FROM THE PROJECT's ROOT directory! @@"
    exit 1
fi

for THE_EXTN in "${EXTN_LIST[@]}"; do
  ./build/extension-build.sh "${THE_EXTN}"
  if [ $? -ne 0 ]; then
      echo "*** BUILD of ${THE_EXTN} Failed??"
      read -p "Press any key to resume next build..."
  fi
done
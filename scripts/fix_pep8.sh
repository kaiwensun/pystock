#!/bin/bash
set -e
pushd $( dirname "${BASH_SOURCE[0]}" )/.. > /dev/null
source "./scripts/bash_utils.sh"
activate_venv

echo "Do you want to make changes to files inplace? [Y/n]"
read answer
if [[ $answer == Y || $answer == y ]]
then
    option="-i" 
else
    option="-d"
fi
autopep8 $option -r --exclude=.venv,./local_settings.py,./config/settings.py  -a .

deactivate
popd > /dev/null

#!/bin/bash
set -e
pushd $( dirname "${BASH_SOURCE[0]}" )/.. > /dev/null
source "./scripts/bash_utils.sh"
activate_venv

python -m app 2>errors.log

deactivate
popd > /dev/null

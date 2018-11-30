activate_venv() {
    if [ ! -d .venv ]; then
        if ! hash py 2>/dev/null ; then
            python3.7 -m venv .venv
        else
            py -3.7 -m venv .venv
        fi
    fi
    WIN_VENV_PATH="./.venv/Scripts/activate"
    LINUX_VENV_PATH="./.venv/bin/activate"
    if [ -f $WIN_VENV_PATH ]; then
        source "${WIN_VENV_PATH}"
    else
        source "${LINUX_VENV_PATH}"
    fi
}

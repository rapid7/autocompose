#!/usr/bin/env bash
# Adds bash completion to autocompose

RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m'

# Get directories from a given path.
_autocompose_get_dirs_from_paths() {
    SUB_PATH=$1
    COLOR=$2
    RESULTS=""

    for DIRECTORY in $(echo ${AUTOCOMPOSE_PATH} | sed 's/:/ /'); do
        CURRENT_PATH=${DIRECTORY}/${SUB_PATH}
        if [ -e ${CURRENT_PATH} ] && [ -d ${CURRENT_PATH} ]; then
            cd ${CURRENT_PATH} &>/dev/null
            RESULTS="${RESULTS} $(ls -d */ | sed 's:/::g')"

            for RESULT in ${RESULTS}; do
                echo "${RESULT}"
            done

            cd - &>/dev/null
        fi
    done
    # echo ${RESULTS}
}

# Bash Autocompletion function.
_autocompose() {
    COMPREPLY=()
    local cur=${COMP_WORDS[COMP_CWORD]}

    # Root command
    if [ $COMP_CWORD -eq 1 ]; then
        COMPREPLY=( $(compgen -W "init login push build clean-containers clean-images update-images clean-networks compose up path" -- "$cur") )
    elif [ $COMP_CWORD -ge 2 ]; then

        COMPREPLY=( $(compgen -W "$(_autocompose_get_dirs_from_paths services ${RED})" -- "$cur") $(compgen -W "$(_autocompose_get_dirs_from_paths scenarios ${YELLOW})" -- "$cur") )
    fi
}

complete -F _autocompose "autocompose"

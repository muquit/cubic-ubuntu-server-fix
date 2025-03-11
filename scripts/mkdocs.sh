#!/bin/sh
# muquit@muquit.com Mar-11-2025 
MH="markdown_helper"
RM="/bin/rm -f"
DOC_DIR="./docs"
pushd $DOC_DIR >/dev/null 
echo " - Assembling README.md"
${MH} include --pristine main.md ../README.md
popd >/dev/null

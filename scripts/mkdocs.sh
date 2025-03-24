#!/bin/sh
# muquit@muquit.com Mar-11-2025 
MH="markdown_helper"
RM="/bin/rm -f"
DOC_DIR="./docs"

# generate Download count doc
# I know this repo has a Releases page
echo "--  Generating Download Count page ..."
githubdownloadcount-go -user=muquit -markdown -project=cubic-ubuntu-server-fix > ${DOC_DIR}/downloads.md

pushd $DOC_DIR >/dev/null 
echo " - Assembling README.md ..."
${MH} include --pristine main.md ../README.md
popd >/dev/null

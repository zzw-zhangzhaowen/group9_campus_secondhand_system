#!/bin/zsh
# Only temporary demo data is created. No default backend data is touched.
cd "${0:A:h:h}" || exit 1
for candidate in "$HOME/.local/bin/python3.12" python3.12 python3; do
    if "$candidate" -c 'import sys, tkinter; assert sys.version_info >= (3, 10)' 2>/dev/null; then
        "$candidate" -m gui_gao --demo
        exit $?
    fi
done
echo '需要安装带 Tkinter 的 Python 3.10 或以上版本。'
read -k 1 '?按任意键关闭…'

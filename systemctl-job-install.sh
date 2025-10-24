#!/usr/bin/env bash

#227  2025-10-12 20:38:13 ./run-check.sh
#  229  2025-10-12 20:38:26 vi checkmail.py
#  230  2025-10-12 20:56:19 ls
#  231  2025-10-12 20:56:37 more comment-update.service
#  234  2025-10-12 20:57:37 vi   comment-update.timer
#  235  2025-10-12 20:59:40 more comment-update.timer
#--
#  242  2025-10-12 21:25:06 ls -latr
#  243  2025-10-12 21:26:11 latr
#  244  2025-10-12 21:26:18 touch foo
#  245  2025-10-12 21:26:23 ls -lag
#  246  2025-10-12 21:26:31 chmod 777 .
#  247  2025-10-12 21:26:36 sudo chmod 777 .
#  248  2025-10-12 21:26:38 touch foo
#  249  2025-10-12 21:26:40 rm foo
#  250  2025-10-12 22:38:56 mkdir comments
#  251  2025-10-12 22:39:25 chown rca comments
sudo cp comment-update.service /usr/lib/systemd/system/
#/etc/systemd/system
sudo cp comment-update.timer /usr/lib/systemd/system/
#/etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable comment-update.timer
sudo systemctl start comment-update.timer
sudo systemctl list-timers --all
systemctl status comment-update.timer

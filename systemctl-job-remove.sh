sudo systemctl stop comment-update.timer
sudo systemctl disable comment-update.timer
sudo rm /usr/lib/systemd/system/comment-update.*
sudo systemctl daemon-reload

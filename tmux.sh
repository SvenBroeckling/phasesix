#! /bin/sh -u
SESSION_NAME='urpg'


tmux new-session -s $SESSION_NAME -n sql -d
#tmux send-keys -t $SESSION_NAME 'tail -f logs/sql.log' C-m

tmux new-window -n celery -t $SESSION_NAME
#tmux send-keys -t $SESSION_NAME:1 'workon magily; celery -A magily worker --events --beat --loglevel DEBUG --concurrency=1 -Q default,books' C-m
tmux new-window -n shell -t $SESSION_NAME
tmux send-keys -t $SESSION_NAME:2 'workon urpg; ./update.sh; ./manage.py runserver 0.0.0.0:8000' C-m
tmux split-window -h -t $SESSION_NAME:2
tmux send-keys -t $SESSION_NAME:2 'workon urpg' C-m

tmux attach -t $SESSION_NAME

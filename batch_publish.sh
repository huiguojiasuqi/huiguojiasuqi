#!/bin/bash
# 批量发布剩余文章：每批50篇 fetch+commit+push，进度写 progress.log
cd /root/github-huiguojiasuqi
TOTAL=1921
DONE=30
BATCH=50
while [ $DONE -lt $TOTAL ]; do
  N=$BATCH
  LEFT=$((TOTAL - DONE))
  [ $LEFT -lt $BATCH ] && N=$LEFT
  echo "[$(date '+%F %T')] batch start=$DONE n=$N" >> progress.log
  python3 publish.py $N --start $DONE >> progress.log 2>&1
  NEW=$(find posts -name '*.md' | wc -l)
  if [ "$NEW" -le "$DONE" ] && [ "$NEW" -le 30 ]; then
    echo "[$(date '+%F %T')] no new files (total $NEW), stop" >> progress.log
    break
  fi
  git add posts >> progress.log 2>&1
  git -c user.name=huiguojiasuqi -c user.email=huiguojiasuqi@users.noreply.github.com \
    commit -m "publish: posts batch start=$DONE n=$N (total $NEW)" >> progress.log 2>&1 || true
  git push origin main >> progress.log 2>&1 || echo "[$(date '+%F %T')] PUSH FAILED" >> progress.log
  DONE=$NEW
  sleep 2
done
echo "[$(date '+%F %T')] ALL DONE total=$(find posts -name '*.md' | wc -l)" >> progress.log

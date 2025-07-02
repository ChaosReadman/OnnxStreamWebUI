#!/bin/bash

BASE_DIR="$(cd "$(dirname "$0")"; pwd)"
SD_EXEC="$BASE_DIR/../OnnxStream/src/build/sd"
MODELS_PATH="$BASE_DIR/../models"

LOCKFILE="/tmp/generate.lock"
LOGFILE="/tmp/generate.log"

# Check lock file and existing process
if [ -f "$LOCKFILE" ]; then
    OLD_PID=$(cat "$LOCKFILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "Another process is runnning (PID=$OLD_PID)" >> "$LOGFILE"
        exit 1
    else
        echo "Locck file left, but process was finished. Lock file deleted" >> "$LOGFILE"
        rm -f "$LOCKFILE"
    fi
fi

OUTFILE=$1
PROMPT=$2
NEGATIVE_PROMPT=$3
STEPS=$4
WIDTH=$5
HEIGHT=$6
# JSON FileName（.png.json）
JSONFILE="${OUTFILE}.json"

# Generate process on backend + trap to clean up lock file
(
  trap "rm -f $LOCKFILE" EXIT
 "$SD_EXEC" \
    --rpi "A" \
    --turbo \
    --models-path "$MODELS_PATH" \
    --prompt "$PROMPT" \
    --neg-prompt "$NEGATIVE_PROMPT" \
    --steps "$STEPS" \
    --res "${WIDTH}x${HEIGHT}" \
    --output "$OUTFILE" >> "$LOGFILE" 2>&1

    # If generated successfully, write metadata to JSON
    if [ $? -eq 0 ] && [ -f "$OUTFILE" ]; then
        echo "generated successfully, write meta data." >> "$LOGFILE" 2>&1
        echo "{" > "$JSONFILE"
        echo "  \"prompt\": \"$PROMPT\"," >> "$JSONFILE"
        echo "  \"negative_prompt\": \"$NEGATIVE_PROMPT\"," >> "$JSONFILE"
        echo "  \"steps\": \"$STEPS\"," >> "$JSONFILE"
        echo "  \"width\": \"$WIDTH\"," >> "$JSONFILE"
        echo "  \"height\": \"$HEIGHT\"," >> "$JSONFILE"
        echo "  \"created_at\": \"$(date --iso-8601=seconds)\"" >> "$JSONFILE"
        echo "}" >> "$JSONFILE"
    else
        echo "Failed to generate, no JSON output." >>"$LOGFILE"
    fi

    rm -f "$LOCKFILE"
) &

SD_PID=$!

echo "Generate Start: PID=$SD_PID PROMPT=$PROMPT STEPS=$STEPS WIDTH=$WIDTH HEIGHT=$HEIGHT"  >> "$LOGFILE"
echo "$SD_PID" > "$LOCKFILE"


#!/usr/bin/env bash

TMPFILE=$(mktemp)

if [ $# -ne 2 ]; then
    echo "Usage: $0 <chrome log file> <output pcap file>"
    exit 1
fi


# Extract the pcap from the Chrome log
grep SCTP_PACKET "$1" > "$TMPFILE"
# Convert the text to pcap
text2pcap -n -l 248 -D -t '%H:%M:%S.' "$TMPFILE" "$2"
# Remove the temporary file
rm "$TMPFILE"
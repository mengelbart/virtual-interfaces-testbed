#!/bin/bash

# set -x
# set -e
# set -o pipefail

check_sudo() {
	if [ "$EUID" -ne 0 ]; then
		echo "Please run as root."
		exit
	fi
}

host1() {
	ip netns exec ns1 bash
}

host2() {
	ip netns exec ns4 bash
}

kitty () {
	local ns=$1
	if [[ $ns == "hosts" ]]; then
		sudo kitty --hold sh -c "ip netns exec ns1 bash" &
		sudo kitty --hold sh -c "ip netns exec ns4 bash" &
	else
		sudo kitty --hold sh -c "ip netns exec ns$ns bash" &
	fi
}

main() {
	check_sudo
        echo "If connectivity doesn't work, remember to run: "
        echo "modprobe br_netfilter"
        echo "sysctl -w net.bridge.bridge-nf-call-arptables=0"
        echo "sysctl -w net.bridge.bridge-nf-call-ip6tables=0"
        echo "sysctl -w net.bridge.bridge-nf-call-iptables=0"
        echo "sysctl -w net.ipv4.ip_forward=1"

	local cmd=$1
	if [[ $cmd == "kitty" ]]; then
		kitty $2
	elif [[ $cmd == "host1" ]]; then
		host1
	elif [[ $cmd == "host2" ]]; then
		host2
	else
		echo "usage: ventns.sh { kitty [hosts | <host-N> ] | host1 | host2 }"
	fi
}

main "$@"


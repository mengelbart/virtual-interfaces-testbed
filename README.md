# Network Emulation

## Network setup

The `network` module implements helper functions to set up a dumbbell topology using Linux network namespaces and virtual interfaces. `main.py` can be used to interact with the network module. It implements commands to add or remove the necessary namespaces and network interfaces, add some network limits using `tc` and can directly run the iperf3 or webrtc testcases.

To allow connectivity between the created interfaces you might have to run these commands:

```shell
modprobe br_netfilter
sysctl -w net.bridge.bridge-nf-call-arptables=0
sysctl -w net.bridge.bridge-nf-call-ip6tables=0
sysctl -w net.bridge.bridge-nf-call-iptables=0
sysctl -w net.ipv4.ip_forward=1
```

## Iperf3 Tests

The `iperf3test` module implements a simple function that runs an Iperf3 server and client in the emulated network and stores the log files for further analysis. The test requires iperf3 to be installed on the system.

## WebRTC Tests

The `webrtc` subdirectory contains selenium tests taken from the webrtc/samples repository. The test case starts two browsers and tries to establish a WebRTC connection between the two browsers. The testcases are implemented in javascript and will be invoked by a python function that can be called from the `main.py` script.

In order to run the browsers in the respective namespaces, the script will not invoke the webdriver itself, but connect to a remote instance instead. The python script will try to run the webdriver instances in the correct namespace. It will try to run the driver binary located at `webrtc/driver/chromedriver-linux64/chromedriver`. Chromium webdrivers are available [here](https://googlechromelabs.github.io/chrome-for-testing/). You can obtain the driver by running the following commands:

```shell
mkdir -p webrtc/driver
cd webrtc/driver
curl -O https://storage.googleapis.com/chrome-for-testing-public/<version>/linux64/chromedriver-linux64.zip # replace version with version from https://googlechromelabs.github.io/chrome-for-testing/
unzip chromedriver-linux64.zip
```

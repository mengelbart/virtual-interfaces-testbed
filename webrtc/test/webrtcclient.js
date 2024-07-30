/*
 *  Copyright (c) 2022 The WebRTC project authors. All Rights Reserved.
 *
 *  Use of this source code is governed by a BSD-style license
 *  that can be found in the LICENSE file in the root of the source
 *  tree.
 */
// Disable no-undef since this file is a mix of code executed
// in JS and the browser.
/* eslint no-undef: 0 */
class MediaStream {
  constructor(tracks = []) {
    this.tracks = tracks;
    this.id = 0;
  }

  getTracks() {
    return this.tracks;
  }

  getAudioTracks() {
    return this.getTracks().filter(t => t.kind === 'audio');
  }

  getVideoTracks() {
    return this.getTracks().filter(t => t.kind === 'video');
  }
}

class MediaDevices {
  constructor(driver) {
    this.driver = driver;
  }

  getUserMedia(constraints) {
    return this.driver.executeAsyncScript((constraints) => {
      const callback = arguments[arguments.length - 1];
      if (!window.localStreams) {
        window.localStreams = {};
      }

      return navigator.mediaDevices.getUserMedia(constraints)
        .then((stream) => {
          window.localStreams[stream.id] = stream;
          callback({
            id: stream.id, tracks: stream.getTracks().map((t) => {
              return { id: t.id, kind: t.kind };
            })
          });
        }, (e) => callback(e));
    }, constraints || { audio: true, video: true })
      .then((streamObj) => {
        const stream = new MediaStream(streamObj.tracks);
        stream.id = streamObj.id;
        return stream;
      });
  }

  getUserMedia2(constraints) {
    return this.driver.executeScript(() => {
      return navigator.mediaDevices.getUserMedia({ audio: true, video: true });
    });
  }
}

class PeerConnection {
  constructor(driver) {
    this.driver = driver;
  }

  create(rtcConfiguration) {
    return this.driver.executeScript(rtcConfiguration => {
      window.pc = new RTCPeerConnection(rtcConfiguration);
      const sendChannel = pc.createDataChannel('send');
      sendChannel.onopen = () => {
        const readyState = sendChannel.readyState;
        console.log('dc state ' + readyState);
      }
      window.sendChannel = sendChannel;
    }, rtcConfiguration);
  }

  addTrack(track, stream) {
    return this.driver.executeScript((track, stream) => {
      stream = localStreams[stream.id];
      track = stream.getTracks().find(t => t.id === track.id);
      pc.addTrack(track, stream);
      if (document.getElementById('local-video-' + stream.id)) {
        return;
      }
      const video = document.createElement('video');
      video.id = 'local-video-' + stream.id;
      video.autoplay = true;
      video.srcObject = stream;
      document.body.appendChild(video);
    }, track, stream);
  }

  createOffer(offerOptions) {
    return this.driver.executeAsyncScript((offerOptions) => {
      const callback = arguments[arguments.length - 1];

      pc.createOffer(offerOptions)
        .then(callback, callback);
    }, offerOptions);
  }

  createAnswer() {
    return this.driver.executeAsyncScript(() => {
      const callback = arguments[arguments.length - 1];

      pc.createAnswer()
        .then(callback, callback);
    });
  }

  // resolves with non-trickle description including candidates.
  setLocalDescription(desc) {
    return this.driver.executeAsyncScript((desc) => {
      const callback = arguments[arguments.length - 1];

      pc.onicecandidate = (event) => {
        console.log('candidate', event.candidate);
        if (!event.candidate) {
          pc.onicecandidate = null;
          callback(pc.localDescription);
        }
      };
      pc.setLocalDescription(desc)
        .catch(callback);
    }, desc);
  }

  // TODO: this implicitly creates video elements, is that deseriable?
  setRemoteDescription(desc) {
    return this.driver.executeAsyncScript(function (desc) {
      const callback = arguments[arguments.length - 1];

      pc.ontrack = function (event) {
        const id = event.streams[0].id;
        if (document.getElementById('video-' + id)) {
          return;
        }
        const video = document.createElement('video');
        video.id = 'video-' + id;
        video.autoplay = true;
        video.srcObject = event.streams[0];
        document.body.appendChild(video);

        window.chunks = [];
        window.mediaRecorder = new MediaRecorder(event.streams[0]);
        window.mediaRecorder.start(1000);
        window.mediaRecorder.ondataavailable = (e) => {
          console.log('got chunk');
          window.chunks.push(e.data);
        };
      };

      pc.ondatachannel = function (event) {
        console.log('got dc');
        receiveChannel = event.channel;
        receiveChannel.onmessage = (event) => {
          console.log(event.data);
        };
        receiveChannel.onopen = () => {
          const readyState = receiveChannel.readyState;
          console.log(`Receive channel state is: ${readyState}`);
        }
        receiveChannel.onclose = () => {
          const readyState = receiveChannel.readyState;
          console.log(`Receive channel state is: ${readyState}`);
        }
      }
      pc.setRemoteDescription(new RTCSessionDescription(desc))
        .then(callback, callback);
    }, desc);
  }

  sendDataChannel() {
    return this.driver.executeScript(() => {
      sendChannel.bufferedAmountLowThreshold = 1024;

      sendChannel.onbufferedamountlow = () => {
        console.log('buffered amount low event');
        if (sendChannel.readyState === 'open') {
          const randomData = new Uint8Array(Array.from({length: 65535}, () => Math.floor(Math.random() * 65535)));
          sendChannel.send(randomData);
          console.log('Sent random data:', randomData);
        }
      };
      
      // Initial data send to kick off the process
      if (sendChannel.readyState === 'open') {
        const initialData = new Uint8Array(Array.from({length: 65535}, () => Math.floor(Math.random() * 65535)));
        sendChannel.send(initialData);
        console.log('Sent initial random data:', initialData);
      }
    });
  }


  getStats() {
    return this.driver.executeAsyncScript(() => {
      const callback = arguments[arguments.length - 1];
      let reports = [];
      pc.getStats(null).then((stats) => {
        stats.forEach((report) => {
          reports.push(report);
        });
      });
      callback(reports);
    });
  }

  saveRecording() {
    return this.driver.executeAsyncScript(() => {
      const callback = arguments[arguments.length - 1];
      window.mediaRecorder.stop();
      const blob = new Blob(window.chunks);
      callback(new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onloadend = () => {
            resolve(reader.result.split(',')[1]); // Remove the "data:..." prefix
        };
        reader.onerror = reject;
        reader.readAsDataURL(blob);
      }));
    });
  }
}

module.exports = {
  PeerConnection,
  MediaDevices,
  MediaStream,
};


/*
 *  Copyright (c) 2022 The WebRTC project authors. All Rights Reserved.
 *
 *  Use of this source code is governed by a BSD-style license
 *  that can be found in the LICENSE file in the root of the source
 *  tree.
 */
const { buildDriver } = require('../webdriver');
const { PeerConnection, MediaDevices } = require('../webrtcclient');
const steps = require('../steps');
const fs = require('fs');

const browserA = process.env.BROWSER_A || 'chrome';
const browserB = process.env.BROWSER_B || 'chrome';

describe(`basic interop test ${browserA} => ${browserB}`, function () {
    let drivers;
    let clients;
    beforeAll(async () => {
        const options = {
            version: process.env.BVER || 'stable',
            browserLogging: true,
        }
        drivers = [
            await buildDriver(browserA, options, remoteUrl = 'http://10.1.0.10:8080'),
            await buildDriver(browserB, options, remoteUrl = 'http://10.3.0.20:8080'),
        ];
        clients = drivers.map(driver => {
            return {
                connection: new PeerConnection(driver),
                mediaDevices: new MediaDevices(driver),
            };
        });
    });
    afterAll(async () => {
        await drivers.map(driver => driver.close());
    });

    it('establishes a connection', async () => {
        await Promise.all(drivers); // timeouts in before(Each)?
        await steps.step(drivers, (d) => d.get('http://localhost:8000/'), 'Empty page loaded');
        await steps.step(clients, (client) => client.connection.create(), 'Created RTCPeerConnection');
        await new Promise(r => setTimeout(r, 1000));

        const stream = await clients[0].mediaDevices.getUserMedia({ audio: true, video: true });
        await Promise.all(stream.getTracks().map(async track => {
            return clients[0].connection.addTrack(track, stream);
        }));
        // For some reason this still needs to be called for remote media to play...
        await clients[1].mediaDevices.getUserMedia2();

        const offerWithCandidates = await clients[0].connection.setLocalDescription();
        await clients[1].connection.setRemoteDescription(offerWithCandidates);
        const answerWithCandidates = await clients[1].connection.setLocalDescription();
        await clients[0].connection.setRemoteDescription(answerWithCandidates);

        await steps.step(drivers, (d) => steps.waitNVideosExist(d, 1), 'Video elements exist');
        await steps.step(drivers, steps.waitAllVideosHaveEnoughData, 'Video elements have enough data');
        await steps.step(clients, (client) => client.connection.sendDataChannel(), 'Created data channel');
        
        const client0Stats = fs.createWriteStream("get_stats_client_0.json");
        const client1Stats = fs.createWriteStream("get_stats_client_1.json");
        let intervalID = setInterval(async () => {
            const c0stats = await clients[0].connection.getStats();
            client0Stats.write(JSON.stringify(c0stats));
            const c1stats = await clients[1].connection.getStats();
            client1Stats.write(JSON.stringify(c1stats));
        }, 1000)

        await new Promise(r => setTimeout(r, 4*60000));

        clearInterval(intervalID);
        client0Stats.end();
        client1Stats.end();

        const recordingFile = fs.createWriteStream("media_recording.txt");
        recordingFile.write(await clients[1].connection.saveRecording());
        recordingFile.end();

    }, 5*60000);
}, 90000);

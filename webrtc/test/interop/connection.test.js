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
        await steps.step(clients, async (client) => {
            const stream = await client.mediaDevices.getUserMedia({ audio: true, video: true });
            return Promise.all(stream.getTracks().map(async track => {
                return client.connection.addTrack(track, stream);
            }));
        }, 'Acquired and added audio/video stream');
        const offerWithCandidates = await clients[0].connection.setLocalDescription();
        await clients[1].connection.setRemoteDescription(offerWithCandidates);
        const answerWithCandidates = await clients[1].connection.setLocalDescription();
        await clients[0].connection.setRemoteDescription(answerWithCandidates);

        await steps.step(drivers, (d) => steps.waitNVideosExist(d, 1), 'Video elements exist');
        await steps.step(drivers, steps.waitAllVideosHaveEnoughData, 'Video elements have enough data');
        await steps.step(clients, (client) => client.connection.sendDataChannel(), 'Created data channel');
    }, 30000);
}, 90000);

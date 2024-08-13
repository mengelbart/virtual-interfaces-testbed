// SPDX-FileCopyrightText: 2023 The Pion community <https://pion.ly>
// SPDX-License-Identifier: MIT

// pion-to-pion is an example of two pion instances communicating directly!
package main

import (
	"bytes"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"sync"
	"time"

	"github.com/pion/interceptor"
	"github.com/pion/interceptor/pkg/cc"
	"github.com/pion/interceptor/pkg/gcc"
	"github.com/pion/randutil"
	"github.com/pion/webrtc/v3"
	"github.com/pion/webrtc/v3/pkg/media"
	"github.com/pion/webrtc/v3/pkg/media/ivfreader"
)

const (
	lowBitrate = 300_000
	medBitrate = 1_000_000
	highBitrate = 2_500_000

	ivfHeaderSize = 32
)

func signalCandidate(addr string, c *webrtc.ICECandidate) error {
	payload := []byte(c.ToJSON().Candidate)
	resp, err := http.Post(fmt.Sprintf("http://%s/candidate", addr), "application/json; charset=utf-8", bytes.NewReader(payload)) //nolint:noctx
	if err != nil {
		return err
	}
	log.Printf("sent candidate %v", c)
	return resp.Body.Close()
}

func main() { //nolint:gocognit
	offerAddr := flag.String("offer-address", ":50000", "Address that the Offer HTTP server is hosted on.")
	answerAddr := flag.String("answer-address", "127.0.0.1:60000", "Address that the Answer HTTP server is hosted on.")
	highRateFile :=flag.String("high", "high.ivf", "IVF file to read high bitrate video")
	medRateFile :=flag.String("med", "med.ivf", "IVF file to read medium bitrate video")
	lowRateFile :=flag.String("low", "low.ivf", "IVF file to read low bitrate video")
	flag.Parse()

	qualityLevels := []struct {
		fileName string
		bitrate  int
	}{
		{*lowRateFile, lowBitrate},
		{*medRateFile, medBitrate},
		{*highRateFile, highBitrate},
	}
	currentQuality := 0

	for _, level := range qualityLevels {
		_, err := os.Stat(level.fileName)
		if os.IsNotExist(err) {
			panic(fmt.Sprintf("File %s was not found", level.fileName))
		}
	}

	i := &interceptor.Registry{}
	m := &webrtc.MediaEngine{}
	if err := m.RegisterDefaultCodecs(); err != nil {
		panic(err)
	}

	congestionController, err := cc.NewInterceptor(func() (cc.BandwidthEstimator, error) {
		return gcc.NewSendSideBWE(gcc.SendSideBWEInitialBitrate(lowBitrate))
	})
	if err != nil {
		panic(err)
	}

	estimatorChan := make(chan cc.BandwidthEstimator, 1)
	congestionController.OnNewPeerConnection(func(id string, estimator cc.BandwidthEstimator) { //nolint: revive
		estimatorChan <- estimator
	})

	i.Add(congestionController)
	if err = webrtc.ConfigureTWCCHeaderExtensionSender(m, i); err != nil {
		panic(err)
	}

	if err = webrtc.RegisterDefaultInterceptors(m, i); err != nil {
		panic(err)
	}

	api:=webrtc.NewAPI(webrtc.WithInterceptorRegistry(i), webrtc.WithMediaEngine(m))

	var candidatesMux sync.Mutex
	pendingCandidates := make([]*webrtc.ICECandidate, 0)

	// Everything below is the Pion WebRTC API! Thanks for using it ❤️.

	// Prepare the configuration
	config := webrtc.Configuration{
		ICEServers: []webrtc.ICEServer{
			{
				URLs: []string{"stun:stun.l.google.com:19302"},
			},
		},
	}

	// Create a new RTCPeerConnection
	peerConnection, err := api.NewPeerConnection(config)
	if err != nil {
		panic(err)
	}
	defer func() {
		if cErr := peerConnection.Close(); cErr != nil {
			fmt.Printf("cannot close peerConnection: %v\n", cErr)
		}
	}()

	estimator := <-estimatorChan

	videoTrack, err := webrtc.NewTrackLocalStaticSample(webrtc.RTPCodecCapability{MimeType: webrtc.MimeTypeVP8}, "video", "pion")
	if err != nil {
		panic(err)
	}

	rtpSender, err := peerConnection.AddTrack(videoTrack)
	if err != nil {
		panic(err)
	}

	// When an ICE candidate is available send to the other Pion instance
	// the other Pion instance will add this candidate by calling AddICECandidate
	peerConnection.OnICECandidate(func(c *webrtc.ICECandidate) {
		log.Printf("offer candidate: %v", c)
		if c == nil {
			return
		}

		candidatesMux.Lock()
		defer candidatesMux.Unlock()

		desc := peerConnection.RemoteDescription()
		if desc == nil {
			pendingCandidates = append(pendingCandidates, c)
		} else if onICECandidateErr := signalCandidate(*answerAddr, c); onICECandidateErr != nil {
			panic(onICECandidateErr)
		}
	})

	// A HTTP handler that allows the other Pion instance to send us ICE candidates
	// This allows us to add ICE candidates faster, we don't have to wait for STUN or TURN
	// candidates which may be slower
	http.HandleFunc("/candidate", func(w http.ResponseWriter, r *http.Request) { //nolint: revive
		candidate, candidateErr := io.ReadAll(r.Body)
		if candidateErr != nil {
			panic(candidateErr)
		}
		if candidateErr := peerConnection.AddICECandidate(webrtc.ICECandidateInit{Candidate: string(candidate)}); candidateErr != nil {
			panic(candidateErr)
		}
	})

	// A HTTP handler that processes a SessionDescription given to us from the other Pion process
	http.HandleFunc("/sdp", func(w http.ResponseWriter, r *http.Request) { //nolint: revive
		sdp := webrtc.SessionDescription{}
		if sdpErr := json.NewDecoder(r.Body).Decode(&sdp); sdpErr != nil {
			panic(sdpErr)
		}

		if sdpErr := peerConnection.SetRemoteDescription(sdp); sdpErr != nil {
			panic(sdpErr)
		}

		candidatesMux.Lock()
		defer candidatesMux.Unlock()

		for _, c := range pendingCandidates {
			if onICECandidateErr := signalCandidate(*answerAddr, c); onICECandidateErr != nil {
				panic(onICECandidateErr)
			}
		}
	})
	// Start HTTP server that accepts requests from the answer process
	// nolint: gosec
	go func() { panic(http.ListenAndServe(*offerAddr, nil)) }()

	// Create a datachannel with label 'data'
	dataChannel, err := peerConnection.CreateDataChannel("data", nil)
	if err != nil {
		panic(err)
	}

	// Set the handler for Peer connection state
	// This will notify you when the peer has connected/disconnected
	peerConnection.OnConnectionStateChange(func(s webrtc.PeerConnectionState) {
		fmt.Printf("Peer Connection State has changed: %s\n", s.String())

		if s == webrtc.PeerConnectionStateFailed {
			// Wait until PeerConnection has had no network activity for 30 seconds or another failure. It may be reconnected using an ICE Restart.
			// Use webrtc.PeerConnectionStateDisconnected if you are interested in detecting faster timeout.
			// Note that the PeerConnection may come back from PeerConnectionStateDisconnected.
			fmt.Println("Peer Connection has gone to failed exiting")
			os.Exit(0)
		}

		if s == webrtc.PeerConnectionStateClosed {
			// PeerConnection was explicitly closed. This usually happens from a DTLS CloseNotify
			fmt.Println("Peer Connection has gone to closed exiting")
			os.Exit(0)
		}
	})

	// Register channel opening handling
	dataChannel.OnOpen(func() {
		fmt.Printf("Data channel '%s'-'%d' open. Random data will now be sent to any connected DataChannels\n", dataChannel.Label(), dataChannel.ID())

		sendData:=func(){
			message, sendTextErr := randutil.GenerateCryptoRandomString(10*1024, "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
			if sendTextErr != nil {
				panic(sendTextErr)
			}
			
			// Send the message as text
			// fmt.Printf("Sending '%v' bytes\n", len(message))
			if sendTextErr = dataChannel.SendText(message); sendTextErr != nil {
				panic(sendTextErr)
			}
		}
		sendData()
		dataChannel.SetBufferedAmountLowThreshold(1024)
		dataChannel.OnBufferedAmountLow(func ()  {
			sendData()
		})
	})

	// Register text message handling
	dataChannel.OnMessage(func(msg webrtc.DataChannelMessage) {
		fmt.Printf("Message from DataChannel '%s': '%s'\n", dataChannel.Label(), string(msg.Data))
	})

	// Create an offer to send to the other process
	offer, err := peerConnection.CreateOffer(nil)
	if err != nil {
		panic(err)
	}

	// Sets the LocalDescription, and starts our UDP listeners
	// Note: this will start the gathering of ICE candidates
	if err = peerConnection.SetLocalDescription(offer); err != nil {
		panic(err)
	}

	// Send our offer to the HTTP server listening in the other process
	payload, err := json.Marshal(offer)
	if err != nil {
		panic(err)
	}
	resp, err := http.Post(fmt.Sprintf("http://%s/sdp", *answerAddr), "application/json; charset=utf-8", bytes.NewReader(payload)) // nolint:noctx
	if err != nil {
		panic(err)
	} else if err := resp.Body.Close(); err != nil {
		panic(err)
	}


	go func() {
		rtcpBuf := make([]byte, 1500)
		for {
			if _, _, rtcpErr := rtpSender.Read(rtcpBuf); rtcpErr != nil {
				return
			}
		}
	}()

	file, err := os.Open(qualityLevels[currentQuality].fileName)
	if err != nil {
		panic(err)
	}

	ivf, header, err := ivfreader.NewWith(file)
	if err != nil {
		panic(err)
	}

	ticker := time.NewTicker(time.Millisecond * time.Duration((float32(header.TimebaseNumerator)/float32(header.TimebaseDenominator))*1000))
	defer ticker.Stop()
	frame := []byte{}
	frameHeader := &ivfreader.IVFFrameHeader{}
	currentTimestamp := uint64(0)

	switchQualityLevel := func(newQualityLevel int) {
		fmt.Printf("Switching from %s to %s \n", qualityLevels[currentQuality].fileName, qualityLevels[newQualityLevel].fileName)
		currentQuality = newQualityLevel
		ivf.ResetReader(setReaderFile(qualityLevels[currentQuality].fileName))
		for {
			if frame, frameHeader, err = ivf.ParseNextFrame(); err != nil {
				break
			} else if frameHeader.Timestamp >= currentTimestamp && frame[0]&0x1 == 0 {
				break
			}
		}
	}

	start:=time.Now()
	end:=start.Add(20*time.Second)
	for ; time.Now().Before(end); <-ticker.C {
		targetBitrate := estimator.GetTargetBitrate()
		switch {
		// If current quality level is below target bitrate drop to level below
		case currentQuality != 0 && targetBitrate < qualityLevels[currentQuality].bitrate:
			switchQualityLevel(currentQuality - 1)

			// If next quality level is above target bitrate move to next level
		case len(qualityLevels) > (currentQuality+1) && targetBitrate > qualityLevels[currentQuality+1].bitrate:
			switchQualityLevel(currentQuality + 1)

		// Adjust outbound bandwidth for probing
		default:
			frame, _, err = ivf.ParseNextFrame()
		}

		switch {
		// If we have reached the end of the file start again
		case errors.Is(err, io.EOF):
			ivf.ResetReader(setReaderFile(qualityLevels[currentQuality].fileName))

		// No error write the video frame
		case err == nil:
			currentTimestamp = frameHeader.Timestamp
			if err = videoTrack.WriteSample(media.Sample{Data: frame, Duration: time.Second}); err != nil {
				panic(err)
			}
		// Error besides io.EOF that we dont know how to handle
		default:
			panic(err)
		}
	}
}

func setReaderFile(filename string) func(_ int64) io.Reader {
	return func(_ int64) io.Reader {
		file, err := os.Open(filename) // nolint
		if err != nil {
			panic(err)
		}
		if _, err = file.Seek(ivfHeaderSize, io.SeekStart); err != nil {
			panic(err)
		}
		return file
	}
}
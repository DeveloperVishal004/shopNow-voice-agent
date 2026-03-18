import streamlit as st
import requests

API_BASE = "http://localhost:8000"
WS_BASE  = "ws://localhost:8000"

def show():
    st.title("Live Voice Call")
    st.markdown("Talk directly to Priya — ShopNow's AI support agent")
    st.markdown("---")

    if "call_id"   not in st.session_state:
        st.session_state.call_id   = None
    if "messages"  not in st.session_state:
        st.session_state.messages  = []
    if "escalated" not in st.session_state:
        st.session_state.escalated = False

    # ── pre call screen ──────────────────────────────────
    if not st.session_state.call_id:
        st.subheader("Ready to connect")
        phone = st.text_input("Your phone number", value="+919876543210")

        if st.button("Call ShopNow Support", type="primary"):
            response = requests.post(
                f"{API_BASE}/call/start",
                json={"customer_phone": phone}
            )
            if response.status_code == 200:
                st.session_state.call_id  = response.json()["call_id"]
                st.session_state.messages = []
                st.rerun()

    # ── active call screen ───────────────────────────────
    else:
        call_id = st.session_state.call_id

        col1, col2 = st.columns([4, 1])
        with col1:
            if st.session_state.escalated:
                st.error("Transferred to human agent")
            else:
                st.success("Connected to Priya — ShopNow Support")
        with col2:
            if st.button("Hang Up"):
                requests.post(
                    f"{API_BASE}/call/end",
                    json={"call_id": call_id, "outcome": "resolved"}
                )
                st.session_state.call_id   = None
                st.session_state.messages  = []
                st.session_state.escalated = False
                st.rerun()

        st.markdown("---")

        # escalation brief
        if st.session_state.escalated:
            brief = st.session_state.get("escalation_brief", {})
            if brief:
                st.subheader("Escalation brief")
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.metric("Customer", brief.get("customer_name", "Unknown"))
                with col_b:
                    st.metric("Intent",   brief.get("current_intent", "Unknown"))
                with col_c:
                    st.metric("Tone",     brief.get("recommended_tone", "empathetic"))
            return

        # conversation transcript
        for msg in st.session_state.messages:
            if msg["role"] == "customer":
                with st.chat_message("user"):
                    st.markdown(msg["text"])
                    if msg.get("sentiment"):
                        colors = {
                            "positive": "🟢",
                            "neutral":  "🔵",
                            "negative": "🟠",
                            "angry":    "🔴"
                        }
                        st.caption(
                            f"{colors.get(msg['sentiment'], '⚪')} {msg['sentiment']} "
                            f"| intent: {msg.get('intent', 'unknown')}"
                        )
            else:
                with st.chat_message("assistant", avatar="🎧"):
                    st.markdown(msg["text"])

        st.markdown("---")

        # inject the full call interface as HTML component
        ws_url = f"{WS_BASE}/ws/{call_id}"

        st.components.v1.html(f"""
<!DOCTYPE html>
<html>
<head>
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
    font-family: -apple-system, BlinkMacSystemFont, sans-serif;
    background: transparent;
    padding: 20px;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 16px;
}}
.phone {{
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 12px;
    padding: 24px;
    border-radius: 20px;
    border: 1px solid #e0e0e0;
    width: 100%;
    max-width: 360px;
    background: #fff;
}}
.avatar {{
    width: 64px; height: 64px;
    border-radius: 50%;
    background: linear-gradient(135deg, #667eea, #764ba2);
    display: flex; align-items: center; justify-content: center;
    font-size: 28px;
    color: white;
}}
.name {{
    font-size: 18px;
    font-weight: 600;
    color: #1a1a1a;
}}
.status {{
    font-size: 13px;
    color: #888;
    height: 20px;
    text-align: center;
}}
.status.listening {{ color: #27ae60; font-weight: 500; }}
.status.speaking  {{ color: #8e44ad; font-weight: 500; }}
.status.thinking  {{ color: #e67e22; font-weight: 500; }}
.status.error     {{ color: #e74c3c; }}

.visualizer {{
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 3px;
    height: 40px;
    width: 160px;
}}
.bar {{
    width: 3px;
    background: #667eea;
    border-radius: 2px;
    transition: height 0.08s ease;
    min-height: 3px;
}}

.controls {{
    display: flex;
    gap: 20px;
    align-items: center;
    margin-top: 8px;
}}
.btn-mic {{
    width: 64px; height: 64px;
    border-radius: 50%;
    border: none;
    background: #27ae60;
    color: white;
    font-size: 26px;
    cursor: pointer;
    transition: all 0.2s;
    display: flex; align-items: center; justify-content: center;
}}
.btn-mic.recording {{
    background: #e74c3c;
    animation: pulse 1.2s ease-in-out infinite;
}}
.btn-mic:disabled {{
    background: #bdc3c7;
    cursor: not-allowed;
}}
@keyframes pulse {{
    0%,100% {{ box-shadow: 0 0 0 0 rgba(231,76,60,0.35); }}
    50%      {{ box-shadow: 0 0 0 12px rgba(231,76,60,0); }}
}}

.log {{
    width: 100%;
    max-width: 360px;
    font-size: 12px;
    color: #666;
    max-height: 120px;
    overflow-y: auto;
    border: 1px solid #eee;
    border-radius: 8px;
    padding: 8px;
    background: #fafafa;
}}
.log-entry {{ margin-bottom: 4px; }}
.log-entry.customer {{ color: #2980b9; }}
.log-entry.agent    {{ color: #8e44ad; }}
.log-entry.system   {{ color: #888; font-style: italic; }}
</style>
</head>
<body>

<div class="phone">
    <div class="avatar">🎧</div>
    <div class="name">Priya</div>
    <div class="name" style="font-size:13px;font-weight:400;color:#888">ShopNow Support</div>
    <div class="status" id="status">Connecting...</div>

    <div class="visualizer" id="visualizer">
        {''.join([f'<div class="bar" id="b{i}" style="height:3px"></div>' for i in range(24)])}
    </div>

    <div class="controls">
        <button class="btn-mic" id="micBtn" onclick="toggleMic()" disabled>🎤</button>
    </div>
</div>

<div class="log" id="log"></div>

<script>
const WS_URL = "{ws_url}";

let ws            = null;
let audioCtx      = null;
let mediaStream   = null;
let processor     = null;
let analyser      = null;
let isRecording   = false;
let isAgentSpeaking = false;
let speechActive  = false;
let lastSpeechTs  = 0;

const SILENCE_THRESHOLD   = 0.012;
const SILENCE_HOLD_MS     = 800;
const MIN_UTTERANCE_MS    = 250;
let utteranceStartTs      = 0;

// audio playback
let pcmBuffer     = new Int16Array(0);
let playbackCtx   = null;
let nextStartTime = 0;

function log(msg, cls='system') {{
    const el  = document.getElementById('log');
    const div = document.createElement('div');
    div.className = 'log-entry ' + cls;
    div.textContent = msg;
    el.appendChild(div);
    el.scrollTop = el.scrollHeight;
}}

function setStatus(text, cls='') {{
    const el      = document.getElementById('status');
    el.textContent = text;
    el.className   = 'status ' + cls;
}}

// ── WebSocket ────────────────────────────────────────────
function connect() {{
    ws = new WebSocket(WS_URL);
    ws.binaryType = 'arraybuffer';

    ws.onopen = () => {{
        setStatus('Connected — tap mic once to enable auto listening', 'listening');
        document.getElementById('micBtn').disabled = false;
        log('Connected to ShopNow support');
        initPlaybackContext();
    }};

    ws.onmessage = (event) => {{
        // ── binary: raw PCM16 audio from agent ───────────
        if (event.data instanceof ArrayBuffer) {{
            if (event.data.byteLength === 0) return;
            appendAndPlay(event.data);
            isAgentSpeaking = true;
            setStatus('Priya is speaking...', 'speaking');
            return;
        }}

        // ── text: control/transcript messages ────────────
        try {{
            const msg = JSON.parse(event.data);

            if (msg.type === 'transcript') {{
                if (msg.role === 'customer') {{
                    log('You: ' + msg.text, 'customer');
                    setStatus('Processing...', 'thinking');
                }} else {{
                    log('Priya: ' + msg.text, 'agent');
                    // notify Streamlit to refresh transcript
                    window.parent.postMessage({{
                        type:      'shopnow_transcript',
                        role:      msg.role,
                        text:      msg.text,
                        intent:    msg.intent    || '',
                        sentiment: msg.sentiment || ''
                    }}, '*');
                }}
            }}

            else if (msg.type === 'escalation') {{
                log('Escalating to human agent...', 'system');
                setStatus('Transferring...', 'error');
                window.parent.postMessage({{
                    type:             'shopnow_escalation',
                    escalation_brief: msg.escalation_brief
                }}, '*');
            }}

            else if (msg.type === 'call_ended') {{
                setStatus('Call ended', '');
                log('Call ended');
            }}

            else if (msg.type === 'error') {{
                setStatus('Error: ' + msg.message, 'error');
                log('Error: ' + msg.message);
            }}

        }} catch(e) {{
            log('Parse error: ' + e.message);
        }}
    }};

    ws.onclose = () => {{
        setStatus('Disconnected', 'error');
        document.getElementById('micBtn').disabled = true;
        log('Connection closed');
    }};

    ws.onerror = () => {{
        setStatus('Connection failed', 'error');
        log('WebSocket error — check backend is running');
    }};
}}

// ── Mic Recording ────────────────────────────────────────
async function toggleMic() {{
    if (isRecording) {{
        stopMic();
    }} else {{
        await startMic();
    }}
}}

async function startMic() {{
    try {{
        mediaStream = await navigator.mediaDevices.getUserMedia({{
            audio: {{
                channelCount:     1,
                sampleRate:       24000,
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl:  true
            }}
        }});

        audioCtx  = new AudioContext({{ sampleRate: 24000 }});
        analyser  = audioCtx.createAnalyser();
        analyser.fftSize = 64;

        const source = audioCtx.createMediaStreamSource(mediaStream);
        processor    = audioCtx.createScriptProcessor(2048, 1, 1);

        source.connect(analyser);
        analyser.connect(processor);
        processor.connect(audioCtx.destination);

        processor.onaudioprocess = (e) => {{
            if (!isRecording || !ws || ws.readyState !== WebSocket.OPEN) return;
            const input  = e.inputBuffer.getChannelData(0);
            const rms    = computeRms(input);
            const now    = Date.now();

            // Skip sending mic frames while the agent is speaking to avoid feedback loops.
            if (isAgentSpeaking) return;

            if (rms > SILENCE_THRESHOLD) {{
                if (!speechActive) {{
                    speechActive     = true;
                    utteranceStartTs = now;
                    setStatus('Listening...', 'listening');
                }}
                lastSpeechTs = now;
            }} else if (speechActive) {{
                const silenceMs   = now - lastSpeechTs;
                const utteranceMs = now - utteranceStartTs;
                if (silenceMs >= SILENCE_HOLD_MS && utteranceMs >= MIN_UTTERANCE_MS) {{
                    speechActive = false;
                    commitCurrentUtterance();
                }}
            }}

            const pcm16  = float32ToPCM16(input);
            ws.send(pcm16.buffer);
        }};

        isRecording = true;
        speechActive = false;
        lastSpeechTs = 0;
        utteranceStartTs = 0;
        const btn   = document.getElementById('micBtn');
        btn.classList.add('recording');
        btn.textContent = '🔇';
        setStatus('Auto listening enabled', 'listening');
        log('Mic enabled with automatic silence detection');
        visualize();

    }} catch(e) {{
        setStatus('Mic error: ' + e.message, 'error');
        log('Mic access failed: ' + e.message);
    }}
}}

function stopMic() {{
    const hadPendingSpeech = speechActive;
    isRecording = false;
    speechActive = false;
    lastSpeechTs = 0;
    utteranceStartTs = 0;

    if (processor)    {{ processor.disconnect();    processor    = null; }}
    if (analyser)     {{ analyser.disconnect();     analyser     = null; }}
    if (audioCtx)     {{ audioCtx.close();          audioCtx     = null; }}
    if (mediaStream)  {{
        mediaStream.getTracks().forEach(t => t.stop());
        mediaStream = null;
    }}

    const btn       = document.getElementById('micBtn');
    btn.classList.remove('recording');
    btn.textContent = '🎤';
    setStatus('Mic muted', '');
    log('Mic muted');

    // reset visualizer bars
    for (let i = 0; i < 24; i++) {{
        document.getElementById('b' + i).style.height = '3px';
    }}

    if (hadPendingSpeech) {{
        commitCurrentUtterance();
    }}

}}

function commitCurrentUtterance() {{
    if (!ws || ws.readyState !== WebSocket.OPEN) return;
    ws.send(JSON.stringify({{ type: "commit_audio" }}));
    setStatus('Processing...', 'thinking');
    log('Silence detected — sending your turn to Priya');
}}

// ── Audio Playback (PCM16 streaming) ────────────────────
function initPlaybackContext() {{
    playbackCtx   = new AudioContext({{ sampleRate: 24000 }});
    nextStartTime = playbackCtx.currentTime;
}}

function appendAndPlay(arrayBuffer) {{
    if (!playbackCtx) initPlaybackContext();

    const pcm16   = new Int16Array(arrayBuffer);
    const float32 = new Float32Array(pcm16.length);

    for (let i = 0; i < pcm16.length; i++) {{
        float32[i] = pcm16[i] / 32768.0;
    }}

    const buffer  = playbackCtx.createBuffer(1, float32.length, 24000);
    buffer.copyToChannel(float32, 0);

    const source  = playbackCtx.createBufferSource();
    source.buffer = buffer;
    source.connect(playbackCtx.destination);

    // schedule sequentially so chunks play without gaps
    const startAt = Math.max(nextStartTime, playbackCtx.currentTime + 0.01);
    source.start(startAt);
    nextStartTime = startAt + buffer.duration;

    source.onended = () => {{
        // check if this was the last chunk
        if (nextStartTime <= playbackCtx.currentTime + 0.05) {{
            isAgentSpeaking = false;
            if (isRecording) {{
                setStatus('Listening...', 'listening');
            }} else {{
                setStatus('Connected — tap mic to enable auto listening', 'listening');
            }}
        }}
    }};
}}

// ── Visualizer ───────────────────────────────────────────
function visualize() {{
    if (!isRecording || !analyser) return;

    const data = new Uint8Array(analyser.frequencyBinCount);
    analyser.getByteFrequencyData(data);

    for (let i = 0; i < 24; i++) {{
        const val    = data[Math.floor(i * data.length / 24)] || 0;
        const height = Math.max(3, (val / 255) * 36);
        document.getElementById('b' + i).style.height = height + 'px';
    }}

    requestAnimationFrame(visualize);
}}

// ── Helpers ──────────────────────────────────────────────
function float32ToPCM16(float32) {{
    const pcm16 = new Int16Array(float32.length);
    for (let i = 0; i < float32.length; i++) {{
        const clamped = Math.max(-1, Math.min(1, float32[i]));
        pcm16[i]      = clamped < 0 ? clamped * 0x8000 : clamped * 0x7FFF;
    }}
    return pcm16;
}}

function computeRms(float32) {{
    let sumSquares = 0;
    for (let i = 0; i < float32.length; i++) {{
        sumSquares += float32[i] * float32[i];
    }}
    return Math.sqrt(sumSquares / float32.length);
}}

// ── Start ────────────────────────────────────────────────
connect();
</script>

</body>
</html>
""", height=420)

        # refresh button to pull latest transcript
        col_r1, col_r2 = st.columns([3, 1])
        with col_r2:
            if st.button("Refresh transcript"):
                resp = requests.get(f"{API_BASE}/call/session/{call_id}")
                if resp.status_code == 200:
                    turns = resp.json().get("turns", [])
                    st.session_state.messages = [
                        {{
                            "role":      t["role"],
                            "text":      t["text"],
                            "intent":    t.get("intent", ""),
                            "sentiment": t.get("sentiment", "")
                        }}
                        for t in turns
                    ]
                    st.rerun()
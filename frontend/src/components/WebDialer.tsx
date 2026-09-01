"use client";

import { useEffect, useRef, useState, useCallback } from "react";

type CallStatus = "idle" | "connecting" | "active" | "ending";

interface TranscriptEntry {
  role: "assistant" | "user";
  text: string;
  time: string;
}

const VAPI_PUBLIC_KEY = process.env.NEXT_PUBLIC_VAPI_PUBLIC_KEY ?? "";
const ASSISTANT_ID    = process.env.NEXT_PUBLIC_VAPI_ASSISTANT_ID ?? "";

// Module-level singleton to maintain a single WebRTC connection
// eslint-disable-next-line @typescript-eslint/no-explicit-any
let _vapi: any = null;
let _ready = false;

function ts() {
  return new Date().toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" });
}

export default function WebDialer() {
  const [status,     setStatus]     = useState<CallStatus>("idle");
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [transcript, setTranscript] = useState<TranscriptEntry[]>([]);
  const [error,      setError]      = useState<string | null>(null);
  const [uiReady,    setUiReady]    = useState(_ready); // syncs with singleton
  const observerRef = useRef<MutationObserver | null>(null);
  const transcriptEndRef = useRef<HTMLDivElement>(null);

  // ── Load SDK once + attach listeners ──────────────────────────────────────
  useEffect(() => {
    if (!VAPI_PUBLIC_KEY) {
      setTimeout(() => setError("Missing NEXT_PUBLIC_VAPI_PUBLIC_KEY in frontend/.env.local"), 0);
      return;
    }

    if (_ready && _vapi) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setUiReady(true);
      return;
    }

    let cancelled = false;

    import("@vapi-ai/web").then(({ default: Vapi }) => {
      if (cancelled || _vapi) return; // guard against double-init

      _vapi = new Vapi(VAPI_PUBLIC_KEY);

      _vapi.on("call-start", () => {
        setStatus("active");
        setError(null);

        const obs = new MutationObserver((mutations) => {
          for (const m of mutations) {
            m.addedNodes.forEach((node) => {
              const els: HTMLAudioElement[] = [];
              if (node instanceof HTMLAudioElement) els.push(node);
              else if (node instanceof Element)
                els.push(...Array.from(node.querySelectorAll<HTMLAudioElement>("audio")));
              els.forEach((el) => {
                el.muted = false;
                el.volume = 1;
                el.play().catch(() => {});
              });
            });
          }
        });
        obs.observe(document.body, { childList: true, subtree: true });
        observerRef.current = obs;

        document
          .querySelectorAll<HTMLAudioElement>("audio")
          .forEach((el) => { el.muted = false; el.volume = 1; el.play().catch(() => {}); });
      });

      _vapi.on("call-end", () => {
        setStatus("idle");
        setIsSpeaking(false);
        observerRef.current?.disconnect();
        observerRef.current = null;
      });

      _vapi.on("speech-start", () => setIsSpeaking(true));
      _vapi.on("speech-end",   () => setIsSpeaking(false));

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      _vapi.on("message", (msg: any) => {
        if (
          msg.type === "transcript" &&
          msg.transcriptType === "final" &&
          msg.role &&
          msg.transcript?.trim()
        ) {
          setTranscript((prev) => [
            ...prev,
            { role: msg.role, text: msg.transcript.trim(), time: ts() },
          ]);
        }
      });

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      _vapi.on("error", (err: any) => {
        console.error("[Vapi error]", JSON.stringify(err));
        const msg: string =
          (typeof err?.message        === "string" && err.message)        ||
          (typeof err?.error?.message === "string" && err.error.message)  ||
          (typeof err?.error?.errorMsg === "string" && err.error.errorMsg)||
          (typeof err?.error?.error?.msg === "string" && err.error.error.msg) ||
          "Call error — check the browser Console for details.";

        if (msg.includes("Meeting has ended")) {
          setStatus("idle");
          observerRef.current?.disconnect();
          observerRef.current = null;
          return;
        }

        setError(msg);
        setStatus("idle");
        observerRef.current?.disconnect();
        observerRef.current = null;
      });

      _ready = true;
      if (!cancelled) setUiReady(true);
    });

    return () => { cancelled = true; };
  }, []);

  // Auto-scroll transcript
  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [transcript]);

  // ── Call handlers ──────────────────────────────────────────────────────────
  const startCall = useCallback(async () => {
    if (!_vapi || !ASSISTANT_ID) {
      setError("Vapi not ready — ensure keys are set in frontend/.env.local");
      return;
    }
    setError(null);
    setStatus("connecting");
    setTranscript([]);

    try {
      await _vapi.start(ASSISTANT_ID);
      _vapi.setMuted(false);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Unknown error starting call");
      setStatus("idle");
    }
  }, []);

  const stopCall = useCallback(() => {
    setStatus("ending");
    _vapi?.stop();
  }, []);

  const isActive = status === "active";
  const isBusy   = status === "connecting" || status === "ending";

  // ── UI ─────────────────────────────────────────────────────────────────────
  return (
    <div className="glass-panel rounded-2xl overflow-hidden flex flex-col h-[600px]">
      <div className="p-6 flex flex-col gap-5 h-full">

        {/* Header */}
        <div className="flex items-center justify-between flex-shrink-0">
          <div>
            <p className="text-base font-semibold text-white">Talk to Alex</p>
            <p className="text-xs text-white/40">
              {uiReady ? "Browser microphone ready" : "Loading voice agent…"}
            </p>
          </div>
          {isActive && (
            <div className="flex items-center gap-1.5 text-xs text-emerald-400">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse inline-block" />
              {isSpeaking ? "Alex speaking…" : "Listening…"}
            </div>
          )}
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-3 text-xs text-red-400 flex-shrink-0">
            ⚠️ {error}
          </div>
        )}

        {/* Call button */}
        <div className="flex justify-center py-2 flex-shrink-0">
          <button
            id="vapi-call-button"
            onClick={isActive ? stopCall : startCall}
            disabled={isBusy || !uiReady}
            aria-label={isActive ? "End call" : "Start call"}
            className={[
              "relative w-20 h-20 rounded-full transition-all duration-300",
              "focus:outline-none focus:ring-2 focus:ring-offset-2",
              isActive
                ? "bg-red-500/20 border-2 border-red-500 text-red-400 hover:bg-red-500/30 focus:ring-red-500"
                : "bg-indigo-500/20 border-2 border-indigo-500 text-indigo-300 hover:bg-indigo-500/30 focus:ring-indigo-500",
              (isBusy || !uiReady)
                ? "opacity-50 cursor-not-allowed"
                : "cursor-pointer hover:scale-105 active:scale-95",
            ].join(" ")}
          >
            {isActive && (
              <>
                <span className="absolute inset-0 rounded-full bg-red-500/15 animate-ping" />
                <span className="absolute inset-[-10px] rounded-full border border-red-500/20 animate-pulse" />
              </>
            )}
            {isBusy && (
              <span className="absolute inset-0 rounded-full border-t-2 border-indigo-400 animate-spin" />
            )}
            <span className="relative z-10 text-2xl">
              {isActive ? "⏹" : isBusy ? "" : "🎤"}
            </span>
          </button>
        </div>

        <p className="text-center text-xs text-white/50 flex-shrink-0">
          {!uiReady                && "Initialising…"}
          {uiReady && status === "idle"      && "Click to start a call"}
          {status === "connecting"           && "Connecting to Alex…"}
          {status === "active"               && "Call active — click ⏹ to hang up"}
          {status === "ending"               && "Ending call…"}
        </p>

        {/* Transcript */}
        <div className="flex flex-col gap-2 flex-grow overflow-hidden mt-2">
          <div className="flex items-center justify-between flex-shrink-0">
            <p className="text-xs font-semibold text-white/40 uppercase tracking-wider">
              Live Transcript
            </p>
            {transcript.length > 0 && (
              <button
                onClick={() => setTranscript([])}
                className="text-xs text-white/30 hover:text-white/60 transition-colors"
              >
                Clear
              </button>
            )}
          </div>

          <div className="bg-black/30 rounded-xl p-3 flex-grow overflow-y-auto flex flex-col gap-3">
            {transcript.length === 0 ? (
              <p className="text-xs text-white/20 text-center mt-8">
                {isActive
                  ? "Waiting for speech…"
                  : "Transcript will appear here during the call."}
              </p>
            ) : (
              transcript.map((entry, i) => (
                <div
                  key={i}
                  className={`flex gap-2 ${
                    entry.role === "assistant" ? "flex-row" : "flex-row-reverse"
                  }`}
                >
                  <div
                    className={`w-6 h-6 rounded-full flex-shrink-0 flex items-center justify-center text-xs ${
                      entry.role === "assistant"
                        ? "bg-indigo-500/30 text-indigo-300"
                        : "bg-emerald-500/30 text-emerald-300"
                    }`}
                  >
                    {entry.role === "assistant" ? "A" : "U"}
                  </div>
                  <div
                    className={`flex flex-col gap-0.5 max-w-[80%] ${
                      entry.role !== "assistant" ? "items-end" : ""
                    }`}
                  >
                    <div
                      className={`px-3 py-2 rounded-2xl text-sm leading-relaxed ${
                        entry.role === "assistant"
                          ? "bg-indigo-500/15 text-indigo-100 rounded-tl-sm"
                          : "bg-emerald-500/15 text-emerald-100 rounded-tr-sm"
                      }`}
                    >
                      {entry.text}
                    </div>
                    <span className="text-[10px] text-white/20 px-1">
                      {entry.time}
                    </span>
                  </div>
                </div>
              ))
            )}
            <div ref={transcriptEndRef} />
          </div>
        </div>
      </div>
    </div>
  );
}

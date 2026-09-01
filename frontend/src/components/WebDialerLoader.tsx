"use client";

import dynamic from "next/dynamic";

const WebDialer = dynamic(() => import("./WebDialer"), {
  ssr: false,
  loading: () => (
    <div className="glass-panel rounded-2xl h-[600px] flex items-center justify-center">
      <p className="text-white/30 text-sm">Loading voice agent…</p>
    </div>
  ),
});

export default function WebDialerLoader() {
  return <WebDialer />;
}

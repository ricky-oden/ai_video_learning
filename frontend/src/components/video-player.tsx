"use client";

import { useRef, useState } from "react";

import { seekVideo } from "@/lib/video/seek";

export function VideoPlayer({ src, title }: { src: string; title: string }) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [seconds, setSeconds] = useState(2);
  return (
    <section aria-labelledby="player-title">
      <h2 id="player-title">動画プレイヤー</h2>
      <video
        ref={videoRef}
        controls
        preload="metadata"
        aria-label={`${title}の動画`}
      >
        <source src={src} type="video/mp4" />
      </video>
      <div className="seek-controls">
        <label>
          再生位置（秒）
          <input
            type="number"
            min="0"
            value={seconds}
            onChange={(event) => setSeconds(Number(event.target.value))}
          />
        </label>
        <button
          type="button"
          onClick={() => {
            if (videoRef.current) seekVideo(videoRef.current, seconds * 1000);
          }}
        >
          指定位置へ移動
        </button>
      </div>
    </section>
  );
}

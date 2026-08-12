export function millisecondsToSeconds(milliseconds: number): number {
  return Math.max(0, milliseconds) / 1000;
}

export function seekVideo(
  video: Pick<HTMLVideoElement, "currentTime" | "duration">,
  milliseconds: number,
): number {
  const requested = millisecondsToSeconds(milliseconds);
  const duration = Number.isFinite(video.duration) ? video.duration : requested;
  const target = Math.min(requested, duration);
  video.currentTime = target;
  return target;
}

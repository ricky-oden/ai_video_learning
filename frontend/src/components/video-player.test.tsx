import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { millisecondsToSeconds, seekVideo } from "@/lib/video/seek";

import { VideoPlayer } from "./video-player";

describe("video seeking", () => {
  it("converts and clamps a requested playback position", () => {
    const video = { currentTime: 0, duration: 5 };
    expect(millisecondsToSeconds(2500)).toBe(2.5);
    expect(millisecondsToSeconds(-100)).toBe(0);
    expect(seekVideo(video, 9000)).toBe(5);
    expect(video.currentTime).toBe(5);
  });

  it("renders the local video and seek control", () => {
    const { container } = render(
      <VideoPlayer src="/media/demo-hair-technique.mp4" title="demo" />,
    );
    const video = screen.getByLabelText("demoの動画") as HTMLVideoElement;
    Object.defineProperty(video, "duration", { value: 6, configurable: true });
    fireEvent.click(screen.getByRole("button", { name: "指定位置へ移動" }));
    expect(video.currentTime).toBe(2);
    expect(container.querySelector("source")).toHaveAttribute(
      "src",
      "/media/demo-hair-technique.mp4",
    );
  });

  it("seeks to a citation position after metadata loads", () => {
    render(
      <VideoPlayer
        src="/media/demo-hair-technique.mp4"
        title="citation demo"
        initialStartMs={2400}
      />,
    );
    const video = screen.getByLabelText(
      "citation demoの動画",
    ) as HTMLVideoElement;
    Object.defineProperty(video, "duration", { value: 6, configurable: true });
    fireEvent.loadedMetadata(video);
    expect(video.currentTime).toBe(2.4);
  });
});

import { ImageResponse } from "next/og";

export const alt = "DevFocus - 开发者聚焦";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";
export const dynamic = "force-static";

export default function Image() {
  const date = new Date().toISOString().slice(0, 10);
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          background: "#f5f3fa",
          color: "#1a1530",
        }}
      >
        <div style={{ display: "flex", fontSize: 108, fontWeight: 700, letterSpacing: -2 }}>
          <span>Dev</span>
          <span style={{ color: "#6a5fc1" }}>Focus</span>
        </div>
        <div style={{ display: "flex", marginTop: 28, fontSize: 36, color: "#4a4560" }}>
          开发者聚焦 · Daily Tech Digest for Developers
        </div>
        <div
          style={{
            display: "flex",
            marginTop: 56,
            padding: "10px 28px",
            borderRadius: 999,
            background: "#ede9f5",
            fontSize: 24,
            color: "#6a5fc1",
          }}
        >
          {date}
        </div>
      </div>
    ),
    { ...size }
  );
}

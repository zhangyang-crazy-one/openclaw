import { registerRoot, Composition, AbsoluteFill } from "remotion";

const MyComponent = () => {
  return (
    <AbsoluteFill
      style={{ backgroundColor: "#0f0f23", justifyContent: "center", alignItems: "center" }}
    >
      <div style={{ textAlign: "center" }}>
        <h1 style={{ color: "white", fontSize: 80, margin: 0 }}>Hello World!</h1>
        <p style={{ color: "#00d4ff", fontSize: 40, marginTop: 20 }}>OpenClaw AI Agent</p>
        <p style={{ color: "#888888", fontSize: 24, marginTop: 40 }}>Powered by Remotion</p>
      </div>
    </AbsoluteFill>
  );
};

registerRoot(() => (
  <Composition
    id="HelloWorld"
    component={MyComponent}
    durationInFrames={60}
    fps={30}
    width={1080}
    height={1080}
  />
));

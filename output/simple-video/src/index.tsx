import { registerRoot } from "remotion";
import { AbsoluteFill, Text } from "remotion";

const HelloWorld = () => {
  return (
    <AbsoluteFill
      style={{ backgroundColor: "#1a1a2e", justifyContent: "center", alignItems: "center" }}
    >
      <Text style={{ fontSize: 80, color: "white", fontWeight: "bold" }}>Hello World!</Text>
      <Text style={{ fontSize: 40, color: "#4cc9f0", marginTop: 20 }}>Welcome to Remotion</Text>
    </AbsoluteFill>
  );
};

registerRoot(HelloWorld);

export default HelloWorld;

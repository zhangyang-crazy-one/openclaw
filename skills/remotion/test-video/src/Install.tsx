import { useCurrentFrame } from "remotion";

export const Install: React.FC = () => {
  const frame = useCurrentFrame();
  const progress = frame / 120;
  
  return (
    <div style={{
      background: "linear-gradient(135deg, #0f0f23 0%, #1a1a2e 100%)",
      width: 1080,
      height: 1080,
      color: "white",
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center"
    }}>
      <div style={{ 
        fontSize: 55, 
        fontWeight: "bold", 
        color: "#4ade80", 
        marginBottom: 40,
        opacity: Math.min(1, progress)
      }}>
        🚀 快速开始
      </div>
      
      <div style={{ 
        background: "#1e1e3f", 
        padding: 28, 
        borderRadius: 12, 
        fontSize: 26,
        fontFamily: "monospace",
        opacity: Math.max(0, progress - 0.2)
      }}>
        npx remotion new my-video
      </div>
      
      <div style={{ fontSize: 28, marginTop: 45, color: "#888", opacity: Math.max(0, progress - 0.4) }}>
        或使用在线平台
      </div>
      
      <div style={{ 
        background: "#1e1e3f", 
        padding: 20, 
        borderRadius: 12, 
        fontSize: 22,
        marginTop: 18,
        color: "#60a5fa",
        opacity: Math.max(0, progress - 0.6)
      }}>
        302.AI / Vercel / Netlify
      </div>
    </div>
  );
};

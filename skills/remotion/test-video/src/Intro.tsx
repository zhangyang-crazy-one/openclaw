import { useCurrentFrame } from "remotion";

export const Intro: React.FC = () => {
  const frame = useCurrentFrame();
  const progress = frame / 90;
  
  return (
    <div style={{
      background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
      width: 1080,
      height: 1080,
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      color: "white"
    }}>
      <div style={{ 
        fontSize: 100 * Math.min(1, progress * 2), 
        opacity: Math.min(1, progress * 2)
      }}>
        🎬
      </div>
      <div style={{ 
        fontSize: 70, 
        fontWeight: "bold", 
        marginTop: 20,
        opacity: progress
      }}>
        Remotion
      </div>
      <div style={{ 
        fontSize: 35, 
        marginTop: 15, 
        color: "#ffd700",
        opacity: Math.max(0, progress - 0.3)
      }}>
        Best Practices 技能
      </div>
    </div>
  );
};

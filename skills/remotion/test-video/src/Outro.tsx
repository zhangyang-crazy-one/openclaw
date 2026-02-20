import { useCurrentFrame } from "remotion";

export const Outro: React.FC = () => {
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
        fontSize: 70 * Math.min(1, progress * 1.5), 
        fontWeight: "bold",
        opacity: Math.min(1, progress)
      }}>
        🎉 开始创作!
      </div>
      <div style={{ 
        fontSize: 32, 
        marginTop: 25, 
        color: "#ffd700",
        opacity: Math.max(0, progress - 0.2)
      }}>
        用代码定义视频
      </div>
      <div style={{ 
        fontSize: 24, 
        marginTop: 50, 
        color: "#ccc",
        opacity: Math.max(0, progress - 0.4)
      }}>
        技能位置: /skills/remotion
      </div>
    </div>
  );
};

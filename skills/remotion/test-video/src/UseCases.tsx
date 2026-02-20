import { useCurrentFrame } from "remotion";

const useCases = [
  { emoji: "📺", title: "营销视频" },
  { emoji: "🎓", title: "教育内容" },
  { emoji: "📱", title: "社交媒体" },
  { emoji: "📊", title: "数据报告" },
  { emoji: "🎮", title: "游戏内容" },
  { emoji: "🎤", title: "播客视频" }
];

export const UseCases: React.FC = () => {
  const frame = useCurrentFrame();
  
  return (
    <div style={{
      background: "#1a1a2e",
      width: 1080,
      height: 1080,
      color: "white",
      padding: 40
    }}>
      <div style={{ 
        fontSize: 55, 
        fontWeight: "bold", 
        color: "#f472b6", 
        marginBottom: 40, 
        textAlign: "center",
        opacity: Math.min(1, frame / 30)
      }}>
        📋 使用场景
      </div>
      
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
        {useCases.map((item, i) => {
          const delay = 30 + i * 20;
          const opacity = Math.max(0, Math.min(1, (frame - delay) / 30));
          
          return (
            <div key={i} style={{
              background: "#2d2d4a",
              padding: 20,
              borderRadius: 15,
              textAlign: "center",
              opacity: opacity,
              transform: `scale(${0.5 + opacity * 0.5})`
            }}>
              <div style={{ fontSize: 40 }}>{item.emoji}</div>
              <div style={{ fontSize: 24, fontWeight: "bold", marginTop: 8 }}>{item.title}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

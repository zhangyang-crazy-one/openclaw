import { useCurrentFrame } from "remotion";

const features = [
  { emoji: "🎨", title: "动画制作" },
  { emoji: "📝", title: "组件化" },
  { emoji: "🎬", title: "视频编辑" },
  { emoji: "🔊", title: "音频处理" },
  { emoji: "📊", title: "数据可视化" },
  { emoji: "✨", title: "字幕同步" },
  { emoji: "📱", title: "社交媒体" },
  { emoji: "🌐", title: "跨平台" }
];

export const Features: React.FC = () => {
  const frame = useCurrentFrame();
  
  return (
    <div style={{
      background: "linear-gradient(180deg, #0f0f23 0%, #1a1a2e 100%)",
      width: 1080,
      height: 1080,
      color: "white",
      padding: 40
    }}>
      <div style={{ 
        fontSize: 55, 
        fontWeight: "bold", 
        color: "#4ade80", 
        marginBottom: 40, 
        textAlign: "center",
        opacity: Math.min(1, frame / 30)
      }}>
        ✨ 核心功能
      </div>
      
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 25 }}>
        {features.map((f, i) => {
          const delay = 20 + i * 15;
          const opacity = Math.max(0, Math.min(1, (frame - delay) / 30));
          
          return (
            <div key={i} style={{
              background: "#2d2d4a",
              padding: 20,
              borderRadius: 15,
              opacity: opacity,
              transform: `translateX(${(1 - opacity) * 30}px)`
            }}>
              <div style={{ fontSize: 35 }}>{f.emoji}</div>
              <div style={{ fontSize: 24, fontWeight: "bold", marginTop: 5 }}>{f.title}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

import { useCurrentFrame } from "remotion";

const steps = [
  { emoji: "💬", title: "描述需求", color: "#4ade80" },
  { emoji: "🤖", title: "AI生成代码", color: "#60a5fa" },
  { emoji: "🎬", title: "渲染视频", color: "#f472b6" }
];

export const HowItWorks: React.FC = () => {
  const frame = useCurrentFrame();
  
  return (
    <div style={{
      background: "linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)",
      width: 1080,
      height: 1080,
      color: "white",
      padding: 40,
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center"
    }}>
      <div style={{ 
        fontSize: 55, 
        fontWeight: "bold", 
        color: "#60a5fa", 
        marginBottom: 50,
        opacity: Math.min(1, frame / 30)
      }}>
        🔄 工作流程
      </div>
      
      <div style={{ display: "flex", alignItems: "center", gap: 25 }}>
        {steps.map((step, i) => {
          const delay = 30 + i * 35;
          const opacity = Math.max(0, Math.min(1, (frame - delay) / 30));
          
          return (
            <div key={i} style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              opacity: opacity
            }}>
              <div style={{
                background: step.color,
                padding: 25,
                borderRadius: 18,
                opacity: opacity
              }}>
                <div style={{ fontSize: 45 }}>{step.emoji}</div>
              </div>
              <div style={{ fontSize: 22, fontWeight: "bold", marginTop: 12 }}>{step.title}</div>
              
              {i < 2 && (
                <div style={{ fontSize: 35, color: "#888", marginTop: 25 }}>→</div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

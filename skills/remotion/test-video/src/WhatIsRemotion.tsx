import { useCurrentFrame } from "remotion";

export const WhatIsRemotion: React.FC = () => {
  const frame = useCurrentFrame();
  const progress = frame / 180;
  
  return (
    <div style={{
      background: "#1a1a2e",
      width: 1080,
      height: 1080,
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      color: "white",
      padding: 60
    }}>
      <div style={{ 
        fontSize: 55, 
        fontWeight: "bold", 
        color: "#667eea", 
        marginBottom: 50,
        opacity: progress
      }}>
        什么是 Remotion?
      </div>
      
      <div style={{ 
        fontSize: 38, 
        textAlign: "center", 
        lineHeight: 1.6,
        opacity: Math.max(0, progress - 0.2)
      }}>
        用 React 代码创建视频
      </div>
      
      <div style={{ 
        fontSize: 32, 
        marginTop: 40, 
        color: "#4ade80",
        opacity: Math.max(0, progress - 0.4)
      }}>
        自然语言 → React 代码 → MP4视频
      </div>
    </div>
  );
};

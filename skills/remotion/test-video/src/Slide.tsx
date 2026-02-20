import { useCurrentFrame, useVideoConfig, spring } from "remotion";
import { Audio } from "remotion";
import bgm from "../public/bgm.mp3";

export const Slide: React.FC<{ imageIndex: number; wish: string }> = ({ imageIndex, wish }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  
  const fadeIn = Math.min(1, frame / 30);
  const fadeOut = Math.max(0, 1 - (frame - 150) / 30);
  const opacity = fadeIn * fadeOut;
  
  const bounce = spring({ frame: Math.min(frame, 30), fps, config: { damping: 10 } });
  
  const images = ["bg1.png", "bg2.png"];
  
  return (
    <>
      {/* 背景音乐 */}
      <Audio src={bgm} volume={0.4} />
      
      <div style={{
        width: 1080,
        height: 1920,
        position: "relative",
        overflow: "hidden",
        background: imageIndex === 0 ? "linear-gradient(135deg, #8B0000 0%, #FFD700 100%)" :
                    "linear-gradient(135deg, #1a1a2e 0%, #8B0000 100%)"
      }}>
        {/* 背景图片 */}
        <img 
          src={images[imageIndex]} 
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
            position: "absolute",
            top: 0,
            left: 0,
            opacity: 0.5
          }} 
        />
        
        {/* 黑色遮罩 */}
        <div style={{
          position: "absolute",
          top: 0,
          left: 0,
          width: "100%",
          height: "100%",
          background: "rgba(0,0,0,0.3)",
          opacity: fadeIn
        }} />
        
        {/* 祝福文字 */}
        <div style={{
          position: "absolute",
          top: "35%",
          left: 0,
          right: 0,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          opacity
        }}>
          <div style={{
            fontSize: 100 * bounce,
            fontWeight: "bold",
            color: "#FFD700",
            textShadow: "0 0 30px rgba(255,215,0,0.8), 0 0 60px rgba(255,215,0,0.4)",
            transform: `scale(${bounce})`
          }}>
            {wish}
          </div>
          
          <div style={{
            fontSize: 36,
            marginTop: 40,
            color: "#fff",
            textShadow: "0 2px 10px rgba(0,0,0,0.5)",
            opacity: Math.max(0, fadeIn - 0.3)
          }}>
            ✨ 新年吉祥 ✨
          </div>
        </div>
        
        {/* 装饰 */}
        <div style={{ position: "absolute", top: 100, left: 50, fontSize: 60, opacity: fadeIn * 0.8 }}>🧧</div>
        <div style={{ position: "absolute", top: 150, right: 80, fontSize: 50, opacity: fadeIn * 0.7 }}>🎊</div>
        <div style={{ position: "absolute", bottom: 200, left: 80, fontSize: 55, opacity: fadeIn * 0.6 }}>🏮</div>
        <div style={{ position: "absolute", bottom: 180, right: 60, fontSize: 45, opacity: fadeIn * 0.7 }}>🎉</div>
        
        {/* 底部 */}
        <div style={{
          position: "absolute",
          bottom: 50,
          left: 0,
          right: 0,
          textAlign: "center",
          color: "rgba(255,255,255,0.7)",
          fontSize: 22,
          opacity: fadeIn
        }}>
          🤖 AI祝福视频 - Remotion + SiliconFlow
        </div>
      </div>
    </>
  );
};

import { useCurrentFrame, useVideoConfig, spring } from "remotion";
import { Audio } from "remotion";
import bgm from "../public/bgm.mp3";

const scenes = [
  {
    title: "🤔 AI也会'失忆'？",
    content: "当对话变长，AI突然忘记之前说过的话...",
    sub: "这是AI领域的热门话题",
    bg: "linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)"
  },
  {
    title: "📊 问题的本质",
    content: "上下文窗口有限\n→ 信息超载\n→ 早期记忆被遗忘",
    sub: "就像人类的短期记忆一样",
    bg: "linear-gradient(135deg, #0f0c29 0%, #302b63 100%)"
  },
  {
    title: "💡 方案一：记忆分层",
    content: "将信息分类存储\n• 核心事实 → 长期记忆\n• 上下文细节 → 短期记忆\n• 临时信息 → 实时处理",
    sub: "类似人脑的记忆分区",
    bg: "linear-gradient(135deg, #200122 0%, #6f0000 100%)"
  },
  {
    title: "💡 方案二：摘要压缩",
    content: "定期将长对话压缩为摘要\n• 保留关键信息\n• 删除冗余细节\n• 保持语义连贯",
    sub: "类似做会议记录",
    bg: "linear-gradient(135deg, #000046 0%, #1CB5E0 100%)"
  },
  {
    title: "💡 方案三：外部向量库",
    content: "将重要信息存入向量数据库\n• Milvus / Pinecone / Weaviate\n• 支持语义检索\n• 突破上下文限制",
    sub: "AI的'外接硬盘'",
    bg: "linear-gradient(135deg, #134E5E 0%, #71B280 100%)"
  },
  {
    title: "🛠️ 方案四：知识图谱",
    content: "用图结构管理关系\n• 实体-关系-实体\n• 支持推理查询\n• Neo4j / Graphiti",
    sub: "让AI记住'谁是谁'",
    bg: "linear-gradient(135deg, #4b134f 0%, #c94b4b 100%)"
  },
  {
    title: "🔮 未来方向",
    content: "多模态记忆 + 持续学习\n让AI像人类一样\n形成长期知识体系",
    sub: "Moltbook讨论热度: 2256👍",
    bg: "linear-gradient(135deg, #2C3E50 0%, #4CA1AF 100%)"
  }
];

export const MemoryVideo = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  
  const totalFrames = 420; // 14秒 (7个场景)
  const sceneCount = scenes.length;
  const framesPerScene = totalFrames / sceneCount;
  
  const sceneIndex = Math.floor(frame / framesPerScene);
  const safeIndex = Math.min(sceneIndex, sceneCount - 1);
  const scene = scenes[safeIndex];
  
  const sceneProgress = (frame % framesPerScene) / framesPerScene;
  const fadeIn = Math.min(1, sceneProgress * 20);
  const fadeOut = Math.max(0, 1 - (sceneProgress - 0.85) * 20);
  const opacity = fadeIn * fadeOut;
  
  const bounce = spring({ frame: Math.min(frame % 25, 20), fps, config: { damping: 14 } });

  return (
    <>
      <Audio src={bgm} volume={0.25} />
      
      <div style={{
        width: 1080,
        height: 1920,
        background: scene.bg,
        position: "relative",
        overflow: "hidden"
      }}>
        {/* 场景标题 */}
        <div style={{
          position: "absolute",
          top: "12%",
          left: 0,
          right: 0,
          textAlign: "center",
          opacity
        }}>
          <div style={{
            fontSize: 70 * bounce,
            fontWeight: "bold",
            color: "#fff",
            textShadow: "0 4px 20px rgba(0,0,0,0.5)",
            transform: `scale(${bounce})`
          }}>
            {scene.title}
          </div>
        </div>
        
        {/* 主内容 */}
        <div style={{
          position: "absolute",
          top: "30%",
          left: 0,
          right: 0,
          textAlign: "center",
          opacity: Math.max(0, fadeIn - 0.2),
          padding: "0 40px"
        }}>
          <div style={{
            fontSize: 32,
            color: "rgba(255,255,255,0.95)",
            lineHeight: 1.9,
            whiteSpace: "pre-line",
            textShadow: "0 2px 10px rgba(0,0,0,0.3)"
          }}>
            {scene.content}
          </div>
        </div>
        
        {/* 副标题/说明 */}
        <div style={{
          position: "absolute",
          top: "72%",
          left: 0,
          right: 0,
          textAlign: "center",
          opacity: Math.max(0, fadeIn - 0.4)
        }}>
          <div style={{
            fontSize: 26,
            color: "rgba(255,255,255,0.6)",
            fontStyle: "italic"
          }}>
            {scene.sub}
          </div>
        </div>
        
        {/* 页码指示 */}
        <div style={{
          position: "absolute",
          top: 80,
          left: 0,
          right: 0,
          display: "flex",
          justifyContent: "center",
          gap: 12,
          opacity: fadeIn * 0.7
        }}>
          {scenes.map((_, i) => (
            <div style={{
              width: i === safeIndex ? 30 : 10,
              height: 10,
              borderRadius: 5,
              background: i === safeIndex ? "#FFD700" : "rgba(255,255,255,0.3)",
              transition: "all 0.3s"
            }} />
          ))}
        </div>
        
        {/* 来源 */}
        <div style={{
          position: "absolute",
          bottom: 40,
          left: 0,
          right: 0,
          textAlign: "center",
          color: "rgba(255,255,255,0.5)",
          fontSize: 20,
          opacity: fadeIn
        }}>
          📱 Moltbook 热门讨论 | AI记忆管理方案
        </div>
      </div>
    </>
  );
};

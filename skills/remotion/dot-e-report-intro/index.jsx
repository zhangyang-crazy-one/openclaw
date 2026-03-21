import {
  Composition,
  Sequence,
  spring,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

const TitleSlide = ({ title }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const opacity = interpolate(frame, [0, 30], [0, 1], { extrapolateRight: "clamp" });
  const scale = spring({ frame, fps });

  return (
    <div
      style={{
        flex: 1,
        backgroundColor: "#1a1a2e",
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        padding: 40,
      }}
    >
      <div
        style={{
          color: "#fff",
          fontSize: 72,
          fontWeight: "bold",
          textAlign: "center",
          opacity,
          transform: `scale(${scale})`,
        }}
      >
        {title}
      </div>
      <div
        style={{
          color: "#ffc107",
          fontSize: 36,
          marginTop: 30,
          opacity,
        }}
      >
        作战试验鉴定年度报告
      </div>
      <div
        style={{
          color: "#888",
          fontSize: 24,
          marginTop: 60,
          opacity,
        }}
      >
        FY2024 年度报告介绍
      </div>
    </div>
  );
};

const ChapterSlide = ({ chapterNum, chapterTitle, content }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const opacity = interpolate(frame, [0, 30], [0, 1], { extrapolateRight: "clamp" });
  const slideUp = interpolate(frame, [0, 45], [80, 0], { extrapolateRight: "clamp" });

  return (
    <div
      style={{
        flex: 1,
        backgroundColor: "#16213e",
        display: "flex",
        flexDirection: "column",
        padding: 60,
        transform: `translateY(${slideUp}px)`,
        opacity,
      }}
    >
      <div
        style={{
          color: "#ffc107",
          fontSize: 32,
          marginBottom: 30,
        }}
      >
        第 {chapterNum} 章
      </div>
      <div
        style={{
          color: "#fff",
          fontSize: 56,
          fontWeight: "bold",
          marginBottom: 40,
        }}
      >
        {chapterTitle}
      </div>
      <div
        style={{
          color: "#ccc",
          fontSize: 28,
          lineHeight: 1.8,
        }}
      >
        {content}
      </div>
    </div>
  );
};

const ClosingSlide = () => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 30], [0, 1], { extrapolateRight: "clamp" });

  return (
    <div
      style={{
        flex: 1,
        backgroundColor: "#0f3460",
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        padding: 40,
        opacity,
      }}
    >
      <div
        style={{
          color: "#ffc107",
          fontSize: 48,
          fontWeight: "bold",
          marginBottom: 30,
        }}
      >
        敬请期待更多章节
      </div>
      <div
        style={{
          color: "#888",
          fontSize: 24,
        }}
      >
        陆军/海军/空军项目 | 导弹防御系统
      </div>
    </div>
  );
};

export const DOTEIntro = () => {
  const fps = 30;

  return (
    <div style={{ width: "100%", height: "100%" }}>
      <Sequence from={0} durationInFrames={5 * fps}>
        <TitleSlide title="DOT&E FY2024" />
      </Sequence>

      <Sequence from={5 * fps} durationInFrames={13 * fps}>
        <ChapterSlide
          chapterNum="1"
          chapterTitle="引言 (Introduction)"
          content="局长致辞、战略政策与指导、五大战略支柱"
        />
      </Sequence>

      <Sequence from={18 * fps} durationInFrames={12 * fps}>
        <ChapterSlide chapterNum="2" chapterTitle="任务 (Mission)" content="DOT&E的四大核心任务" />
      </Sequence>

      <Sequence from={30 * fps} durationInFrames={15 * fps}>
        <ChapterSlide
          chapterNum="3"
          chapterTitle="执行摘要 (Executive Summary)"
          content="25个新系统监督、29份独立评估报告"
        />
      </Sequence>

      <Sequence from={45 * fps} durationInFrames={10 * fps}>
        <ChapterSlide chapterNum="4" chapterTitle="战略实施计划 (I-Plan)" content="五大战略支柱" />
      </Sequence>

      <Sequence from={55 * fps} durationInFrames={3 * fps}>
        <ClosingSlide />
      </Sequence>
    </div>
  );
};

export const RemotionVideo = () => {
  return (
    <Composition
      id="DOTE-Report-Intro"
      component={DOTEIntro}
      durationInFrames={58 * 30}
      fps={30}
      width={1920}
      height={1080}
    />
  );
};

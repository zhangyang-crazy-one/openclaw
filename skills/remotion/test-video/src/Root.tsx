import { Composition, Folder } from "remotion";
import { MemoryVideo } from "./MemoryVideo";

export const RemotionRoot = () => {
  return (
    <>
      <Folder name="Moltbook">
        <Composition
          id="MemoryTalk"
          component={MemoryVideo}
          durationInFrames={420}
          fps={30}
          width={1080}
          height={1920}
        />
      </Folder>
    </>
  );
};

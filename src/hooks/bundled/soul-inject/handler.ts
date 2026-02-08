/**
 * Soul-Inject Hook
 *
 * Injects SOUL.md content into the system prompt on every message
 * to ensure the agent's personality is always reinforced.
 *
 * This addresses the problem where bootstrap files (like SOUL.md)
 * are only loaded once at the start of a run, and may be forgotten
 * as the context window fills up.
 */

import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import type { OpenClawConfig } from "../../../config/config.js";
import type { HookHandler } from "../../hooks.js";
import { resolveAgentIdFromSessionKey } from "../../../routing/session-key.js";
import { resolveHookConfig } from "../../config.js";

/**

 * Read SOUL.md content from workspace
 */
async function readSoulFile(workspaceDir: string): Promise<string | null> {
  const soulPath = path.join(workspaceDir, "SOUL.md");
  try {
    return await fs.readFile(soulPath, "utf-8");
  } catch {
    return null;
  }
}

/**
 * Hook handler for soul-inject
 *
 * This hook is designed to be triggered on every message.
 * However, the current OpenClaw hook system only supports:
 * - command events (/new, /reset, etc.)
 * - agent:bootstrap (run start)
 * - session lifecycle events
 *
 * To fully enable per-message injection, the core would need
 * to trigger a new event type like 'agent:turn' or 'message:start'.
 *
 * Current workaround: This hook injects SOUL.md into the system prompt
 * during bootstrap, and can be manually triggered via command.
 */
const soulInjectHandler: HookHandler = async (event) => {
  // Only process bootstrap events (run start)
  // Full per-message support requires core modification
  if (event.type !== "agent" || event.action !== "bootstrap") {
    return;
  }

  try {
    const context = event.context as Record<string, unknown> | undefined;
    const cfg = context?.cfg as OpenClawConfig | undefined;
    const workspaceDir = context?.workspaceDir as string | undefined;

    if (!workspaceDir) {
      console.log("[soul-inject] No workspaceDir in context, skipping");
      return;
    }

    // Read SOUL.md content
    const soulContent = await readSoulFile(workspaceDir);
    if (!soulContent) {
      console.log("[soul-inject] No SOUL.md found in workspace");
      return;
    }

    console.log(`[soul-inject] SOUL.md loaded (${soulContent.length} chars)`);

    // Check if this hook should inject on bootstrap
    const hookConfig = resolveHookConfig(cfg, "soul-inject");
    const injectOnBootstrap = hookConfig?.injectOnBootstrap ?? true;

    if (injectOnBootstrap) {
      // The bootstrap process will include SOUL.md in contextFiles
      // This ensures it's always at the start of the system prompt
      console.log("[soul-inject] Will inject SOUL.md on bootstrap");

      // Store SOUL.md content in context for use by bootstrap process
      const bootstrapFiles = context.bootstrapFiles as Array<{ name: string; content?: string }> | undefined;
      if (bootstrapFiles) {
        // Ensure SOUL.md is at the beginning
        const soulFileIndex = bootstrapFiles.findIndex((f) => f.name === "SOUL.md");
        if (soulFileIndex === -1) {
          // Add SOUL.md to bootstrap files
          bootstrapFiles.unshift({
            name: "SOUL.md",
            content: soulContent,
          });
          console.log("[soul-inject] SOUL.md prepended to bootstrap files");
        }
      }
    }
  } catch (err) {
    console.error(
      "[soul-inject] Failed to inject SOUL.md:",
      err instanceof Error ? err.message : String(err),
    );
  }
};

export default soulInjectHandler;

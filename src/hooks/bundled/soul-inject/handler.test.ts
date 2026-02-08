/**
 * Soul-Inject Hook Tests
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import path from "node:path";
import fs from "node:fs/promises";
import defaultHandler from "./handler.js";

describe("soul-inject hook", () => {
  const testWorkspace = "/tmp/test-workspace-soul-inject";
  const testSoulContent = `# SOUL.md - Test

This is a test SOUL.md file.

## Core Truths
- Be genuinely helpful
- Have opinions
`;

  beforeEach(async () => {
    // Create test workspace with SOUL.md
    await fs.mkdir(testWorkspace, { recursive: true });
    await fs.writeFile(path.join(testWorkspace, "SOUL.md"), testSoulContent);
  });

  afterEach(async () => {
    // Cleanup
    try {
      await fs.rm(testWorkspace, { recursive: true, force: true });
    } catch {
      // Ignore cleanup errors
    }
  });

  it("should read SOUL.md from workspace", async () => {
    const event = {
      type: "agent",
      action: "bootstrap",
      sessionKey: "agent:main:test",
      context: {
        workspaceDir: testWorkspace,
        bootstrapFiles: [{ name: "OTHER.md", content: "Other file" }],
      },
      timestamp: new Date(),
      messages: [],
    };

    // Mock resolveHookConfig
    vi.doUnmock("../../config.js");
    vi.doMock("../../config.js", () => ({
      resolveHookConfig: () => ({ injectOnBootstrap: true }),
    }));

    await defaultHandler(event);

    // SOUL.md should be prepended
    const files = event.context.bootstrapFiles as Array<{ name: string; content?: string }>;
    expect(files[0].name).toBe("SOUL.md");
    expect(files[0].content).toBe(testSoulContent);
  });

  it("should not modify context for non-bootstrap events", async () => {
    const event = {
      type: "command",
      action: "new",
      sessionKey: "agent:main:test",
      context: {
        workspaceDir: testWorkspace,
        bootstrapFiles: [{ name: "OTHER.md", content: "Other file" }],
      },
      timestamp: new Date(),
      messages: [],
    };

    await defaultHandler(event);

    // Context should be unchanged
    const files = event.context.bootstrapFiles as Array<{ name: string }>;
    expect(files.length).toBe(1);
    expect(files[0].name).toBe("OTHER.md");
  });
});

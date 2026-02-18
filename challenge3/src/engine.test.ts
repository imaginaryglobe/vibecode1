import { describe, it, expect } from "vitest";
import {
  RNG, createInitialBoard, reshuffle,
  findMatches, mergeMatchGroups,
  isAdjacent, swap, isSwapValid, hasAnyValidMove,
  resolveBoard, scoreEvents,
} from "./engine";
import type { Board } from "./engine";
import { GameConfig } from "./gameConfig";

// ── Helpers ───────────────────────────────────────────────────────────────────

/** 8×8 board filled with alternating types (usually no matches), then overrides applied. */
function makeBoard(overrides: Record<string, number> = {}, fill = -1): Board {
  const board: Board = Array.from({ length: 8 }, (_, r) =>
    Array.from({ length: 8 }, (_, c) => ({
      type: fill === -1 ? (r * 8 + c) % GameConfig.candyTypes : fill,
    }))
  );
  for (const [key, type] of Object.entries(overrides)) {
    const [r, c] = key.split(",").map(Number);
    board[r][c].type = type;
  }
  return board;
}

const B = 10; // GameConfig.basePerPiece

// ── findMatches ───────────────────────────────────────────────────────────────

describe("findMatches", () => {
  it("detects a horizontal run of 3", () => {
    // Force row 0 cols 0-2 to be the same type (something that doesn't appear in makeBoard row 0)
    const board = makeBoard({ "0,0": 5, "0,1": 5, "0,2": 5 });
    const m = findMatches(board);
    const found = m.find(g => g.cells.every(c => c.r === 0) && g.length === 3);
    expect(found).toBeDefined();
  });

  it("detects a vertical run of 3", () => {
    const board = makeBoard({ "0,7": 5, "1,7": 5, "2,7": 5 });
    const m = findMatches(board);
    const found = m.find(g => g.cells.every(c => c.c === 7) && g.length === 3);
    expect(found).toBeDefined();
  });

  it("detects a run of 5", () => {
    const board = makeBoard({ "3,0": 4, "3,1": 4, "3,2": 4, "3,3": 4, "3,4": 4 });
    const m = findMatches(board);
    const found = m.find(g => g.length === 5);
    expect(found).toBeDefined();
  });

  it("returns empty when no matches", () => {
    // Strict alternating board: no 3-in-a-row possible
    const board: Board = Array.from({ length: 8 }, (_, r) =>
      Array.from({ length: 8 }, (_, c) => ({ type: (r + c) % 2 }))
    );
    // A 2-color board like checkerboard won't have run >= 3 in any row/col
    // because values alternate 0,1,0,1...
    expect(findMatches(board)).toHaveLength(0);
  });
});

// ── mergeMatchGroups ──────────────────────────────────────────────────────────

describe("mergeMatchGroups", () => {
  it("returns empty for no input", () => {
    expect(mergeMatchGroups([])).toHaveLength(0);
  });

  it("merges a T-shape (overlapping row + col run) into one group", () => {
    // type 5 at: row 4 cols 2-4 (horizontal run of 3)  +  col 3 rows 2-4 (vertical run of 3)
    // They share cell (4,3)
    const rawGroups = [
      { length: 3, cells: [{ r: 4, c: 2 }, { r: 4, c: 3 }, { r: 4, c: 4 }] },
      { length: 3, cells: [{ r: 2, c: 3 }, { r: 3, c: 3 }, { r: 4, c: 3 }] },
    ];
    const merged = mergeMatchGroups(rawGroups);
    expect(merged).toHaveLength(1);
    // 3 + 3 - 1 shared cell = 5 unique cells
    expect(merged[0].cells).toHaveLength(5);
    expect(merged[0].length).toBe(3);
  });

  it("keeps non-overlapping groups separate", () => {
    const rawGroups = [
      { length: 3, cells: [{ r: 0, c: 0 }, { r: 0, c: 1 }, { r: 0, c: 2 }] },
      { length: 3, cells: [{ r: 7, c: 5 }, { r: 7, c: 6 }, { r: 7, c: 7 }] },
    ];
    expect(mergeMatchGroups(rawGroups)).toHaveLength(2);
  });
});

// ── createInitialBoard ────────────────────────────────────────────────────────

describe("createInitialBoard", () => {
  it("is 8×8", () => {
    const b = createInitialBoard(new RNG(1));
    expect(b).toHaveLength(8);
    b.forEach(row => expect(row).toHaveLength(8));
  });

  it("has no matches at spawn (10 seeds)", () => {
    for (let s = 0; s < 10; s++) {
      const b = createInitialBoard(new RNG(s));
      expect(findMatches(b)).toHaveLength(0);
    }
  });

  it("has at least one valid move (10 seeds)", () => {
    for (let s = 0; s < 10; s++) {
      expect(hasAnyValidMove(createInitialBoard(new RNG(s)))).toBe(true);
    }
  });

  it("all types in range", () => {
    const b = createInitialBoard(new RNG(42));
    b.flat().forEach(cell => {
      expect(cell.type).toBeGreaterThanOrEqual(0);
      expect(cell.type).toBeLessThan(GameConfig.candyTypes);
    });
  });
});

// ── reshuffle ─────────────────────────────────────────────────────────────────

describe("reshuffle", () => {
  it("result has no matches", () => {
    const b = createInitialBoard(new RNG(7));
    const rb = reshuffle(b.map(r => r.map(c => ({ ...c }))), new RNG(99));
    expect(findMatches(rb)).toHaveLength(0);
  });

  it("result has a valid move", () => {
    const b = createInitialBoard(new RNG(7));
    const rb = reshuffle(b.map(r => r.map(c => ({ ...c }))), new RNG(99));
    expect(hasAnyValidMove(rb)).toBe(true);
  });

  it("preserves total piece count", () => {
    const b = createInitialBoard(new RNG(5));
    const before = b.flat().reduce((acc, { type }) => {
      acc[type] = (acc[type] ?? 0) + 1; return acc;
    }, {} as Record<number, number>);
    const rb = reshuffle(b.map(r => r.map(c => ({ ...c }))), new RNG(55));
    const after = rb.flat().reduce((acc, { type }) => {
      acc[type] = (acc[type] ?? 0) + 1; return acc;
    }, {} as Record<number, number>);
    expect(Object.values(before).reduce((a, b) => a + b, 0))
      .toBe(Object.values(after).reduce((a, b) => a + b, 0));
  });
});

// ── Swap helpers ──────────────────────────────────────────────────────────────

describe("isAdjacent", () => {
  it("true for orthogonal neighbours", () => {
    expect(isAdjacent({ r: 3, c: 3 }, { r: 3, c: 4 })).toBe(true);
    expect(isAdjacent({ r: 3, c: 3 }, { r: 4, c: 3 })).toBe(true);
    expect(isAdjacent({ r: 3, c: 3 }, { r: 3, c: 2 })).toBe(true);
    expect(isAdjacent({ r: 3, c: 3 }, { r: 2, c: 3 })).toBe(true);
  });
  it("false for diagonal / 2-away / same", () => {
    expect(isAdjacent({ r: 0, c: 0 }, { r: 1, c: 1 })).toBe(false);
    expect(isAdjacent({ r: 0, c: 0 }, { r: 0, c: 2 })).toBe(false);
    expect(isAdjacent({ r: 2, c: 2 }, { r: 2, c: 2 })).toBe(false);
  });
});

describe("swap (in-place)", () => {
  it("exchanges two cells", () => {
    const b: Board = [[{ type: 0 }, { type: 1 }], [{ type: 2 }, { type: 3 }]];
    swap(b, { r: 0, c: 0 }, { r: 0, c: 1 });
    expect(b[0][0].type).toBe(1);
    expect(b[0][1].type).toBe(0);
  });
});

describe("isSwapValid", () => {
  it("false for non-adjacent cells", () => {
    const b = createInitialBoard(new RNG(1));
    expect(isSwapValid(b, { r: 0, c: 0 }, { r: 0, c: 2 })).toBe(false);
  });

  it("does not mutate the board", () => {
    const b = createInitialBoard(new RNG(2));
    const snap = b.map(r => r.map(c => c.type));
    isSwapValid(b, { r: 0, c: 0 }, { r: 0, c: 1 });
    b.forEach((row, r) => row.forEach((cell, c) => {
      expect(cell.type).toBe(snap[r][c]);
    }));
  });

  it("true when swap creates a horizontal match", () => {
    // row 0: [X, 1, 1, 1, ...] — swapping (0,0)↔(0,1) would put X at col1, but
    // we set it up so the swap puts a matching type at col 0:
    // row 0: col 0 = type 3, cols 1-3 = type 3→ already a match; let's make col 0 = type 0
    // and do a swap that puts the type-3 piece next to two other type-3 pieces.
    const b = makeBoard({
      "0,0": 0,
      "0,1": 3, "0,2": 3, "0,3": 3, // three type-3 in a row at cols 1-3
    });
    // Swapping (0,1) left puts type-3 at col 0 → cols 0,2,3 don't match (not contiguous)
    // Better: swap (0,0) with (0,1) → col0=3, col1=0, col2=3, col3=3 — no run
    // Let's use a direct known case: set col 0 row 0 to type 3, cols 2,3 to type 3 — swap(0,1)↔(0,2)
    const b2 = makeBoard({
      "0,0": 3, "0,1": 0,
      "0,2": 3, "0,3": 3,
    });
    // Swap (0,1)↔(0,0): col0=0, col1=3; plus col2,col3=3 → run at cols 1,2,3 ✓
    expect(isSwapValid(b2, { r: 0, c: 0 }, { r: 0, c: 1 })).toBe(true);
  });
});

// ── resolveBoard ──────────────────────────────────────────────────────────────

describe("resolveBoard", () => {
  it("board is stable after resolution", () => {
    // Fill entire board with type 0 → massive matches → resolves completely
    const b: Board = Array.from({ length: 8 }, () =>
      Array.from({ length: 8 }, () => ({ type: 0 }))
    );
    resolveBoard(b, new RNG(11));
    expect(findMatches(b)).toHaveLength(0);
  });

  it("cascades >= 1 when matches existed", () => {
    const b: Board = Array.from({ length: 8 }, () =>
      Array.from({ length: 8 }, () => ({ type: 0 }))
    );
    const { cascades } = resolveBoard(b, new RNG(22));
    expect(cascades).toBeGreaterThanOrEqual(1);
  });

  it("stable board → 0 cascades, 0 events", () => {
    // Strictly alternating — 0 runs
    const b: Board = Array.from({ length: 8 }, (_, r) =>
      Array.from({ length: 8 }, (_, c) => ({ type: (r + c) % 2 }))
    );
    const { cascades, events } = resolveBoard(b, new RNG(1));
    expect(cascades).toBe(0);
    expect(events).toHaveLength(0);
  });

  it("spawned types stay in valid range", () => {
    const b: Board = Array.from({ length: 8 }, () =>
      Array.from({ length: 8 }, () => ({ type: 0 }))
    );
    resolveBoard(b, new RNG(77));
    b.flat().forEach(cell => {
      expect(cell.type).toBeGreaterThanOrEqual(0);
      expect(cell.type).toBeLessThan(GameConfig.candyTypes);
    });
  });
});

// ── scoreEvents ───────────────────────────────────────────────────────────────

describe("scoreEvents — moves mode (simple, no multiplier)", () => {
  it("3-match: score = base × cleared, 0 extra moves", () => {
    const r = scoreEvents("moves", [{ cleared: 3, matchLen: 3 }]);
    expect(r.score).toBe(B * 3);
    expect(r.extraMoves).toBe(0);
  });

  it("4-match: +1 extra move  (4-3=1)", () => {
    const r = scoreEvents("moves", [{ cleared: 4, matchLen: 4 }]);
    expect(r.score).toBe(B * 4);
    expect(r.extraMoves).toBe(1);
  });

  it("5-match: +2 extra moves (5-3=2)", () => {
    const r = scoreEvents("moves", [{ cleared: 5, matchLen: 5 }]);
    expect(r.extraMoves).toBe(2);
  });

  it("6-match: +3 extra moves (6-3=3)", () => {
    const r = scoreEvents("moves", [{ cleared: 6, matchLen: 6 }]);
    expect(r.extraMoves).toBe(3);
  });

  it("sums extra moves across multiple events in same cascade step", () => {
    const r = scoreEvents("moves", [
      { cleared: 4, matchLen: 4 },
      { cleared: 4, matchLen: 4 },
    ]);
    expect(r.extraMoves).toBe(2); // 1+1
    expect(r.score).toBe(B * 4 + B * 4);
  });

  it("no extra moves for matchLen < 4", () => {
    const r = scoreEvents("moves", [{ cleared: 3, matchLen: 3 }, { cleared: 3, matchLen: 3 }]);
    expect(r.extraMoves).toBe(0);
  });
});

describe("scoreEvents — time mode (multipliers)", () => {
  it("3-match: multiplier 1  (3-2=1)  → base×cleared×1", () => {
    const r = scoreEvents("time", [{ cleared: 3, matchLen: 3 }]);
    expect(r.score).toBe(B * 3 * 1);
    expect(r.extraMoves).toBe(0);
  });

  it("4-match: multiplier 2 → base×cleared×2", () => {
    expect(scoreEvents("time", [{ cleared: 4, matchLen: 4 }]).score).toBe(B * 4 * 2);
  });

  it("5-match: multiplier 3", () => {
    expect(scoreEvents("time", [{ cleared: 5, matchLen: 5 }]).score).toBe(B * 5 * 3);
  });

  it("6-match: multiplier 4", () => {
    expect(scoreEvents("time", [{ cleared: 6, matchLen: 6 }]).score).toBe(B * 6 * 4);
  });

  it("sums correctly across multiple events", () => {
    const r = scoreEvents("time", [
      { cleared: 3, matchLen: 3 }, // 10*3*1 = 30
      { cleared: 4, matchLen: 4 }, // 10*4*2 = 80
    ]);
    expect(r.score).toBe(110);
  });
});

describe("GameConfig formulas", () => {
  it("multiplier = matchLen - 2", () => {
    [3, 4, 5, 6].forEach(n => expect(GameConfig.multiplier(n)).toBe(n - 2));
  });
  it("extraMoves = matchLen - 3", () => {
    [4, 5, 6].forEach(n => expect(GameConfig.extraMoves(n)).toBe(n - 3));
  });
});

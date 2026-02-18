import { GameConfig } from "./gameConfig";
import type { GameMode } from "./gameConfig";

// ── Types ─────────────────────────────────────────────────────────────────────

export type Coord = { r: number; c: number };
export type CandyType = number; // 0..N-1
export type Cell = { type: CandyType };
export type Board = Cell[][];

export type MatchGroup = { cells: Coord[]; length: number };

export type MatchEvent = {
  cleared: number;  // unique cells in this group
  matchLen: number; // longest run in the group
};

export type ResolveResult = {
  cascades: number;
  events: MatchEvent[];
};

export type SwapResult = {
  cascades: number;
  events: MatchEvent[];
  score: number;
  extraMoves: number;
  reshuffled: boolean;
};

// ── RNG (seeded LCG) ──────────────────────────────────────────────────────────

export class RNG {
  private seed: number;
  constructor(seed = Date.now()) { this.seed = seed >>> 0; }
  next(): number {
    this.seed = (Math.imul(1664525, this.seed) + 1013904223) >>> 0;
    return this.seed / 0x100000000;
  }
  int(max: number): number { return Math.floor(this.next() * max); }
}

// ── Board helpers ─────────────────────────────────────────────────────────────

function emptyBoard(): Board {
  const s = GameConfig.gridSize;
  return Array.from({ length: s }, () =>
    Array.from({ length: s }, () => ({ type: 0 }))
  );
}

export function createInitialBoard(rng: RNG): Board {
  while (true) {
    const board = emptyBoard();
    for (let r = 0; r < GameConfig.gridSize; r++)
      for (let c = 0; c < GameConfig.gridSize; c++)
        board[r][c].type = rng.int(GameConfig.candyTypes);
    if (findMatches(board).length === 0 && hasAnyValidMove(board))
      return board;
  }
}

export function reshuffle(board: Board, rng: RNG): Board {
  // Collect all piece types (preserves counts)
  const flat = board.flat().map(c => c.type);
  while (true) {
    // Fisher-Yates shuffle
    for (let i = flat.length - 1; i > 0; i--) {
      const j = rng.int(i + 1);
      [flat[i], flat[j]] = [flat[j], flat[i]];
    }
    const nb = emptyBoard();
    let idx = 0;
    for (let r = 0; r < GameConfig.gridSize; r++)
      for (let c = 0; c < GameConfig.gridSize; c++)
        nb[r][c].type = flat[idx++];
    if (findMatches(nb).length === 0 && hasAnyValidMove(nb))
      return nb;
  }
}

// ── Match detection ───────────────────────────────────────────────────────────

/** Raw runs of 3+ same-type cells (before merging overlapping shapes). */
function findRawRuns(board: Board): MatchGroup[] {
  const groups: MatchGroup[] = [];
  const size = GameConfig.gridSize;

  // Horizontal runs
  for (let r = 0; r < size; r++) {
    let run = 1;
    for (let c = 1; c <= size; c++) {
      if (c < size && board[r][c].type === board[r][c - 1].type) {
        run++;
      } else {
        if (run >= 3)
          groups.push({
            length: run,
            cells: Array.from({ length: run }, (_, i) => ({ r, c: c - 1 - i })),
          });
        run = 1;
      }
    }
  }

  // Vertical runs
  for (let c = 0; c < size; c++) {
    let run = 1;
    for (let r = 1; r <= size; r++) {
      if (r < size && board[r][c].type === board[r - 1][c].type) {
        run++;
      } else {
        if (run >= 3)
          groups.push({
            length: run,
            cells: Array.from({ length: run }, (_, i) => ({ r: r - 1 - i, c })),
          });
        run = 1;
      }
    }
  }

  return groups;
}

/**
 * Merges overlapping raw runs (T/L/cross shapes) into unified groups via
 * Union-Find. Each merged group becomes one match event for scoring.
 */
export function mergeMatchGroups(rawGroups: MatchGroup[]): MatchGroup[] {
  if (!rawGroups.length) return [];

  const parent = rawGroups.map((_, i) => i);
  function find(i: number): number {
    return parent[i] === i ? i : (parent[i] = find(parent[i]));
  }

  const cellOwner = new Map<string, number>();
  for (let i = 0; i < rawGroups.length; i++) {
    for (const cell of rawGroups[i].cells) {
      const key = `${cell.r},${cell.c}`;
      if (cellOwner.has(key)) {
        // Union the two groups that share this cell
        const a = find(i), b = find(cellOwner.get(key)!);
        if (a !== b) parent[a] = b;
      } else {
        cellOwner.set(key, i);
      }
    }
  }

  const merged = new Map<number, { cellSet: Set<string>; maxLen: number }>();
  for (let i = 0; i < rawGroups.length; i++) {
    const root = find(i);
    if (!merged.has(root)) merged.set(root, { cellSet: new Set(), maxLen: 0 });
    const m = merged.get(root)!;
    for (const cell of rawGroups[i].cells) m.cellSet.add(`${cell.r},${cell.c}`);
    m.maxLen = Math.max(m.maxLen, rawGroups[i].length);
  }

  return Array.from(merged.values()).map(m => ({
    length: m.maxLen,
    cells: Array.from(m.cellSet).map(k => {
      const [r, c] = k.split(",").map(Number);
      return { r, c };
    }),
  }));
}

/** Public: returns raw runs (used for hasAnyValidMove / initial board checks). */
export function findMatches(board: Board): MatchGroup[] {
  return findRawRuns(board);
}

// ── Swap helpers ──────────────────────────────────────────────────────────────

export function isAdjacent(a: Coord, b: Coord): boolean {
  return Math.abs(a.r - b.r) + Math.abs(a.c - b.c) === 1;
}

export function swap(board: Board, a: Coord, b: Coord): void {
  const t = board[a.r][a.c].type;
  board[a.r][a.c].type = board[b.r][b.c].type;
  board[b.r][b.c].type = t;
}

export function isSwapValid(board: Board, a: Coord, b: Coord): boolean {
  if (!isAdjacent(a, b)) return false;
  swap(board, a, b);
  const valid = findMatches(board).length > 0;
  swap(board, a, b); // restore
  return valid;
}

export function hasAnyValidMove(board: Board): boolean {
  const size = GameConfig.gridSize;
  for (let r = 0; r < size; r++)
    for (let c = 0; c < size; c++) {
      if (c + 1 < size && isSwapValid(board, { r, c }, { r, c: c + 1 })) return true;
      if (r + 1 < size && isSwapValid(board, { r, c }, { r: r + 1, c })) return true;
    }
  return false;
}

// ── Resolution loop ───────────────────────────────────────────────────────────

export function resolveBoard(board: Board, rng: RNG): ResolveResult {
  let cascades = 0;
  const events: MatchEvent[] = [];
  const size = GameConfig.gridSize;

  while (true) {
    const raw = findRawRuns(board);
    if (!raw.length) break;
    cascades++;

    // Merge overlapping runs so T/L shapes become one event
    const merged = mergeMatchGroups(raw);

    // Collect all cells to clear
    const clearSet = new Set<string>();
    for (const group of merged) {
      for (const cell of group.cells) clearSet.add(`${cell.r},${cell.c}`);
      events.push({ cleared: group.cells.length, matchLen: group.length });
    }

    // Clear
    for (const key of clearSet) {
      const [r, c] = key.split(",").map(Number);
      board[r][c].type = -1;
    }

    // Gravity: slide pieces down column by column, fill top with new pieces
    for (let c = 0; c < size; c++) {
      let write = size - 1;
      for (let r = size - 1; r >= 0; r--)
        if (board[r][c].type !== -1) board[write--][c].type = board[r][c].type;
      for (let r = write; r >= 0; r--)
        board[r][c].type = rng.int(GameConfig.candyTypes);
    }
  }

  return { cascades, events };
}

// ── Scoring ───────────────────────────────────────────────────────────────────

export function scoreEvents(
  mode: GameMode,
  events: MatchEvent[]
): { score: number; extraMoves: number } {
  let score = 0;
  let extraMoves = 0;

  for (const e of events) {
    if (mode === "moves") {
      // Simple scoring — no multiplier in v1
      score += GameConfig.basePerPiece * e.cleared;
      if (e.matchLen >= 4) extraMoves += GameConfig.extraMoves(e.matchLen);
    } else {
      // Time mode — multiplier = matchLen - 2 (min 1)
      const mult = Math.max(1, GameConfig.multiplier(e.matchLen));
      score += GameConfig.basePerPiece * e.cleared * mult;
    }
  }

  return { score, extraMoves };
}

// ── GameEngine (orchestrates everything) ─────────────────────────────────────

export class GameEngine {
  board: Board;
  rng: RNG;

  constructor(seed?: number) {
    this.rng = new RNG(seed);
    this.board = createInitialBoard(this.rng);
  }

  trySwap(mode: GameMode, a: Coord, b: Coord): SwapResult | null {
    if (!isSwapValid(this.board, a, b)) return null;

    swap(this.board, a, b);
    const result = resolveBoard(this.board, this.rng);
    const rewards = scoreEvents(mode, result.events);

    let reshuffled = false;
    if (!hasAnyValidMove(this.board)) {
      this.board = reshuffle(this.board, this.rng);
      reshuffled = true;
    }

    return {
      cascades: result.cascades,
      events: result.events,
      score: rewards.score,
      extraMoves: rewards.extraMoves,
      reshuffled,
    };
  }
}

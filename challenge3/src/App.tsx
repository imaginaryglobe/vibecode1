import React, { useState, useRef, useEffect, useCallback } from "react";
import { GameEngine } from "./engine";
import type { Coord, Board, MatchEvent } from "./engine";
import { GameConfig } from "./gameConfig";
import type { GameMode } from "./gameConfig";
import "./index.css";

// ── Types ─────────────────────────────────────────────────────────────────────

type Screen = "menu" | "game" | "gameover";
type MenuConfig = { mode: GameMode; moves: number; timeSeconds: number };
type GameResult = {
  score: number; mode: GameMode;
  matchesMade: number; biggestMatch: number; longestCascade: number;
};

// ── Persistence ───────────────────────────────────────────────────────────────

function getBest(mode: GameMode): number {
  return Number(localStorage.getItem(`cc_best_${mode}`) || 0);
}
function saveBest(mode: GameMode, score: number) {
  if (score > getBest(mode)) localStorage.setItem(`cc_best_${mode}`, String(score));
}
function getLastMode(): GameMode {
  return localStorage.getItem("cc_mode") === "time" ? "time" : "moves";
}
function saveLastMode(mode: GameMode) {
  localStorage.setItem("cc_mode", mode);
}

// ── Menu Screen ───────────────────────────────────────────────────────────────

function MenuScreen({ onStart }: { onStart: (cfg: MenuConfig) => void }) {
  const [mode, setMode] = useState<GameMode>(getLastMode());
  const [moves, setMoves] = useState(GameConfig.movesStart);
  const [secs, setSecs] = useState(GameConfig.timeStartSeconds);

  return (
    <div className="screen">
      <h1 className="title">CrushClone</h1>
      <p className="subtitle">Match-3 Puzzle</p>

      <div className="mode-row">
        <button className={`mode-btn${mode === "moves" ? " active" : ""}`}
          onClick={() => setMode("moves")}>Moves</button>
        <button className={`mode-btn${mode === "time" ? " active" : ""}`}
          onClick={() => setMode("time")}>Time</button>
      </div>

      <div className="settings-box">
        {mode === "moves" ? (
          <label>Starting Moves
            <input type="number" min={1} max={999} value={moves}
              onChange={e => setMoves(Math.max(1, Number(e.target.value)))} />
          </label>
        ) : (
          <label>Seconds
            <input type="number" min={10} max={600} value={secs}
              onChange={e => setSecs(Math.max(10, Number(e.target.value)))} />
          </label>
        )}
      </div>

      <div className="bests">
        <span>Best Moves: <b>{getBest("moves").toLocaleString()}</b></span>
        <span>Best Time: <b>{getBest("time").toLocaleString()}</b></span>
      </div>

      <button className="start-btn"
        onClick={() => { saveLastMode(mode); onStart({ mode, moves, timeSeconds: secs }); }}>
        Play
      </button>
    </div>
  );
}

// ── Game Screen ───────────────────────────────────────────────────────────────

function copyBoard(b: Board): Board {
  return b.map(row => row.map(cell => ({ ...cell })));
}

function GameScreen({ cfg, onGameOver }: { cfg: MenuConfig; onGameOver: (r: GameResult) => void }) {
  const engineRef = useRef<GameEngine | null>(null);
  const [board, setBoard] = useState<Board>([]);
  const [selected, setSelected] = useState<Coord | null>(null);
  const [snapCells, setSnapCells] = useState<Set<string>>(new Set());
  const [score, setScore] = useState(0);
  const [movesLeft, setMovesLeft] = useState(cfg.moves);
  const [timeMs, setTimeMs] = useState(cfg.timeSeconds * 1000);
  const [paused, setPaused] = useState(false);
  const [locked, setLocked] = useState(false);
  const [showShuffle, setShowShuffle] = useState(false);

  // Mutable refs to avoid stale closure issues in callbacks
  const scoreRef = useRef(0);
  const movesRef = useRef(cfg.moves);
  const firedRef = useRef(false);
  const statsRef = useRef({ matchesMade: 0, biggestMatch: 0, longestCascade: 0 });

  // Init engine once
  useEffect(() => {
    const eng = new GameEngine();
    engineRef.current = eng;
    setBoard(copyBoard(eng.board));
  }, []);

  // Timer (time mode only)
  useEffect(() => {
    if (cfg.mode !== "time" || paused || locked || !board.length) return;
    const id = setInterval(() => setTimeMs(t => Math.max(0, t - 100)), 100);
    return () => clearInterval(id);
  }, [cfg.mode, paused, locked, board.length]);

  const fireGameOver = useCallback(() => {
    if (firedRef.current) return;
    firedRef.current = true;
    saveBest(cfg.mode, scoreRef.current);
    onGameOver({ score: scoreRef.current, mode: cfg.mode, ...statsRef.current });
  }, [cfg.mode, onGameOver]);

  // Time-mode end
  useEffect(() => {
    if (cfg.mode === "time" && timeMs <= 0 && !locked) fireGameOver();
  }, [timeMs]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleClick = useCallback((r: number, c: number) => {
    if (locked || paused) return;
    const eng = engineRef.current;
    if (!eng) return;

    const clicked: Coord = { r, c };

    // No selection yet — select this cell
    if (!selected) { setSelected(clicked); return; }

    // Same cell — deselect
    if (selected.r === r && selected.c === c) { setSelected(null); return; }

    // Non-adjacent — re-select
    if (Math.abs(r - selected.r) + Math.abs(c - selected.c) !== 1) {
      setSelected(clicked);
      return;
    }

    // Adjacent — attempt swap
    setLocked(true);
    const prev = selected;
    setSelected(null);

    const result = eng.trySwap(cfg.mode, prev, clicked);

    if (!result) {
      // Invalid: snap-back animation, no move consumed
      const key = `${prev.r},${prev.c}`;
      const key2 = `${r},${c}`;
      setSnapCells(new Set([key, key2]));
      setTimeout(() => { setSnapCells(new Set()); setLocked(false); }, 300);
      return;
    }

    // Valid swap — update board and state
    setBoard(copyBoard(eng.board));

    const ns = scoreRef.current + result.score;
    scoreRef.current = ns;
    setScore(ns);

    statsRef.current.matchesMade += result.events.length;
    statsRef.current.longestCascade = Math.max(statsRef.current.longestCascade, result.cascades);
    for (const e of result.events)
      statsRef.current.biggestMatch = Math.max(statsRef.current.biggestMatch, e.matchLen);

    if (result.reshuffled) {
      setShowShuffle(true);
      setTimeout(() => setShowShuffle(false), 1800);
    }

    if (cfg.mode === "moves") {
      const nm = movesRef.current - 1 + result.extraMoves;
      movesRef.current = nm;
      setMovesLeft(nm);
    }

    setTimeout(() => {
      setLocked(false);
      if (cfg.mode === "moves" && movesRef.current <= 0) fireGameOver();
    }, 200);
  }, [selected, locked, paused, cfg.mode, fireGameOver]);

  if (!board.length) return <div className="screen">Loading…</div>;

  const timeSecs = timeMs / 1000;
  const timeLow = cfg.mode === "time" && timeSecs <= 10;
  const movesLow = cfg.mode === "moves" && movesLeft <= 5;

  return (
    <div className="screen">
      {/* HUD */}
      <div className="hud">
        <div className="hud-score">⭐ {score.toLocaleString()}</div>
        {cfg.mode === "moves"
          ? <div className={`hud-stat${movesLow ? " low" : ""}`}>🎯 {movesLeft}</div>
          : <div className={`hud-stat${timeLow ? " low" : ""}`}>⏱ {timeSecs.toFixed(1)}s</div>}
        <button className="pause-btn" onClick={() => setPaused(p => !p)}>
          {paused ? "▶" : "⏸"}
        </button>
      </div>

      {/* Board */}
      <div className="board">
        {board.map((row, r) =>
          row.map((cell, c) => {
            const key = `${r},${c}`;
            const isSel = selected?.r === r && selected?.c === c;
            const isSnap = snapCells.has(key);
            return (
              <div key={key}
                className={[
                  "candy", `candy-${cell.type}`,
                  isSel ? "selected" : "",
                  isSnap ? "snap" : "",
                  locked ? "locked" : "",
                ].filter(Boolean).join(" ")}
                onClick={() => handleClick(r, c)}
              />
            );
          })
        )}
      </div>

      {/* Pause overlay */}
      {paused && (
        <div className="overlay" onClick={() => setPaused(false)}>
          <div className="pause-box" onClick={e => e.stopPropagation()}>
            <h2>PAUSED</h2>
            <button onClick={() => setPaused(false)}>Resume</button>
          </div>
        </div>
      )}

      {showShuffle && <div className="toast">Shuffling board…</div>}
    </div>
  );
}

// ── Game Over Screen ──────────────────────────────────────────────────────────

function GameOverScreen({
  result, onRestart, onMenu,
}: { result: GameResult; onRestart: () => void; onMenu: () => void }) {
  const best = getBest(result.mode);
  const isRecord = result.score > 0 && result.score >= best;

  return (
    <div className="screen gameover">
      <h1 className="go-title">Game Over</h1>
      <div className="final-score">{result.score.toLocaleString()}</div>
      {isRecord && <div className="record">⭐ New Record!</div>}

      <div className="stats">
        <div className="stat">
          <span className="stat-val">{result.matchesMade}</span>
          <span className="stat-lbl">Matches</span>
        </div>
        <div className="stat">
          <span className="stat-val">{result.biggestMatch || "—"}</span>
          <span className="stat-lbl">Biggest</span>
        </div>
        <div className="stat">
          <span className="stat-val">{result.longestCascade}</span>
          <span className="stat-lbl">Cascade</span>
        </div>
      </div>

      <div className="best-line">Best ({result.mode}): <b>{best.toLocaleString()}</b></div>

      <div className="go-btns">
        <button className="btn-primary" onClick={onRestart}>Play Again</button>
        <button className="btn-secondary" onClick={onMenu}>Menu</button>
      </div>
    </div>
  );
}

// ── App (screen router) ───────────────────────────────────────────────────────

export default function App() {
  const [screen, setScreen] = useState<Screen>("menu");
  const [menuCfg, setMenuCfg] = useState<MenuConfig | null>(null);
  const [result, setResult] = useState<GameResult | null>(null);
  const [gameKey, setGameKey] = useState(0);

  if (screen === "menu") {
    return (
      <MenuScreen onStart={cfg => { setMenuCfg(cfg); setGameKey(k => k + 1); setScreen("game"); }} />
    );
  }

  if (screen === "game" && menuCfg) {
    return (
      <GameScreen
        key={gameKey}
        cfg={menuCfg}
        onGameOver={r => { setResult(r); setScreen("gameover"); }}
      />
    );
  }

  if (screen === "gameover" && result) {
    return (
      <GameOverScreen
        result={result}
        onRestart={() => { setGameKey(k => k + 1); setScreen("game"); }}
        onMenu={() => setScreen("menu")}
      />
    );
  }

  return null;
}

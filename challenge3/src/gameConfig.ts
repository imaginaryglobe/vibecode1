export type GameMode = "moves" | "time";

export const GameConfig = {
  gridSize: 8,
  candyTypes: 6,
  basePerPiece: 10,
  movesStart: 20,
  timeStartSeconds: 60,
  multiplier: (matchLen: number) => matchLen - 2,
  extraMoves: (matchLen: number) => matchLen - 3,
};

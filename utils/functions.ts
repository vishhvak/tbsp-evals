export const ms = (steps: number) => {
  const base = 16;
  const ratio = 1.25;
  return base * Math.pow(ratio, steps);
};
